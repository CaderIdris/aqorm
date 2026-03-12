import datetime as dt
from functools import partial

import numpy as np
import pandas as pd
import pytest
from sqlalchemy.engine.base import Engine

import aqorm.metadata as meta
import aqorm.query as query

from conftest import DBs

@pytest.mark.parametrize("db", list(DBs))
@pytest.mark.parametrize(
    "expected",
    [
        ("A1", {"NO": "no_test", "NO2": "no2_test", "O3": "o3_test"}),
        ("A2", {"NO": "no_test", "NO2": "no2_test", "O3": "o3_test"}),
        ("A3", {"NO": "no_test", "NO2": "no2_test", "O3": None}),
        ("A4", {"NO": "no_test", "NO2": None, "O3": "o3_test"}),
        ("A5", {"NO": None, "NO2": "no2_test", "O3": "o3_test"}),
        ("R1", {
            "NO": "no_test_r",
            "NO2": "no2_test_r",
            "O3": "o3_test_r",
            "PM10": "pm10_test_r",
        })
    ]
)
@pytest.mark.query
def test_get_headers_from_device_parameters_good(
    db: DBs,
    populated_connections: dict[DBs, Engine],
    expected: tuple[str, dict[str, str | None]],
):
    """"""
    conn_engine = populated_connections.get(db)
    if conn_engine is None:
        pytest.skip()
    metadata = meta.reflect_db(
        conn_engine,
        schema_name="query"
    )
    tests = {}
    device_name = expected[0]
    parameters = ("NO", "NO2", "O3", "PM10")
    expected_output = expected[1]
    output = query.get_headers_from_device_parameters(
        conn_engine,
        metadata,
        "query",
        device_name,
        parameters
    )
    print(output)
    for k, v in expected_output.items():
        tests[f"{k} result valid"] = v == output.get(k, np.nan)

    for test_name, outcome in tests.items():
        if not outcome:
            print(test_name)

    assert all(tests.values())


@pytest.mark.parametrize("db", list(DBs))
@pytest.mark.parametrize("empty_argument", ["parameters", "device"])
@pytest.mark.query
def test_get_headers_from_device_parameters_no_matches(
    db: DBs,
    populated_connections: dict[DBs, Engine],
    empty_argument: str
):
    """"""
    conn_engine = populated_connections.get(db)
    if conn_engine is None:
        pytest.skip()
    metadata = meta.reflect_db(
        conn_engine,
        schema_name="query"
    )
    tests = {}
    func = partial(
        query.get_headers_from_device_parameters,
        engine=conn_engine,
        metadata=metadata,
        schema_name="query",
        device="A1",
        parameters="NO"
    )
    extra = {empty_argument: "BAD"}
    output = func(  # type: ignore[misc]
        **extra  # type: ignore[arg-type]
    )
    for k, v in output.items():
        tests[f"{k} result valid"] = v is None

    for test_name, outcome in tests.items():
        if not outcome:
            print(test_name)

    assert all(tests.values())


@pytest.mark.parametrize("db", list(DBs))
@pytest.mark.query
def test_get_headers_from_device_parameters_bad_schema(
    db: DBs,
    empty_connections: dict[DBs, Engine]
):
    """"""
    conn_engine = empty_connections.get(db)
    if conn_engine is None:
        pytest.skip()
    metadata = meta.reflect_db(
        conn_engine,
        schema_name="empty"
    )
    with pytest.raises(
        ValueError,
        match=r"table could not be found in (empty|main) schema"
    ):
        _ = query.get_headers_from_device_parameters(
            conn_engine,
            metadata,
            "empty",
            "A1",
            "NO"
        )


@pytest.mark.parametrize("db", list(DBs))
@pytest.mark.parametrize(
    "devices_and_headers",
    [
        ("A1", {"NO": "no_test", "NO2": "no2_test", "O3": "o3_test"}),
        ("A2", {"NO": "no_test", "NO2": "no2_test", "O3": "o3_test"}),
        ("A3", {"NO": "no_test", "NO2": "no2_test"}),
        ("A4", {"NO": "no_test", "O3": "o3_test"}),
        ("A5", {"NO2": "no2_test", "O3": "o3_test"}),
        ("R1", {
            "NO": "no_test_r",
            "NO2": "no2_test_r",
            "O3": "o3_test_r",
            "PM10": "pm10_test_r",
        })
    ]
)
@pytest.mark.query
def test_get_measurements_good_no_colocation(
    db: DBs,
    populated_connections: dict[DBs, Engine],
    devices_and_headers: tuple[str, dict[str, str]],
):
    """"""
    conn_engine = populated_connections.get(db)
    if conn_engine is None:
        pytest.skip()
    metadata = meta.reflect_db(
        conn_engine,
        schema_name="query"
    )
    tests = {}
    device_name = devices_and_headers[0]
    headers = devices_and_headers[1]
    raw_output = query.get_measurements(
        conn_engine,
        metadata,
        "query",
        device_name,
        headers,
        dt.datetime(2020, 1, 1),
        dt.datetime(2022, 1, 1)
    )
    output = pd.DataFrame.from_dict(
        raw_output,
        orient="tight"
    )
    tests["Correct number of rows"] = output.shape[0] == 1000
    tests["Correct number of columns"] = output.shape[1] == len(headers)
    for param, col in zip(headers, output.columns, strict=True):
        tests[f"{param} ordered correctly"] = param == col

    for test_name, outcome in tests.items():
        if not outcome:
            print(test_name)

    assert all(tests.values())


