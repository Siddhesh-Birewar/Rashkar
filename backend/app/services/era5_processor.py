"""
ERA5-Land Hourly Preprocessor and Retrospective Heat Risk Standardizer.

Standardizes raw ECMWF ERA5-Land reanalysis products for agricultural heat risk modeling:
- Kelvin to Celsius conversion
- Logarithmic wind profile height conversion (10m to 2m over crop canopy)
- Accumulated solar radiation (J/m^2) to flux (W/m^2)
- Relative humidity via August-Roche-Magnus formula
- Retrospective Wet Bulb Globe Temperature (WBGT) via Liljegren et al. (2008)

IMPORTANT NOTICE:
ERA5-Land is retrospective reanalysis data used strictly for historical baseline calibration,
threshold validation, and model backtesting. It must NEVER be presented to users as a live
weather forecast or used in live production scoring without explicit disclosure.
"""

import math
from pathlib import Path
import numpy as np
import xarray as xr
from sqlalchemy.orm import Session
import hashlib

from backend.app.core.config import settings, BASE_DIR
from backend.app.db.models.registry import DatasetRegistryModel
from backend.app.schemas.registry import DatasetRegisterRequest
from backend.app.services.registry_service import RegistryService
from backend.app.services.wbgt_solver import calculate_wbgt, STANDARD_PRESSURE_KPA


def process_era5_land_file(
    input_nc_path: Path,
    output_nc_path: Path,
    crop_roughness_z0: float = 0.03,
    cadence_seconds: float = 10800.0  # 3 hours = 10,800 s for 3-hourly ERA5-Land slices
) -> xr.Dataset:
    """
    Standardizes raw ERA5-Land NetCDF and computes physical agrometeorological variables
    plus retrospective Liljegren WBGT.
    """
    ds = xr.open_dataset(input_nc_path)

    # 1. Temperature conversions (Kelvin to Celsius)
    t2m_c = ds["t2m"] - 273.15
    t2m_c.attrs = {"units": "degC", "long_name": "2 metre air temperature in Celsius"}

    d2m_c = ds["d2m"] - 273.15
    d2m_c.attrs = {"units": "degC", "long_name": "2 metre dewpoint temperature in Celsius"}

    # 2. Relative humidity via August-Roche-Magnus formula
    # es = 6.1094 * exp(17.625 * T / (243.04 + T))
    # ea = 6.1094 * exp(17.625 * Td / (243.04 + Td))
    # RH = 100 * (ea / es)
    es = 6.1094 * np.exp((17.625 * t2m_c) / (243.04 + t2m_c))
    ea = 6.1094 * np.exp((17.625 * d2m_c) / (243.04 + d2m_c))
    rh_pct = np.clip(100.0 * (ea / es), 0.0, 100.0)
    rh_pct.attrs = {"units": "%", "long_name": "Relative Humidity computed from t2m and d2m"}

    # 3. Wind speed conversion (Pythagorean u10 + v10)
    wind_10m = np.sqrt(ds["u10"] ** 2 + ds["v10"] ** 2)
    wind_10m.attrs = {"units": "m s**-1", "long_name": "10 metre horizontal wind speed"}

    # Logarithmic wind profile conversion: u(z) = u(z_ref) * ln(z / z0) / ln(z_ref / z0)
    # For z = 2m, z_ref = 10m, agricultural crop canopy z0 = 0.03m:
    # factor = ln(2 / 0.03) / ln(10 / 0.03) = 4.1997 / 5.8091 = 0.72296
    log_factor = math.log(2.0 / crop_roughness_z0) / math.log(10.0 / crop_roughness_z0)
    wind_2m = np.maximum(0.15, wind_10m * log_factor)
    wind_2m.attrs = {
        "units": "m s**-1",
        "long_name": "2 metre crop-level wind speed (logarithmic profile with z0=0.03m)",
        "roughness_z0_m": crop_roughness_z0,
        "height_reduction_factor": round(log_factor, 4)
    }

    # 4. Solar radiation conversion: ssrd (accumulated J/m^2) to flux (W/m^2)
    # Average flux over interval = J/m^2 / delta_t (seconds)
    solar_flux = np.clip(ds["ssrd"] / cadence_seconds, 0.0, 1400.0)
    solar_flux.attrs = {
        "units": "W m**-2",
        "long_name": "Downwelling surface solar radiation flux (derived from accumulated ssrd)",
        "accumulation_interval_seconds": cadence_seconds
    }

    # 5. Surface pressure in kPa
    pressure_kpa = ds["sp"] / 1000.0
    pressure_kpa.attrs = {"units": "kPa", "long_name": "Surface atmospheric pressure"}

    # 6. Retrospective WBGT computation using Liljegren solver
    # Extract coordinate shapes
    time_coords = ds["valid_time"].values
    lat_coords = ds["latitude"].values
    lon_coords = ds["longitude"].values

    n_times = len(time_coords)
    n_lats = len(lat_coords)
    n_lons = len(lon_coords)

    wbgt_sun_arr = np.zeros((n_times, n_lats, n_lons), dtype=np.float32)
    wbgt_shade_arr = np.zeros((n_times, n_lats, n_lons), dtype=np.float32)

    # Flatten arrays for vector/iterative execution
    t2m_vals = t2m_c.values
    rh_vals = rh_pct.values
    w2m_vals = wind_2m.values
    sol_vals = solar_flux.values
    pres_vals = pressure_kpa.values

    for t_idx in range(n_times):
        for lat_idx in range(n_lats):
            for lon_idx in range(n_lons):
                t = float(t2m_vals[t_idx, lat_idx, lon_idx])
                rh = float(rh_vals[t_idx, lat_idx, lon_idx])
                w = float(w2m_vals[t_idx, lat_idx, lon_idx])
                s = float(sol_vals[t_idx, lat_idx, lon_idx])
                p = float(pres_vals[t_idx, lat_idx, lon_idx])

                # Sun
                res_sun = calculate_wbgt(
                    temp_c=t,
                    rh_pct=rh,
                    wind_speed_ms=w,
                    solar_irradiance_wm2=s,
                    in_sun=True,
                    pressure_kpa=p
                )
                wbgt_sun_arr[t_idx, lat_idx, lon_idx] = res_sun["wbgt_estimated_c"]

                # Shade
                res_shade = calculate_wbgt(
                    temp_c=t,
                    rh_pct=rh,
                    wind_speed_ms=w,
                    solar_irradiance_wm2=s,
                    in_sun=False,
                    pressure_kpa=p
                )
                wbgt_shade_arr[t_idx, lat_idx, lon_idx] = res_shade["wbgt_estimated_c"]

    wbgt_sun_da = xr.DataArray(
        wbgt_sun_arr,
        dims=["valid_time", "latitude", "longitude"],
        coords={"valid_time": time_coords, "latitude": lat_coords, "longitude": lon_coords},
        attrs={
            "units": "degC",
            "long_name": "Outdoor Wet Bulb Globe Temperature (in sun) via Liljegren et al. (2008)",
            "purpose": "Retrospective occupational heat stress validation"
        }
    )

    wbgt_shade_da = xr.DataArray(
        wbgt_shade_arr,
        dims=["valid_time", "latitude", "longitude"],
        coords={"valid_time": time_coords, "latitude": lat_coords, "longitude": lon_coords},
        attrs={
            "units": "degC",
            "long_name": "Shaded Wet Bulb Globe Temperature (in shade) via Liljegren et al. (2008)",
            "purpose": "Retrospective occupational heat stress validation"
        }
    )

    # Build standardized dataset
    proc_ds = xr.Dataset(
        data_vars={
            "t2m_c": t2m_c,
            "d2m_c": d2m_c,
            "rh_pct": rh_pct,
            "wind_speed_10m": wind_10m,
            "wind_speed_2m": wind_2m,
            "solar_radiation_flux_wm2": solar_flux,
            "surface_pressure_kpa": pressure_kpa,
            "wbgt_sun_c": wbgt_sun_da,
            "wbgt_shade_c": wbgt_shade_da
        },
        coords=ds.coords,
        attrs={
            "title": "ERA5-Land Standardized Agrometeorological & WBGT Series (Pune Pilot)",
            "publisher": "ECMWF / Copernicus CDS / Rashkar Retrospective Processing",
            "source_dataset": "reanalysis-era5-land",
            "intended_use": "Model training, historical risk baseline, and retrospective validation only.",
            "operational_warning": "Strictly retrospective data. Never to be presented as a live forecast or used in live scoring without disclosure.",
            "wind_log_profile": f"Roughness length z0={crop_roughness_z0}m over agricultural crop canopy",
            "wbgt_method": "Liljegren et al. (2008) numerical energy-balance solver"
        }
    )

    output_nc_path.parent.mkdir(parents=True, exist_ok=True)
    proc_ds.to_netcdf(output_nc_path)
    ds.close()
    proc_ds.close()
    return proc_ds


