"""Functions relating to querying measurement info from database."""
from collections import Counter, defaultdict
from collections.abc import Iterable
import datetime as dt
import logging
from typing import TypedDict

from sqlalchemy import desc, func, MetaData, select
from sqlalchemy.engine.base import Engine
from sqlalchemy.orm import Session

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

    if f"{schema_to_use}.bridge_device_header" not in metadata.tables:
        msg = (
            "bridge_device_header table could not be found in "
            f"{schema_to_use} schema."
        )
        raise ValueError(msg)
    bridge_device_header = orm.BridgeDeviceHeader

    if f"{schema_to_use}.dim_header" not in metadata.tables: # pragma: no cover
        #INFO: Skipping this in coverage as it's effectively tested by
        # previous check
        msg = (
            "dim_header table could not be found in "
            f"{schema_to_use} schema."
        )
        raise ValueError(msg)
    dim_header = orm.DimHeader

    select_statement = (
        select(
            dim_header.parameter,
            bridge_device_header.header
        )
        .where(
            dim_header.parameter.in_(params),
            bridge_device_header.device_key == device
        )
        .outerjoin(
            bridge_device_header,
            bridge_device_header.header == dim_header.header
        )
        .order_by(
            desc(func.length(bridge_device_header.header)),
            desc(bridge_device_header.header)
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

    if f"{schema_to_use}.fact_measurement" not in metadata.tables:
        msg = (
            "fact_measurement table could not be found in "
            f"{schema_to_use} schema."
        )
        raise ValueError(msg)
    fact_measurement = orm.FactMeasurement

    if (
        f"{schema_to_use}.dim_colocation" not in metadata.tables and
        colocated_with is not None
    ): # pragma: no cover
        #INFO: Skipping this in coverage as it's effectively tested by
        # previous check
        msg = (
            "dim_colocation table could not be found in "
            f"{schema_to_use} schema."
        )
        raise ValueError(msg)
    dim_colocation = orm.DimColocation

    parameters = [
        fact_measurement.measurements[v].label(k)
        for k, v in headers.items()
    ]
    if colocated_with is not None:
        parameters.append(
            dim_colocation.other_key.label("Colocator")
        )

    select_stmt = (
        select(
            fact_measurement.time.label("Timestamp"),
            *parameters
        )
        .where(
            fact_measurement.device_key == device,
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
                dim_colocation.device_key == fact_measurement.device_key
            )
            .where(
                dim_colocation.other_key.in_(colocated_devices),
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
