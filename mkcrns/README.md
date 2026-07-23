# CRNS Soil Moisture Observations (`mkcrns/`)

Creates TSMP-PDAF observation files from Cosmic-Ray Neutron Sensor (CRNS) soil
moisture data provided by the [COSMOS-Europe](https://doi.org/10.34731/x9s3-kr48)
network.

## Data Citation

When using COSMOS-Europe data, please cite:

> Bogena, H. R., Schrön, M., Jakobi, J., Ney, P., Zacharias, S., Andreasen, M.,
> et al.: COSMOS-Europe: a European network of cosmic-ray neutron soil moisture
> sensors, Earth Syst. Sci. Data, 14, 1125–1151,
> https://doi.org/10.5194/essd-14-1125-2022, 2022.

**Data DOI:** https://doi.org/10.34731/x9s3-kr48
**Contact:** h.bogena@fz-juelich.de

## Data

The COSMOS-Europe dataset (revision 1, DOI:
[10.34731/x9s3-kr48](https://doi.org/10.34731/x9s3-kr48)) can be
downloaded automatically:

```bash
python mkcrns/create_crns_obs.py --download-data
```

This downloads and extracts the dataset into `mkcrns/` as
`COSMOS_Europe_Data_rev1/`. To place it elsewhere, combine with `--crns-data-dir`:

```bash
python mkcrns/create_crns_obs.py --download-data \
    --crns-data-dir /path/to/COSMOS_Europe_Data_rev1
```

The expected directory layout after extraction is:

```
COSMOS_Europe_Data_rev1/
├── General_ information_rev1.csv
├── Additional_information_rev1.csv
└── processed_crns_data_and_diagnostics_rev1/
    ├── SEC001.csv               # Selhausen (example)
    └── ...
```

Pass the root folder via `--crns-data-dir` when it is not inside `mkcrns/`.

## Quick Start

```bash
# Download the dataset (first time only)
python mkcrns/create_crns_obs.py --download-data

# List available CRNS stations
python mkcrns/create_crns_obs.py --list-stations

# Generate observation files for station SEC001, year 2018
python mkcrns/create_crns_obs.py SEC001 2018 \
    --output-dir /path/to/output

# With quality-flag masking and custom localization radii
python mkcrns/create_crns_obs.py SEC001 2018 \
    --output-dir /path/to/output \
    --skip-flagged \
    --dr 0.004 0.003
```

Output files are written to `OUTPUT_DIR/YEAR/PREFIX.DDDDD` (zero-padded
day-of-year), one file per calendar day. Days with no valid soil moisture
produce an empty file (`no_obs=0`) so that TSMP-PDAF can scan forward to the
next assimilation step.

## `create_crns_obs.py`: Full Option Reference

| Argument          | Default                                   | Description                                                                                                                                 |
|-------------------|-------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------|
| `station_id`      | *(required)*                              | CRNS station ID, e.g. `SEC001`                                                                                                              |
| `year`            | *(required)*                              | Year to process                                                                                                                             |
| `--crns-data-dir` | `mkcrns/COSMOS_Europe_Data_rev1/`          | Root COSMOS-Europe data directory                                                                                                           |
| `--output-dir`    | `.`                                       | Output root; files go to `OUTPUT_DIR/YEAR/`                                                                                                 |
| `--prefix`        | `CRNS_SM_CLM`                             | Output filename prefix                                                                                                                      |
| `--obs-var`       | `SoilMoisture_volumetric_MovAvg24h`       | CRNS column to use as observation value                                                                                                     |
| `--layer`         | `1`                                       | CLM5 soil layer index (0-based)                                                                                                             |
| `--obs-type`      | `SM`                                      | Observation type string written to `type_clm`; must match `current_observation_type` in TSMP-PDAF to avoid silent skipping in joint DA runs |
| `--dr DR_H DR_V`  | `0.00387525 0.002500534`                  | Localization radii [horizontal, vertical]                                                                                                   |
| `--setup`         | `undefined`                               | Setup name stored in NetCDF global attributes                                                                                               |
| `--skip-flagged`  | off                                       | Mask quality-flagged hourly records as NaN before computing daily means                                                                     |
| `--list-stations` | off                                       | Print available stations and exit                                                                                                           |
| `--download-data` | off                                       | Download the COSMOS-Europe dataset (revision 1) and exit                                                                                    |

## Python API (`cosmos_europe/`)

`download_cosmos_europe` and `parse_crns_data` can be imported directly —
see [`cosmos_europe/README.md`](cosmos_europe/README.md) for usage examples.
