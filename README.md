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
│   ├── download_cosmos_europe.py # Download COSMOS-Europe CRNS dataset from TERENO
│   ├── create_crns_obs.py       # Main script: CRNS data → TSMP-PDAF NetCDF files
│   └── parse_crns_data.py       # Parser: COSMOS-Europe CSV → pandas DataFramex
├── mkoldummy/                   # Dummy observation files for open-loop / spin-up runs
│   └── create_dummy_obs.py      # Single placeholder obs file (no_obs=1) for OL runs
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
- **[`mkoldummy/`](mkoldummy/)** — Dummy observation files for open-loop simulations
- **[`utils/`](utils/README.md)** — Shared utilities (NetCDF provenance attributes)
