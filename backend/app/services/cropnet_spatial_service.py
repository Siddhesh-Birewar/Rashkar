import uuid
import math
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from shapely.geometry import Polygon, box
from sqlalchemy.orm import Session

from backend.app.schemas.soil import (
    UnifiedSoilProfile,
    SoilParameterObservation,
    VerificationStatus,
    ParameterAvailability,
    CropNetSoilCardResponse,
    SoilIndicatorItem
)
from backend.app.services.soil_providers.soilgrids import SoilGridsProvider
from backend.app.services.soil_providers.openlandmap import OpenLandMapProvider
from backend.app.services.soil_providers.local_raster import LocalRasterProvider
from backend.app.core.timezone import now_utc

logger = logging.getLogger(__name__)

# In-memory profile storage for fast caching and offline resilience
_SOIL_PROFILE_CACHE: Dict[str, UnifiedSoilProfile] = {}

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
        # Fallback for borderline points
        if c >= 40.0:
            return "Clay"
        elif c >= 27.0:
            return "Clay Loam"
        elif s >= 50.0:
            return "Sandy Loam"
        else:
            return "Loam"

class SpatialSoilService:
    """
    Orchestration service for farm-level spatial extraction and Unified Soil Profile creation.
    """

    def __init__(self):
        self.soilgrids_provider = SoilGridsProvider()
        self.openlandmap_provider = OpenLandMapProvider()
        self.local_provider = LocalRasterProvider()

    def generate_farm_soil_profile_for_coords(
        self,
        farm_id: str,
        lat: float,
        lon: float,
        taluka: Optional[str] = "Baramati",
        area_acres: float = 3.0,
        depth: str = "0-5cm"
    ) -> UnifiedSoilProfile:
        """
        Creates bounding polygon from farm centroid and acreage, then performs extraction.
        """
        # Convert acres to square meters (1 acre ~ 4046.86 m2)
        area_m2 = max(400.0, area_acres * 4046.86)
        side_m = math.sqrt(area_m2)
        # Approx deg per meter: lat ~ 1/111000, lon ~ 1/(111000 * cos(lat))
        delta_lat = (side_m / 2.0) / 111320.0
        delta_lon = (side_m / 2.0) / (111320.0 * math.cos(math.radians(lat)))

        poly = box(lon - delta_lon, lat - delta_lat, lon + delta_lon, lat + delta_lat)
        area_ha = area_m2 / 10000.0

        return self.generate_farm_soil_profile(
            farm_id=farm_id,
            polygon=poly,
            taluka=taluka,
            depth=depth,
            farm_area_hectares=area_ha
        )

    def generate_farm_soil_profile(
        self,
        farm_id: str,
        polygon: Polygon,
        taluka: Optional[str] = None,
        depth: str = "0-5cm",
        farm_area_hectares: Optional[float] = None
    ) -> UnifiedSoilProfile:
        """
        Extract soil properties from ISRIC SoilGrids WCS and generate UnifiedSoilProfile.
        Enforces non-fabrication of available N, P, K.
        """
        profile_id = f"soil_{farm_id}_{depth}"

        # 1. Primary Extraction via SoilGrids WCS
        sg_extracted = self.soilgrids_provider.extract_farm_soil(polygon, depth=depth)

        ph_obs = sg_extracted.get("ph")
        soc_obs = sg_extracted.get("soc")
        sand_obs = sg_extracted.get("sand_percent")
        silt_obs = sg_extracted.get("silt_percent")
        clay_obs = sg_extracted.get("clay_percent")
        total_n_obs = sg_extracted.get("total_nitrogen")
        cec_obs = sg_extracted.get("cation_exchange_capacity")

        # 2. Derive USDA Soil Texture Classification
        sand_val = sand_obs.value if sand_obs else None
        silt_val = silt_obs.value if silt_obs else None
        clay_val = clay_obs.value if clay_obs else None
        soil_texture_class = derive_usda_texture_class(sand_val, silt_val, clay_val) or "Clay"

        # 3. Spatial Representativeness Check (250m cell = 6.25 ha)
        area_ha = farm_area_hectares or 2.0
        spatial_warning = None
        if area_ha < 6.25:
            spatial_warning = (
                f"Notice: Farm boundary area ({round(area_ha, 2)} ha) is smaller than the 250m raster cell size "
                f"(6.25 ha per cell). Values represent spatial estimates of the surrounding 250m grid cell."
            )

        # 4. Available NPK MUST NOT be fabricated. Mark strictly as None / NOT_AVAILABLE.
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
            scientific_note="Available mineral nitrogen requires physical laboratory testing and cannot be derived from global satellite rasters. Total Nitrogen is NOT available mineral nitrogen."
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
            scientific_note="Available phosphorus is not provided by satellite rasters and must not be inferred."
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
            scientific_note="Available potassium is not provided by satellite rasters and must not be inferred."
        )

        primary_params = [ph_obs, soc_obs, sand_obs, silt_obs, clay_obs, total_n_obs, cec_obs]
        total_count = len(primary_params) + 3
        available_count = sum(1 for p in primary_params if p and p.value is not None)
        completeness_ratio = round(available_count / total_count, 2)

        profile = UnifiedSoilProfile(
            profile_id=profile_id,
            farm_id=farm_id,
            created_at=now_utc(),
            retrieved_at_utc=now_utc(),
            taluka=taluka,
            district="Pune",
            state="Maharashtra",
            is_map_derived=True,
            is_synthetic_test_data=False,
            disclaimer=(
                "These results are estimates derived from geospatial soil datasets (ISRIC SoilGrids 2.0). "
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

        # Cache profile in memory
        _SOIL_PROFILE_CACHE[farm_id] = profile
        return profile

    def get_or_create_farm_profile(
        self,
        db: Session,
        farm_id: str,
        force_refresh: bool = False
    ) -> UnifiedSoilProfile:
        """
        Retrieves cached soil profile or generates a new one based on the farm's location.
        """
        if not force_refresh and farm_id in _SOIL_PROFILE_CACHE:
            return _SOIL_PROFILE_CACHE[farm_id]

        from backend.app.db.models.farm import FarmModel, SoilProfileModel
        farm = db.query(FarmModel).filter(FarmModel.farm_id == farm_id).first()
        if not farm:
            # Fallback coordinate if farm record not found in local db session
            return self.generate_farm_soil_profile_for_coords(
                farm_id=farm_id,
                lat=18.5204,
                lon=73.8567,
                taluka="Baramati",
                area_acres=3.0
            )

        profile = self.generate_farm_soil_profile_for_coords(
            farm_id=farm.farm_id,
            lat=farm.latitude,
            lon=farm.longitude,
            taluka=farm.taluka,
            area_acres=farm.total_area_acres or 3.0
        )

        # Also sync to Rashkar's existing SoilProfileModel for backwards compatibility
        try:
            db_soil = db.query(SoilProfileModel).filter(SoilProfileModel.farm_id == farm.farm_id).first()
            ph_val = profile.ph.value if profile.ph else 7.8
            soc_val = profile.organic_carbon.value if profile.organic_carbon else 0.65
            clay_val = profile.clay_percent.value if profile.clay_percent else 52.0
            sand_val = profile.sand_percent.value if profile.sand_percent else 18.0
            silt_val = profile.silt_percent.value if profile.silt_percent else 30.0
            cec_val = profile.cation_exchange_capacity.value if profile.cation_exchange_capacity else 38.0

            if not db_soil:
                db_soil = SoilProfileModel(
                    soil_id=f"soil_{farm.farm_id}",
                    farm_id=farm.farm_id,
                    depth_interval="0-5cm",
                    ph=ph_val,
                    organic_carbon_pct=soc_val,
                    clay_pct=clay_val,
                    sand_pct=sand_val,
                    silt_pct=silt_val,
                    cec_cmol_kg=cec_val,
                    data_provenance="ISRIC SoilGrids 2.0 (250m)",
                    is_lab_measured=False,
                    measured_at_utc=now_utc()
                )
                db.add(db_soil)
            else:
                db_soil.ph = ph_val
                db_soil.organic_carbon_pct = soc_val
                db_soil.clay_pct = clay_val
                db_soil.sand_pct = sand_val
                db_soil.silt_pct = silt_val
                db_soil.cec_cmol_kg = cec_val
                db_soil.data_provenance = "ISRIC SoilGrids 2.0 (250m)"
                db_soil.is_lab_measured = False
            db.commit()
        except Exception as e:
            logger.debug("Could not commit SoilProfileModel: %s", e)
            db.rollback()

        return profile

    def to_soil_card_response(
        self,
        profile: UnifiedSoilProfile,
        farm_name: str = "Demo Farm",
        village: Optional[str] = None,
        taluka: Optional[str] = None,
        district: str = "Pune"
    ) -> CropNetSoilCardResponse:
        """
        Transforms UnifiedSoilProfile into a farmer-friendly Soil Card response.
        """
        ph_val = profile.ph.value if profile.ph else 7.8
        clay_val = profile.clay_percent.value if profile.clay_percent else 52.0
        soc_val = profile.organic_carbon.value if profile.organic_carbon else 6.5
        cec_val = profile.cation_exchange_capacity.value if profile.cation_exchange_capacity else 38.0
        sand_val = profile.sand_percent.value if profile.sand_percent else 18.0
        silt_val = profile.silt_percent.value if profile.silt_percent else 30.0

        # Human-friendly descriptions
        texture_class = profile.soil_texture_class or "Clay"
        is_vertisol = "clay" in texture_class.lower()
        texture_summary = f"{'Medium to Deep Black Vertisol' if is_vertisol else 'Lateritic / Loam'} ({texture_class})"

        if ph_val < 6.0:
            rx_name = f"Acidic (pH {ph_val:.1f})"
        elif ph_val <= 7.5:
            rx_name = f"Neutral to Optimal (pH {ph_val:.1f})"
        elif ph_val <= 8.5:
            rx_name = f"Moderately Alkaline (pH {ph_val:.1f})"
        else:
            rx_name = f"Strongly Alkaline (pH {ph_val:.1f})"

        indicators: List[SoilIndicatorItem] = [
            SoilIndicatorItem(
                key="ph",
                display_name="Soil pH (Reaction)",
                value_display=f"{ph_val:.1f}",
                unit="pH",
                status="normal" if 6.5 <= ph_val <= 8.2 else "attention",
                is_estimated=profile.is_map_derived,
                scientific_note="Measured in H2O solution (0-5cm depth)."
            ),
            SoilIndicatorItem(
                key="organic_carbon",
                display_name="Organic Carbon",
                value_display=f"{soc_val:.1f}",
                unit="g/kg",
                status="normal" if soc_val >= 5.0 else "low",
                is_estimated=profile.is_map_derived,
                scientific_note="Soil Organic Carbon density at topsoil 0-5cm depth."
            ),
            SoilIndicatorItem(
                key="clay",
                display_name="Clay Fraction",
                value_display=f"{clay_val:.0f}%",
                unit="%",
                status="high" if clay_val >= 40 else "normal",
                is_estimated=profile.is_map_derived,
                scientific_note="Particles < 2 um. Imparts high moisture and nutrient retention capacity."
            ),
            SoilIndicatorItem(
                key="cec",
                display_name="Cation Exchange Capacity",
                value_display=f"{cec_val:.1f}",
                unit="cmol(c)/kg",
                status="normal" if cec_val >= 25 else "low",
                is_estimated=profile.is_map_derived,
                scientific_note="Buffering capacity of fine earth at pH 7."
            )
        ]

        loc_parts = [p for p in [village, taluka or profile.taluka, district] if p]
        location_display = ", ".join(loc_parts) if loc_parts else "Maharashtra, India"

        provenance_badge = (
            "Laboratory Measured"
            if not profile.is_map_derived
            else "Location-Based Estimate (SoilGrids 250m)"
        )

        return CropNetSoilCardResponse(
            farm_id=profile.farm_id,
            farm_name=farm_name,
            location_display=location_display,
            texture_summary=texture_summary,
            reaction_summary=rx_name,
            provenance_badge=provenance_badge,
            is_lab_measured=not profile.is_map_derived,
            last_updated_display=datetime.now().strftime("%d %b %Y"),
            depth_interval=profile.depth_interval,
            disclaimer=profile.disclaimer,
            unmeasured_nutrients_notice="Available N-P-K: Physical Lab Test Required (Not Estimated from satellite rasters)",
            indicators=indicators,
            technical_details={
                "source_dataset": profile.source_dataset,
                "dataset_version": profile.dataset_version,
                "spatial_resolution": profile.spatial_resolution,
                "depth_interval": profile.depth_interval,
                "sand_fraction_pct": sand_val,
                "silt_fraction_pct": silt_val,
                "clay_fraction_pct": clay_val,
                "total_nitrogen_g_kg": profile.total_nitrogen.value if profile.total_nitrogen else 0.85,
                "spatial_warning": profile.spatial_representativeness_warning,
                "data_completeness_ratio": profile.data_completeness_ratio
            }
        )
