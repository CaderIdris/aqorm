import datetime as dt

import numpy as np
import pandas as pd

def dim_device() -> list[dict[str, str | bool | dict[str, str] | None]]:
    """"""
    return [
        {
            "key": "A1",
            "name": "A1",
            "short_name": "A1",
            "dataset": "Test",
            "reference": False,
            "other": {"test": "test"}
        },
        {
            "key": "A2",
            "name": "A2",
            "short_name": "A2",
            "dataset": "Test",
            "reference": False,
            "other": None
        },
        {
            "key": "A3",
            "name": "A3",
            "short_name": "A3",
            "dataset": "Test",
            "reference": False,
            "other": {"test": "test"}
        },
        {
            "key": "A4",
            "name": "A4",
            "short_name": "A4",
            "dataset": "Test",
            "reference": False,
            "other": None
        },
        {
            "key": "A5",
            "name": "A5",
            "short_name": "A5",
            "dataset": "Test",
            "reference": False,
            "other": None
        },
        {
            "key": "R1",
            "name": "R1",
            "short_name": "R1",
            "dataset": "Test",
            "reference": True,
            "other": {"test": "test"}
        },
        {
            "key": "R2",
            "name": "R2",
            "short_name": "R2",
            "dataset": "Test",
            "reference": True,
            "other": {"test": "test"}
        },
    ]


def dim_header() -> list[dict[str, str | bool | dict[str, str] | None]]:
    """"""
    return [
        {
            "header": "no_test",
            "parameter": "NO",
            "unit": "unit1",
            "other": {"test": "test"}
        },
        {
            "header": "no2_test",
            "parameter": "NO2",
            "unit": "unit1",
            "other": {"test": "test"}
        },
        {
            "header": "o3_test",
            "parameter": "O3",
            "unit": "unit1",
            "other": {"test": "test"}
        },
        {
            "header": "no_test_r",
            "parameter": "NO",
            "unit": "unit2",
            "other": {"test": "test"}
        },
        {
            "header": "no2_test_r",
            "parameter": "NO2",
            "unit": "unit2",
            "other": {"test": "test"}
        },
        {
            "header": "o3_test_r",
            "parameter": "O3",
            "unit": "unit2",
            "other": {"test": "test"}
        },
        {
            "header": "pm10_test_r",
            "parameter": "PM10",
            "unit": "unit2",
            "other": {"test": "test"}
        },
        {
            "header": "pm10_test_s",
            "parameter": "PM10",
            "unit": "unit2",
            "other": {"test": "test"}
        },
        {
            "header": "pm10_test_longer",
            "parameter": "PM10",
            "unit": "unit2",
            "other": {"test": "test"}
        },
    ]


def dim_unit_conversion() -> list[dict[str, str | float]]:
    """"""
    return [
        {
            "unit_in": "unit2",
            "unit_out": "unit3",
            "parameter": "NO",
            "scale": 2.0
        },
        {
            "unit_in": "unit2",
            "unit_out": "unit3",
            "parameter": "NO2",
            "scale": 3.0
        },
        {
            "unit_in": "unit2",
            "unit_out": "unit3",
            "parameter": "O3",
            "scale": 4.0
        }
    ]


