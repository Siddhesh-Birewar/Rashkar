from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict

class DatasetRegisterRequest(BaseModel):
    dataset_id: str = Field(..., json_schema_extra={"example": "Y-01"})
    dataset_name: str = Field(..., json_schema_extra={"example": "Maharashtra District, Season and Crop APY"})
    publisher: str = Field(..., json_schema_extra={"example": "Ministry of Agriculture & Farmers Welfare / Dataful"})
    source_url: Optional[str] = None
    classification: str = Field(..., json_schema_extra={"example": "direct_download"})
    format: str = Field(..., json_schema_extra={"example": "csv"})
    temporal_coverage: Optional[str] = Field(default=None, json_schema_extra={"example": "1997-2025"})
    spatial_coverage: Optional[str] = Field(default=None, json_schema_extra={"example": "Maharashtra Statewide"})
    spatial_resolution: Optional[str] = Field(default=None, json_schema_extra={"example": "District"})
    licence: str = Field(..., json_schema_extra={"example": "Open Government Data / Attribution"})
    commercial_use_status: Optional[str] = Field(default="Permitted with attribution")
    storage_path: Optional[str] = None
    row_count: Optional[int] = None
    provenance_metadata: Dict[str, Any] = Field(default_factory=dict)

class DatasetRegistryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    dataset_id: str
    dataset_name: str
    publisher: str
    classification: str
    format: str
    temporal_coverage: Optional[str] = None
    spatial_coverage: Optional[str] = None
    licence: str
    sha256_checksum: Optional[str] = None
    retrieved_at_utc: datetime
    quality_status: str
    row_count: Optional[int] = None
    storage_path: Optional[str] = None

class ProvenanceEnvelope(BaseModel):
    source_id: str
    source_name: str
    source_version: Optional[str] = "1.0"
    retrieved_at_utc: datetime
    observed_at_utc: Optional[datetime] = None
    valid_at_utc: Optional[datetime] = None
    spatial_resolution_m: Optional[int] = None
    depth_interval: Optional[str] = None
    unit: str
    quality_flag: str = "PASSED_RANGE_CHECK"
    processing_pipeline: str = "rashkar_v1.0.0"