@pytest.mark.parametrize("db", list(DBs))
@pytest.mark.query
def test_get_measurements_bad_schema_no_colocation(
    db: DBs,
    empty_connections: dict[DBs, Engine]
):
    """"""
    conn_engine = empty_connections.get(db)
    if conn_engine is None:
        pytest.skip()
    metadata = meta.reflect_db(
        conn_engine,
        schema_name="empty"
    )
    with pytest.raises(
        ValueError,
        match=r"table could not be found in (empty|main) schema"
    ):
        _ = query.get_measurements(
            conn_engine,
            metadata,
            "empty",
            "No device name needed",
            {"Not": "Needed"},
            dt.datetime(1990, 1, 1),
            dt.datetime(2100, 1, 1)
        )


@pytest.mark.parametrize("db", list(DBs))
@pytest.mark.query
def test_get_measurements_empty(
    db: DBs,
    populated_connections: dict[DBs, Engine]
):
    """"""
    conn_engine = populated_connections.get(db)
    if conn_engine is None:
        pytest.skip()
    metadata = meta.reflect_db(
        conn_engine,
        schema_name="query"
    )
    tests = {}
    device_name = "A1"
    headers = {
        "Bad": "Header",
        "Does": "Not",
        "Exist": "Here"
    }
    raw_output = query.get_measurements(
        conn_engine,
        metadata,
        "query",
        device_name,
        headers,
        dt.datetime(2020, 1, 1),
        dt.datetime(2022, 1, 1)
    )
    output = pd.DataFrame.from_dict(
        raw_output,
        orient="tight"
    )
    tests["Correct number of rows"] = output.shape[0] == 1000
    tests["Correct number of columns"] = output.shape[1] == len(headers)
    for param, col in zip(headers, output.columns, strict=True):
        tests[f"{param} ordered correctly"] = param == col

    tests["All values are None"] = output.isna().all(axis=None)

    for test_name, outcome in tests.items():
        if not outcome:
            print(test_name)

    assert all(tests.values())


@pytest.mark.parametrize("db", list(DBs))
@pytest.mark.query
def test_get_measurements_out_of_range(
    db: DBs,
    populated_connections: dict[DBs, Engine],
):
    """"""
    conn_engine = populated_connections.get(db)
    if conn_engine is None:
        pytest.skip()
    metadata = meta.reflect_db(
        conn_engine,
        schema_name="query"
    )
    tests = {}
    device_name = "A1"
    headers = {"NO": "no_test", "NO2": "no2_test", "O3": "o3_test"}
    raw_output = query.get_measurements(
        conn_engine,
        metadata,
        "query",
        device_name,
        headers,
        dt.datetime(2100, 1, 1),
        dt.datetime(2101, 1, 1)
    )
    output = pd.DataFrame.from_dict(
        raw_output,
        orient="tight"
    )
    tests["No rows"] = output.shape[0] == 0
    tests["Correct number of columns"] = output.shape[1] == len(headers)
    for param, col in zip(headers, output.columns, strict=True):
        tests[f"{param} ordered correctly"] = param == col

    for test_name, outcome in tests.items():
        if not outcome:
            print(test_name)

    assert all(tests.values())


@pytest.mark.parametrize("db", list(DBs))
@pytest.mark.parametrize(
    "devices_and_headers",
    [
        ("A1", {"NO": "no_test", "NO2": "no2_test", "O3": "o3_test"}, 1),
        ("A2", {"NO": "no_test", "NO2": "no2_test", "O3": "o3_test"}, 2),
        ("A3", {"NO": "no_test", "NO2": "no2_test"}, 3),
        ("A4", {"NO": "no_test", "O3": "o3_test"}, 4),
        ("A5", {"NO2": "no2_test", "O3": "o3_test"}, 5),
    ]
)
@pytest.mark.query
def test_get_measurements_good_colocation(
    db: DBs,
    populated_connections: dict[DBs, Engine],
    devices_and_headers: tuple[str, dict[str, str], int],
):
    """"""
    conn_engine = populated_connections.get(db)
    if conn_engine is None:
        pytest.skip()
    metadata = meta.reflect_db(
        conn_engine,
        schema_name="query"
    )
    tests = {}
    device_name = devices_and_headers[0]
    headers = devices_and_headers[1]
    expected_first_day = devices_and_headers[2]
    raw_output = query.get_measurements(
        conn_engine,
        metadata,
        "query",
        device_name,
        headers,
        dt.datetime(2020, 1, 1),
        dt.datetime(2022, 1, 1),
        colocated_with="R1"
    )
    output = pd.DataFrame.from_dict(
        raw_output,
        orient="tight"
    )

    all_expected_cols = (*headers, "Colocator")

    tests["Correct number of rows"] = output.shape[0] < 1000 and output.shape[0] > 0
    tests["Correct number of columns"] = output.shape[1] == len(headers) + 1
    for param, col in zip(all_expected_cols, output.columns, strict=True):
        tests[f"{param} ordered correctly"] = param == col

    tests["Correct first day"] = output.index.day[0] == expected_first_day
    tests["No empty colocator rows"] = not output["Colocator"].isna().any()
    tests["One Colocator"] = len(set(output["Colocator"])) == 1
    tests["Correct Colocator"] = set(output["Colocator"].unique()) == {"R1",}

    for test_name, outcome in tests.items():
        if not outcome:
            print(test_name)

    assert all(tests.values())


