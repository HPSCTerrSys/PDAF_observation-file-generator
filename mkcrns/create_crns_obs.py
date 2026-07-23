#!/usr/bin/env python3
"""
Create TSMP-PDAF observation files from CRNS (Cosmic-Ray Neutron
Sensor) data.

Reads processed CRNS soil moisture data from the COSMOS-Europe dataset
for a given station and year, and writes one NetCDF observation file
per day in the format used by TSMP-PDAF.

A file is written for every calendar day of the year. Days with
missing (NaN) soil moisture produce an empty file containing only
dim_obs and no_obs=0, which tells TSMP-PDAF there is no observation
for that day allowing TSMP-PDAF to scan forward to the next valid
observation file. Use --skip-flagged to additionally treat
quality-flagged hours as missing before computing the daily mean.

Usage:
    python mkcrns/create_crns_obs.py --download-data
    python mkcrns/create_crns_obs.py --download-data --crns-data-dir /path/to/dir
    python mkcrns/create_crns_obs.py SEC001 2018 --crns-data-dir /path/to/COSMOS_Europe_Data_rev1
    python mkcrns/create_crns_obs.py SEC001 2018 --output-dir /path/to/output
    python mkcrns/create_crns_obs.py SEC001 2018 --dr 0.004 0.003 --layer 1 --type-clm SM --skip-flagged
    python mkcrns/create_crns_obs.py --list-stations --crns-data-dir /path/to/COSMOS_Europe_Data_rev1
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

# Make the shared utils package and the cosmos_europe subpackage importable
# regardless of the working directory from which this script is called.
_REPO_ROOT = Path(__file__).resolve().parent.parent
_COSMOS_EUROPE = Path(__file__).resolve().parent / "cosmos_europe"
for _p in [str(_REPO_ROOT), str(_COSMOS_EUROPE)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from parse_crns_data import load_crns_data, list_available_stations
from download_cosmos_europe import download_cosmos_europe
import utils.nc_attributes as pdaf_obs_utils

# Fixed reference epoch for the time variable, matching CF conventions.
TIME_UNITS = "days since 1900-01-01 00:00:00"
TIME_CALENDAR = "gregorian"


def _date_to_timevalue(date: datetime.date) -> float:
    """Convert a date to a float value relative to TIME_UNITS / TIME_CALENDAR."""
    dt = datetime.datetime(date.year, date.month, date.day, 0, 0, 0)
    return float(nc.date2num(dt, units=TIME_UNITS, calendar=TIME_CALENDAR))


def _resample_daily(df: pd.DataFrame, obs_col: str, year: int) -> pd.Series:
    """Filter for year and compute daily mean of obs_col."""
    df_year = df[[obs_col]][df.index.year == year].copy()
    if df_year.index.tz is not None:
        df_year.index = df_year.index.tz_localize(None)
    return df_year[obs_col].resample("D").mean()


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
    sm_value: float,
    layer: int,
    dr: list,
    type_clm: str,
    setup: str,
    script_name: str,
):
    """Write a single-observation PDAF NetCDF file."""
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
    v_layer[0] = layer
    v_dim_dr[:] = np.arange(1, 3)
    v_dim_obs[:] = [1]
    v_no_obs[:] = 1
    v_dr[:] = dr
    v_obs_clm[0] = sm_value
    # netCDF4 ≤1.7.4 does `view.shape = ...` internally (deprecated in NumPy 2.5)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        v_type_clm[:] = np.array([list(type_clm.ljust(strlen))], dtype="S1")

    dst.close()


def main():
    parser = argparse.ArgumentParser(
        description="Create TSMP-PDAF observation files from CRNS soil moisture data",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "station_id",
        nargs="?",
        help="CRNS station ID (e.g., SEC001 for Selhausen)",
    )
    parser.add_argument(
        "year",
        nargs="?",
        type=int,
        help="Year to process",
    )
    parser.add_argument(
        "--crns-data-dir",
        type=Path,
        default=None,
        metavar="DIR",
        help=(
            "Root COSMOS-Europe data directory (the folder that contains "
            "General_information.csv and processed_crns_data_and_diagnostics/). "
            "Defaults to COSMOS_Europe_Data_rev1/ inside mkcrns/."
        ),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("."),
        metavar="DIR",
        help="Root output directory; files are written to OUTPUT_DIR/YEAR/",
    )
    parser.add_argument(
        "--prefix",
        default="CRNS_SM_CLM",
        help="Output filename prefix",
    )
    parser.add_argument(
        "--obs-var",
        default="SoilMoisture_volumetric_MovAvg24h",
        metavar="VAR",
        help="CRNS column to use as observation value",
    )
    parser.add_argument(
        "--layer",
        type=int,
        default=1,
        help="CLM5 soil layer index (0-based) written to the observation file",
    )
    parser.add_argument(
        "--type-clm",
        default="SM",
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
        metavar=("DR_H", "DR_V"),
        help="Localization radii [horizontal, vertical]",
    )
    parser.add_argument(
        "--setup",
        default="undefined",
        help="Setup name stored in NetCDF global attributes",
    )
    parser.add_argument(
        "--skip-flagged",
        action="store_true",
        help="Set quality-flagged hourly records to NaN before computing daily means",
    )
    parser.add_argument(
        "--list-stations",
        action="store_true",
        help="Print available CRNS stations and exit",
    )
    parser.add_argument(
        "--download-data",
        action="store_true",
        help=(
            "Download the COSMOS-Europe dataset (revision 1) from "
            "Forschungszentrum Jülich and exit. The dataset is extracted into "
            "--crns-data-dir if given, otherwise next to parse_crns_data.py."
        ),
    )

    args = parser.parse_args()

    if args.download_data:
        dest_dir = args.crns_data_dir.parent if args.crns_data_dir is not None else None
        download_cosmos_europe(dest_dir=dest_dir)
        sys.exit(0)

    if args.list_stations:
        print("Available CRNS stations:")
        print(list_available_stations(data_dir=args.crns_data_dir).to_string())
        sys.exit(0)

    if args.station_id is None or args.year is None:
        parser.error("station_id and year are required (unless --list-stations is used)")

    # Load CRNS data
    print(f"Loading CRNS data for station: {args.station_id}")
    df = load_crns_data(args.station_id, data_dir=args.crns_data_dir)
    metadata = df.attrs

    lat = float(metadata["latitude"])
    lon = float(metadata["longitude"])
    station_name = metadata.get("station_name", args.station_id)
    print(f"  Station: {station_name}")
    print(f"  Lat/Lon: {lat:.6f}, {lon:.6f}")
    print(f"  Records: {len(df)}")
    print(f"  Date range: {df.index.min()} to {df.index.max()}")

    # Apply quality flags
    flag_cols = [c for c in df.columns if c.startswith("Flag_")]
    if args.skip_flagged and flag_cols:
        flagged = df[flag_cols].any(axis=1)
        df.loc[flagged, args.obs_var] = np.nan
        print(f"  Masked {flagged.sum()} records due to quality flags")

    # Resample to daily means for the requested year
    daily_sm = _resample_daily(df, args.obs_var, args.year)

    if len(daily_sm) == 0:
        print(f"No data found for year {args.year}. Check the station's time period.")
        sys.exit(1)

    print(f"\nProcessing year {args.year} ({len(daily_sm)} calendar days)")

    script_name = Path(__file__).name
    n_written = 0
    n_empty = 0

    for date, sm_val in daily_sm.items():
        doy = date.timetuple().tm_yday  # 1-based day of year
        dst_path = str(
            args.output_dir / str(args.year) / f"{args.prefix}.{str(doy).zfill(5)}"
        )

        if np.isnan(sm_val):
            _create_empty_obs_file(dst_path, date, args.setup, script_name)
            n_empty += 1
        else:
            _create_obs_file(
                dst_path,
                date,
                lat,
                lon,
                float(sm_val),
                args.layer,
                args.dr,
                args.type_clm,
                args.setup,
                script_name,
            )
            n_written += 1

    print(
        f"Done: {n_written} observation files, {n_empty} empty files (no_obs=0, NaN/missing)"
    )
    print(f"Output directory: {args.output_dir / str(args.year)}/")


if __name__ == "__main__":
    main()
