from datetime import datetime, date
from sqlalchemy import Column, String, DateTime, Date, Text, Float, Integer, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from backend.app.db.session import Base
from backend.app.core.timezone import now_utc

class FarmModel(Base):
    __tablename__ = "farms"

    farm_id = Column(String(50), primary_key=True, index=True)
    owner_id = Column(String(50), nullable=False, index=True)
    farm_name = Column(String(100), nullable=False)
    state = Column(String(50), default="Maharashtra")
    district = Column(String(50), nullable=False, index=True)  # e.g., "Pune"
    taluka = Column(String(50), nullable=False, index=True)    # e.g., "Baramati", "Indapur", "Maval", "Mulshi"
    village = Column(String(100), nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    created_at = Column(DateTime, default=now_utc)
    updated_at = Column(DateTime, default=now_utc, onupdate=now_utc)

    plots = relationship("FarmPlotModel", back_populates="farm", cascade="all, delete-orphan")

class FarmPlotModel(Base):
    __tablename__ = "farm_plots"

    plot_id = Column(String(50), primary_key=True, index=True)
    farm_id = Column(String(50), ForeignKey("farms.farm_id"), nullable=False, index=True)
    plot_name = Column(String(100), nullable=False)
    area_acres = Column(Float, nullable=False)
    polygon_geojson = Column(JSON, nullable=True)  # GeoJSON representation of boundary
    irrigation_type = Column(String(50), default="rainfed")  # rainfed, borewell, canal, drip
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
    current_stage_code = Column(String(50), nullable=True)
    stage_updated_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=now_utc)

    plot = relationship("FarmPlotModel", back_populates="crop_cycles")
