#!/usr/bin/env python3
"""
Create TSMP-PDAF observation files from Sentinel-2 LAI time series data.

Reads LAI values from a two-column CSV file (ts_date, ts_lai) for a single
site and writes one NetCDF observation file per day in the format used by
TSMP-PDAF.

A file is written for every calendar day of the requested year. Days without
an observation produce an empty file containing only dim_obs and no_obs=0,
which tells TSMP-PDAF there is no observation for that day, allowing it to
scan forward to the next valid observation file.

Usage:
    python mklai/create_lai_obs.py 2018
    python mklai/create_lai_obs.py 2018 --lai-csv mklai/S2_LAI_timeseries_CPP_10.csv
    python mklai/create_lai_obs.py 2018 --output-dir /path/to/output --prefix LAI_CLM
    python mklai/create_lai_obs.py 2018 --lat 50.865886 --lon 6.447111 --dr 0.004 0.003
"""

import argparse
import sys
import os
import warnings
from pathlib import Path

import datetime

import numpy as np
import netCDF4 as nc
import pandas as pd

# Make the shared utils package importable regardless of working directory.
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import utils.nc_attributes as pdaf_obs_utils

# Fixed reference epoch for the time variable, matching CF conventions.
TIME_UNITS = "days since 1900-01-01 00:00:00"
TIME_CALENDAR = "gregorian"

# Selhausen field site coordinates (DE-RuS)
_DEFAULT_LAT = 50.865886
_DEFAULT_LON = 6.447111

# Default LAI CSV path relative to the repository root
_DEFAULT_CSV = Path(__file__).resolve().parent / "S2_LAI_timeseries_CPP_10.csv"


def _date_to_timevalue(date: datetime.date) -> float:
    """Convert a date to a float value relative to TIME_UNITS / TIME_CALENDAR."""
    dt = datetime.datetime(date.year, date.month, date.day, 0, 0, 0)
    return float(nc.date2num(dt, units=TIME_UNITS, calendar=TIME_CALENDAR))


def _load_lai_csv(csv_path: Path) -> pd.Series:
    """Load LAI CSV and return a Series indexed by date.

    The CSV is expected to have two columns: ts_date (DD/MM/YYYY) and ts_lai.
    """
    df = pd.read_csv(csv_path, parse_dates=["ts_date"], dayfirst=True)
    series = df.set_index("ts_date")["ts_lai"]
    series.index = series.index.normalize()  # strip any time component
    return series


def _create_empty_obs_file(
    dst_path: str, date: datetime.date, setup: str, script_name: str
):
    """Write an empty PDAF observation file (no_obs=0) for days without valid data.

    TSMP-PDAF scans observation files to determine the next assimilation step;
    an empty file (dim_obs present, no_obs=0) signals no observation for this day
    while still allowing the forward scan to continue.
    """
    os.makedirs(os.path.dirname(dst_path), exist_ok=True)
    dst = nc.Dataset(dst_path, "w")

    pdaf_obs_utils.set_netcdf_attributes(dst, script_name, setup)

    dst.createDimension("time", 1)
    dst.createDimension("dim_obs", 1)

    v_time = dst.createVariable("time", np.float64, ("time",))
    v_time.long_name = "time"
    v_time.units = TIME_UNITS
    v_time.calendar = TIME_CALENDAR
    v_time[0] = _date_to_timevalue(date)

    v_no_obs = dst.createVariable("no_obs", np.int32, ("dim_obs",))
    v_no_obs[:] = 0

    dst.close()


def _create_obs_file(
    dst_path: str,
    date: datetime.date,
    lat: float,
    lon: float,
    lai_value: float,
    dr: list,
    type_clm: str,
    setup: str,
    script_name: str,
):
    """Write a single-observation PDAF NetCDF file for one LAI value."""
    os.makedirs(os.path.dirname(dst_path), exist_ok=True)
    dst = nc.Dataset(dst_path, "w")

    pdaf_obs_utils.set_netcdf_attributes(dst, script_name, setup)

    dst.createDimension("time", 1)
    dst.createDimension("dim_obs", 1)
    dst.createDimension("dim_dr", 2)
    strlen = 20
    dst.createDimension("strlen", strlen)

    v_time = dst.createVariable("time", np.float64, ("time",))
    v_time.long_name = "time"
    v_time.units = TIME_UNITS
    v_time.calendar = TIME_CALENDAR
    v_time[0] = _date_to_timevalue(date)

    v_lat = dst.createVariable("lat", np.float32, ("dim_obs",))
    v_lon = dst.createVariable("lon", np.float32, ("dim_obs",))
    v_layer = dst.createVariable("layer", np.int32, ("dim_obs",))
    # dim_dr and dim_obs are also written as variables (in addition to being
    # dimensions). Reason is unclear to the author.
    # read_obs_nc_type in TSMP-PDAF only reads the dimension, not the variable.
    v_dim_dr = dst.createVariable("dim_dr", np.int32, ("dim_dr",))
    v_dim_obs = dst.createVariable("dim_obs", np.int32, ("dim_obs",))
    # no_obs is not read by read_obs_nc_type; it is used by the
    # TSMP-PDAF routine `next_observation_pdaf` that determines the
    # next assimilation time step.
    v_no_obs = dst.createVariable("no_obs", np.int32, ("dim_obs",))
    v_dr = dst.createVariable("dr", np.float32, ("dim_dr",))
    v_obs_clm = dst.createVariable("obs_clm", np.float32, ("dim_obs",))
    # type_clm is read by read_obs_nc_type to filter observations by type in
    # joint DA runs where multiple observation files may be present.
    # Must be NC_CHAR (S1 + strlen dim), not NC_STRING, so Fortran's
    # nf90_get_var into character(len=20) does not raise a text/number
    # conversion error.
    v_type_clm = dst.createVariable("type_clm", "S1", ("dim_obs", "strlen"))

    v_lat.units = "degrees_north"
    v_lon.units = "degrees_east"

    v_lat[0] = lat
    v_lon[0] = lon
    v_layer[0] = 1  # no soil layer concept for LAI; 1 written for
                    # compatibility with init_dim_obs
    v_dim_dr[:] = np.arange(1, 3)
    v_dim_obs[:] = [1]
    v_no_obs[:] = 1
    v_dr[:] = dr
    v_obs_clm[0] = lai_value
    # netCDF4 ≤1.7.4 does `view.shape = ...` internally (deprecated in NumPy 2.5)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        v_type_clm[:] = np.array([list(type_clm.ljust(strlen))], dtype="S1")

    dst.close()


