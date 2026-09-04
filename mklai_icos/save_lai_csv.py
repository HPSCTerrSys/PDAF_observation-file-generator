"""Save mean ICOS LAI values to a CSV compatible with create_lai_obs.py.

Filters the DataFrame from :mod:`extract_lai` to rows where
``LAI_STATISTIC == "Mean"`` and, optionally, to a specific ``LAI_TYPE``
("GAI" or "PAI"). The output CSV uses the same two-column format as
``mklai/S2_LAI_timeseries_CPP_10.csv``:

    ts_date,ts_lai
    22/02/2018,1.23
    ...

where ``ts_date`` is formatted as DD/MM/YYYY, so that the file can be passed
directly to ``mklai/create_lai_obs.py`` via ``--lai-csv``.

Usage:
    python mklai_icos/save_lai_csv.py
    python mklai_icos/save_lai_csv.py --lai-type GAI
    python mklai_icos/save_lai_csv.py --lai-type PAI --output my_lai.csv
    python mklai_icos/save_lai_csv.py --ancillary-csv /path/to/ICOSETC_DE-RuS_ANCILLARY_L2.csv

Note
----
When ``--lai-type all`` (the default) is used and both GAI and PAI
measurements exist for the same date, the output CSV will contain duplicate
dates. ``create_lai_obs.py`` uses only the last value per date in that case.
Specify ``--lai-type GAI`` or ``--lai-type PAI`` to avoid ambiguity.
"""

import argparse
from pathlib import Path

from extract_lai import _DEFAULT_ANCILLARY, load_lai_dataframe


def save_lai_csv(
    lai_df,
    output_path: Path = None,
    lai_type: str = "all",
) -> None:
    """Write mean LAI date + value to a CSV in create_lai_obs.py format.

    Parameters
    ----------
    lai_df : pd.DataFrame
        DataFrame as returned by :func:`extract_lai.load_lai_dataframe`.
    output_path : Path, optional
        Destination CSV file. Defaults to the source CSV path with
        ``_mean_{lai_type}`` appended to the stem (taken from
        ``lai_df.attrs["source_file"]``).
    lai_type : str
        ``"all"`` to include all LAI types, or a specific type string
        (e.g. ``"GAI"``, ``"PAI"``) to filter by ``LAI_TYPE``.
    """
    if output_path is None:
        stem = lai_df.attrs["source_file"].stem + f"_mean_{lai_type}"
        output_path = lai_df.attrs["source_file"].with_stem(stem)
    mean = lai_df[lai_df["LAI_STATISTIC"] == "Mean"].copy()

    if lai_type != "all":
        mean = mean[mean["LAI_TYPE"] == lai_type]
        if mean.empty:
            raise ValueError(
                f"No mean LAI rows found for LAI_TYPE='{lai_type}'. "
                f"Available types: {lai_df['LAI_TYPE'].unique().tolist()}"
            )

    result = mean[["LAI_DATE", "LAI"]].copy()
    result["ts_date"] = result["LAI_DATE"].dt.strftime("%d/%m/%Y")
    result = result.rename(columns={"LAI": "ts_lai"})[["ts_date", "ts_lai"]]

    result.to_csv(output_path, index=False)
    print(f"Saved {len(result)} mean LAI records to {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Save mean ICOS LAI values to a CSV compatible with create_lai_obs.py",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--ancillary-csv",
        type=Path,
        default=_DEFAULT_ANCILLARY,
        metavar="ANCILLARY_CSV",
        help="Path to the ICOSETC_*_ANCILLARY_L2.csv file",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        metavar="OUTPUT",
        help="Destination CSV file (default: source CSV stem + _mean_{lai_type}.csv)",
    )
    parser.add_argument(
        "--lai-type",
        default="all",
        metavar="LAI_TYPE",
        help=(
            'LAI type to export: "all" (both GAI and PAI), "GAI" (Green Area '
            'Index), or "PAI" (Plant Area Index)'
        ),
    )
    args = parser.parse_args()

    df = load_lai_dataframe(args.ancillary_csv)
    save_lai_csv(df, args.output, args.lai_type)


if __name__ == "__main__":
    main()
