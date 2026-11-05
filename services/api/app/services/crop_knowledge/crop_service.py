import uuid
import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload

from cropnet.services.api.app.models.crops import (
    AgriculturalKnowledgeSourceModel,
    CropCatalogModel,
    CropSoilRequirementModel,
    CropClimateRequirementModel,
    CropSeasonRequirementModel,
    CropWaterRequirementModel,
    CropRegionalSuitabilityModel
)
from cropnet.services.api.app.schemas.crop import (
    CropCatalogSummaryResponse,
    CropFullProfileResponse,
    CropSoilRequirementsResponse,
    CropClimateRequirementsResponse,
    CropSeasonRequirementResponse,
    CropWaterRequirementsResponse,
    CropRegionalSuitabilityResponse,
    AgriculturalKnowledgeSourceResponse,
    MaharashtraSeasonCalendarResponse
)
from cropnet.services.api.app.services.crop_knowledge.seed_data import KNOWLEDGE_SOURCES, CROPS_DATA

logger = logging.getLogger(__name__)

# In-memory crop store for fast testing and offline lookup
_CROPS_CACHE: Dict[str, CropFullProfileResponse] = {}
_SOURCES_CACHE: Dict[str, AgriculturalKnowledgeSourceResponse] = {}


class CropKnowledgeService:
    """
    Agricultural Knowledge Base Service for crop requirements, environmental tolerances,
    and institutional scientific citations.
    """

    def __init__(self):
        self._initialize_memory_cache()

    def _initialize_memory_cache(self):
        """Pre-populate memory cache from authoritative seed data."""
        for src in KNOWLEDGE_SOURCES:
            _SOURCES_CACHE[src["id"]] = AgriculturalKnowledgeSourceResponse(
                id=src["id"],
                organization=src["organization"],
                publication_title=src["publication_title"],
                publication_year=src.get("publication_year"),
                document_url_or_ref=src.get("document_url_or_ref"),
                section_or_pages=src.get("section_or_pages"),
                evidence_quality=src["evidence_quality"],
                last_verified_date=src.get("last_verified_date") or __import__("datetime").datetime.utcnow()
            )

        for c in CROPS_DATA:
            soil_obj = None
            if "soil" in c:
                soil_obj = CropSoilRequirementsResponse(**c["soil"])

            climate_obj = None
            if "climate" in c:
                climate_obj = CropClimateRequirementsResponse(**c["climate"])

            seasons_objs = [CropSeasonRequirementResponse(**s) for s in c.get("seasons", [])]

            water_obj = None
            if "water" in c:
                water_obj = CropWaterRequirementsResponse(**c["water"])

            regional_objs = [CropRegionalSuitabilityResponse(**r) for r in c.get("regional", [])]

            crop_sources = []
            if c.get("source_id") in _SOURCES_CACHE:
                crop_sources.append(_SOURCES_CACHE[c["source_id"]])

            _CROPS_CACHE[c["id"]] = CropFullProfileResponse(
                id=c["id"],
                common_name=c["common_name"],
                scientific_name=c["scientific_name"],
                marathi_name=c.get("marathi_name"),
                hindi_name=c.get("hindi_name"),
                category=c["category"],
                crop_type=c["crop_type"],
                typical_duration_days_min=c.get("typical_duration_days_min"),
                typical_duration_days_max=c.get("typical_duration_days_max"),
                recommended_varieties=c.get("recommended_varieties", []),
                soil=soil_obj,
                climate=climate_obj,
                seasons=seasons_objs,
                water=water_obj,
                regional_suitability=regional_objs,
                sources=crop_sources
            )

    def seed_knowledge_base(self, db: Session) -> int:
        """
        Deterministically seed authoritative knowledge sources and crop profiles into PostgreSQL.
        Idempotent: updates existing records or inserts new ones.
        """
        seeded_count = 0
        try:
            # 1. Seed Knowledge Sources
            for src in KNOWLEDGE_SOURCES:
                existing_src = db.query(AgriculturalKnowledgeSourceModel).filter_by(id=src["id"]).first()
                if not existing_src:
                    new_src = AgriculturalKnowledgeSourceModel(**src)
                    db.add(new_src)
                else:
                    for k, v in src.items():
                        setattr(existing_src, k, v)
            db.commit()

            # 2. Seed Crops and Nested Modules
            for c_data in CROPS_DATA:
                c_id = c_data["id"]
                existing_crop = db.query(CropCatalogModel).filter_by(id=c_id).first()

                if not existing_crop:
                    crop_model = CropCatalogModel(
                        id=c_id,
                        common_name=c_data["common_name"],
                        scientific_name=c_data["scientific_name"],
                        marathi_name=c_data.get("marathi_name"),
                        hindi_name=c_data.get("hindi_name"),
                        category=c_data["category"],
                        crop_type=c_data["crop_type"],
                        typical_duration_days_min=c_data.get("typical_duration_days_min"),
                        typical_duration_days_max=c_data.get("typical_duration_days_max"),
                        recommended_varieties=c_data.get("recommended_varieties", []),
                        source_id=c_data["source_id"]
                    )
                    db.add(crop_model)
                    db.commit()
                    seeded_count += 1
                else:
                    existing_crop.common_name = c_data["common_name"]
                    existing_crop.scientific_name = c_data["scientific_name"]
                    existing_crop.marathi_name = c_data.get("marathi_name")
                    existing_crop.hindi_name = c_data.get("hindi_name")
                    existing_crop.category = c_data["category"]
                    existing_crop.crop_type = c_data["crop_type"]
                    existing_crop.recommended_varieties = c_data.get("recommended_varieties", [])
                    db.commit()

                # Seed Soil Requirements
                if "soil" in c_data:
                    existing_soil = db.query(CropSoilRequirementModel).filter_by(crop_id=c_id).first()
                    if not existing_soil:
                        db.add(CropSoilRequirementModel(crop_id=c_id, **c_data["soil"]))
                    else:
                        for k, v in c_data["soil"].items():
                            setattr(existing_soil, k, v)

                # Seed Climate Requirements
                if "climate" in c_data:
                    existing_clim = db.query(CropClimateRequirementModel).filter_by(crop_id=c_id).first()
                    if not existing_clim:
                        db.add(CropClimateRequirementModel(crop_id=c_id, **c_data["climate"]))
                    else:
                        for k, v in c_data["climate"].items():
                            setattr(existing_clim, k, v)

                # Seed Season Requirements
                for s in c_data.get("seasons", []):
                    existing_season = (
                        db.query(CropSeasonRequirementModel)
                        .filter_by(crop_id=c_id, season_name=s["season_name"])
                        .first()
                    )
                    if not existing_season:
                        db.add(CropSeasonRequirementModel(crop_id=c_id, **s))
                    else:
                        for k, v in s.items():
                            setattr(existing_season, k, v)

                # Seed Water Requirements
                if "water" in c_data:
                    existing_water = db.query(CropWaterRequirementModel).filter_by(crop_id=c_id).first()
                    if not existing_water:
                        db.add(CropWaterRequirementModel(crop_id=c_id, **c_data["water"]))
                    else:
                        for k, v in c_data["water"].items():
                            setattr(existing_water, k, v)

                # Seed Regional Suitability
                for r in c_data.get("regional", []):
                    existing_reg = (
                        db.query(CropRegionalSuitabilityModel)
                        .filter_by(crop_id=c_id, taluka=r["taluka"])
                        .first()
                    )
                    if not existing_reg:
                        db.add(CropRegionalSuitabilityModel(crop_id=c_id, **r))
                    else:
                        for k, v in r.items():
                            setattr(existing_reg, k, v)

                db.commit()

            logger.info("Successfully seeded %d crops into agricultural database", len(CROPS_DATA))
            return len(CROPS_DATA)
        except Exception as e:
            logger.error("Error seeding agricultural knowledge base: %s", e)
            db.rollback()
            return 0

    def get_all_crops(
        self,
        db: Optional[Session] = None,
        category: Optional[str] = None,
        season: Optional[str] = None
    ) -> List[CropCatalogSummaryResponse]:
        """
        List all crops with optional filtering by agricultural category and season.
        """
        summaries: List[CropCatalogSummaryResponse] = []

        if db is not None:
            try:
                query = db.query(CropCatalogModel).filter(CropCatalogModel.is_active == True)
                if category:
                    query = query.filter(CropCatalogModel.category.ilike(f"%{category}%"))
                if season:
                    query = query.join(CropCatalogModel.season_requirements).filter(
                        CropSeasonRequirementModel.season_name.ilike(f"%{season}%")
                    )

                models = query.all()
                for m in models:
                    summaries.append(CropCatalogSummaryResponse(
                        id=m.id,
                        common_name=m.common_name,
                        scientific_name=m.scientific_name,
                        marathi_name=m.marathi_name,
                        hindi_name=m.hindi_name,
                        category=m.category,
                        crop_type=m.crop_type,
                        typical_duration_days_min=m.typical_duration_days_min,
                        typical_duration_days_max=m.typical_duration_days_max,
                        recommended_varieties=m.recommended_varieties or [],
                        primary_source_org=m.primary_source.organization if m.primary_source else "MPKV / ICAR"
                    ))
                if summaries:
                    return summaries
            except Exception as e:
                logger.debug("DB crop list error: %s, falling back to cache", e)

        # Fallback to in-memory cache
        for c in _CROPS_CACHE.values():
            if category and category.lower() not in c.category.lower():
                continue
            if season:
                season_match = any(season.lower() in s.season_name.lower() for s in c.seasons)
                if not season_match:
                    continue

            summaries.append(CropCatalogSummaryResponse(
                id=c.id,
                common_name=c.common_name,
                scientific_name=c.scientific_name,
                marathi_name=c.marathi_name,
                hindi_name=c.hindi_name,
                category=c.category,
                crop_type=c.crop_type,
                typical_duration_days_min=c.typical_duration_days_min,
                typical_duration_days_max=c.typical_duration_days_max,
                recommended_varieties=c.recommended_varieties,
                primary_source_org=c.sources[0].organization if c.sources else "MPKV / ICAR"
            ))

        return summaries

    def get_crop_profile(
        self,
        crop_id: str,
        db: Optional[Session] = None
    ) -> Optional[CropFullProfileResponse]:
        """
        Retrieve full crop requirement profile by crop ID.
        """
        if db is not None:
            try:
                crop = (
                    db.query(CropCatalogModel)
                    .options(
                        joinedload(CropCatalogModel.soil_requirements),
                        joinedload(CropCatalogModel.climate_requirements),
                        joinedload(CropCatalogModel.season_requirements),
                        joinedload(CropCatalogModel.water_requirements),
                        joinedload(CropCatalogModel.regional_suitability),
                        joinedload(CropCatalogModel.primary_source),
                    )
                    .filter(CropCatalogModel.id == crop_id)
                    .first()
                )
                if crop:
                    soil_obj = None
                    if crop.soil_requirements:
                        s = crop.soil_requirements
                        soil_obj = CropSoilRequirementsResponse(
                            preferred_textures=s.preferred_textures,
                            acceptable_textures=s.acceptable_textures,
                            ph_optimum_min=s.ph_optimum_min,
                            ph_optimum_max=s.ph_optimum_max,
                            ph_tolerable_min=s.ph_tolerable_min,
                            ph_tolerable_max=s.ph_tolerable_max,
                            drainage_requirement=s.drainage_requirement,
                            salinity_sensitivity=s.salinity_sensitivity,
                            min_soil_depth_cm=s.min_soil_depth_cm,
                            optimum_organic_carbon_g_kg=s.optimum_organic_carbon_g_kg,
                            water_holding_capacity_pref=s.water_holding_capacity_pref,
                            source_id=s.source_id
                        )

                    clim_obj = None
                    if crop.climate_requirements:
                        cl = crop.climate_requirements
                        clim_obj = CropClimateRequirementsResponse(
                            temp_optimum_min_c=cl.temp_optimum_min_c,
                            temp_optimum_max_c=cl.temp_optimum_max_c,
                            temp_tolerable_min_c=cl.temp_tolerable_min_c,
                            temp_tolerable_max_c=cl.temp_tolerable_max_c,
                            annual_rainfall_min_mm=cl.annual_rainfall_min_mm,
                            annual_rainfall_max_mm=cl.annual_rainfall_max_mm,
                            humidity_preference=cl.humidity_preference,
                            frost_sensitivity=cl.frost_sensitivity,
                            heat_sensitivity=cl.heat_sensitivity,
                            solar_radiation_requirement=cl.solar_radiation_requirement,
                            source_id=cl.source_id
                        )

                    seasons_objs = [
                        CropSeasonRequirementResponse(
                            season_name=sn.season_name,
                            is_primary_season=sn.is_primary_season or False,
                            planting_window_maharashtra=sn.planting_window_maharashtra,
                            harvesting_window_maharashtra=sn.harvesting_window_maharashtra,
                            duration_days_min=sn.duration_days_min,
                            duration_days_max=sn.duration_days_max,
                            planting_calendar_by_region=sn.planting_calendar_by_region,
                            source_id=sn.source_id
                        )
                        for sn in crop.season_requirements
                    ]

                    water_obj = None
                    if crop.water_requirements:
                        w = crop.water_requirements
                        water_obj = CropWaterRequirementsResponse(
                            annual_water_requirement_mm_min=w.annual_water_requirement_mm_min,
                            annual_water_requirement_mm_max=w.annual_water_requirement_mm_max,
                            rainfed_suitable=w.rainfed_suitable,
                            irrigation_dependency=w.irrigation_dependency,
                            critical_growth_stages=w.critical_growth_stages,
                            waterlogging_sensitivity=w.waterlogging_sensitivity,
                            drought_sensitivity=w.drought_sensitivity,
                            source_id=w.source_id
                        )

                    regional_objs = [
                        CropRegionalSuitabilityResponse(
                            taluka=r.taluka,
                            district=r.district,
                            suitability_status=r.suitability_status,
                            agronomic_rationale=r.agronomic_rationale,
                            limiting_factors=r.limiting_factors,
                            source_id=r.source_id
                        )
                        for r in crop.regional_suitability
                    ]

                    src_objs = []
                    if crop.primary_source:
                        ps = crop.primary_source
                        src_objs.append(AgriculturalKnowledgeSourceResponse(
                            id=ps.id,
                            organization=ps.organization,
                            publication_title=ps.publication_title,
                            publication_year=ps.publication_year,
                            document_url_or_ref=ps.document_url_or_ref,
                            section_or_pages=ps.section_or_pages,
                            evidence_quality=ps.evidence_quality,
                            last_verified_date=ps.last_verified_date
                        ))

                    return CropFullProfileResponse(
                        id=crop.id,
                        common_name=crop.common_name,
                        scientific_name=crop.scientific_name,
                        marathi_name=crop.marathi_name,
                        hindi_name=crop.hindi_name,
                        category=crop.category,
                        crop_type=crop.crop_type,
                        typical_duration_days_min=crop.typical_duration_days_min,
                        typical_duration_days_max=crop.typical_duration_days_max,
                        recommended_varieties=crop.recommended_varieties or [],
                        soil=soil_obj,
                        climate=clim_obj,
                        seasons=seasons_objs,
                        water=water_obj,
                        regional_suitability=regional_objs,
                        sources=src_objs
                    )
            except Exception as e:
                logger.debug("DB crop profile fetch error: %s, checking cache", e)

        return _CROPS_CACHE.get(crop_id)

    def get_crop_sources(
        self,
        crop_id: str,
        db: Optional[Session] = None
    ) -> List[AgriculturalKnowledgeSourceResponse]:
        """
        Retrieve all authoritative scientific sources and publications cited for a crop.
        """
        crop = self.get_crop_profile(crop_id, db=db)
        if not crop:
            return []
        return crop.sources

    def get_maharashtra_seasons(self) -> List[MaharashtraSeasonCalendarResponse]:
        """
        Authoritative reference on standard agricultural cropping seasons in Maharashtra.
        """
        return [
            MaharashtraSeasonCalendarResponse(
                season_name="Kharif",
                marathi_name="खरीप",
                period_months="June – October (Onset of Southwest Monsoon)",
                primary_crops=["Soybean", "Cotton", "Maize", "Pearl Millet (Bajra)", "Groundnut", "Pigeonpea (Tur)"],
                rainfall_dependency="High (Dependent on Southwest Monsoon precipitation: 500–1200 mm)",
                description="Primary agricultural cropping season initiated by the onset of the Southwest monsoon. Focuses on rainfed and canal-supported field crops."
            ),
            MaharashtraSeasonCalendarResponse(
                season_name="Rabi",
                marathi_name="रब्बी",
                period_months="October – March (Post-Monsoon & Winter)",
                primary_crops=["Wheat", "Rabi Sorghum (Maldandi Jowar)", "Chickpea (Chana)", "Maize", "Mustard"],
                rainfall_dependency="Low Rainfall; Dependent on conserved subsoil Vertisol moisture and canal/well irrigation",
                description="Post-monsoon winter crop season with cool temperatures and low humidity. Deep Vertisols store residual monsoon moisture to sustain high-protein grain production."
            ),
            MaharashtraSeasonCalendarResponse(
                season_name="Zaid / Summer",
                marathi_name="उन्हाळी",
                period_months="January – May (Hot Pre-Monsoon Summer)",
                primary_crops=["Summer Groundnut", "Summer Bajra", "Watermelon", "Summer Maize", "Vegetables"],
                rainfall_dependency="Zero Rainfall Reliance; Strictly Irrigated via Micro-Irrigation (Drip/Sprinkler)",
                description="High heat and intense solar radiation season. Limited to short-duration crops with secure irrigation sources."
            )
        ]
