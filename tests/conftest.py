from enum import auto, Flag
from pathlib import Path
from typing import Any, TYPE_CHECKING

from docker.errors import DockerException
import pytest
from sqlalchemy.engine.base import Engine
from sqlalchemy.dialects.postgresql import insert
from testcontainers.postgres import PostgresContainer

import aqorm.orm as orm
from t_utils import build_tables as bt
import aqorm.engine as engine

if TYPE_CHECKING:
    from collections.abc import Callable

try:
    postgres = PostgresContainer("postgres:18-alpine", driver="psycopg")
except (ImportError, DockerException):
    postgres = None

if postgres is not None:
    @pytest.fixture(scope="session", autouse=True)
    def setup(request) -> None:
        """Setup the postgres docker container."""
        if postgres is not None:
            postgres.start()

        def remove_container() -> None:
            if postgres is not None:
                postgres.stop()

        request.addfinalizer(remove_container)  # noqa: PT021


class DBs(Flag):
    """DBs to test with the ORM."""

    SQLite = auto()
    DuckDB = auto()
    PostgreSQL = auto()


@pytest.fixture(scope="session")
def db_path(tmp_path_factory):
    """Path to the test database."""
    return tmp_path_factory.mktemp("db")


@pytest.fixture(scope="session")
def connections(db_path: Path) -> dict[DBs, Engine]:
    db_path_sqlite = db_path / "sqlite.db"
    db_path_duckdb = db_path / "duckdb.db"
    engines = {
        DBs.SQLite: engine.get_engine(f"sqlite+pysqlite:///{db_path_sqlite}"),
        DBs.DuckDB: engine.get_engine(f"duckdb:///{db_path_duckdb}"),
    }
    if postgres is not None:
        engines[DBs.PostgreSQL] = engine.get_engine(
            postgres.get_connection_url()
        )
    for db_engine in engines.values():
        orm._BaseV1.metadata.create_all(db_engine)  #noqa: SLF001
    return engines


@pytest.fixture(scope="session")
def populated_connections(db_path: Path) -> dict[DBs, Engine]:
    db_path_sqlite = db_path / "sqlite_populated.db"
    db_path_duckdb = db_path / "duckdb.db"
    engines = {
        DBs.SQLite: engine.get_engine(f"sqlite+pysqlite:///{db_path_sqlite}"),
        DBs.DuckDB: engine.get_engine(
            f"duckdb:///{db_path_duckdb}",
            schema_name="query"

        ),
    }
    if postgres is not None:
        engines[DBs.PostgreSQL] = engine.get_engine(
            postgres.get_connection_url(),
            schema_name="query"
        )
    for db_engine in engines.values():
        orm._BaseV1.metadata.create_all(db_engine)  #noqa: SLF001
        build_tables(db_engine)
    return engines


@pytest.fixture(scope="session")
def empty_connections(db_path: Path) -> dict[DBs, Engine]:
    db_path_sqlite = db_path / "empty_sqlite.db"
    db_path_duckdb = db_path / "duckdb.db"
    engines = {
        DBs.SQLite: engine.get_engine(
            f"sqlite+pysqlite:///{db_path_sqlite}"
        ),
        DBs.DuckDB: engine.get_engine(
            f"duckdb:///{db_path_duckdb}",
            schema_name="empty"
        ),
    }
    if postgres is not None:
        engines[DBs.PostgreSQL] = engine.get_engine(
            postgres.get_connection_url(),
            schema_name="empty"
        )
    return engines


def build_tables(conn_engine: Engine) -> None:
    """"""
    tables: tuple[tuple[Any, Callable[..., Any]], ...] = (
        (orm.DimDevice, bt.dim_device),
        (orm.DimHeader, bt.dim_header),
        (orm.DimUnitConversion, bt.dim_unit_conversion),
        (orm.BridgeDeviceHeader, bt.bridge_device_header),
        (orm.FactMeasurement, bt.fact_measurement),
        (orm.DimColocation, bt.dim_colocation)
    )
    for table in tables:
        insert_statement = insert(table[0]).on_conflict_do_nothing()
        with conn_engine.connect() as conn:
            conn.execute(
                insert_statement.values(table[1]())
            )
            conn.commit()

