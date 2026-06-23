"""
Parse CRNS (Cosmic-Ray Neutron Sensor) soil moisture data from
COSMOS-Europe dataset.

This module provides functions to load processed CRNS data and
associated metadata from the COSMOS-Europe dataset. The data includes
soil moisture measurements, neutron counts, and quality flags.

Reference:
    COSMOS-Europe: A European network of Cosmic-Ray Neutron Soil
    Moisture Sensors Contact: h.bogena@fz-juelich.de

Usage:
    from parse_crns_data import load_crns_data
    df = load_crns_data("SEC001")                                    # data co-located with this file
    df = load_crns_data("SEC001", data_dir="/path/to/COSMOS_Europe_Data_rev1")  # explicit path
    print(df.attrs)  # Access metadata

Note on metadata:
    Station metadata (latitude, longitude, station name, etc.) is
    attached to the returned DataFrame via df.attrs. Be aware that
    pandas does not preserve .attrs through most operations -
    filtering, resampling, groupby, and similar transformations
    silently drop the attributes. Extract any metadata you need
    *before* transforming the DataFrame:

        df = load_crns_data("SEC001")
        lat = df.attrs["latitude"]   # extract first
        lon = df.attrs["longitude"]
        df_daily = df.resample("D").mean()  # .attrs lost after this
"""

import pandas as pd
from pathlib import Path
from typing import Optional


# Fallback data directory used when no data_dir is passed explicitly.
# Assumes the COSMOS_Europe_Data folder is co-located with this module,
# which holds for local / side-by-side use. Pass data_dir explicitly when
# the module is installed as a package and the data lives elsewhere.
_DEFAULT_DATA_DIR = Path(__file__).parent / "COSMOS_Europe_Data_rev1"


def _resolve_data_dir(data_dir: Optional[Path]) -> Path:
    """Return data_dir as a Path, falling back to the module-relative default."""
    return Path(data_dir) if data_dir is not None else _DEFAULT_DATA_DIR


def load_general_info(
    data_dir: Optional[Path] = None,
    filename: str = "General_ information_rev1.csv",
) -> pd.DataFrame:
    """Load general station information/metadata."""
    # Note: the space in "General_ information*.csv" is present in the original dataset.
    filepath = _resolve_data_dir(data_dir) / filename
    df = pd.read_csv(filepath, encoding="latin-1")
    df = df.rename(columns=lambda x: x.strip())
    df = df.set_index("File name")
    return df


def load_additional_info(
    data_dir: Optional[Path] = None,
    filename: str = "Additional_information_rev1.csv",
) -> pd.DataFrame:
    """Load additional station information (physical quantities)."""
    filepath = _resolve_data_dir(data_dir) / filename
    df = pd.read_csv(filepath, encoding="latin-1")
    df = df.rename(columns=lambda x: x.strip())
    df = df.set_index("Station ID")
    return df


