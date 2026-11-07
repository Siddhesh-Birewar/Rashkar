import uuid
import logging
from typing import Dict, Any, Optional, List
from shapely.geometry import Polygon
from pyproj import Geod
from sqlalchemy.orm import Session

from cropnet.services.api.app.schemas.soil import (
    UnifiedSoilProfile,
    SoilParameterObservation,
    VerificationStatus,
    ParameterAvailability
)
from cropnet.services.api.app.models.soil_and_farm import (
    FarmSoilProfileModel,
    SoilParameterModel
)
from cropnet.services.api.app.services.soil_providers.soilgrids import SoilGridsProvider
from cropnet.services.api.app.services.soil_providers.openlandmap import OpenLandMapProvider
from cropnet.services.api.app.services.soil_providers.natmo import NATMOProvider
from cropnet.services.api.app.services.soil_providers.bhoomi import BhoomiProvider
from cropnet.services.api.app.services.soil_providers.local_raster import LocalRasterProvider

logger = logging.getLogger(__name__)

# WGS84 Geodesic for precise metric area calculation
geod = Geod(ellps="WGS84")

# In-memory profile storage for fast caching and offline resilience
_SOIL_PROFILE_CACHE: Dict[str, List[UnifiedSoilProfile]] = {}


def derive_usda_texture_class(
    sand: Optional[float],
    silt: Optional[float],
    clay: Optional[float]
) -> Optional[str]:
    """
    Derives standard USDA Soil Texture Classification from Sand, Silt, and Clay percentages.
    Follows official USDA-NRCS soil texture triangle definitions.
    """
    if sand is None or silt is None or clay is None:
        return None
    
    total = sand + silt + clay
    if total <= 0:
        return None
    
    # Normalize percentages to 100%
    s = (sand / total) * 100.0
    si = (silt / total) * 100.0
    c = (clay / total) * 100.0

    # USDA NRCS Classification Boundaries:
    # 1. Sand
    if s >= 85.0 and (si + 1.5 * c) < 15.0:
        return "Sand"
    # 2. Loamy Sand
    elif s >= 70.0 and (si + 1.5 * c) >= 15.0 and (si + 2.0 * c) < 30.0:
        return "Loamy Sand"
    # 3. Sandy Loam
    elif (c < 20.0 and s > 52.0 and (si + 2.0 * c) >= 30.0) or (c < 7.0 and si < 50.0 and (si + 2.0 * c) >= 30.0):
        return "Sandy Loam"
    # 4. Loam
    elif (7.0 <= c < 27.0) and (28.0 <= si < 50.0) and (s <= 52.0):
        return "Loam"
    # 5. Silt Loam
    elif (si >= 50.0 and (12.0 <= c < 27.0)) or (50.0 <= si < 80.0 and c < 12.0):
        return "Silt Loam"
    # 6. Silt
    elif si >= 80.0 and c < 12.0:
        return "Silt"
    # 7. Sandy Clay Loam
    elif (20.0 <= c < 35.0) and (si < 28.0) and (s > 45.0):
        return "Sandy Clay Loam"
    # 8. Clay Loam
    elif (27.0 <= c < 40.0) and (20.0 < s <= 45.0):
        return "Clay Loam"
    # 9. Silty Clay Loam
    elif (27.0 <= c < 40.0) and (s <= 20.0):
        return "Silty Clay Loam"
    # 10. Sandy Clay
    elif c >= 35.0 and s >= 45.0:
        return "Sandy Clay"
    # 11. Silty Clay
    elif c >= 40.0 and si >= 40.0:
        return "Silty Clay"
    # 12. Clay
    elif c >= 40.0 and s <= 45.0 and si < 40.0:
        return "Clay"
    else:
        # Fallback for borderline or edge points
        if c >= 40.0:
            return "Clay"
        elif c >= 27.0:
            return "Clay Loam"
        elif s >= 50.0:
            return "Sandy Loam"
        else:
            return "Loam"


def calculate_polygon_area(polygon: Polygon) -> Dict[str, float]:
    """
    Calculate geodesic area of polygon in square meters, hectares, and acres.
    Never calculates area directly from latitude/longitude degrees.
    """
    poly_area, _ = geod.geometry_area_perimeter(polygon)
    area_sq_m = abs(poly_area)
    hectares = area_sq_m / 10000.0
    acres = hectares * 2.47105
    return {
        "square_meters": round(area_sq_m, 2),
        "hectares": round(hectares, 3),
        "acres": round(acres, 3)
    }


