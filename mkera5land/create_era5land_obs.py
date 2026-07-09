#!/usr/bin/env python3
"""
Create TSMP-PDAF observation files from ERA5-Land soil moisture.

Reads ERA5-Land daily mean volumetric soil water (swvl1) from a downloaded
NetCDF file and writes one TSMP-PDAF observation file per day of the month.

Two spatial modes are available:

  --location LAT LON
      Extract the single nearest ERA5-Land grid point and write one
      single-point observation per day (same format as the CRNS pipeline).
      The actual grid-point coordinates are written to the file, not the
      requested coordinates.

  (no --location)
      Write all valid grid points as a multi-observation file per day.
      Use --area N W S E to subset the domain before writing.

A file is written for every calendar day in the month. Days where all
values are NaN produce an empty file (no_obs=0), which tells TSMP-PDAF
there is no observation for that day while allowing the forward scan to
continue.

Usage:
    python mkera5land/create_era5land_obs.py 2018 1
    python mkera5land/create_era5land_obs.py 2018 1 --location 50.866 6.447
    python mkera5land/create_era5land_obs.py 2018 1 --area 52 6 50 7
    python mkera5land/create_era5land_obs.py 2018 1 --input-dir ./data --output-dir ./obs
"""

import argparse
import datetime
import os
import sys
import warnings
from pathlib import Path

import numpy as np
import netCDF4 as nc
import pandas as pd
import xarray as xr

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import utils.nc_attributes as pdaf_obs_utils

# Fixed reference epoch for the time variable, matching CF conventions.
TIME_UNITS = "days since 1900-01-01 00:00:00"
TIME_CALENDAR = "gregorian"
_STRLEN = 20


def _date_to_timevalue(date: datetime.date) -> float:
    """Convert a date to a float value relative to TIME_UNITS / TIME_CALENDAR."""
    dt = datetime.datetime(date.year, date.month, date.day, 0, 0, 0)
    return float(nc.date2num(dt, units=TIME_UNITS, calendar=TIME_CALENDAR))