def get_station_metadata(
    station_id: str,
    data_dir: Optional[Path] = None,
    general_info_filename: str = "General_ information_rev1.csv",
    additional_info_filename: str = "Additional_information_rev1.csv",
) -> dict:
    """
    Get combined metadata for a station from both info files.

    Parameters
    ----------
    station_id : str
        Station identifier (e.g., "SEC001" for Selhausen)
    data_dir : Path, optional
        Root COSMOS-Europe data directory. Defaults to the directory co-located
        with this module.
    general_info_filename : str, optional
        Filename of the general information CSV inside data_dir.
    additional_info_filename : str, optional
        Filename of the additional information CSV inside data_dir.

    Returns
    -------
    dict
        Combined metadata from the two info CSV files.
    """
    general_info = load_general_info(data_dir, filename=general_info_filename)
    additional_info = load_additional_info(data_dir, filename=additional_info_filename)

    metadata = {}

    # Get general info
    if station_id in general_info.index:
        row = general_info.loc[station_id]
        metadata["station_name"] = row.get("Station", "")
        metadata["country"] = row.get("Country", "")
        metadata["affiliation"] = row.get("Affiliation", "")
        metadata["detector_type"] = row.get("Detector Typ", "")
        metadata["latitude"] = row.get("Latitude (°)", row.get("Latitude (°)", None))
        metadata["longitude"] = row.get("Longitude (°)", row.get("Longitude (°)", None))
        metadata["altitude_m"] = row.get("Altitude (m)", None)
        metadata["land_use"] = row.get("Main land use", "")
        metadata["mean_air_temp_C"] = row.get(
            "Mean air temperature (°C)", row.get("Mean air temperature (°C)", None)
        )
        metadata["mean_annual_precip_mm"] = row.get("Mean annual precipitation (mm)", None)
        metadata["climate_classification"] = row.get("Climate classification (Koeppen&Geiger)", "")
        metadata["time_period_start"] = row.get("Time period start", "")
        metadata["time_period_end"] = row.get("Time period end", "")

    # Get additional info
    if station_id in additional_info.index:
        row = additional_info.loc[station_id]
        metadata["porosity"] = row.get("Porosity", None)
        metadata["bulk_density_g_cm3"] = row.get("Bulk density*(g/cm3)", None)
        metadata["soil_organic_carbon_g_g"] = row.get("Soil organic carbon*(g/g)", None)
        metadata["lattice_water_g_g"] = row.get("Lattice water*(g/g)", None)
        metadata["cutoff_rigidity_GV"] = row.get("Cutoff rigidity(GV)", None)
        metadata["N0_cts_h"] = row.get("N0(cts/h)", None)
        metadata["mean_raw_neutrons_cts_h"] = row.get("Mean raw epithermal neutrons(cts/h)", None)
        metadata["mean_corrected_neutrons_cts_h"] = row.get(
            "Mean corrected epithermal neutrons(cts/h)", None
        )
        metadata["mean_soil_moisture_m3_m3"] = row.get("Mean soil moisture(m3/m3)", None)
        metadata["soil_moisture_range_m3_m3"] = row.get("Soil moisture range(m3/m3)", None)
        metadata["mean_footprint_depth_m"] = row.get("Mean Footprint depth(m)", None)
        metadata["mean_footprint_radius_m"] = row.get("Mean Footprint radius(m)", None)
        metadata["references"] = row.get("References", "")

    metadata["station_id"] = station_id
    metadata["data_source"] = "COSMOS-Europe"

    return metadata


