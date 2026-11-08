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
    district: str
    taluka: str
    village: Optional[str] = None
    latitude: float
    longitude: float
    created_at: datetime