def standardize_and_register_era5(db: Session, raw_nc: Path, out_nc: Path):
    """Standardizes raw ERA5-Land file and registers both raw and processed artifacts."""
    process_era5_land_file(raw_nc, out_nc)
    sha = hashlib.sha256(out_nc.read_bytes()).hexdigest()

    reg_req = DatasetRegisterRequest(
        dataset_id="P-03-ERA5-LAND-STANDARDIZED-2024-05",
        dataset_name="ERA5-Land Standardized Heat Series & Liljegren WBGT (May 2024 Pune)",
        publisher="ECMWF Copernicus / Rashkar Derived Products",
        source_url="https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land",
        classification="derived_product",
        format="netcdf",
        temporal_coverage="2024-05-01 00:00 to 2024-05-15 21:00 (120 hourly/3-hourly steps)",
        spatial_coverage="Pune Pilot Bounding Box (17.8-19.2 N, 73.2-75.2 E)",
        spatial_resolution="0.1 deg (~9 km)",
        licence="Copernicus Open Access / ECMWF Licence to Use Copernicus Products",
        commercial_use_status="Permitted with attribution",
        storage_path=str(out_nc),
        row_count=120,
        provenance_metadata={
            "variables_included": [
                "t2m_c", "d2m_c", "rh_pct", "wind_speed_10m",
                "wind_speed_2m", "solar_radiation_flux_wm2",
                "surface_pressure_kpa", "wbgt_sun_c", "wbgt_shade_c"
            ],
            "sha256": sha,
            "retrospective_only": True,
            "not_a_live_forecast": True
        }
    )
    rec = RegistryService.register_dataset(db, reg_req, file_path=out_nc)
    return rec
