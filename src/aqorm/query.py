"""Functions relating to querying measurement info from database."""
from collections import Counter, defaultdict
from collections.abc import Iterable
import datetime as dt
import logging
from typing import TypedDict

from sqlalchemy import desc, func, MetaData, select
from sqlalchemy.engine.base import Engine
from sqlalchemy.orm import aliased, Session

from .metadata import get_schema_name
from . import orm

_logger = logging.getLogger("aqorm")
_logger_level = _logger.getEffectiveLevel()

class StrictOrientation(TypedDict):
    """Structure of a dictionary, matching pandas strict orientation.

    Attributes
    ----------
    columns : list[str]
        The column names.
    data : list[tuple[float, ...]]
        All measurement values.
    index : list[dt.datetime]
        The dates of the measurements.
    index_names : list[str]
        The names of the index.
    column_names : list[str]
        The names of the column levels.

    """

    columns: list[str]
    data: list[tuple[float, ...]]
    index: list[dt.datetime]
    index_names: list[str]
    column_names: list[str]


def check_for_table(name: str, schema: str, metadata: MetaData) -> None:
    """Check if table exists.

    Parameters
    ----------
    name : str
        The name of the table.
    schema : str
        The schema the table should be in
    metadata : MetaData
        Metadata of database

    Raises
    ------
    ValueError
        Table not found

    """
    if f"{schema}.{name}" not in metadata.tables:
        #INFO: Skipping this in coverage as it's effectively tested by
        # previous check
        msg = (
            "dim_header table could not be found in "
            f"{schema} schema."
        )
        raise ValueError(msg)


def get_headers_from_device_parameters(
    engine: Engine,
    metadata: MetaData,
    schema_name: str,
    device: str,
    parameters: Iterable[str] | str,
) -> dict[str, str | None]:
    """Get corresponding headers for parameters a device is measuring.

    Parameters
    ----------
    engine : Engine
        The SQLAlchemy engine.
    metadata : MetaData
        Metadata associated with the database.
    schema_name : str
        Schema name of the database.
    device : str
        Name of the device.
    parameters : Iterable[str] | str
        The parameter(s) to find the headers for.

    Raises
    ------
        ValueError:
        - If bridge_device_header not in database.
        - If dim_header not in database.

    Returns
    -------
    dict[str, str | None]
        The parameters (key) and associated header (value).

    """
    schema_to_use = get_schema_name(engine, schema_name)
    _logger.debug(
        "Checking headers for %s measured by device %s.",
        parameters,
        device
    )
    if isinstance(parameters, str):
        params: set[str] = {parameters,}
    elif isinstance(parameters, Iterable):
        params = set(parameters)

    check_for_table("dim_header", schema_to_use, metadata)
    dim_header = orm.DimHeader

    check_for_table("dim_device", schema_to_use, metadata)
    dim_device = orm.DimDevice

    check_for_table("bridge_device_header", schema_to_use, metadata)
    bridge_device_header = orm.BridgeDeviceHeader

    select_statement = (
        select(
            dim_header.parameter,
            dim_header.header
        )
        .join(
            bridge_device_header,
            bridge_device_header.hash_header == dim_header.hash_header
        )
        .join(
            dim_device,
            bridge_device_header.hash_device == dim_device.hash_device
        )
        .where(
            dim_header.parameter.in_(params),
            dim_device.key == device
        )
        .order_by(
            desc(func.length(dim_header.header)),
            desc(dim_header.header)
        )
    )
    _logger.debug("%s", str(select_statement))
    with Session(bind=engine) as session:
        result = session.execute(select_statement).all()
        counts = Counter([row[0] for row in result])
        headers: dict[str, str | None] = {
            row[0]: row[1]
            for row
            in result
        }
    all_headers = defaultdict(list)
    if _logger_level == logging.DEBUG:
        for row in result:
            all_headers[row[0]].append(row[1])

    for param, param_count in counts.items():
        if param_count > 1:
            _logger.warning(
                "%s headers present for parameter %s, "
                "device %s. Defaulting to %s.",
                param_count,
                param,
                device,
                headers.get(param)
            )
        _logger.debug(
            "%s: %s",
            param,
            all_headers.get(param)
        )

    for param in params - set(headers.keys()):
        headers[param] = None

    return headers


