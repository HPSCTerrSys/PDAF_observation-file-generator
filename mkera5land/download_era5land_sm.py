#!/usr/bin/env python3
"""
Download ERA5-Land soil moisture data from Copernicus Climate Data Store (CDS).

Downloads the volumetric soil water layer 1 (swvl1) daily mean from the
'derived-era5-land-daily-statistics' dataset for a given year and month.

Requirements:
    - cdsapi library (pip install cdsapi)
    - CDS API credentials configured in ~/.cdsapirc

Usage:
    python mkera5land/download_era5land_sm.py --year 2018 --month 1 --dirout ./data
    python mkera5land/download_era5land_sm.py --year 2018 --month 1 --dirout ./data --area 52 6 50 7
    python mkera5land/download_era5land_sm.py --year 2018 --month 1 --dirout ./data --force
"""

import argparse
import calendar
import os
import sys
import tempfile
import zipfile
from pathlib import Path

import cdsapi


_DATASET = "derived-era5-land-daily-statistics"


def _generate_days(year: int, month: int) -> list:
    """Return zero-padded day strings for all days in the given month."""
    num_days = calendar.monthrange(year, month)[1]
    return [f"{d:02d}" for d in range(1, num_days + 1)]


def _detect_file_type(filepath) -> str:
    """Return '.nc', '.zip', or '.grib' based on magic bytes.

    Raises ValueError for unrecognized formats.
    """
    with open(filepath, "rb") as f:
        magic = f.read(8)
    if magic[:2] == b"PK":
        return ".zip"
    if magic[:3] == b"CDF" or magic[:4] == b"\x89HDF":
        return ".nc"
    if magic[:4] == b"GRIB":
        return ".grib"
    raise ValueError(
        f"Unrecognized file format for '{filepath}'. "
        f"Magic bytes: {magic.hex()}. "
        f"Expected NetCDF (CDF/HDF5), GRIB, or ZIP (PK) format."
    )


def download_era5land_sm(
    year: int,
    month: int,
    dirout: Path,
    area: list = None,
    force: bool = False,
) -> Path:
    """
    Download ERA5-Land daily mean swvl1 for a given year and month.

    Parameters
    ----------
    year : int
    month : int
    dirout : Path
        Output directory. Created if it does not exist.
    area : list of float, optional
        Bounding box [N, W, S, E] in degrees. Defaults to global.
    force : bool
        Re-download even if the output file already exists.

    Returns
    -------
    Path
        Path to the downloaded NetCDF file.
    """
    dirout = Path(dirout)
    dirout.mkdir(parents=True, exist_ok=True)

    monthstr = f"{month:02d}"
    output_path = dirout / f"era5land_swvl1_{year}_{monthstr}.nc"

    if output_path.exists() and not force:
        print(f"Output already exists, skipping: {output_path}")
        print("Use --force to re-download.")
        return output_path

    days = _generate_days(year, month)

    request = {
        "variable": ["volumetric_soil_water_layer_1"],
        "year": str(year),
        "month": monthstr,
        "day": days,
        "daily_statistic": "daily_mean",
        "time_zone": "utc+00:00",
        "frequency": "6_hourly",
        "area": area if area is not None else [90, -180, -90, 180],
    }

    print(f"Downloading ERA5-Land swvl1 daily mean for {year}-{monthstr}")
    print(f"  Dataset : {_DATASET}")
    print(f"  Area    : {request['area']} (N, W, S, E)")
    print(f"  Days    : {len(days)}")
    print(f"  Output  : {output_path}")

    client = cdsapi.Client()

    # Download to a temporary file; detect format by magic bytes before renaming.
    tmp_fd, tmp_path = tempfile.mkstemp(
        prefix=f"era5land_swvl1_{year}_{monthstr}_", dir=dirout
    )
    os.close(tmp_fd)

    try:
        client.retrieve(_DATASET, request, tmp_path)

        ext = _detect_file_type(tmp_path)

        if ext == ".zip":
            print("  Extracting zip archive ...")
            with zipfile.ZipFile(tmp_path, "r") as zf:
                nc_members = [m for m in zf.namelist() if m.endswith(".nc")]
                if len(nc_members) != 1:
                    raise ValueError(
                        f"Expected exactly one .nc file inside the zip, "
                        f"found: {nc_members}"
                    )
                extracted = zf.extract(nc_members[0], path=dirout)
            Path(tmp_path).unlink()
            Path(extracted).rename(output_path)
        elif ext == ".nc":
            Path(tmp_path).rename(output_path)
        else:
            raise ValueError(
                f"Unexpected file format '{ext}'. "
                "Only NetCDF (.nc) and ZIP (.zip) are supported."
            )
    except Exception:
        Path(tmp_path).unlink(missing_ok=True)
        raise

    print(f"Download complete: {output_path}")
    return output_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "Download ERA5-Land volumetric soil water layer 1 (swvl1) "
            "daily means from the Copernicus Climate Data Store."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--year", type=int, required=True, help="Year to download")
    parser.add_argument(
        "--month", type=int, required=True, help="Month to download (1-12)"
    )
    parser.add_argument(
        "--dirout", type=Path, required=True, help="Output directory"
    )
    parser.add_argument(
        "--area",
        type=float,
        nargs=4,
        metavar=("N", "W", "S", "E"),
        default=None,
        help="Spatial bounding box N W S E in degrees. Defaults to global.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-download even if the output file already exists.",
    )

    args = parser.parse_args()

    if not (1 <= args.month <= 12):
        parser.error(f"--month must be between 1 and 12, got {args.month}")

    download_era5land_sm(
        year=args.year,
        month=args.month,
        dirout=args.dirout,
        area=args.area,
        force=args.force,
    )
