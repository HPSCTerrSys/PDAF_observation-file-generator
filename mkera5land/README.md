# ERA5-Land Soil Moisture Observations (`mkera5land/`)

Creates TSMP-PDAF observation files from ERA5-Land volumetric soil water
(layer 1, `swvl1`) provided by the
[Copernicus Climate Data Store (CDS)](https://cds.climate.copernicus.eu).

## Data

The ERA5-Land daily statistics dataset (`derived-era5-land-daily-statistics`)
is downloaded via the CDS API. A CDS account and a configured `~/.cdsapirc`
credentials file are required before running the download script.

See the [CDS API how-to](https://cds.climate.copernicus.eu/api-how-to) for
setup instructions.

## Quick Start

```bash
# 1. Download January 2018 (global)
python mkera5land/download_era5land_sm.py \
    --year 2018 --month 1 --dirout ./data

# 2a. Generate observation files for a single location (Selhausen)
python mkera5land/create_era5land_obs.py 2018 1 \
    --location 50.866 6.447 \
    --input-dir ./data --output-dir ./obs

# 2b. Or generate for a spatial domain subset
python mkera5land/create_era5land_obs.py 2018 1 \
    --area 52 6 50 7 \
    --input-dir ./data --output-dir ./obs
```

Output files are written to `OUTPUT_DIR/YEAR/PREFIX.DDDDD` (zero-padded
day-of-year), one file per calendar day of the requested month. Days where
all grid-point values are NaN produce an empty file (`no_obs=0`) so that
TSMP-PDAF can scan forward to the next assimilation step.

## Spatial Modes

### Single location (`--location LAT LON`)

The nearest ERA5-Land grid point to the requested coordinates is found and
written as a single-observation file, identical in structure to CRNS output.
The actual grid-point coordinates (not the requested ones) are stored in the
file.

```bash
python mkera5land/create_era5land_obs.py 2018 1 \
    --location 50.866 6.447 \
    --input-dir ./data --output-dir ./obs
```

### All grid points (default)

Without `--location`, all valid grid points in the downloaded file are written
as a multi-observation file per day. Use `--area` to limit the domain:

```bash
python mkera5land/create_era5land_obs.py 2018 1 \
    --area 52 6 50 7 \
    --input-dir ./data --output-dir ./obs
```

## `download_era5land_sm.py`: Full Option Reference

| Argument    | Default  | Description                                         |
|-------------|----------|-----------------------------------------------------|
| `--year`    | required | Year to download                                    |
| `--month`   | required | Month to download (1–12)                            |
| `--dirout`  | required | Output directory                                    |
| `--area N W S E` | global | Spatial bounding box in degrees (N W S E)    |
| `--force`   | off      | Re-download even if the output file already exists  |

The downloaded file is named `era5land_swvl1_{year}_{month:02d}.nc` and
placed in `--dirout`.

## `create_era5land_obs.py`: Full Option Reference

| Argument           | Default                  | Description                                                                                                                                 |
|--------------------|--------------------------|---------------------------------------------------------------------------------------------------------------------------------------------|
| `year`             | required                 | Year to process                                                                                                                             |
| `month`            | required                 | Month to process (1–12)                                                                                                                     |
| `--input-dir`      | `.`                      | Directory containing downloaded ERA5-Land NetCDF files                                                                                      |
| `--output-dir`     | `.`                      | Output root; files go to `OUTPUT_DIR/YEAR/`                                                                                                 |
| `--location LAT LON` | *(all grid points)*    | Extract only the nearest ERA5-Land grid point                                                                                               |
| `--area N W S E`   | *(full file extent)*     | Spatial subset in degrees; ignored when `--location` is given                                                                               |
| `--era5land-var`   | `swvl1`                  | ERA5-Land NetCDF variable name to read                                                                                                      |
| `--prefix`         | `ERA5LAND_SM_CLM`        | Output filename prefix                                                                                                                      |
| `--layer`          | `0`                      | CLM5 soil layer index (0-based) written to the observation file                                                                             |
| `--obs-type`       | `SM`                     | Observation type string written to `type_clm`; must match `current_observation_type` in TSMP-PDAF to avoid silent skipping in joint DA runs |
| `--dr DR_H DR_V`   | `0.00387525 0.002500534` | Localization radii [horizontal, vertical]                                                                                                   |
| `--setup`          | `undefined`              | Setup name stored in NetCDF global attributes                                                                                               |

## Data Citation

When using ERA5-Land data, please cite:

> Muñoz Sabater, J. (2021): ERA5-Land hourly data from 1950 to present.
> Copernicus Climate Change Service (C3S) Climate Data Store (CDS).
> https://doi.org/10.24381/cds.e2161bac

> Muñoz-Sabater, J., Dutra, E., Agustí-Panareda, A., Albergel, C.,
> Arduini, G., Balsamo, G., Boussetta, S., Choulga, M., Harrigan, S.,
> Hersbach, H., Martens, B., Miralles, D. G., Piles, M., Rodríguez-Fernández,
> N. J., Zsoter, E., Buontempo, C., and Thépaut, J.-N.: ERA5-Land: a
> state-of-the-art global reanalysis dataset for land applications,
> Earth Syst. Sci. Data, 13, 4349–4383,
> https://doi.org/10.5194/essd-13-4349-2021, 2021.