def _write_empty_obs_file(
    dst_path: str, date: datetime.date, setup: str, script_name: str
):
    """Write an empty PDAF observation file (no_obs=0) for days without valid data.

    TSMP-PDAF scans observation files to determine the next assimilation step;
    an empty file (dim_obs present, no_obs=0) signals no observation for this
    day while still allowing the forward scan to continue.
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


def _write_obs_file(
    dst_path: str,
    date: datetime.date,
    lats: np.ndarray,
    lons: np.ndarray,
    values: np.ndarray,
    layer: int,
    dr: list,
    obs_type: str,
    setup: str,
    script_name: str,
):
    """Write a PDAF NetCDF observation file with one or more observations.

    Parameters
    ----------
    lats, lons, values : 1-D arrays of length N
        Observation locations and soil moisture values [m³/m³].
    layer : int
        CLM5 soil layer index (0-based).
    dr : list of two floats
        Localization radii [horizontal, vertical].
    obs_type : str
        Observation type string for type_clm (max 20 characters).
    """
    N = len(values)
    os.makedirs(os.path.dirname(dst_path), exist_ok=True)
    dst = nc.Dataset(dst_path, "w")
    pdaf_obs_utils.set_netcdf_attributes(dst, script_name, setup)

    dst.createDimension("time", 1)
    dst.createDimension("dim_obs", N)
    dst.createDimension("dim_dr", 2)
    dst.createDimension("strlen", _STRLEN)

    v_time = dst.createVariable("time", np.float64, ("time",))
    v_time.long_name = "time"
    v_time.units = TIME_UNITS
    v_time.calendar = TIME_CALENDAR
    v_time[0] = _date_to_timevalue(date)

    v_lat = dst.createVariable("lat", np.float32, ("dim_obs",))
    v_lon = dst.createVariable("lon", np.float32, ("dim_obs",))
    v_layer = dst.createVariable("layer", np.int32, ("dim_obs",))
    # dim_dr and dim_obs are also written as variables (in addition to being
    # dimensions). read_obs_nc_type in TSMP-PDAF only reads the dimension,
    # not the variable.
    v_dim_dr = dst.createVariable("dim_dr", np.int32, ("dim_dr",))
    v_dim_obs = dst.createVariable("dim_obs", np.int32, ("dim_obs",))
    # no_obs is used by the TSMP-PDAF routine `next_observation_pdaf` to
    # determine the next assimilation time step. Only the first element
    # is read (no_obs(1) in Fortran).
    v_no_obs = dst.createVariable("no_obs", np.int32, ("dim_obs",))
    v_dr = dst.createVariable("dr", np.float32, ("dim_dr",))
    v_obs_clm = dst.createVariable("obs_clm", np.float32, ("dim_obs",))
    # type_clm is read by read_obs_nc_type to filter observations by type in
    # joint DA runs. Must be NC_CHAR (S1 + strlen dim), not NC_STRING.
    v_type_clm = dst.createVariable("type_clm", "S1", ("dim_obs", "strlen"))

    v_lat.units = "degrees_north"
    v_lon.units = "degrees_east"

    v_lat[:] = lats.astype(np.float32)
    v_lon[:] = lons.astype(np.float32)
    v_layer[:] = layer
    v_dim_dr[:] = np.arange(1, 3)
    v_dim_obs[:] = np.arange(1, N + 1)
    v_no_obs[:] = N
    v_dr[:] = dr
    v_obs_clm[:] = values.astype(np.float32)

    padded = obs_type.ljust(_STRLEN)
    type_array = np.array([list(padded)] * N, dtype="S1")
    # netCDF4 ≤1.7.4 does `view.shape = ...` internally (deprecated in NumPy 2.5)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        v_type_clm[:] = type_array

    dst.close()


def main():
    parser = argparse.ArgumentParser(
        description="Create TSMP-PDAF observation files from ERA5-Land soil moisture",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("year", type=int, help="Year to process")
    parser.add_argument("month", type=int, help="Month to process (1-12)")
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("."),
        metavar="DIR",
        help="Directory containing downloaded ERA5-Land NetCDF files",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("."),
        metavar="DIR",
        help="Root output directory; files are written to OUTPUT_DIR/YEAR/",
    )
    parser.add_argument(
        "--era5land-var",
        default="swvl1",
        metavar="VAR",
        help="ERA5-Land NetCDF variable name to read",
    )
    parser.add_argument(
        "--location",
        type=float,
        nargs=2,
        metavar=("LAT", "LON"),
        default=None,
        help=(
            "Extract only the nearest ERA5-Land grid point to this location "
            "(e.g. --location 50.866 6.447 for Selhausen). "
            "If omitted, all valid grid points are written as multi-obs files."
        ),
    )
    parser.add_argument(
        "--area",
        type=float,
        nargs=4,
        metavar=("N", "W", "S", "E"),
        default=None,
        help=(
            "Spatial subset N W S E in degrees (ignored when --location is given)."
        ),
    )
    parser.add_argument(
        "--prefix",
        default="ERA5LAND_SM_CLM",
        help="Output filename prefix",
    )
    parser.add_argument(
        "--layer",
        type=int,
        default=0,
        help="CLM5 soil layer index (0-based) written to the observation file",
    )
    parser.add_argument(
        "--obs-type",
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

    args = parser.parse_args()

    if not (1 <= args.month <= 12):
        parser.error(f"month must be between 1 and 12, got {args.month}")

    monthstr = f"{args.month:02d}"
    input_file = args.input_dir / f"era5land_swvl1_{args.year}_{monthstr}.nc"

    if not input_file.exists():
        print(f"Input file not found: {input_file}", file=sys.stderr)
        print(
            f"Run download_era5land_sm.py --year {args.year} --month {monthstr} "
            f"--dirout {args.input_dir} first.",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"Loading {input_file}")
    ds = xr.open_dataset(input_file)

    if args.era5land_var not in ds:
        print(
            f"Variable '{args.era5land_var}' not found in {input_file}. "
            f"Available: {list(ds.data_vars)}",
            file=sys.stderr,
        )
        sys.exit(1)

    da = ds[args.era5land_var]

    # ERA5-Land uses 'latitude'/'longitude'; fall back to 'lat'/'lon'.
    lat_name = "latitude" if "latitude" in da.dims else "lat"
    lon_name = "longitude" if "longitude" in da.dims else "lon"

    script_name = Path(__file__).name
    n_written = 0
    n_empty = 0

    if args.location is not None:
        # --- Single nearest grid-point mode ---
        target_lat, target_lon = args.location
        da_point = da.sel(
            {lat_name: target_lat, lon_name: target_lon}, method="nearest"
        )
        actual_lat = float(da_point[lat_name])
        actual_lon = float(da_point[lon_name])
        print(
            f"Target location  : ({target_lat}, {target_lon})"
        )
        print(
            f"Nearest grid point: ({actual_lat:.4f}, {actual_lon:.4f})"
        )

        for t in da_point.time.values:
            date = pd.Timestamp(t).date()
            doy = date.timetuple().tm_yday
            dst_path = str(
                args.output_dir / str(args.year) / f"{args.prefix}.{doy:05d}"
            )

            value = float(da_point.sel(time=t).values)
            if np.isnan(value):
                _write_empty_obs_file(dst_path, date, args.setup, script_name)
                n_empty += 1
            else:
                _write_obs_file(
                    dst_path,
                    date,
                    np.array([actual_lat]),
                    np.array([actual_lon]),
                    np.array([value]),
                    args.layer,
                    args.dr,
                    args.obs_type,
                    args.setup,
                    script_name,
                )
                n_written += 1

    else:
        # --- Multi grid-point mode ---
        if args.area is not None:
            n, w, s, e = args.area
            # ERA5-Land latitude is ordered N→S (decreasing), so slice(N, S) is correct.
            da = da.sel({lat_name: slice(n, s), lon_name: slice(w, e)})
            print(f"Subsetting to area N={n}, W={w}, S={s}, E={e}")

        lat_vals = da[lat_name].values  # 1-D, N→S
        lon_vals = da[lon_name].values  # 1-D, W→E
        lat_2d, lon_2d = np.meshgrid(lat_vals, lon_vals, indexing="ij")
        print(f"Grid points in domain: {lat_2d.size}")

        for t in da.time.values:
            date = pd.Timestamp(t).date()
            doy = date.timetuple().tm_yday
            dst_path = str(
                args.output_dir / str(args.year) / f"{args.prefix}.{doy:05d}"
            )

            values_2d = da.sel(time=t).values  # shape (lat, lon)
            mask = ~np.isnan(values_2d)

            if not mask.any():
                _write_empty_obs_file(dst_path, date, args.setup, script_name)
                n_empty += 1
            else:
                _write_obs_file(
                    dst_path,
                    date,
                    lat_2d[mask],
                    lon_2d[mask],
                    values_2d[mask],
                    args.layer,
                    args.dr,
                    args.obs_type,
                    args.setup,
                    script_name,
                )
                n_written += 1

    print(
        f"Done: {n_written} observation files, {n_empty} empty files "
        f"(no_obs=0, all-NaN days)"
    )
    print(f"Output directory: {args.output_dir / str(args.year)}/")


if __name__ == "__main__":
    main()
