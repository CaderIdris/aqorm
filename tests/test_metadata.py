import re

import pytest
from sqlalchemy.engine.base import Engine

import aqorm.metadata as meta

from conftest import DBs

@pytest.mark.parametrize("db", list(DBs))
@pytest.mark.metadata
def test_get_table_names(db: DBs, connections: dict[DBs, Engine]):
    """Not useful for funtionality of program, useful to check tests will work.

    """
    conn_engine = connections.get(db)
    if conn_engine is None:
        pytest.skip()
    tests = {}
    expected_tables = {
        "dim_device",
        "dim_header",
        "dim_colocation",
        "bridge_device_header",
        "dim_unit_conversion",
        "fact_measurement",
        "meta_files_processed"
    }
    actual_tables = set(
        meta.get_table_names(
            conn_engine,
            "measurement"
        )
    )
    tests["All expected tables"] = len(expected_tables ^ actual_tables) == 0

    for outcome in tests.values():
        if not outcome:
            pass

    assert all(tests.values())

@pytest.mark.parametrize("db", list(DBs))
@pytest.mark.metadata
def test_validate_expected_tables_good(db: DBs, connections: dict[DBs, Engine]):
    """

    """
    conn_engine = connections.get(db)
    if conn_engine is None:
        pytest.skip()
    tests = {}
    meta.validate_expected_tables(
        conn_engine
    )
    tests["Function ran"] = True

    for outcome in tests.values():
        if not outcome:
            pass

    assert all(tests.values())


@pytest.mark.parametrize("db", list(DBs))
@pytest.mark.metadata
def test_validate_expected_tables_empty(
    db: DBs,
    empty_connections: dict[DBs, Engine]
):
    """Not useful for funtionality of program, useful to check tests will work.

    """
    conn_engine = empty_connections.get(db)
    if conn_engine is None:
        pytest.skip()
    with pytest.raises(
        ValueError,
        match=r"Expected tables not found. Missing:"
    ):
        meta.validate_expected_tables(
            conn_engine,
            schema_name="empty"
        )


@pytest.mark.parametrize("db", list(DBs))
@pytest.mark.metadata
def test_reflect_db(
    db: DBs,
    connections: dict[DBs, Engine]
):
    """"""
    conn_engine = connections.get(db)
    if conn_engine is None:
        pytest.skip()
    tests = {}
    metadata = meta.reflect_db(
        conn_engine,
        schema_name="measurement"
    )
    expected_tables = {
        "dim_device",
        "dim_header",
        "dim_colocation",
        "bridge_device_header",
        "dim_unit_conversion",
        "fact_measurement",
        "meta_files_processed"
    }
    actual_tables = {
        re.sub(r"measurement\.|main\.", "", m) for m in metadata.tables
    }
    tests["All expected tables"] = len(expected_tables ^ actual_tables) == 0

    for outcome in tests.values():
        if not outcome:
            pass

    assert all(tests.values())
