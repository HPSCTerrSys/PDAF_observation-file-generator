# ICOS LAI Observations (`mklai_icos/`)

Extracts Leaf Area Index (LAI) from the ICOS ETC L2 Archive for the
Selhausen/Jülich field site (DE-RuS) and converts it to the CSV format
consumed by `mklai/create_lai_obs.py`.

## Data

### Citation

Schmidt, M., Bagheri, S., Becker, N., Dolfus, D., Esser, O., Graf, A.,
Haustein, A., Kettler, M., Kummer, S., Mattes, J. (2026).  ETC L2
ARCHIVE from Selhausen Juelich, 2019–2025, ICOS RI.
<https://hdl.handle.net/11676/AQkeUlosB336FxC7gNA6_F0I>

### Download

Automated download is **not possible** since the ICOS data portal
requires manual consent to the data usage agreement before the file is
served.

1. Open the DOI URL in a browser:
   <https://hdl.handle.net/11676/AQkeUlosB336FxC7gNA6_F0I>
2. Click `Download`.
2. Read and accept the data usage agreement (click the consent button)
   on the resulting download page.
3. Click `Download` after it has become clickable.
4. Place the ZIP file in this directory (`mklai_icos/`).

## Workflow

Run the scripts in order. All scripts default to paths inside this
directory, so no arguments are required if the ZIP is placed here.

### Step 1 — Extract the ancillary CSV from the archive

```bash
python mklai_icos/unzip_ancillary.py
```

This extracts only `ICOSETC_DE-RuS_ANCILLARY_L2.csv` from the ZIP,
leaving the remainder of the archive untouched.

### Step 2 — Inspect the full LAI dataframe

```bash
python mklai_icos/extract_lai.py
```

Prints all LAI records (both GAI and PAI, all statistics) to stdout.
Useful for a quick sanity check before exporting.

### Step 3 — Plot the LAI time series

```bash
python mklai_icos/plot_lai.py
```

Saves a PNG next to the ancillary CSV with the `.csv` suffix replaced by
`.png` (e.g. `ICOSETC_DE-RuS_ANCILLARY_L2.png`): mean ± std LAI over
time, coloured by index type (GAI = green, PAI = brown).

### Step 4 — Export mean LAI to CSV

```bash
# Export all mean LAI rows (both GAI and PAI)
python mklai_icos/save_lai_csv.py

# Export only Green Area Index (GAI) — recommended for create_lai_obs.py
python mklai_icos/save_lai_csv.py --lai-type GAI
```

The output filename is derived from the ancillary CSV by appending
`_mean_{lai_type}` to the stem, e.g.:

```
ICOSETC_DE-RuS_ANCILLARY_L2_mean_all.csv
ICOSETC_DE-RuS_ANCILLARY_L2_mean_GAI.csv
ICOSETC_DE-RuS_ANCILLARY_L2_mean_PAI.csv
```

The output CSV uses the same two-column format as
`mklai/S2_LAI_timeseries_CPP_10.csv`:

```
ts_date,ts_lai
15/04/2019,1.42
...
```

> **Note on `--lai-type all`**: when both GAI and PAI measurements exist
> for the same date, the CSV will contain duplicate `ts_date` entries.
> `create_lai_obs.py` retains only the last value per date in that case.
> Use `--lai-type GAI` or `--lai-type PAI` to avoid ambiguity.

### Step 5 — Create TSMP-PDAF observation files

Pass the exported CSV to `mklai/create_lai_obs.py` with `--dataset ICOS`
so the NetCDF global attribute `obs_source` reflects the data origin:

```bash
python mklai/create_lai_obs.py 2019 \
    --lai-csv mklai_icos/ICOSETC_DE-RuS_ANCILLARY_L2_mean_GAI.csv \
    --dataset ICOS \
    --output-dir /path/to/output
```

## Script Reference

| Script                | Purpose                                                    |
|-----------------------|------------------------------------------------------------|
| `unzip_ancillary.py`  | Extract `ICOSETC_*_ANCILLARY_L2.csv` from the archive ZIP |
| `extract_lai.py`      | Load and print the full LAI dataframe                      |
| `plot_lai.py`         | Plot mean ± std LAI time series as PNG                     |
| `save_lai_csv.py`     | Export mean LAI to `ts_date,ts_lai` CSV                    |

### `save_lai_csv.py` options

| Argument          | Default                              | Description                                         |
|-------------------|--------------------------------------|-----------------------------------------------------|
| `--ancillary-csv` | `mklai_icos/ICOSETC_DE-RuS_ANCILLARY_L2.csv` | Path to the extracted ancillary CSV       |
| `--output`        | `{ancillary_stem}_mean_{lai_type}.csv` | Destination CSV file                              |
| `--lai-type`      | `all`                                | `all`, `GAI`, or `PAI`                              |
