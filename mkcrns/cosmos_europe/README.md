# COSMOS-Europe Data Utilities (`cosmos_europe/`)

Standalone modules for downloading and parsing the COSMOS-Europe CRNS dataset.
Used internally by `../create_crns_obs.py`; can also be imported directly.

## `download_cosmos_europe.py`: Python API

Downloads and extracts the COSMOS-Europe dataset (revision 1) from the TERENO
data portal. The default destination is `mkcrns/COSMOS_Europe_Data_rev1/`.

```python
from mkcrns.cosmos_europe.download_cosmos_europe import download_cosmos_europe

# Download to the default location (mkcrns/COSMOS_Europe_Data_rev1/)
data_dir = download_cosmos_europe()

# Download to an explicit location
data_dir = download_cosmos_europe(dest_dir="/path/to/dir")
# → /path/to/dir/COSMOS_Europe_Data_rev1/
```

The download is skipped if the destination directory already exists.

## `parse_crns_data.py`: Python API

`parse_crns_data` can also be used directly in Python scripts or notebooks:

```python
from mkcrns.cosmos_europe.parse_crns_data import load_crns_data, list_available_stations

# List all available stations
print(list_available_stations(data_dir="/path/to/COSMOS_Europe_Data_rev1"))

# Load hourly data for a station
df = load_crns_data("SEC001", data_dir="/path/to/COSMOS_Europe_Data_rev1")

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
