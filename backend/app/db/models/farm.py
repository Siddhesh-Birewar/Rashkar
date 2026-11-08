from datetime import datetime, date
from sqlalchemy import Column, String, DateTime, Date, Text, Float, Integer, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from backend.app.db.session import Base
from backend.app.core.timezone import now_utc

class FarmerModel(Base):
    __tablename__ = "farmers"

    farmer_id = Column(String(50), primary_key=True, index=True)
    full_name = Column(String(100), nullable=False)
    phone_number = Column(String(20), nullable=True, index=True)
    state = Column(String(50), default="Maharashtra")
    district = Column(String(50), nullable=False, index=True)
    taluka = Column(String(50), nullable=False, index=True)
    village = Column(String(100), nullable=True)
    preferred_language = Column(String(10), default="en")
    created_at = Column(DateTime, default=now_utc)
    updated_at = Column(DateTime, default=now_utc, onupdate=now_utc)

    farms = relationship("FarmModel", back_populates="farmer", cascade="all, delete-orphan")

class FarmModel(Base):
    __tablename__ = "farms"

    farm_id = Column(String(50), primary_key=True, index=True)
    owner_id = Column(String(50), ForeignKey("farmers.farmer_id"), nullable=False, index=True)
    farm_name = Column(String(100), nullable=False)
    total_area_acres = Column(Float, nullable=True)
    state = Column(String(50), default="Maharashtra")
    district = Column(String(50), nullable=False, index=True)  # e.g., "Pune"
    taluka = Column(String(50), nullable=False, index=True)    # e.g., "Baramati", "Indapur", "Maval", "Mulshi"
    village = Column(String(100), nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    created_at = Column(DateTime, default=now_utc)
    updated_at = Column(DateTime, default=now_utc, onupdate=now_utc)

    farmer = relationship("FarmerModel", back_populates="farms")
    plots = relationship("FarmPlotModel", back_populates="farm", cascade="all, delete-orphan")
    soil_profile = relationship("SoilProfileModel", back_populates="farm", uselist=False, cascade="all, delete-orphan")

class SoilProfileModel(Base):
    __tablename__ = "soil_profiles"

    soil_id = Column(String(50), primary_key=True, index=True)
    farm_id = Column(String(50), ForeignKey("farms.farm_id"), nullable=False, index=True)
    depth_interval = Column(String(50), default="0-30cm")  # 0-5cm, 5-15cm, 15-30cm, 0-30cm
    ph = Column(Float, nullable=True)
    organic_carbon_pct = Column(Float, nullable=True)
    clay_pct = Column(Float, nullable=True)
    sand_pct = Column(Float, nullable=True)
    silt_pct = Column(Float, nullable=True)
    bulk_density_g_cm3 = Column(Float, nullable=True)
    cec_cmol_kg = Column(Float, nullable=True)  # Internal/technical; not on main UI
    available_water_capacity_mm_m = Column(Float, nullable=True)
    data_provenance = Column(String(100), default="CropNet_Synthetic_v1")  # CropNet, SoilHealthCard, Lab
    is_lab_measured = Column(Boolean, default=False)
    measured_at_utc = Column(DateTime, nullable=True)
    raw_response_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=now_utc)

    farm = relationship("FarmModel", back_populates="soil_profile")

class FarmPlotModel(Base):
    __tablename__ = "farm_plots"

    plot_id = Column(String(50), primary_key=True, index=True)
    farm_id = Column(String(50), ForeignKey("farms.farm_id"), nullable=False, index=True)
    plot_name = Column(String(100), nullable=False)
    area_acres = Column(Float, nullable=False)
    polygon_geojson = Column(JSON, nullable=True)  # GeoJSON representation of boundary
    irrigation_type = Column(String(50), default="rainfed")  # rainfed, borewell, canal, drip, unknown
    created_at = Column(DateTime, default=now_utc)

    farm = relationship("FarmModel", back_populates="plots")
    crop_cycles = relationship("CropCycleModel", back_populates="plot", cascade="all, delete-orphan")

class CropCycleModel(Base):
    __tablename__ = "crop_cycles"

    cycle_id = Column(String(50), primary_key=True, index=True)
    plot_id = Column(String(50), ForeignKey("farm_plots.plot_id"), nullable=False, index=True)
    crop_code = Column(String(50), nullable=False, index=True)  # e.g., "soybean", "cotton"
    variety_name = Column(String(100), nullable=True)
    season = Column(String(20), nullable=False)  # kharif, rabi, summer, perennial
    sowing_date = Column(Date, nullable=False)
    harvest_date_actual = Column(Date, nullable=True)
    planted_area_acres = Column(Float, nullable=True)
    current_stage_code = Column(String(50), nullable=True)
    stage_updated_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=now_utc)

    plot = relationship("FarmPlotModel", back_populates="crop_cycles")
