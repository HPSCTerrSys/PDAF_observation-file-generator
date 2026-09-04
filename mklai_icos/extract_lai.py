"""Extract the LAI (Leaf/Green/Plant Area Index) records from the ICOS
ancillary data file into a tidy Pandas DataFrame.

The source file ``ICOSETC_DE-RuS_ANCILLARY_L2.csv`` stores all ancillary
variables in long format: one row per (GROUP_ID, VARIABLE) pair, with the
actual value in DATAVALUE. Each LAI observation date is one GROUP_ID and
spans several rows (LAI, LAI_TYPE, LAI_STATISTIC, LAI_DATE, ...), as defined
in ``BIF_Ancillary_Variables.csv``. This module selects the rows belonging
to the "GRP_LAI" variable group and pivots them into one row per GROUP_ID.

Usage:
    python mklai_icos/extract_lai.py
    python mklai_icos/extract_lai.py --ancillary-csv /path/to/ICOSETC_DE-RuS_ANCILLARY_L2.csv
"""

import argparse
from pathlib import Path

import pandas as pd

_DEFAULT_ANCILLARY = Path(__file__).resolve().parent / "ICOSETC_DE-RuS_ANCILLARY_L2.csv"

# The ICOS BIF files are encoded as Latin-1, not UTF-8.
FILE_ENCODING = "latin1"


def load_lai_dataframe(csv_path: Path = _DEFAULT_ANCILLARY) -> pd.DataFrame:
    """Load the ANCILLARY_L2 CSV and extract the LAI variable group.

    Parameters
    ----------
    csv_path : Path
        Path to an ``ICOSETC_*_ANCILLARY_L2.csv`` file.

    Returns
    -------
    pd.DataFrame
        One row per LAI observation (indexed by GROUP_ID), sorted by date,
        with columns:

        - LAI_DATE : datetime64, the measurement date
        - LAI : float, the index value (m² m⁻²)
        - LAI_TYPE : str, "GAI" (green) or "PAI" (plant) area index
        - LAI_STATISTIC : str, e.g. "Mean", "Standard Deviation"
        - LAI_STATISTIC_NUMBER : int, number of samples the statistic is based on
        - LAI_METHOD : str, measurement method (e.g. "Direct", "SUNSCAN")
        - LAI_APPROACH, LAI_CANOPY_TYPE : str, further metadata
    """
    raw = pd.read_csv(csv_path, encoding=FILE_ENCODING)

    lai_long = raw[raw["VARIABLE_GROUP"] == "GRP_LAI"]

    # Long -> wide: one row per GROUP_ID, one column per VARIABLE.
    lai = lai_long.pivot(index="GROUP_ID", columns="VARIABLE", values="DATAVALUE")
    lai = lai.reset_index(drop=True)

    lai["LAI_DATE"] = pd.to_datetime(lai["LAI_DATE"], format="%Y%m%d")
    lai["LAI"] = lai["LAI"].astype(float)
    lai["LAI_STATISTIC_NUMBER"] = lai["LAI_STATISTIC_NUMBER"].astype(int)

    lai = lai.sort_values("LAI_DATE").reset_index(drop=True)
    lai.attrs["source_file"] = Path(csv_path)
    return lai


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Extract and print the LAI records from an ICOS ANCILLARY_L2 CSV",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--ancillary-csv",
        type=Path,
        default=_DEFAULT_ANCILLARY,
        metavar="ANCILLARY_CSV",
        help="Path to the ICOSETC_*_ANCILLARY_L2.csv file",
    )
    args = parser.parse_args()

    lai_df = load_lai_dataframe(args.ancillary_csv)
    print(f"Extracted {len(lai_df)} LAI records from {args.ancillary_csv.name}")
    print()
    with pd.option_context("display.max_rows", None, "display.max_columns", None):
        print(lai_df.to_string())
