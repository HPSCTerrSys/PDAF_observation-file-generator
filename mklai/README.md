# LAI Observations (`mklai/`)

Creates TSMP-PDAF observation files from Sentinel-2 Leaf Area Index (LAI)
time series data for a single field site.

## Data

The input is a two-column CSV file with columns `ts_date` (DD/MM/YYYY) and
`ts_lai` (m²/m²):

```
ts_date,ts_lai
22/02/2018,0.634700923
08/04/2018,2.035070253
...
```

The file included in this repository (`S2_LAI_timeseries_CPP_10.csv`)
contains Sentinel-2 LAI retrievals for the Selhausen field site (DE-RuS,
Jülich Research Centre, Germany) spanning 2018–2022. Observations are
irregularly spaced in time (cloud-free Sentinel-2 acquisitions only).

## Quick Start

```bash
# Generate observation files for 2018, writing to the current directory
python mklai/create_lai_obs.py 2018

# Specify output directory
python mklai/create_lai_obs.py 2018 --output-dir /path/to/output

# Use a different LAI CSV or site coordinates
python mklai/create_lai_obs.py 2020 \
    --lai-csv /path/to/my_lai.csv \
    --lat 50.123 --lon 6.456 \
    --output-dir /path/to/output
```

Output files are written to `OUTPUT_DIR/YEAR/PREFIX.DDDDD` (zero-padded
day-of-year), one file per calendar day. Days without a LAI observation
produce an empty file (`no_obs=0`) so that TSMP-PDAF can scan forward to
the next assimilation step.

## `create_lai_obs.py`: Full Option Reference

| Argument             | Default                            | Description                                                                                                                                  |
|----------------------|------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------|
| `year`               | *(required)*                       | Year to process                                                                                                                              |
| `--lai-csv`          | `mklai/S2_LAI_timeseries_CPP_10.csv` | Path to the LAI CSV file (columns: `ts_date`, `ts_lai`)                                                                                   |
| `--output-dir`       | `.`                                | Output root; files go to `OUTPUT_DIR/YEAR/`                                                                                                  |
| `--prefix`           | `LAI_CLM`                          | Output filename prefix                                                                                                                       |
| `--lat`              | `50.865886`                        | Site latitude [degrees_north]                                                                                                                |
| `--lon`              | `6.447111`                         | Site longitude [degrees_east]                                                                                                                |
| `--type-clm`         | `LAI`                              | Observation type string written to `type_clm`; must match `current_observation_type` in TSMP-PDAF to avoid silent skipping in joint DA runs  |
| `--dr DR_LON DR_LAT` | `0.00387525 0.002500534`           | Snapping distances [longitude, latitude]                                                                                                     |
| `--setup`            | `undefined`                        | Setup name stored in NetCDF global attributes                                                                                                |

## Output File Format

Each file is a NetCDF-4 file containing a single LAI observation (or no
observation on days without a valid LAI value). The format matches the
TSMP-PDAF observation file convention:

| Variable   | Type    | Dimensions          | Content                                    |
|------------|---------|---------------------|--------------------------------------------|
| `time`     | float64 | `(time)`            | Days since 1900-01-01 (CF convention)      |
| `lat`      | float32 | `(dim_obs)`         | Site latitude [degrees_north]              |
| `lon`      | float32 | `(dim_obs)`         | Site longitude [degrees_east]              |
| `layer`    | int32   | `(dim_obs)`         | `0` (written for format compatibility)     |
| `no_obs`   | int32   | `(dim_obs)`         | `1` if valid LAI present, `0` if not       |
| `dr`       | float32 | `(dim_dr)`          | Snapping distances [lon, lat]              |
| `obs_clm`  | float32 | `(dim_obs)`         | LAI value [m²/m²]                          |
| `type_clm` | char    | `(dim_obs, strlen)` | `"LAI"` padded to 20 characters            |