def load_crns_data(
    station_id: str = "SEC001",
    data_dir: Optional[Path] = None,
    include_metadata: bool = True,
    processed_dir_name: str = "processed_crns_data_and_diagnostics_rev1",
    general_info_filename: str = "General_ information_rev1.csv",
    additional_info_filename: str = "Additional_information_rev1.csv",
) -> pd.DataFrame:
    """
    Load processed CRNS soil moisture data for a given station.

    Parameters
    ----------
    station_id : str, optional
        Station identifier (default: "SEC001" for Selhausen)
    data_dir : Path, optional
        Root COSMOS-Europe data directory (i.e. the folder that contains
        the general info CSV files and the processed data subdirectory).
        Defaults to the COSMOS_Europe_Data_rev1 directory co-located with
        this module. Pass an explicit path when the module is installed as
        a package and the data lives elsewhere.
    include_metadata : bool, optional
        Whether to include station metadata as DataFrame attributes (default: True).
        Note: pandas .attrs are not preserved through most DataFrame operations
        (filtering, resampling, etc.). Extract metadata before transforming the
        DataFrame if you need to keep it.
    processed_dir_name : str, optional
        Name of the subdirectory inside data_dir that contains per-station CSVs.
    general_info_filename : str, optional
        Filename of the general information CSV inside data_dir.
    additional_info_filename : str, optional
        Filename of the additional information CSV inside data_dir.

    Returns
    -------
    pd.DataFrame
        DataFrame with CRNS data indexed by datetime (UTC).
        Metadata is available via df.attrs if include_metadata=True.

    Columns
    -------
    NeutronCount_Epithermal_Cum1h_corrected : float
        Corrected cumulative 1-hour epithermal neutron count
    NeutronCount_Epithermal_Cum1h_corrected_std : float
        Standard deviation of corrected 1-hour neutron count
    NeutronCount_Epithermal_MovAvg24h_corrected : float
        Corrected 24-hour moving average epithermal neutron count
    NeutronCount_Epithermal_MovAvg24h_corrected_std : float
        Standard deviation of corrected 24-hour moving average
    Flag_Extreme_Counts : int
        Quality flag for extreme neutron counts (0=ok, 1=flagged)
    Flag_AirPressure_ERA5 : int
        Quality flag for air pressure from ERA5 (0=ok, 1=flagged)
    AirHumidity_gapfilled : float
        Gap-filled air humidity
    Flag_AirHumidity_ERA5 : int
        Quality flag for air humidity from ERA5 (0=ok, 1=flagged)
    Flag_Porosity_Excess : int
        Quality flag for porosity excess (0=ok, 1=flagged)
    Flag_Snow_ERA5 : int
        Quality flag for snow from ERA5 (0=ok, 1=flagged)
    SoilMoisture_volumetric_MovAvg24h : float
        Volumetric soil moisture (24-hour moving average) [m3/m3]
    SoilMoisture_volumetric_MovAvg24h_std : float
        Standard deviation of volumetric soil moisture
    SoilMoisture_volumetric_MovAvg24h_lower : float
        Lower uncertainty bound of soil moisture
    SoilMoisture_volumetric_MovAvg24h_upper : float
        Upper uncertainty bound of soil moisture
    Footprint_Radius_m : float
        Footprint radius [m]
    Footprint_Depth_m : float
        Footprint depth [m]
    Biomass : float
        Biomass estimate (if available)

    Examples
    --------
    >>> df = load_crns_data("SEC001")
    >>> print(df.columns.tolist())
    >>> print(df.attrs['station_name'])
    'Selhausen'
    >>> df['SoilMoisture_volumetric_MovAvg24h'].plot()
    """
    root_dir = _resolve_data_dir(data_dir)
    processed_dir = root_dir / processed_dir_name
    filepath = processed_dir / f"{station_id}.csv"

    if not filepath.exists():
        raise FileNotFoundError(f"Data file not found: {filepath}")

    # Read CSV with datetime parsing
    df = pd.read_csv(
        filepath,
        parse_dates=["DateTime_utc"],
        index_col="DateTime_utc",
    )

    # Add metadata as attributes
    if include_metadata:
        df.attrs = get_station_metadata(
            station_id,
            data_dir,
            general_info_filename=general_info_filename,
            additional_info_filename=additional_info_filename,
        )

    return df


def list_available_stations(
    data_dir: Optional[Path] = None,
    general_info_filename: str = "General_ information_rev1.csv",
) -> pd.DataFrame:
    """
    List all available stations with their basic information.

    Parameters
    ----------
    data_dir : Path, optional
        Root COSMOS-Europe data directory. Defaults to the directory
        `COSMOS_Europe_Data_rev1` co-located with this module.
    general_info_filename : str, optional
        Filename of the general information CSV inside data_dir.

    Returns
    -------
    pd.DataFrame
        DataFrame with station IDs as index and basic info columns
    """
    general_info = load_general_info(data_dir, filename=general_info_filename)
    return general_info[["Station", "Country", "Main land use", "Time period start", "Time period end"]]


# For IPython/Jupyter convenience
if __name__ == "__main__":
    # Example usage
    df = load_crns_data("SEC001")
    print(f"Loaded {len(df)} records for station: {df.attrs.get('station_name', 'Unknown')}")
    print(f"\nColumns: {df.columns.tolist()}")
    print(f"\nDate range: {df.index.min()} to {df.index.max()}")
    print(f"\nMetadata:")
    for key, value in df.attrs.items():
        print(f"  {key}: {value}")
