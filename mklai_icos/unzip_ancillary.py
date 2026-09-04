"""Extract only the ANCILLARY_L2 CSV from the ICOS Archive ZIP.

The ICOS data portal delivers a wrapper ZIP containing a licence, a table of
contents, and the real archive ZIP as a nested entry. This script transparently
handles both the flat layout (CSV directly inside the ZIP) and the nested
layout (CSV inside a ZIP-within-a-ZIP), extracting only the
``ICOSETC_*_ANCILLARY_L2.csv`` file.

Usage:
    python mklai_icos/unzip_ancillary.py
    python mklai_icos/unzip_ancillary.py --zip /path/to/ICOSETC_DE-RuS_ARCHIVE_L2.zip
    python mklai_icos/unzip_ancillary.py --output-dir /path/to/output/
"""

import argparse
import io
import zipfile
from pathlib import Path

_DEFAULT_ZIP = Path(__file__).resolve().parent / "ICOSETC_DE-RuS_ARCHIVE_L2.zip"
_DEFAULT_OUT = Path(__file__).resolve().parent


def _find_ancillary(zf: zipfile.ZipFile):
    """Return (member_name, open_file) for the ANCILLARY_L2 CSV in *zf*.

    If the CSV is not found at the top level, the function looks for a nested
    ZIP entry (the wrapper layout used by the ICOS data portal) and searches
    inside it.

    Returns
    -------
    tuple[str, IO[bytes]]
        The bare filename and an open binary stream for the CSV content.

    Raises
    ------
    FileNotFoundError
        If no ``*ANCILLARY_L2.csv`` is found at either level.
    """
    members = zf.namelist()

    # --- flat layout: CSV is a direct member ---
    direct = [m for m in members if m.endswith("ANCILLARY_L2.csv")]
    if direct:
        name = direct[0]
        return Path(name).name, zf.open(name)

    # --- nested layout: one of the members is itself a ZIP ---
    nested_zips = [m for m in members if m.endswith(".zip")]
    for nested_name in nested_zips:
        inner_bytes = io.BytesIO(zf.read(nested_name))
        with zipfile.ZipFile(inner_bytes) as inner_zf:
            inner_members = inner_zf.namelist()
            inner = [m for m in inner_members if m.endswith("ANCILLARY_L2.csv")]
            if inner:
                name = inner[0]
                return Path(name).name, io.BytesIO(inner_zf.read(name))

    raise FileNotFoundError(
        f"No file matching '*ANCILLARY_L2.csv' found in {zf.filename} "
        f"(checked top-level and any nested ZIPs).\n"
        f"Top-level entries: {members}"
    )


def extract_ancillary(zip_path: Path, output_dir: Path) -> Path:
    """Extract the ANCILLARY_L2 CSV from *zip_path* into *output_dir*.

    Parameters
    ----------
    zip_path : Path
        Path to the ICOS archive ZIP file (flat or wrapper layout).
    output_dir : Path
        Directory where the extracted CSV will be written.

    Returns
    -------
    Path
        Path to the extracted CSV file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path) as zf:
        filename, stream = _find_ancillary(zf)
        target = output_dir / filename
        target.write_bytes(stream.read())

    print(f"Extracted: {target}")
    return target


def main():
    parser = argparse.ArgumentParser(
        description="Extract the ANCILLARY_L2 CSV from the ICOS Archive ZIP",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--zip",
        type=Path,
        default=_DEFAULT_ZIP,
        metavar="ZIP",
        help="Path to the ICOS Archive ZIP file",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=_DEFAULT_OUT,
        metavar="OUTPUT_DIR",
        help="Directory where the extracted CSV is written",
    )
    args = parser.parse_args()
    extract_ancillary(args.zip, args.output_dir)


if __name__ == "__main__":
    main()