def bridge_device_header() -> list[dict[str, str | None]]:
    """"""
    return [
        {
            "device_key": "A1",
            "header": "no_test",
            "flag": "no_test_flag"
        },
        {
            "device_key": "A2",
            "header": "no_test",
            "flag": "no_test_flag"
        },
        {
            "device_key": "A3",
            "header": "no_test",
            "flag": "no_test_flag"
        },
        {
            "device_key": "A4",
            "header": "no_test",
            "flag": "no_test_flag"
        },
        {
            "device_key": "R1",
            "header": "no_test_r",
            "flag": None
        },
        {
            "device_key": "A1",
            "header": "no2_test",
            "flag": "no2_test_flag"
        },
        {
            "device_key": "A2",
            "header": "no2_test",
            "flag": "no2_test_flag"
        },
        {
            "device_key": "A3",
            "header": "no2_test",
            "flag": "no2_test_flag"
        },
        {
            "device_key": "A5",
            "header": "no2_test",
            "flag": "no2_test_flag"
        },
        {
            "device_key": "R1",
            "header": "no2_test_r",
            "flag": None
        },
        {
            "device_key": "A1",
            "header": "o3_test",
            "flag": "o3_test_flag"
        },
        {
            "device_key": "A2",
            "header": "o3_test",
            "flag": "o3_test_flag"
        },
        {
            "device_key": "A4",
            "header": "o3_test",
            "flag": "o3_test_flag"
        },
        {
            "device_key": "A5",
            "header": "o3_test",
            "flag": "o3_test_flag"
        },
        {
            "device_key": "R1",
            "header": "o3_test_r",
            "flag": None
        },
        {
            "device_key": "R1",
            "header": "pm10_test_r",
            "flag": None
        },
        {
            "device_key": "R1",
            "header": "pm10_test_s",
            "flag": None
        },
        {
            "device_key": "R1",
            "header": "pm10_test_longer",
            "flag": None
        },
    ]


def fact_measurement(
    length: int = 1000,
) -> list[dict[str, dt.datetime | str | dict[str, float | str] | None]]:
    """"""
    devices = (
        ("A1", ( "no_test", "no2_test", "o3_test" ), True),
        ("A2", ( "no_test", "no2_test", "o3_test" ), True),
        ("A3", ( "no_test", "no2_test" ), True),
        ("A4", ( "no_test", "o3_test" ), True),
        ("A5", ( "no2_test", "o3_test" ), True),
        ("R1", (
            "no_test_r",
            "no2_test_r",
            "o3_test_r",
            "pm10_test_r",
            "pm10_test_s",
            "pm10_test_longer",
        ), False),
    )
    records = []
    rng = np.random.default_rng()
    dates = list(pd.date_range(
        start=dt.datetime(2020,1,1),
        periods=length,
        freq="15min"
    ))
    for device in devices:
        device_name = device[0]
        cols = device[1]
        use_flag = device[2]
        measurements = [
            i[1].to_dict() for i in
            pd.DataFrame(
                rng.standard_normal((length, len(cols))),
                columns=pd.Index(cols)
            )
            .iterrows()
        ]
        if use_flag:
            flags = [
                i[1].to_dict() for i in
                pd.DataFrame(
                    rng.choice(["Y", "N"], (length, len(cols)), p=(0.9, 0.1)),
                    columns=pd.Index([f"{i}_flag" for i in cols])
                )
                .iterrows()
            ]
        else:
            flags = [None for _ in range(length)]
        records.extend([
            {
                "time": t,
                "device_key": device_name,
                "measurements": m,
                "flags": f,
                "meta": None,
            }
            for t, m, f in zip(dates, measurements, flags, strict=False)
        ])
    return records


def dim_colocation() -> list[dict[str, str | dt.datetime | None]]:
    """"""
    return [
        {
            "device_key": "A1",
            "other_key": "R1",
            "start_date": dt.datetime(2020, 1, 1),
            "end_date": dt.datetime(2020, 1, 4),
        },
        {
            "device_key": "A2",
            "other_key": "R1",
            "start_date": dt.datetime(2020, 1, 2),
            "end_date": dt.datetime(2020, 1, 5),
        },
        {
            "device_key": "A3",
            "other_key": "R1",
            "start_date": dt.datetime(2020, 1, 3),
            "end_date": dt.datetime(2020, 1, 6),
        },
        {
            "device_key": "A4",
            "other_key": "R1",
            "start_date": dt.datetime(2020, 1, 4),
            "end_date": dt.datetime(2020, 1, 7),
        },
        {
            "device_key": "A5",
            "other_key": "R1",
            "start_date": dt.datetime(2020, 1, 5),
            "end_date": dt.datetime(2022, 1, 1),
        },
        {
            "device_key": "A5",
            "other_key": "R2",
            "start_date": dt.datetime(2020, 1, 1),
            "end_date": dt.datetime(2020, 1, 4, 23, 59, 59),
        },
    ]