@pytest.mark.parametrize("db", list(DBs))
@pytest.mark.query
def test_get_measurements_colocator_does_not_exist(
    db: DBs,
    populated_connections: dict[DBs, Engine],
):
    """"""
    conn_engine = populated_connections.get(db)
    if conn_engine is None:
        pytest.skip()
    metadata = meta.reflect_db(
        conn_engine,
        schema_name="query"
    )
    tests = {}
    device_name = "A1"
    headers = {"NO": "no_test", "NO2": "no2_test", "O3": "o3_test"}
    raw_output = query.get_measurements(
        conn_engine,
        metadata,
        "query",
        device_name,
        headers,
        dt.datetime(2020, 1, 1),
        dt.datetime(2022, 1, 1),
        colocated_with="DOESN'T EXIST"
    )
    output = pd.DataFrame.from_dict(
        raw_output,
        orient="tight"
    )

    all_expected_cols = (*headers, "Colocator")

    tests["Correct number of rows"] = output.shape[0] == 0
    tests["Correct number of columns"] = output.shape[1] == len(headers) + 1
    for param, col in zip(all_expected_cols, output.columns, strict=True):
        tests[f"{param} ordered correctly"] = param == col

    for test_name, outcome in tests.items():
        if not outcome:
            print(test_name)

    assert all(tests.values())


@pytest.mark.parametrize("db", list(DBs))
@pytest.mark.query
def test_get_measurements_colocator_out_of_range(
    db: DBs,
    populated_connections: dict[DBs, Engine],
):
    """"""
    conn_engine = populated_connections.get(db)
    if conn_engine is None:
        pytest.skip()
    metadata = meta.reflect_db(
        conn_engine,
        schema_name="query"
    )
    tests = {}
    device_name = "A1"
    headers = {"NO": "no_test", "NO2": "no2_test", "O3": "o3_test"}
    raw_output = query.get_measurements(
        conn_engine,
        metadata,
        "query",
        device_name,
        headers,
        dt.datetime(2020, 1, 4, 0, 0, 1),
        dt.datetime(2022, 1, 1),
        colocated_with="R1"
    )
    output = pd.DataFrame.from_dict(
        raw_output,
        orient="tight"
    )

    all_expected_cols = (*headers, "Colocator")

    tests["Correct number of rows"] = output.shape[0] == 0
    tests["Correct number of columns"] = output.shape[1] == len(headers) + 1
    for param, col in zip(all_expected_cols, output.columns, strict=True):
        tests[f"{param} ordered correctly"] = param == col

    for test_name, outcome in tests.items():
        if not outcome:
            print(test_name)

    assert all(tests.values())


@pytest.mark.parametrize("db", list(DBs))
@pytest.mark.query
def test_get_measurements_two_colocators(
    db: DBs,
    populated_connections: dict[DBs, Engine]
):
    """"""
    conn_engine = populated_connections.get(db)
    if conn_engine is None:
        pytest.skip()
    metadata = meta.reflect_db(
        conn_engine,
        schema_name="query"
    )
    tests = {}
    device_name = "A5"
    headers = {"NO2": "no2_test", "O3": "o3_test"}
    raw_output = query.get_measurements(
        conn_engine,
        metadata,
        "query",
        device_name,
        headers,
        dt.datetime(2020, 1, 1),
        dt.datetime(2022, 1, 1),
        colocated_with=("R1", "R2")
    )
    output = pd.DataFrame.from_dict(
        raw_output,
        orient="tight"
    )

    all_expected_cols = (*headers, "Colocator")

    tests["Correct number of rows"] = output.shape[0] == 1000
    tests["Correct number of columns"] = output.shape[1] == len(headers) + 1
    for param, col in zip(all_expected_cols, output.columns, strict=True):
        tests[f"{param} ordered correctly"] = param == col

    tests["Correct first day"] = output.index.day[0] == 1
    tests["No empty colocator rows"] = not output["Colocator"].isna().any()
    tests["Two Colocators"] = output["Colocator"].nunique() == 2
    tests["Correct Colocators"] = set(output["Colocator"].unique()) == {"R2", "R1"}
    print(output["Colocator"])
    tests["Correct First"] = output["Colocator"][0] == "R2"
    tests["Correct Last"] = output["Colocator"][-1] == "R1"

    for test_name, outcome in tests.items():
        if not outcome:
            print(test_name)

    assert all(tests.values())
