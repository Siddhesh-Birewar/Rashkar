import uuid
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from shapely.geometry import Polygon
from shapely.validation import explain_validity


class GeoJSONPolygonGeometry(BaseModel):
    type: str = "Polygon"
    coordinates: List[List[Tuple[float, float]]] = Field(
        ...,
        description="Coordinates in [longitude, latitude] format following GeoJSON standard (EPSG:4326)"
    )

    @field_validator("coordinates")
    @classmethod
    def validate_polygon_coordinates(cls, v):
        if not v or len(v) == 0:
            raise ValueError("Polygon must contain at least one ring of coordinates")
        exterior_ring = v[0]
        if len(exterior_ring) < 4:
            raise ValueError("Polygon exterior ring must contain at least 4 coordinates (including closure point)")
        if exterior_ring[0] != exterior_ring[-1]:
            raise ValueError("Polygon exterior ring must be closed (first coordinate equals last coordinate)")
        
        # Validate coordinate ranges (-180 to 180 lon, -90 to 90 lat)
        distinct_points = set()
        for pt in exterior_ring[:-1]:
            lon, lat = pt
            if not (-180.0 <= lon <= 180.0):
                raise ValueError(f"Longitude {lon} out of valid range [-180, 180]")
            if not (-90.0 <= lat <= 90.0):
                raise ValueError(f"Latitude {lat} out of valid range [-90, 90]")
            distinct_points.add((round(lon, 7), round(lat, 7)))

        # Polygon must contain at least 3 distinct boundary points
        if len(distinct_points) < 3:
            raise ValueError("Polygon must contain at least 3 distinct non-collinear boundary points")
        
        # Verify valid Shapely geometry, no self-intersection, non-empty
        poly = Polygon(exterior_ring)
        if poly.is_empty:
            raise ValueError("Polygon cannot be empty")
        if not poly.is_valid:
            raise ValueError(f"Invalid polygon geometry (self-intersection or degenerate ring): {explain_validity(poly)}")
        if poly.area == 0:
            raise ValueError("Polygon has zero geometric area")

        return v


class FarmBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    village: Optional[str] = None
    taluka: str = Field(..., description="One of: Maval, Mulshi, Baramati, Indapur or surrounding talukas")
    district: str = "Pune"
    state: str = "Maharashtra"
    irrigation_type: Optional[str] = Field("unknown", description="rainfed, irrigated, mixed, unknown")
    water_source: Optional[str] = Field("unknown", description="rainfall, canal, borewell, well, other, unknown")


class FarmCreate(FarmBase):
    geometry: GeoJSONPolygonGeometry


class FarmUpdate(BaseModel):
    name: Optional[str] = None
    village: Optional[str] = None
    taluka: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    irrigation_type: Optional[str] = None
    water_source: Optional[str] = None
    geometry: Optional[GeoJSONPolygonGeometry] = None


class FarmResponse(FarmBase):
    id: uuid.UUID
    owner_id: uuid.UUID
    geometry: GeoJSONPolygonGeometry
    calculated_area_hectares: float
    calculated_area_acres: float
    centroid_latitude: float
    centroid_longitude: float
    latitude: float
    longitude: float
    created_at: datetime
    updated_at: datetime
