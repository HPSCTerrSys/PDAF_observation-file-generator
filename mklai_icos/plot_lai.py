"""Plot the LAI time series from an ICOS ANCILLARY_L2 CSV.

Draws Mean +/- Standard Deviation LAI over time, coloured by index type
(GAI = Green Area Index, PAI = Plant Area Index), and saves the figure as
a PNG file.

Usage:
    python mklai_icos/plot_lai.py
    python mklai_icos/plot_lai.py --ancillary-csv /path/to/ICOSETC_DE-RuS_ANCILLARY_L2.csv
    python mklai_icos/plot_lai.py --output lai_timeseries.png
"""

import argparse
from pathlib import Path

import matplotlib.pyplot as plt

from extract_lai import _DEFAULT_ANCILLARY, load_lai_dataframe


def plot_lai(lai_df, output_path: Path = None) -> None:
    """Plot mean LAI with standard-deviation error bars, split by LAI_TYPE.

    Parameters
    ----------
    lai_df : pd.DataFrame
        DataFrame as returned by :func:`extract_lai.load_lai_dataframe`.
    output_path : Path, optional
        Where to save the figure. Defaults to the source CSV path with the
        suffix replaced by ``.png`` (taken from ``lai_df.attrs["source_file"]``).
    """
    if output_path is None:
        output_path = lai_df.attrs["source_file"].with_suffix(".png")
    mean = lai_df[lai_df["LAI_STATISTIC"] == "Mean"].set_index("LAI_DATE")
    std = lai_df[lai_df["LAI_STATISTIC"] == "Standard Deviation"].set_index("LAI_DATE")

    fig, ax = plt.subplots(figsize=(10, 5))

    for lai_type, color in [("GAI", "tab:green"), ("PAI", "tab:brown")]:
        subset = mean[mean["LAI_TYPE"] == lai_type]
        if subset.empty:
            continue
        shared_idx = subset.index.intersection(std.index)
        errors = std.loc[shared_idx, "LAI"] if not shared_idx.empty else None
        ax.errorbar(
            subset.index,
            subset["LAI"],
            yerr=errors,
            fmt="o-",
            color=color,
            label=lai_type,
            capsize=3,
        )

    ax.set_xlabel("Date")
    ax.set_ylabel("LAI (m$^2$ m$^{-2}$)")
    ax.set_title("DE-RuS Leaf/Plant Area Index (mean ± std)")
    ax.legend(title="Index type")
    fig.autofmt_xdate()
    fig.tight_layout()

    fig.savefig(output_path, dpi=150)
    print(f"Saved plot to {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Plot the ICOS LAI time series from an ANCILLARY_L2 CSV",
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
        help="Output PNG file path (default: ancillary CSV path with .png suffix)",
    )
    args = parser.parse_args()

    df = load_lai_dataframe(args.ancillary_csv)
    plot_lai(df, args.output)


if __name__ == "__main__":
    main()