class SpatialSoilService:
    """
    Orchestration service for farm-level spatial extraction and Unified Soil Profile creation.
    """

    def __init__(self):
        self.soilgrids_provider = SoilGridsProvider()
        self.openlandmap_provider = OpenLandMapProvider()
        self.bhoomi_provider = BhoomiProvider()
        self.natmo_provider = NATMOProvider()
        self.local_provider = LocalRasterProvider()

    def generate_farm_soil_profile(
        self,
        farm_id: str,
        polygon: Polygon,
        taluka: Optional[str] = None,
        depth: str = "0-5cm",
        farm_area_hectares: Optional[float] = None
    ) -> UnifiedSoilProfile:
        """
        Extract soil properties from approved providers and generate UnifiedSoilProfile.
        Applies strict scientific guardrails and derives USDA Soil Texture Class.
        """
        profile_id = str(uuid.uuid4())
        logger.info("Generating soil profile %s for farm %s (depth: %s)", profile_id, farm_id, depth)

        # 1. Primary Extraction via SoilGrids WCS
        sg_extracted = self.soilgrids_provider.extract_farm_soil(polygon, depth=depth)

        # 2. Strict Scientific Parameter Mapping
        ph_obs = sg_extracted.get("ph")
        soc_obs = sg_extracted.get("soc")
        sand_obs = sg_extracted.get("sand_percent")
        silt_obs = sg_extracted.get("silt_percent")
        clay_obs = sg_extracted.get("clay_percent")
        total_n_obs = sg_extracted.get("total_nitrogen")
        cec_obs = sg_extracted.get("cation_exchange_capacity")

        # 3. Derive USDA Soil Texture Classification (if sand, silt, clay available)
        sand_val = sand_obs.value if sand_obs else None
        silt_val = silt_obs.value if silt_obs else None
        clay_val = clay_obs.value if clay_obs else None
        soil_texture_class = derive_usda_texture_class(sand_val, silt_val, clay_val)

        # 4. Spatial Representativeness Check (SoilGrids cell is 250m x 250m = 6.25 ha)
        area_ha = farm_area_hectares
        if area_ha is None:
            area_ha = calculate_polygon_area(polygon)["hectares"]
        
        spatial_warning = None
        if area_ha < 6.25:
            spatial_warning = (
                f"Notice: Farm boundary area ({round(area_ha, 2)} ha) is smaller than the 250m raster cell size "
                f"(6.25 ha per cell). Values represent spatial averages of the surrounding 250m cell."
            )

        # 5. Available NPK MUST NOT be fabricated. Mark strictly as NOT_AVAILABLE.
        avail_n_obs = SoilParameterObservation(
            parameter_key="available_nitrogen",
            display_name="Available Mineral Nitrogen (N)",
            value=None,
            unit="kg/ha",
            source="None (Unverified)",
            dataset_version="N/A",
            depth_interval=depth,
            spatial_resolution="N/A",
            verification_status=VerificationStatus.NOT_AVAILABLE,
            availability_status=ParameterAvailability.NOT_AVAILABLE,
            farm_coverage_percent=0.0,
            scientific_note="Available nitrogen cannot be derived from global satellite rasters without physical laboratory testing. Total Nitrogen is NOT available nitrogen."
        )

        avail_p_obs = SoilParameterObservation(
            parameter_key="available_phosphorus",
            display_name="Available Phosphorus (P2O5)",
            value=None,
            unit="kg/ha",
            source="None (Unverified)",
            dataset_version="N/A",
            depth_interval=depth,
            spatial_resolution="N/A",
            verification_status=VerificationStatus.NOT_AVAILABLE,
            availability_status=ParameterAvailability.NOT_AVAILABLE,
            farm_coverage_percent=0.0,
            scientific_note="Available phosphorus is not provided by approved public rasters and must not be inferred."
        )

        avail_k_obs = SoilParameterObservation(
            parameter_key="available_potassium",
            display_name="Available Potassium (K2O)",
            value=None,
            unit="kg/ha",
            source="None (Unverified)",
            dataset_version="N/A",
            depth_interval=depth,
            spatial_resolution="N/A",
            verification_status=VerificationStatus.NOT_AVAILABLE,
            availability_status=ParameterAvailability.NOT_AVAILABLE,
            farm_coverage_percent=0.0,
            scientific_note="Available potassium is not provided by approved public rasters and must not be inferred."
        )

        # Count completeness across primary physical & chemical parameters
        primary_params = [ph_obs, soc_obs, sand_obs, silt_obs, clay_obs, total_n_obs, cec_obs]
        total_count = len(primary_params) + 3 # including N, P, K
        available_count = sum(1 for p in primary_params if p and p.value is not None)
        completeness_ratio = round(available_count / total_count, 2)

        return UnifiedSoilProfile(
            profile_id=profile_id,
            farm_id=farm_id,
            taluka=taluka,
            district="Pune",
            state="Maharashtra",
            is_map_derived=True,
            disclaimer=(
                "These results are estimates derived from geospatial soil datasets. "
                "They are not laboratory soil test results. Actual farm soil conditions may vary."
            ),
            source_dataset="ISRIC SoilGrids 2.0",
            dataset_version="2.0.0",
            spatial_resolution="250m",
            depth_interval=depth,
            spatial_representativeness_warning=spatial_warning,
            soil_texture_class=soil_texture_class,
            ph=ph_obs,
            organic_carbon=soc_obs,
            sand_percent=sand_obs,
            silt_percent=silt_obs,
            clay_percent=clay_obs,
            total_nitrogen=total_n_obs,
            cation_exchange_capacity=cec_obs,
            available_nitrogen=avail_n_obs,
            available_phosphorus=avail_p_obs,
            available_potassium=avail_k_obs,
            total_requested_parameters=total_count,
            available_parameters_count=available_count,
            data_completeness_ratio=completeness_ratio
        )

    def _model_to_profile(
        self,
        profile_model: FarmSoilProfileModel,
        taluka: Optional[str] = None
    ) -> UnifiedSoilProfile:
        """
        Reconstruct a UnifiedSoilProfile schema instance from SQLAlchemy models.
        """
        params_by_key: Dict[str, SoilParameterObservation] = {}
        texture_class: Optional[str] = None
        spatial_warning: Optional[str] = None
        depth_interval: str = "0-5cm"

        for p in profile_model.parameters:
            if p.parameter_key == "soil_texture_class":
                texture_class = p.scientific_note
                depth_interval = p.depth_interval
                continue
            if p.parameter_key == "spatial_representativeness":
                spatial_warning = p.scientific_note
                continue

            depth_interval = p.depth_interval
            obs = SoilParameterObservation(
                parameter_key=p.parameter_key,
                display_name=p.display_name,
                value=p.value,
                unit=p.unit,
                source=p.source,
                dataset_version=p.dataset_version,
                depth_interval=p.depth_interval,
                spatial_resolution=p.spatial_resolution,
                vintage_year=p.vintage_year,
                uncertainty=p.uncertainty,
                verification_status=p.verification_status,
                availability_status=p.availability_status,
                farm_coverage_percent=p.farm_coverage_percent or 100.0,
                scientific_note=p.scientific_note,
            )
            params_by_key[p.parameter_key] = obs

        primary_keys = {"ph", "soc", "sand_percent", "silt_percent", "clay_percent", "total_nitrogen", "cation_exchange_capacity", "available_nitrogen", "available_phosphorus", "available_potassium"}
        available_count = sum(1 for k in primary_keys if k in params_by_key and params_by_key[k].value is not None)
        total_count = len(primary_keys)

        additional_params: Dict[str, SoilParameterObservation] = {
            k: obs for k, obs in params_by_key.items() if k not in primary_keys
        }

        return UnifiedSoilProfile(
            profile_id=profile_model.id,
            farm_id=profile_model.farm_id,
            created_at=profile_model.created_at,
            version=profile_model.version,
            taluka=taluka,
            district="Pune",
            state="Maharashtra",
            is_map_derived=profile_model.is_map_derived,
            disclaimer=profile_model.disclaimer,
            source_dataset="ISRIC SoilGrids 2.0",
            dataset_version="2.0.0",
            spatial_resolution="250m",
            depth_interval=depth_interval,
            soil_texture_class=texture_class,
            spatial_representativeness_warning=spatial_warning,
            ph=params_by_key.get("ph"),
            organic_carbon=params_by_key.get("soc"),
            sand_percent=params_by_key.get("sand_percent"),
            silt_percent=params_by_key.get("silt_percent"),
            clay_percent=params_by_key.get("clay_percent"),
            total_nitrogen=params_by_key.get("total_nitrogen"),
            cation_exchange_capacity=params_by_key.get("cation_exchange_capacity"),
            available_nitrogen=params_by_key.get("available_nitrogen"),
            available_phosphorus=params_by_key.get("available_phosphorus"),
            available_potassium=params_by_key.get("available_potassium"),
            additional_parameters=additional_params,
            total_requested_parameters=total_count,
            available_parameters_count=available_count + len(additional_params),
            data_completeness_ratio=round(available_count / total_count, 2)
        )

    def save_profile(
        self,
        db: Optional[Session],
        profile: UnifiedSoilProfile
    ) -> None:
        """
        Persist soil profile and individual parameter records to DB and memory cache.
        """
        # Save to memory cache
        _SOIL_PROFILE_CACHE.setdefault(profile.farm_id, []).insert(0, profile)

        # Save to Database if session available
        if db is not None:
            try:
                profile_model = FarmSoilProfileModel(
                    id=profile.profile_id,
                    farm_id=profile.farm_id,
                    version=profile.version,
                    is_map_derived=profile.is_map_derived,
                    disclaimer=profile.disclaimer,
                    created_at=profile.created_at
                )
                db.add(profile_model)

                all_obs = [
                    profile.ph, profile.organic_carbon, profile.sand_percent,
                    profile.silt_percent, profile.clay_percent, profile.total_nitrogen,
                    profile.cation_exchange_capacity, profile.available_nitrogen,
                    profile.available_phosphorus, profile.available_potassium
                ]
                if profile.additional_parameters:
                    all_obs.extend(profile.additional_parameters.values())

                for obs in all_obs:
                    if obs:
                        db.add(SoilParameterModel(
                            id=str(uuid.uuid4()),
                            profile_id=profile.profile_id,
                            parameter_key=obs.parameter_key,
                            display_name=obs.display_name,
                            value=obs.value,
                            unit=obs.unit,
                            source=obs.source,
                            dataset_version=obs.dataset_version,
                            depth_interval=obs.depth_interval,
                            spatial_resolution=obs.spatial_resolution,
                            vintage_year=obs.vintage_year,
                            uncertainty=obs.uncertainty,
                            verification_status=obs.verification_status.value if hasattr(obs.verification_status, "value") else str(obs.verification_status),
                            availability_status=obs.availability_status.value if hasattr(obs.availability_status, "value") else str(obs.availability_status),
                            farm_coverage_percent=obs.farm_coverage_percent,
                            scientific_note=obs.scientific_note
                        ))

                if profile.soil_texture_class:
                    db.add(SoilParameterModel(
                        id=str(uuid.uuid4()),
                        profile_id=profile.profile_id,
                        parameter_key="soil_texture_class",
                        display_name="USDA Soil Texture Class",
                        value=None,
                        unit="class",
                        source="Derived from SoilGrids Sand/Silt/Clay",
                        dataset_version="2.0.0",
                        depth_interval=profile.depth_interval,
                        spatial_resolution=profile.spatial_resolution,
                        verification_status="map_derived_estimate",
                        availability_status="available",
                        farm_coverage_percent=100.0,
                        scientific_note=profile.soil_texture_class
                    ))

                if profile.spatial_representativeness_warning:
                    db.add(SoilParameterModel(
                        id=str(uuid.uuid4()),
                        profile_id=profile.profile_id,
                        parameter_key="spatial_representativeness",
                        display_name="Spatial Representativeness Notice",
                        value=None,
                        unit="notice",
                        source="CropNet Geospatial Engine",
                        dataset_version="1.0.0",
                        depth_interval=profile.depth_interval,
                        spatial_resolution=profile.spatial_resolution,
                        verification_status="map_derived_estimate",
                        availability_status="available",
                        farm_coverage_percent=100.0,
                        scientific_note=profile.spatial_representativeness_warning
                    ))

                db.commit()
                logger.info("Successfully persisted soil profile %s to database", profile.profile_id)
            except Exception as e:
                logger.warning("Failed to persist soil profile to DB: %s (in-memory cached)", e)
                db.rollback()

    def get_latest_profile(
        self,
        db: Optional[Session],
        farm_id: str,
        depth: Optional[str] = None
    ) -> Optional[UnifiedSoilProfile]:
        """
        Retrieve the latest cached soil profile for a farm (matching depth if given).
        Checks database first, falls back to in-memory cache.
        """
        if db is not None:
            try:
                models = (
                    db.query(FarmSoilProfileModel)
                    .filter(FarmSoilProfileModel.farm_id == str(farm_id))
                    .order_by(FarmSoilProfileModel.created_at.desc())
                    .all()
                )
                for m in models:
                    profile = self._model_to_profile(m)
                    if depth is None or profile.depth_interval == depth:
                        return profile
            except Exception as e:
                logger.debug("Database profile lookup error: %s", e)

        # Fallback to in-memory cache
        cached_list = _SOIL_PROFILE_CACHE.get(str(farm_id), [])
        for p in cached_list:
            if depth is None or p.depth_interval == depth:
                return p
        return cached_list[0] if (cached_list and depth is None) else None

    def get_profile_history(
        self,
        db: Optional[Session],
        farm_id: str
    ) -> List[UnifiedSoilProfile]:
        """
        Retrieve full history of soil profile snapshots for a farm.
        """
        history: List[UnifiedSoilProfile] = []
        if db is not None:
            try:
                models = (
                    db.query(FarmSoilProfileModel)
                    .filter(FarmSoilProfileModel.farm_id == str(farm_id))
                    .order_by(FarmSoilProfileModel.created_at.desc())
                    .all()
                )
                for m in models:
                    history.append(self._model_to_profile(m))
                if history:
                    return history
            except Exception as e:
                logger.debug("Database history lookup error: %s", e)

        return _SOIL_PROFILE_CACHE.get(str(farm_id), [])
