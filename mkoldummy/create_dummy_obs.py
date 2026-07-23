#!/usr/bin/env python3
"""
Create a single dummy TSMP-PDAF observation file for open-loop / spin-up runs.

In open-loop mode TSMP-PDAF still reads the observation file to determine the
next assimilation step via ``next_observation_pdaf``.  An empty file
(no_obs=0) causes it to scan forward to the next file, which fails when only
one file is present.  This script therefore writes a file with no_obs=1 and a
placeholder observation value so that the forward scan terminates correctly,
while the actual DA update is suppressed by the settings in enkfpf.par.

The output file is observation time agnostic and intended to be placed
in obs/spinup/, decoupled from any real observation dataset.

Usage:
    python mkoldummy/create_dummy_obs.py
    python mkoldummy/create_dummy_obs.py --output-dir /path/to/obs/spinup
    python mkoldummy/create_dummy_obs.py --output-dir /path/to/obs/spinup --setup eclm_pdaf_derusww
"""

import argparse
import sys
import os
import warnings
from pathlib import Path

import datetime

import numpy as np
import netCDF4 as nc

# Make the shared utils package importable from the repository root,
# regardless of the working directory from which this script is called.
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import utils.nc_attributes as pdaf_obs_utils

# Fixed reference epoch for the time variable, matching CF conventions.
TIME_UNITS = "days since 1900-01-01 00:00:00"
TIME_CALENDAR = "gregorian"

# Placeholder timestamp: year-agnostic, just needs to be a valid date.
_DUMMY_DATE = datetime.date(1900, 1, 1)

# Default site coordinates (DE-RuS / Selhausen, matching the CRNS setup).
_DEFAULT_LAT = 50.865700
_DEFAULT_LON = 6.447100

# Default placeholder observation. Not used in OL mode.
_DEFAULT_SM = 0.0


def _date_to_timevalue(date: datetime.date) -> float:
    """Convert a date to a float value relative to TIME_UNITS / TIME_CALENDAR."""
    dt = datetime.datetime(date.year, date.month, date.day, 0, 0, 0)
    return float(nc.date2num(dt, units=TIME_UNITS, calendar=TIME_CALENDAR))


def create_dummy_obs_file(
    dst_path: str,
    lat: float,
    lon: float,
    sm_value: float,
    layer: int,
    dr: list,
    type_clm: str,
    setup: str,
    script_name: str,
):
    """Write a single dummy PDAF observation NetCDF file with no_obs=1."""
    os.makedirs(os.path.dirname(dst_path), exist_ok=True)
    dst = nc.Dataset(dst_path, "w")

    pdaf_obs_utils.set_netcdf_attributes(dst, script_name, setup)
    dst.setncattr("comment", (
        "Dummy observation file for open-loop / spin-up runs. "
        "no_obs=1 prevents next_observation_pdaf from scanning past this file; "
        "the DA update is suppressed by the settings in enkfpf.par."
    ))

    dst.createDimension("time", 1)
    dst.createDimension("dim_obs", 1)
    dst.createDimension("dim_dr", 2)
    strlen = 20
    dst.createDimension("strlen", strlen)

    v_time = dst.createVariable("time", np.float64, ("time",))
    v_time.long_name = "time"
    v_time.units = TIME_UNITS
    v_time.calendar = TIME_CALENDAR
    v_time[0] = _date_to_timevalue(_DUMMY_DATE)

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
        description=(
            "Create a single dummy TSMP-PDAF observation file for "
            "open-loop / spin-up runs (year-agnostic, no real data)."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("."),
        metavar="DIR",
        help="Directory in which to write the dummy observation file.",
    )
    parser.add_argument(
        "--prefix",
        default="DUMMY_OL_CLM",
        help="Output filename prefix (file is always written as PREFIX.00001).",
    )
    parser.add_argument(
        "--lat",
        type=float,
        default=_DEFAULT_LAT,
        help="Placeholder latitude [degrees_north].",
    )
    parser.add_argument(
        "--lon",
        type=float,
        default=_DEFAULT_LON,
        help="Placeholder longitude [degrees_east].",
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
        help="Observation type string written to type_clm.",
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
        "--sm-value",
        type=float,
        default=_DEFAULT_SM,
        metavar="SM",
        help="Placeholder soil moisture value [m³/m³] written to obs_clm.",
    )
    parser.add_argument(
        "--setup",
        default="undefined",
        help="Setup name stored in NetCDF global attributes",
    )

    args = parser.parse_args()

    dst_path = str(args.output_dir / f"{args.prefix}.00001")
    script_name = Path(__file__).name

    print(f"Writing dummy observation file: {dst_path}")
    print(f"  Timestamp : {_DUMMY_DATE} (year-agnostic placeholder)")
    print(f"  Lat/Lon   : {args.lat}, {args.lon}")
    print(f"  no_obs    : 1  (prevents next_observation_pdaf forward scan)")
    print(f"  obs_clm   : {args.sm_value} m³/m³  (placeholder, not used in OL)")

    create_dummy_obs_file(
        dst_path=dst_path,
        lat=args.lat,
        lon=args.lon,
        sm_value=args.sm_value,
        layer=args.layer,
        dr=args.dr,
        type_clm=args.type_clm,
        setup=args.setup,
        script_name=script_name,
    )

    print("Done.")


if __name__ == "__main__":
    main()