def main():
    parser = argparse.ArgumentParser(
        description="Create TSMP-PDAF observation files from Sentinel-2 LAI time series",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "year",
        type=int,
        metavar="YEAR",
        help="Year to process",
    )
    parser.add_argument(
        "--lai-csv",
        type=Path,
        default=_DEFAULT_CSV,
        metavar="LAI_CSV",
        help="Path to the LAI CSV file (columns: ts_date, ts_lai)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("."),
        metavar="OUTPUT_DIR",
        help="Root output directory; files are written to OUTPUT_DIR/YEAR/",
    )
    parser.add_argument(
        "--prefix",
        default="LAI_CLM",
        metavar="PREFIX",
        help="Output filename prefix",
    )
    parser.add_argument(
        "--lat",
        type=float,
        default=_DEFAULT_LAT,
        metavar="LAT",
        help="Station latitude [degrees_north]",
    )
    parser.add_argument(
        "--lon",
        type=float,
        default=_DEFAULT_LON,
        metavar="LON",
        help="Station longitude [degrees_east]",
    )
    parser.add_argument(
        "--type-clm",
        default="LAI",
        metavar="TYPE",
        help=(
            "Observation type string written to type_clm; must match the "
            "current_observation_type passed to TSMP-PDAF with OMI "
            "so that observations are not silently skipped in joint DA runs"
        ),
    )
    parser.add_argument(
        "--dr",
        type=float,
        nargs=2,
        default=[0.00387525, 0.002500534],
        metavar=("DR_LON", "DR_LAT"),
        help="Snapping distances [longitude, latitude]",
    )
    parser.add_argument(
        "--setup",
        default="undefined",
        help="Setup name stored in NetCDF global attributes",
    )

    args = parser.parse_args()

    # Load LAI data
    print(f"Loading LAI data from: {args.lai_csv}")
    lai_series = _load_lai_csv(args.lai_csv)
    print(f"  Records: {len(lai_series)}")
    print(f"  Date range: {lai_series.index.min().date()} to {lai_series.index.max().date()}")

    # Filter to requested year for reporting; actual lookup is by date
    year_mask = lai_series.index.year == args.year
    n_obs_in_year = year_mask.sum()
    print(f"  Observations in {args.year}: {n_obs_in_year}")
    print(f"  Lat/Lon: {args.lat:.6f}, {args.lon:.6f}")

    # Build a date-keyed lookup for O(1) access in the loop
    lai_by_date = {ts.date(): val for ts, val in lai_series.items()}

    # Determine number of calendar days in the requested year
    is_leap = (args.year % 4 == 0 and args.year % 100 != 0) or (args.year % 400 == 0)
    days_in_year = 366 if is_leap else 365

    print(f"\nProcessing year {args.year} ({days_in_year} calendar days)")

    script_name = Path(__file__).name
    n_written = 0
    n_empty = 0

    for doy in range(1, days_in_year + 1):
        date = (datetime.date(args.year, 1, 1) + datetime.timedelta(days=doy - 1))
        dst_path = str(
            args.output_dir / str(args.year) / f"{args.prefix}.{str(doy).zfill(5)}"
        )

        lai_val = lai_by_date.get(date, np.nan)

        if np.isnan(lai_val):
            _create_empty_obs_file(dst_path, date, args.setup, script_name)
            n_empty += 1
        else:
            _create_obs_file(
                dst_path,
                date,
                args.lat,
                args.lon,
                float(lai_val),
                args.dr,
                args.type_clm,
                args.setup,
                script_name,
            )
            n_written += 1

    print(
        f"Done: {n_written} observation files, {n_empty} empty files (no_obs=0, no LAI on that day)"
    )
    print(f"Output directory: {args.output_dir / str(args.year)}/")


if __name__ == "__main__":
    main()