def get_measurements(
    engine: Engine,
    metadata: MetaData,
    schema_name: str,
    device: str,
    headers: dict[str, str],
    time_start: dt.datetime,
    time_end: dt.datetime,
    colocated_with: str | Iterable[str] | None = None
) -> StrictOrientation:
    """Get measurements made by a device, filtering on colocation if necessary.

    Parameters
    ----------
    engine : Engine
        The SQLAlchemy engine.
    metadata : MetaData
        Metadata associated with the database.
    schema_name : str
        Schema name of the database.
    device : str
        Name of the device.
    headers : dict[str, str]
        The header(s) (values) to query and parameter(s) (keys) to use as
        labels.
    time_start : dt.datetime
        When to select measurements from (inclusive)
    time_end : dt.datetime
        When to select measurements until (exclusive)
    colocated_with : str | Iterable[str] | None, default=None
        Filter to only allow the co-located device(s). If None, all
        measurements returned.

    Raises
    ------
        ValueError:
        - If fact_measurement not in database.
        - If dim_colocation not in database.

    Returns
    -------
    StrictOrientation
        All measurements represented in "strict" orientation, recognised by
        pandas and others.

    """
    schema_to_use = get_schema_name(engine, schema_name)
    _logger.debug(
        "Querying measurements for device %s between %s and %s",
        device,
        time_start.strftime("%Y/%m/%d %H:%M:%S"),
        time_end.strftime("%Y/%m/%d %H:%M:%S"),
    )

    check_for_table("fact_measurement", schema_to_use, metadata)
    fact_measurement = orm.FactMeasurement

    if colocated_with is not None:
        check_for_table("dim_colocation", schema_to_use, metadata)
    dim_colocation = orm.DimColocation

    check_for_table("dim_device", schema_to_use, metadata)
    dim_device = aliased(orm.DimDevice)
    dim_device_other = aliased(orm.DimDevice)

    parameters = [
        fact_measurement.measurements[v].label(k)
        for k, v in headers.items()
    ]
    if colocated_with is not None:
        parameters.append(
            dim_device_other.name.label("Colocator")
        )

    select_stmt = (
        select(
            fact_measurement.time.label("Timestamp"),
            *parameters
        )
        .join(
            dim_device,
            dim_device.hash_device == fact_measurement.hash_device
        )
        .where(
            dim_device.key == device,
            fact_measurement.time >= time_start,
            fact_measurement.time < time_end
        )
        .order_by(
            fact_measurement.time
        )
    )
    if colocated_with is not None:
        if isinstance(colocated_with, str):
            colocated_devices = {colocated_with,}
        else:
            colocated_devices = set(colocated_with)
        select_stmt = (
            select_stmt
            .join(
                dim_colocation,
                dim_colocation.hash_device == fact_measurement.hash_device
            )
            .join(
                dim_device_other,
                dim_colocation.hash_other_device == dim_device_other.hash_device
            )
            .where(
                dim_device_other.key.in_(colocated_devices),
                fact_measurement.time >= dim_colocation.start_date,
                fact_measurement.time < dim_colocation.end_date
            )
        )

    with Session(bind=engine) as session:
        result = session.execute(select_stmt)
        columns = [
            k for k in result.keys()  # noqa: SIM118
            if k != "Timestamp"
        ]
        #INFO: Ignoring rule SIM118 as ruff seems to think the result is a
        # dictionary.
        data: StrictOrientation = {
            "columns": columns,
            "index_names": ["Timestamp"],
            "column_names": ["Parameters"],
            "data": [],
            "index": []
        }
        for row in result.all():
            data["index"].append(row[0])
            data["data"].append(tuple(row[1:]))
    return data
