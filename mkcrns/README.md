# CRNS Soil Moisture Observations (`mkcrns/`)

Creates TSMP-PDAF observation files from Cosmic-Ray Neutron Sensor (CRNS) soil
moisture data provided by the [COSMOS-Europe](https://doi.org/10.34731/x9s3-kr48)
network.

## Data

Download the COSMOS-Europe dataset from the TERENO data repository:

> **DOI:** https://doi.org/10.34731/x9s3-kr48

Extract the dataset so that the root folder (`COSMOS_Europe_Data/`) contains:

```
COSMOS_Europe_Data/
├── General_ information.csv
├── Additional_information.csv
└── processed_crns_data_and_diagnostics/
    ├── SEC001.csv               # Selhausen (example)
    └── ...
```

Pass this root folder via `--crns-data-dir`. If omitted, the scripts look for
`COSMOS_Europe_Data/` co-located with `parse_crns_data.py`.

## Quick Start

```bash
# List available CRNS stations
python mkcrns/create_crns_obs.py --list-stations \
    --crns-data-dir /path/to/COSMOS_Europe_Data

# Generate observation files for station SEC001, year 2018
python mkcrns/create_crns_obs.py SEC001 2018 \
    --crns-data-dir /path/to/COSMOS_Europe_Data \
    --output-dir /path/to/output

# With quality-flag masking and custom localization radii
python mkcrns/create_crns_obs.py SEC001 2018 \
    --crns-data-dir /path/to/COSMOS_Europe_Data \
    --output-dir /path/to/output \
    --skip-flagged \
    --dr 0.004 0.003
```

Output files are written to `OUTPUT_DIR/YEAR/PREFIX.DDDDD` (zero-padded
day-of-year), one file per calendar day. Days with no valid soil moisture
produce an empty file (`no_obs=0`) so that TSMP-PDAF can scan forward to the
next assimilation step.

## `create_crns_obs.py`: Full Option Reference

| Argument          | Default                              | Description                                                                                                                                 |
|-------------------|--------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------|
| `station_id`      | *(required)*                         | CRNS station ID, e.g. `SEC001`                                                                                                              |
| `year`            | *(required)*                         | Year to process                                                                                                                             |
| `--crns-data-dir` | `COSMOS_Europe_Data/` next to parser | Root COSMOS-Europe data directory                                                                                                           |
| `--output-dir`    | `.`                                  | Output root; files go to `OUTPUT_DIR/YEAR/`                                                                                                 |
| `--prefix`        | `CRNS_SM_CLM`                        | Output filename prefix                                                                                                                      |
| `--obs-var`       | `SoilMoisture_volumetric_MovAvg24h`  | CRNS column to use as observation value                                                                                                     |
| `--layer`         | `1`                                  | CLM5 soil layer index (0-based)                                                                                                             |
| `--obs-type`      | `SM`                                 | Observation type string written to `type_clm`; must match `current_observation_type` in TSMP-PDAF to avoid silent skipping in joint DA runs |
| `--dr DR_H DR_V`  | `0.00387525 0.002500534`             | Localization radii [horizontal, vertical]                                                                                                   |
| `--setup`         | `undefined`                          | Setup name stored in NetCDF global attributes                                                                                               |
| `--skip-flagged`  | off                                  | Mask quality-flagged hourly records as NaN before computing daily means                                                                     |
| `--list-stations` | off                                  | Print available stations and exit                                                                                                           |

## `parse_crns_data.py`: Python API

`parse_crns_data` can also be used directly in Python scripts or notebooks:

```python
from mkcrns.parse_crns_data import load_crns_data, list_available_stations

# List all available stations
print(list_available_stations(data_dir="/path/to/COSMOS_Europe_Data"))

# Load hourly data for a station
df = load_crns_data("SEC001", data_dir="/path/to/COSMOS_Europe_Data")

# Station metadata is attached as DataFrame attributes
print(df.attrs["station_name"])          # 'Selhausen'
print(df.attrs["latitude"])              # 50.866...
print(df.attrs["mean_footprint_depth_m"])

# Key data columns
sm   = df["SoilMoisture_volumetric_MovAvg24h"]     # [m³/m³], 24h moving average
std  = df["SoilMoisture_volumetric_MovAvg24h_std"] # uncertainty
snow = df["Flag_Snow_ERA5"]                         # 0 = ok, 1 = snow-affected
```

> **Note:** pandas `.attrs` are silently dropped by most DataFrame operations
> (filtering, resampling, etc.). Extract metadata *before* transforming the
> DataFrame — see the module docstring in `parse_crns_data.py` for details.
