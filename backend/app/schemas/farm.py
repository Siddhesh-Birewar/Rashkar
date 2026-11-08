from datetime import date, datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

class FarmCreateRequest(BaseModel):
    owner_id: str = Field(..., json_schema_extra={"example": "farmer_001"})
    farm_name: str = Field(..., json_schema_extra={"example": "Shri Ram Agro Farm"})
    state: str = Field(default="Maharashtra")
    district: str = Field(..., json_schema_extra={"example": "Pune"})
    taluka: str = Field(..., json_schema_extra={"example": "Baramati"})
    village: Optional[str] = Field(default=None, json_schema_extra={"example": "Malegaon"})
    latitude: float = Field(..., json_schema_extra={"example": 18.1512})
    longitude: float = Field(..., json_schema_extra={"example": 74.5768})

class FarmPlotCreateRequest(BaseModel):
    plot_name: str = Field(..., json_schema_extra={"example": "East Canal Plot"})
    area_acres: float = Field(..., json_schema_extra={"example": 2.5})
    irrigation_type: str = Field(default="canal", json_schema_extra={"example": "canal"})
    polygon_geojson: Optional[Dict[str, Any]] = None

class CropCycleCreateRequest(BaseModel):
    crop_code: str = Field(..., json_schema_extra={"example": "soybean"})
    variety_name: Optional[str] = Field(default=None, json_schema_extra={"example": "JS-335"})
    season: str = Field(default="kharif", json_schema_extra={"example": "kharif"})
    sowing_date: date = Field(..., json_schema_extra={"example": "2024-06-25"})
    farmer_confirmed_stage: Optional[str] = Field(default=None, json_schema_extra={"example": "R1_FLOWERING"})

class FarmResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    farm_id: str
    owner_id: str
    farm_name: str
    total_area_acres: Optional[float] = None
    district: str
    taluka: str
    village: Optional[str] = None
    latitude: float
    longitude: float
    created_at: datetime

class FarmerCreateRequest(BaseModel):
    full_name: str = Field(..., json_schema_extra={"example": "Ramesh Patil"})
    phone_number: Optional[str] = Field(default=None, json_schema_extra={"example": "+91 98765 43210"})
    state: str = Field(default="Maharashtra")
    district: str = Field(..., json_schema_extra={"example": "Pune"})
    taluka: str = Field(..., json_schema_extra={"example": "Baramati"})
    village: Optional[str] = Field(default=None, json_schema_extra={"example": "Malegaon Budruk"})
    preferred_language: str = Field(default="en")

class FarmerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    farmer_id: str
    full_name: str
    phone_number: Optional[str] = None
    state: str
    district: str
    taluka: str
    village: Optional[str] = None
    preferred_language: str
    created_at: datetime

class GuidedRegistrationRequest(BaseModel):
    # Screen 1: Farmer
    farmer_name: str = Field(..., json_schema_extra={"example": "Suresh Shinde"})
    phone_number: Optional[str] = Field(default=None)
    village: Optional[str] = Field(default=None)
    taluka: str = Field(..., json_schema_extra={"example": "Baramati"})
    district: str = Field(..., json_schema_extra={"example": "Pune"})
    
    # Screen 2: Farm
    farm_name: Optional[str] = Field(default="My Farm")
    total_area_acres: Optional[float] = Field(default=3.0)
    latitude: float = Field(default=18.151)
    longitude: float = Field(default=74.577)

    # Screen 3: Crop
    crop_code: str = Field(..., json_schema_extra={"example": "soybean"})
    variety_name: Optional[str] = Field(default=None)
    season: str = Field(default="kharif")
    sowing_date: date = Field(..., json_schema_extra={"example": "2024-06-15"})
    irrigation_type: str = Field(default="rainfed")
    planted_area_acres: Optional[float] = Field(default=2.5)

class FarmProfileUpdateRequest(BaseModel):
    # Farmer fields
    farmer_name: Optional[str] = None
    phone_number: Optional[str] = None
    preferred_language: Optional[str] = None
    
    # Farm fields
    farm_name: Optional[str] = None
    district: Optional[str] = None
    taluka: Optional[str] = None
    village: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    total_area_acres: Optional[float] = None
    
    # Plot & Crop fields
    planted_area_acres: Optional[float] = None
    irrigation_type: Optional[str] = None
    crop_code: Optional[str] = None
    variety_name: Optional[str] = None
    sowing_date: Optional[date] = None
    season: Optional[str] = None
    farmer_confirmed_stage: Optional[str] = None

class FarmSummaryResponse(BaseModel):
    farmer_id: str
    farmer_name: str
    farm_id: str
    farm_name: str
    location_display: str  # e.g. "Malegaon, Baramati, Pune"
    latitude: float
    longitude: float
    total_area_acres: Optional[float] = None
    
    # Active crop
    active_crop_code: Optional[str] = None
    active_crop_name: Optional[str] = None
    sowing_date: Optional[str] = None
    days_after_sowing: Optional[int] = None
    estimated_stage_code: Optional[str] = None
    estimated_stage_name: Optional[str] = None
    planted_area_acres: Optional[float] = None
    irrigation_type: Optional[str] = None

    # Weather summary
    weather_summary: Dict[str, Any]
    data_last_updated: str
    is_data_stale: bool = False

    # Soil summary (CropNet)
    soil_summary: Optional[Dict[str, Any]] = None

    # Active alerts (0 to 3 simple alerts)
    active_alerts: List[Dict[str, Any]] = []
