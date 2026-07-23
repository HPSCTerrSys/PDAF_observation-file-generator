"""
Download the COSMOS-Europe CRNS dataset (revision 1) from TERENO.

The dataset is published under DOI 10.34731/x9s3-kr48 and distributed
via the TERENO data portal TEODOOR. The download is a zip archive
containing processed CRNS soil moisture data for 65 European stations.

Reference:
    Bogena, H. & Ney, P. (2024). Dataset of COSMOS-Europe: A European network
    of Cosmic-Ray Neutron Soil Moisture Sensors (Rev. 1).
    https://doi.org/10.34731/x9s3-kr48

Usage:
    from download_cosmos_europe import download_cosmos_europe
    data_dir = download_cosmos_europe()                        # downloads next to this file
    data_dir = download_cosmos_europe(dest_dir="/path/to/dir") # explicit destination
"""

import ssl
import sys
import urllib.request
import zipfile
from pathlib import Path
from typing import Optional


# Stable direct-download URL for revision 1 of the COSMOS-Europe dataset.
# Resolves from: https://hdl.handle.net/20.500.11952/butt.data.handle/00000066
_DOWNLOAD_URL = (
    "https://teodoor.icg.kfa-juelich.de/ibg3butt/ibg.butt.download"
    "?FileIdentifier=9d8abeaf-6633-4d0f-b55d-a4008c40a51b"
)

# Top-level directory name inside the zip archive and on disk after extraction.
DATASET_DIRNAME = "COSMOS_Europe_Data_rev1"

_DEFAULT_DEST_DIR = Path(__file__).parent.parent


def download_cosmos_europe(dest_dir: Optional[Path] = None) -> Path:
    """
    Download and extract the COSMOS-Europe dataset (revision 1).

    Downloads the zip archive from the TERENO data portal and extracts
    it into dest_dir. Skips the download if the dataset directory
    already exists.

    Parameters
    ----------
    dest_dir : Path, optional
        Directory into which the dataset folder is extracted.
        Defaults to the directory containing this module.

    Returns
    -------
    Path
        Path to the extracted dataset directory (dest_dir/COSMOS_Europe_Data_rev1).
    """
    dest_dir = Path(dest_dir) if dest_dir is not None else _DEFAULT_DEST_DIR
    data_dir = dest_dir / DATASET_DIRNAME

    if data_dir.exists():
        print(f"Dataset already present at: {data_dir}")
        return data_dir

    dest_dir.mkdir(parents=True, exist_ok=True)
    zip_path = dest_dir / "COSMOS_Europe_Data_rev1.zip"

    print(f"Downloading COSMOS-Europe dataset (revision 1) ...")
    print(f"  Source : {_DOWNLOAD_URL}")
    print(f"  Target : {zip_path}")
    print(
        "  Note: the server uses a self-signed certificate; "
        "verification is disabled for this download."
    )

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    try:
        with urllib.request.urlopen(_DOWNLOAD_URL, context=ctx) as response:
            total = response.headers.get("Content-Length")
            total_mb = f"{int(total) / 1e6:.1f} MB" if total else "unknown size"
            print(f"  Size   : {total_mb}")

            with open(zip_path, "wb") as f:
                downloaded = 0
                block = 1024 * 256  # 256 KB chunks
                while True:
                    chunk = response.read(block)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total:
                        pct = downloaded / int(total) * 100
                        print(f"\r  Progress: {pct:5.1f}%", end="", flush=True)
            print()  # newline after progress
    except Exception as exc:
        zip_path.unlink(missing_ok=True)
        print(f"Download failed: {exc}", file=sys.stderr)
        raise

    print(f"Extracting to {dest_dir} ...")
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(dest_dir)

    zip_path.unlink()
    print(f"Done. Dataset available at: {data_dir}")
    return data_dir


if __name__ == "__main__":
    download_cosmos_europe()
