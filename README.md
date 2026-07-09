# PDAF Observation File Generator

Scripts and utilities for creating observation files for
[TSMP-PDAF](https://github.com/HPSCTerrSys/TSMP-PDAF) data
assimilation runs.

Each script in this repository reads observations from an external
data source and writes NetCDF files in the format expected by
TSMP-PDAF.

---

## Repository Structure

```
PDAF_observation-file-generator/
├── mkcrns/                      # Observation files from COSMOS-Europe CRNS data
│   ├── create_crns_obs.py       # Main script: CRNS data → TSMP-PDAF NetCDF files
│   └── parse_crns_data.py       # Parser: COSMOS-Europe CSV → pandas DataFrame
├── mkera5land/                  # Observation files from ERA5-Land soil moisture
│   ├── download_era5land_sm.py  # Download swvl1 from Copernicus CDS
│   └── create_era5land_obs.py   # ERA5-Land NetCDF → TSMP-PDAF NetCDF files
└── utils/                       # Shared utilities
    └── nc_attributes.py         # Sets standard provenance attributes on NetCDF files
```

---

## Dependencies

Install the required Python packages (see `pyproject.toml`):

```bash
pip install -e .
```

---

## Tools

- **[`mkcrns/`](mkcrns/README.md)** — CRNS soil moisture observations from COSMOS-Europe
- **[`mkera5land/`](mkera5land/README.md)** — ERA5-Land soil moisture observations from Copernicus CDS
- **[`utils/`](utils/README.md)** — Shared utilities (NetCDF provenance attributes)
