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
- **[`utils/`](utils/README.md)** — Shared utilities (NetCDF provenance attributes)

---

## Data Citation

When using COSMOS-Europe data, please cite:

> Bogena, H. R., Schrön, M., Jakobi, J., Ney, P., Zacharias, S., Andreasen, M.,
> et al.: COSMOS-Europe: a European network of cosmic-ray neutron soil moisture
> sensors, Earth Syst. Sci. Data, 14, 1125–1151,
> https://doi.org/10.5194/essd-14-1125-2022, 2022.

**Data DOI:** https://doi.org/10.34731/x9s3-kr48
**Contact:** h.bogena@fz-juelich.de
