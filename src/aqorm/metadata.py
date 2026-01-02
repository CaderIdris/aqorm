"""All functions relating to the metadata of an associated database."""
import logging
import re

from sqlalchemy import inspect, MetaData
from sqlalchemy.engine.base import Engine

_logger = logging.getLogger("aqorm")

def get_schema_name(engine: Engine, schema_name: str) -> str:
    """Get the proper schema name to use.

    When using SQLite, the schema name is always "main". This
    function checks if the specified schema name is present in
    the database and falls back to main if not.

    Parameters
    ----------
    engine : Engine
        The SQLALchemy engine.
    schema_name : str
        The expected schema name.

    Returns
    -------
    str
        The correct schema name.

    """
    _logger.debug("Checking schema name: %s", schema_name)
    inspector = inspect(engine)
    schema_names = inspector.get_schema_names()
    return (
        schema_name if any(schema_name in i for i in schema_names)
        else "main"
    )

def reflect_db(engine: Engine, schema_name: str) -> MetaData:
    """Reflect an existing database and return metadata.

    Parameters
    ----------
    engine : Engine
        The SQLALchemy engine.
    schema_name : str
        The schema name.

    Returns
    -------
    MetaData
        Info on objects in database.

    """
    schema_to_use = get_schema_name(engine, schema_name)
    _logger.debug("Reflecting schema: %s", schema_to_use)
    metadata = MetaData(schema=schema_to_use)
    metadata.reflect(bind=engine)
    return metadata


def get_table_names(engine: Engine, schema_name: str) -> list[str]:
    """Get all table names in schema.

    Parameters
    ----------
    engine : Engine
        The SQLALchemy engine.
    schema_name : str
        The schema name.

    Returns
    -------
    list[str]
        All table names.

    """
    table_metadata = reflect_db(engine, schema_name)
    table_names = [
        re.sub(r".*?\.", "", m) for m in table_metadata.tables
    ]
    _logger.debug("Table names present:\n- %s", "\n- ".join(table_names))
    return table_names


def validate_expected_tables(
    engine: Engine,
    schema_name: str = "measurement",
) -> None:
    """Check if all expected tables are present.

    Parameters
    ----------
    engine : Engine
        The SQLALchemy engine.
    schema_name : str, default="measurement"
        The schema name.

    Raises
    ------
        ValueError:
        - If expected tables aren't found

    """
    expected_tables = {
        "dim_device",
        "dim_header",
        "dim_colocation",
        "bridge_device_header",
        "dim_unit_conversion",
        "fact_measurement",
    }
    table_names = get_table_names(engine, schema_name)
    missing_tables = expected_tables - set(table_names)
    if len(missing_tables):
        _logger.error(
            "%s missing tables:\n- %s",
            len(missing_tables),
            "\n- ".join(missing_tables)
        )
        msg_list = ["Expected tables not found. Missing:", *missing_tables]
        msg = "\n- ".join(msg_list)
        raise ValueError(msg)
