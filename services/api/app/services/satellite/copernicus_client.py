"""
Copernicus Data Space Ecosystem (CDSE) Sentinel-2 Level-2A Client.

Implements:
1. CDSE OAuth2 Token acquisition and RESTo / OData catalog searches.
2. Scene Classification Layer (SCL) cloud & cloud-shadow masking (classes 3, 8, 9, 10, 11).
3. Exact Band Math:
   - NDVI = (B08 - B04) / (B08 + B04) at 10m
   - NDMI = (B08 - B11) / (B08 + B11) resampled to 10m
4. Statistical aggregation (mean, median, min, max, std).
5. Small farm spatial representativeness safeguards (<0.5 ha or <5 pixels).
6. Deterministic offline/dev fallback with non-fabrication provenance tags.
"""
import os
import math
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Union
import uuid
import httpx
import numpy as np
import pyproj
import shapely
from shapely.geometry import shape, Polygon, mapping
import rasterio
from rasterio.mask import mask
from rasterio.enums import Resampling
from rasterio.warp import reproject

from PIL import Image
import json

try:
    from cropnet.services.api.app.core.config import settings
except ImportError:
    from ...core.config import settings

logger = logging.getLogger(__name__)

CDSE_TOKEN_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
CDSE_CATALOG_URL = "https://catalogue.dataspace.copernicus.eu/resto/api/collections/Sentinel2/search.json"
CDSE_ODATA_URL = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products"

# SCL (Scene Classification Layer) Masking Classes
# Masked: 0 (No data), 1 (Saturated/Defective), 3 (Cloud shadow), 7 (Unclassified),
# 8 (Cloud med prob), 9 (Cloud high prob), 10 (Thin cirrus), 11 (Snow/Ice)
SCL_MASKED_CLASSES = {0, 1, 3, 7, 8, 9, 10, 11}
# Valid surface pixels: 4 (Vegetation), 5 (Not-vegetated / bare soil), 6 (Water)
SCL_VALID_CLASSES = {4, 5, 6}

DERIVED_RASTER_CACHE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "data_cache", "satellite_rasters")
)
os.makedirs(DERIVED_RASTER_CACHE_DIR, exist_ok=True)


def sanitize_farm_id(farm_id: Any) -> str:
    """
    Validates that farm_id is a valid UUID and returns its canonical string representation.
    Rejects directory traversal sequences and non-UUID identifiers.
    """
    if farm_id is None:
        raise ValueError("farm_id cannot be None")
    raw_str = str(farm_id).strip()
    try:
        parsed = uuid.UUID(raw_str)
        return str(parsed)
    except (ValueError, AttributeError, TypeError):
        raise ValueError(f"Invalid farm_id: {raw_str!r}. Must be a valid UUID.")


def _safe_raster_cache_path(farm_id: Any, suffix: str) -> str:
    """
    Constructs and verifies an absolute filesystem path inside DERIVED_RASTER_CACHE_DIR.
    Guarantees strict containment to prevent directory traversal.
    """
    clean_id = sanitize_farm_id(farm_id)
    clean_suffix = str(suffix).strip().lstrip(os.sep)
    if ".." in clean_suffix or "/" in clean_suffix or "\\" in clean_suffix:
        raise ValueError(f"Invalid suffix for raster cache: {suffix!r}")

    target = os.path.abspath(os.path.join(DERIVED_RASTER_CACHE_DIR, f"{clean_id}_{clean_suffix}"))
    if not (target == DERIVED_RASTER_CACHE_DIR or target.startswith(DERIVED_RASTER_CACHE_DIR + os.sep)):
        raise ValueError(f"Path traversal attempt detected for farm_id: {farm_id!r}")
    return target


def save_derived_raster_maps(
    farm_id: str,
    product_id: str,
    obs_date: datetime,
    b04_raw: np.ndarray,
    b08_raw: np.ndarray,
    b11_raw: np.ndarray,
    scl: np.ndarray,
    farm_mask: np.ndarray,
    transform: Any,
    crs: str,
    scale: float,
    offset: float,
    classes: Dict[str, int],
) -> Dict[str, Any]:
    """
    Persists actual clipped 2D raster assets for the farm boundary:
    1. NDVI canopy map (PNG)
    2. NDMI moisture map (PNG)
    3. SCL classification map (PNG)
    4. Spatial metadata JSON with bounding box coordinates in EPSG:4326.
    """
    H, W = b04_raw.shape

    # Calculate WGS84 bounding box of the cropped raster
    try:
        transformer = pyproj.Transformer.from_crs(crs, "EPSG:4326", always_xy=True)
        x_min = float(transform.c)
        y_max = float(transform.f)
        x_max = x_min + (W * float(transform.a))
        y_min = y_max + (H * float(transform.e))
        lon1, lat1 = transformer.transform(x_min, y_max)
        lon2, lat2 = transformer.transform(x_max, y_min)
        bounds = [round(min(lon1, lon2), 6), round(min(lat1, lat2), 6), round(max(lon1, lon2), 6), round(max(lat1, lat2), 6)]
    except Exception as e:
        logger.warning("Could not project raster bounds: %s", e)
        bounds = [0.0, 0.0, 0.0, 0.0]

    # Calibrate reflectances
    cal_b04 = (b04_raw * scale) + offset
    cal_b08 = (b08_raw * scale) + offset
    cal_b11 = (b11_raw * scale) + offset

    ndvi = np.clip((cal_b08 - cal_b04) / (cal_b08 + cal_b04 + 1e-8), -1.0, 1.0)
    ndmi = np.clip((cal_b08 - cal_b11) / (cal_b08 + cal_b11 + 1e-8), -1.0, 1.0)

    # 1. NDVI image
    ndvi_rgba = np.zeros((H, W, 4), dtype=np.uint8)
    # 2. NDMI image
    ndmi_rgba = np.zeros((H, W, 4), dtype=np.uint8)
    # 3. SCL image
    scl_rgba = np.zeros((H, W, 4), dtype=np.uint8)

    for r in range(H):
        for c in range(W):
            if not farm_mask[r, c]:
                continue
            scl_v = int(scl[r, c])

            # SCL Classification image
            if scl_v == 4:
                scl_rgba[r, c] = [46, 125, 50, 255]      # Vegetation canopy (green)
            elif scl_v == 5:
                scl_rgba[r, c] = [215, 180, 140, 255]    # Bare soil (ochre)
            elif scl_v == 6:
                scl_rgba[r, c] = [33, 150, 243, 255]     # Water (blue)
            elif scl_v in (3, 8, 9, 10, 11):
                scl_rgba[r, c] = [238, 238, 238, 240]    # Cloud/Shadow (light grey)
            else:
                scl_rgba[r, c] = [117, 117, 117, 240]    # Boundary/defect (dark grey)

            # NDVI Image
            if scl_v in (0, 1, 3, 7, 8, 9, 10, 11):
                ndvi_rgba[r, c] = [170, 170, 170, 200]   # Masked grey
            elif scl_v == 5:
                ndvi_rgba[r, c] = [215, 180, 140, 255]   # Bare soil
            elif scl_v == 6:
                ndvi_rgba[r, c] = [33, 150, 243, 255]    # Water
            elif scl_v == 4:
                val = ndvi[r, c]
                if val >= 0.70:
                    ndvi_rgba[r, c] = [27, 94, 32, 255]   # Deep forest green
                elif val >= 0.55:
                    ndvi_rgba[r, c] = [46, 125, 50, 255]  # Lush green
                elif val >= 0.40:
                    ndvi_rgba[r, c] = [104, 159, 56, 255] # Healthy green
                elif val >= 0.25:
                    ndvi_rgba[r, c] = [192, 202, 51, 255] # Yellow-green
                else:
                    ndvi_rgba[r, c] = [251, 192, 45, 255] # Olive
            else:
                ndvi_rgba[r, c] = [189, 189, 189, 200]

            # NDMI Image
            if scl_v in (0, 1, 3, 7, 8, 9, 10, 11):
                ndmi_rgba[r, c] = [170, 170, 170, 200]
            elif scl_v == 5:
                ndmi_rgba[r, c] = [215, 180, 140, 255]
            elif scl_v == 6:
                ndmi_rgba[r, c] = [33, 150, 243, 255]
            elif scl_v == 4:
                val = ndmi[r, c]
                if val >= 0.25:
                    ndmi_rgba[r, c] = [2, 119, 189, 255]    # Deep ocean blue
                elif val >= 0.15:
                    ndmi_rgba[r, c] = [3, 169, 244, 255]    # Azure blue
                elif val >= 0.05:
                    ndmi_rgba[r, c] = [77, 208, 225, 255]   # Light cyan
                else:
                    ndmi_rgba[r, c] = [224, 242, 241, 255]  # Pale moisture
            else:
                ndmi_rgba[r, c] = [189, 189, 189, 200]

    clean_farm_id = sanitize_farm_id(farm_id)
    ndvi_path = _safe_raster_cache_path(clean_farm_id, "ndvi.png")
    ndmi_path = _safe_raster_cache_path(clean_farm_id, "ndmi.png")
    scl_path = _safe_raster_cache_path(clean_farm_id, "scl.png")
    meta_path = _safe_raster_cache_path(clean_farm_id, "meta.json")

    Image.fromarray(ndvi_rgba).save(ndvi_path, "PNG")
    Image.fromarray(ndmi_rgba).save(ndmi_path, "PNG")
    Image.fromarray(scl_rgba).save(scl_path, "PNG")

    meta_data = {
        "farm_id": clean_farm_id,
        "product_id": product_id,
        "observation_date": obs_date.isoformat(),
        "bounds": bounds,
        "width": int(W),
        "height": int(H),
        "spatial_resolution_meters": 10.0,
        "b11_native_resolution_meters": 20.0,
        "vegetation_pixel_count": classes.get("vegetation_pixels", 0),
        "bare_soil_pixel_count": classes.get("bare_soil_pixels", 0),
        "water_pixel_count": classes.get("water_pixels", 0),
        "cloud_masked_pixel_count": classes.get("cloud_masked_pixels", 0),
        "boundary_masked_pixel_count": classes.get("other_masked_pixels", 0),
        "total_pixel_count": int(np.sum(farm_mask)),
    }
    with open(meta_path, "w") as f:
        json.dump(meta_data, f, indent=2)

    return meta_data


def get_raster_map_path(farm_id: Any, index_type: str = "ndvi") -> Optional[str]:
    type_clean = str(index_type).lower().strip()
    if type_clean not in ("ndvi", "ndmi", "scl"):
        type_clean = "ndvi"
    try:
        path = _safe_raster_cache_path(farm_id, f"{type_clean}.png")
    except ValueError:
        return None
    if os.path.isfile(path):
        return path
    return None


def get_spatial_metadata(farm_id: Any) -> Optional[Dict[str, Any]]:
    try:
        meta_path = _safe_raster_cache_path(farm_id, "meta.json")
    except ValueError:
        return None
    if not os.path.isfile(meta_path):
        return None
    try:
        with open(meta_path, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.warning("Failed to read spatial metadata: %s", e)
        return None


def calibrate_dn_to_reflectance(
    value: Optional[float],
    metadata: Optional[Dict[str, Any]] = None,
    processing_baseline: Optional[str] = None,
    is_calibrated_reflectance: bool = False,
    allow_negative_reflectance: bool = True,
) -> Optional[float]:
    """
    Calibrates Sentinel-2 Level-2A surface pixel values to BOA surface reflectance.

    Handles:
    1. Provider format: If `is_calibrated_reflectance` is True or indicated in metadata,
       returns value directly without applying offset or scaling twice.
    2. DN = 0: Strictly treated as NO_DATA (masked out, returns None).
    3. Metadata-driven calibration:
       - Extracts `BOA_ADD_OFFSET` and `QUANTIFICATION_VALUE` directly from product metadata.
       - If not explicitly provided in metadata, determines offset from `processing_baseline`:
         * PB 04.00 and later (PB N0400, N0500, N0510, N0511, etc.): offset = -1000.0 DN
         * Legacy PB < 04.00 (N0214, N0300, etc.): offset = 0.0 DN
       - Quantification value defaults to 10000.0 DN per ESA Level-2A Product Specification.
    4. Negative reflectance handling:
       Over dark surfaces or atmospheric over-correction, L2A BOA reflectance can be slightly
       negative (down to -0.10). If allow_negative_reflectance=True, preserves negative values.
       If False, clamps to 0.0.
    """
    if value is None:
        return None

    meta = metadata or {}

    # 1. Provider already returned calibrated reflectance in [0.0, 1.0]
    if is_calibrated_reflectance or meta.get("is_calibrated_reflectance") is True:
        return round(float(value), 4)

    # 2. In Sentinel-2 L2A raster products, DN = 0 is strictly NO_DATA
    if value == 0 or value == 0.0:
        return None

    # 3. Dynamic metadata extraction
    quant_val = float(meta.get("QUANTIFICATION_VALUE", meta.get("quantification_value", 10000.0)))
    if quant_val <= 0:
        quant_val = 10000.0

    if "BOA_ADD_OFFSET" in meta:
        offset = float(meta["BOA_ADD_OFFSET"])
    elif "boa_add_offset" in meta:
        offset = float(meta["boa_add_offset"])
    else:
        # Determine from processing baseline string
        pb = processing_baseline or meta.get("processing_baseline") or "N0500"
        # Extract numeric components e.g. "N0400" -> 400, "05.10" -> 510, "05.11" -> 511, "N0214" -> 214
        pb_clean = pb.upper().replace("N", "").replace(".", "").strip()
        try:
            pb_int = int(pb_clean[:4]) if len(pb_clean) >= 4 else int(pb_clean)
        except (ValueError, TypeError):
            pb_int = 500

        # Processing Baseline >= 04.00 (i.e. >= 400) introduced -1000 DN offset
        offset = -1000.0 if pb_int >= 400 else 0.0

    reflectance = (float(value) + offset) / quant_val

    if not allow_negative_reflectance:
        return round(max(0.0, reflectance), 4)
    else:
        # Physical boundary: Sentinel-2 BOA reflectance physically cannot be < -0.10
        return round(max(-0.10, reflectance), 4)


def convert_raw_dn_to_reflectance(dn: float, processing_baseline: str = "N0500") -> float:
    """
    Converts raw Sentinel-2 Level-2A Digital Numbers (DN) to BOA Surface Reflectance.
    Maintained for backwards-compatibility.
    """
    res = calibrate_dn_to_reflectance(
        value=dn,
        processing_baseline=processing_baseline,
        allow_negative_reflectance=False,
    )
    return res if res is not None else 0.0


def validate_cog_reflectance_conversion(
    item_props: Optional[Dict[str, Any]] = None,
    asset_dict: Optional[Dict[str, Any]] = None,
    raster_scales: Optional[Tuple[float, ...]] = None,
    raster_offsets: Optional[Tuple[float, ...]] = None,
    is_calibrated_reflectance: bool = False,
) -> Tuple[float, float, str]:
    """
    Independently validates and resolves the radiometric conversion formula
    for Sentinel-2 Cloud-Optimized GeoTIFFs (COGs).

    Returns: (scale_factor, additive_offset, conversion_status)
    Where: Surface Reflectance = (DN * scale_factor) + additive_offset

    Handling rules:
    1. Pre-calibrated float reflectance:
       Returns (1.0, 0.0, "PRE_CALIBRATED_FLOAT").
    2. Embedded GeoTIFF scales/offsets:
       If GeoTIFF headers explicitly define non-default scaling (scale != 1.0 or offset != 0.0),
       uses embedded tags directly: (scale, offset, "GEOTIFF_EMBEDDED_METADATA").
    3. Element 84 Earth Search COGs:
       Item property `earthsearch:boa_offset_applied: True` indicates that Element 84
       subtracted the ESA -1000 DN offset during COG creation.
       Stored DN is already harmonized to [0, 10000]:
       Reflectance = DN / 10000.0 = DN * 0.0001 (offset = 0.0).
       Returns (0.0001, 0.0, "HARMONIZED_COG_BOA_OFFSET_ALREADY_APPLIED").
    4. Raw ESA SAFE DNs (or earthsearch:boa_offset_applied: False):
       For PB >= 04.00 (e.g. 05.13):
       Reflectance = (DN - 1000.0) / 10000.0 = (DN * 0.0001) - 0.10.
       Returns (0.0001, -0.10, "RAW_SAFE_DN_OFFSET_REQUIRED").
       For legacy PB < 04.00:
       Returns (0.0001, 0.0, "LEGACY_SAFE_DN_ZERO_OFFSET").
    5. Contradictory Metadata:
       If metadata provides conflicting or unresolvable instructions
       (e.g. invalid negative scale, or contradictory flags),
       fails closed and returns (0.0, 0.0, "CONTRADICTORY_METADATA_UNVERIFIED").
    6. Missing Metadata:
       If item_props is None or empty and no scales/offsets are supplied:
       Returns (0.0, 0.0, "MISSING_CONVERSION_METADATA_UNVERIFIED").
    """
    if is_calibrated_reflectance:
        return (1.0, 0.0, "PRE_CALIBRATED_FLOAT")

    props = item_props or {}
    asset = asset_dict or {}

    # Check for embedded GeoTIFF tags
    if raster_scales and len(raster_scales) > 0 and raster_scales[0] not in (1.0, 0.0, None):
        scale = float(raster_scales[0])
        if scale <= 0.0:
            return (0.0, 0.0, "CONTRADICTORY_METADATA_UNVERIFIED")
        offset = (
            float(raster_offsets[0])
            if (raster_offsets and len(raster_offsets) > 0 and raster_offsets[0] is not None)
            else 0.0
        )
        return (scale, offset, "GEOTIFF_EMBEDDED_METADATA")

    if not props and not asset:
        return (0.0, 0.0, "MISSING_CONVERSION_METADATA_UNVERIFIED")

    # Contradiction flag check
    if props.get("contradictory_metadata") is True or asset.get("contradictory_metadata") is True:
        return (0.0, 0.0, "CONTRADICTORY_METADATA_UNVERIFIED")

    # Check scale factor in raster:bands
    raster_bands = asset.get("raster:bands", [])
    asset_scale = None
    asset_offset = None
    if raster_bands and isinstance(raster_bands, list) and len(raster_bands) > 0:
        asset_scale = raster_bands[0].get("scale")
        asset_offset = raster_bands[0].get("offset")

    # Check for negative or zero scale (invalid physics)
    if asset_scale is not None and float(asset_scale) <= 0.0:
        return (0.0, 0.0, "CONTRADICTORY_METADATA_UNVERIFIED")

    scale = float(asset_scale) if asset_scale is not None else 0.0001

    # Check boa_offset_applied
    boa_applied = props.get("earthsearch:boa_offset_applied")
    if boa_applied is None:
        boa_applied = props.get("boa_offset_applied")

    if boa_applied is True:
        # Harmonized COG where Element 84 already subtracted 1000 DN
        # Stored DN represents reflectance * 10000
        return (scale, 0.0, "HARMONIZED_COG_BOA_OFFSET_ALREADY_APPLIED")
    elif boa_applied is False:
        # Raw ESA SAFE DN
        pb = str(props.get("s2:processing_baseline") or props.get("processing_baseline") or "05.13")
        pb_clean = pb.upper().replace("N", "").replace(".", "").strip()
        try:
            pb_int = int(pb_clean[:4]) if len(pb_clean) >= 4 else int(pb_clean)
        except (ValueError, TypeError):
            pb_int = 500

        if pb_int >= 400:
            offset = -0.10 if scale == 0.0001 else (-1000.0 * scale)
            return (scale, offset, "RAW_SAFE_DN_OFFSET_REQUIRED")
        else:
            return (scale, 0.0, "LEGACY_SAFE_DN_ZERO_OFFSET")
    else:
        # Neither True nor False specified
        if asset_offset is not None and asset_scale is not None:
            return (float(asset_scale), float(asset_offset), "ASSET_SPECIFIED_SCALE_AND_OFFSET")
        return (0.0, 0.0, "MISSING_CONVERSION_METADATA_UNVERIFIED")



class CopernicusClient:
    """
    Client for querying Sentinel-2 Level-2A imagery from Copernicus Data Space Ecosystem.
    """

    def __init__(self):
        self.client_id = os.environ.get("COPERNICUS_CLIENT_ID", "")
        self.client_secret = os.environ.get("COPERNICUS_CLIENT_SECRET", "")
        self._cached_token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None

    @property
    def has_credentials(self) -> bool:
        return bool(self.client_id and self.client_secret)

    def get_token(self) -> Optional[str]:
        if not self.has_credentials:
            return None
        if self._cached_token and self._token_expiry and datetime.utcnow() < self._token_expiry:
            return self._cached_token

        try:
            with httpx.Client(timeout=15.0) as client:
                resp = client.post(
                    CDSE_TOKEN_URL,
                    data={
                        "grant_type": "client_credentials",
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    self._cached_token = data.get("access_token")
                    expires_in = data.get("expires_in", 3600)
                    self._token_expiry = datetime.utcnow() + timedelta(seconds=expires_in - 60)
                    return self._cached_token
        except Exception as e:
            logger.warning("Failed authenticating with Copernicus CDSE: %s", e)
        return None

    def search_scenes(
        self,
        polygon_geojson: Dict[str, Any],
        start_date: datetime,
        end_date: datetime,
        max_cloud_cover: float = 50.0,
    ) -> List[Dict[str, Any]]:
        """Search Sentinel-2 L2A scenes covering the farm polygon."""
        token = self.get_token()
        if not token:
            return []

        poly = shape(polygon_geojson)
        bounds = poly.bounds  # minx, miny, maxx, maxy
        box_str = f"{bounds[0]},{bounds[1]},{bounds[2]},{bounds[3]}"

        params = {
            "box": box_str,
            "startDate": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "completionDate": end_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "productType": "S2MSI2A",
            "cloudCover": f"[0,{int(max_cloud_cover)}]",
            "maxRecords": 10,
        }

        try:
            with httpx.Client(timeout=20.0) as client:
                headers = {"Authorization": f"Bearer {token}"}
                resp = client.get(CDSE_CATALOG_URL, params=params, headers=headers)
                if resp.status_code == 200:
                    features = resp.json().get("features", [])
                    return features
        except Exception as e:
            logger.warning("CDSE catalogue search error: %s", e)
        return []

    def search_odata_scenes(
        self,
        tile_id: str = "T43QDB",
        top: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Queries Copernicus Data Space Ecosystem (CDSE) public OData catalog
        for Sentinel-2 Level-2A products covering the specified MGRS tile.
        Publicly accessible without OAuth2 client credentials.
        """
        try:
            filter_query = f"Collection/Name eq 'SENTINEL-2' and contains(Name,'MSIL2A') and contains(Name,'{tile_id}')"
            params = {
                "$filter": filter_query,
                "$orderby": "ContentDate/Start desc",
                "$top": top,
            }
            with httpx.Client(timeout=20.0) as client:
                resp = client.get(CDSE_ODATA_URL, params=params)
                if resp.status_code == 200:
                    return resp.json().get("value", [])
        except Exception as e:
            logger.warning("CDSE OData catalogue search error: %s", e)
        return []

    def test_cdse_download_access(
        self,
        product_id: str = "1ac198af-5498-4c95-8df5-143e73be6051",
        relative_path: str = "Nodes(S2B_MSIL2A_20261104T053009_N0513_R105_T43QDB_20261104T073410.SAFE)/Nodes(MTD_MSIL2A.xml)/$value",
    ) -> Dict[str, Any]:
        """
        Attempts download from Copernicus Data Space Ecosystem (CDSE) download endpoint.
        Returns precise diagnostic status (e.g. HTTP 401 when uncredentialed).
        """
        url = f"https://download.dataspace.copernicus.eu/odata/v1/Products({product_id})/{relative_path}"
        token = self.get_token()
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        try:
            with httpx.Client(timeout=15.0) as client:
                resp = client.get(url, headers=headers, follow_redirects=True)
                return {
                    "url": url,
                    "status_code": resp.status_code,
                    "authenticated": bool(token),
                    "response_preview": resp.text[:300],
                    "headers": dict(resp.headers),
                }
        except Exception as e:
            return {
                "url": url,
                "status_code": 500,
                "authenticated": bool(token),
                "error": str(e),
            }

    def fetch_live_raster_indices(
        self,
        polygon_geojson: Dict[str, Any],
        farm_area_ha: float,
        observation_date: Optional[datetime] = None,
        scene_id: Optional[str] = None,
        farm_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieves real Sentinel-2 Level-2A raster imagery (B04, B08, B11, SCL) covering
        the farm polygon, performs polygon masking, aligns B11 (bilinear) and SCL (nearest)
        to the native 10m grid, calibrates surface reflectance, and computes pixel-level
        NDVI and NDMI and summary statistics.
        """
        try:
            poly = shape(polygon_geojson)
            bounds = poly.bounds  # minx, miny, maxx, maxy

            # 1. Discover product covering polygon from Earth Search STAC
            stac_url = "https://earth-search.aws.element84.com/v1/search"
            payload: Dict[str, Any] = {
                "collections": ["sentinel-2-l2a"],
                "bbox": [bounds[0], bounds[1], bounds[2], bounds[3]],
                "limit": 5,
            }
            if scene_id:
                payload = {"collections": ["sentinel-2-l2a"], "ids": [scene_id]}
            elif observation_date:
                start_dt = (observation_date - timedelta(days=15)).strftime("%Y-%m-%dT00:00:00Z")
                end_dt = (observation_date + timedelta(days=15)).strftime("%Y-%m-%dT23:59:59Z")
                payload["datetime"] = f"{start_dt}/{end_dt}"

            feature = None
            try:
                with httpx.Client(timeout=15.0) as client:
                    resp = client.post(stac_url, json=payload)
                    if resp.status_code == 200:
                        feats = resp.json().get("features", [])
                        if feats:
                            feats.sort(key=lambda f: f.get("properties", {}).get("eo:cloud_cover", 100.0))
                            feature = feats[0]
            except Exception as e:
                logger.warning("Earth Search STAC search failed: %s", e)

            if not feature:
                logger.warning("No usable Sentinel-2 L2A STAC scene found covering farm geometry.")
                return None

            props = feature.get("properties", {})
            assets = feature.get("assets", {})
            b04_url = assets.get("red", {}).get("href")
            b08_url = assets.get("nir", {}).get("href")
            b11_url = assets.get("swir16", {}).get("href")
            scl_url = assets.get("scl", {}).get("href")

            if not (b04_url and b08_url and b11_url and scl_url):
                logger.warning("Required band URLs missing in STAC feature")
                return None

            with rasterio.Env(GDAL_HTTP_TIMEOUT="15", GDAL_HTTP_MAX_RETRY="2", CPL_VSIL_CURL_TIMEOUT="15"):
                # 2. Open B04 to get CRS, transform, and embedded scales/offsets
                with rasterio.open(b04_url) as src_b04:
                    raster_crs = src_b04.crs.to_string() if src_b04.crs else "EPSG:32643"
                    scales = src_b04.scales
                    offsets = src_b04.offsets

                    transformer = pyproj.Transformer.from_crs("EPSG:4326", raster_crs, always_xy=True)

                    def reproject_coords(coords):
                        x, y = transformer.transform(coords[:, 0], coords[:, 1])
                        return np.column_stack([x, y])

                    poly_proj = shapely.transform(poly, reproject_coords)
                    geom_proj = [mapping(poly_proj)]

                    out_b04, transform_b04 = mask(src_b04, geom_proj, crop=True, all_touched=False)

                with rasterio.open(b08_url) as src_b08:
                    out_b08, transform_b08 = mask(src_b08, geom_proj, crop=True, all_touched=False)

                with rasterio.open(b11_url) as src_b11:
                    out_b11, transform_b11 = mask(src_b11, geom_proj, crop=True, all_touched=False)

                with rasterio.open(scl_url) as src_scl:
                    out_scl, transform_scl = mask(src_scl, geom_proj, crop=True, all_touched=False)

            # 3. Resample B11 (20m -> 10m grid) using Bilinear interpolation
            b11_resampled = np.empty_like(out_b08, dtype=np.float32)
            reproject(
                source=out_b11.astype(np.float32),
                destination=b11_resampled,
                src_transform=transform_b11,
                src_crs=raster_crs,
                dst_transform=transform_b08,
                dst_crs=raster_crs,
                resampling=Resampling.bilinear,
            )

            # 4. Resample SCL (20m -> 10m grid) using Nearest-Neighbor interpolation
            scl_resampled = np.empty_like(out_b08, dtype=np.uint8)
            reproject(
                source=out_scl.astype(np.uint8),
                destination=scl_resampled,
                src_transform=transform_scl,
                src_crs=raster_crs,
                dst_transform=transform_b08,
                dst_crs=raster_crs,
                resampling=Resampling.nearest,
            )

            b04_raw = out_b04[0].astype(np.float32)
            b08_raw = out_b08[0].astype(np.float32)
            b11_raw = b11_resampled[0]
            scl = scl_resampled[0]

            # 5. Masking and Class Separation
            farm_mask = (b04_raw > 0)
            total_pixels = int(np.sum(farm_mask))
            if total_pixels == 0:
                logger.warning("Farm polygon does not overlap any raster pixels")
                return None

            # SCL Classes:
            # 4: Vegetation
            # 5: Bare Soil
            # 6: Water
            # 3, 8, 9, 10, 11: Cloud & Shadow
            # 0, 1, 7: NoData / Defective / Unclassified
            veg_mask = farm_mask & (scl == 4)
            soil_mask = farm_mask & (scl == 5)
            water_mask = farm_mask & (scl == 6)
            cloud_mask = farm_mask & np.isin(scl, [3, 8, 9, 10, 11])
            other_mask = farm_mask & np.isin(scl, [0, 1, 7])
            valid_surface_mask = veg_mask | soil_mask | water_mask

            n_veg = int(np.sum(veg_mask))
            n_soil = int(np.sum(soil_mask))
            n_water = int(np.sum(water_mask))
            n_cloud = int(np.sum(cloud_mask))
            n_other = int(np.sum(other_mask))
            n_valid_surface = n_veg + n_soil + n_water
            n_invalid = total_pixels - n_valid_surface

            valid_surface_coverage_pct = round((n_valid_surface / total_pixels) * 100.0, 1)
            veg_coverage_pct = round((n_veg / total_pixels) * 100.0, 1)
            soil_coverage_pct = round((n_soil / total_pixels) * 100.0, 1)
            water_coverage_pct = round((n_water / total_pixels) * 100.0, 1)
            cloud_pct = round((n_cloud / total_pixels) * 100.0, 1)
            other_pct = round((n_other / total_pixels) * 100.0, 1)

            # 6. Radiometric Calibration Resolution (Fail-Closed Verification)
            scale, offset, conv_status = validate_cog_reflectance_conversion(
                item_props=props,
                asset_dict=assets.get("red", {}),
                raster_scales=scales,
                raster_offsets=offsets,
            )

            if conv_status.endswith("UNVERIFIED"):
                logger.warning("Radiometric conversion unverified: %s", conv_status)
                return {
                    "observation_date": datetime.utcnow(),
                    "product_id": feature.get("id", "UNKNOWN"),
                    "tile_id": "43QDA",
                    "sensor": "Sentinel-2 L2A",
                    "processing_baseline": f"N{props.get('s2:processing_baseline', '05.13').replace('.', '')}",
                    "product_cloud_coverage_percent": round(float(props.get("eo:cloud_cover", 0.0)), 2),
                    "mean_ndvi": None,
                    "median_ndvi": None,
                    "min_ndvi": None,
                    "max_ndvi": None,
                    "std_ndvi": None,
                    "mean_ndmi": None,
                    "valid_pixel_count": n_valid_surface,
                    "total_pixel_count": total_pixels,
                    "farm_coverage_percent": valid_surface_coverage_pct,
                    "cloud_masked_percent": cloud_pct,
                    "spatial_resolution_meters": 10.0,
                    "quality_status": "UNVERIFIED_RADIOMETRY",
                    "quality_notes": f"Observation unverified: {conv_status}.",
                    "radiometric_conversion_provenance": conv_status,
                }

            # 7. Compute Class-Segregated Indices
            # Pure Vegetation Canopy Metrics (Class 4)
            if n_veg >= 5:
                v_b04 = (b04_raw[veg_mask] * scale) + offset
                v_b08 = (b08_raw[veg_mask] * scale) + offset
                v_b11 = (b11_raw[veg_mask] * scale) + offset

                veg_ndvi_pixels = np.clip((v_b08 - v_b04) / (v_b08 + v_b04 + 1e-8), -1.0, 1.0)
                veg_ndmi_pixels = np.clip((v_b08 - v_b11) / (v_b08 + v_b11 + 1e-8), -1.0, 1.0)

                veg_mean_ndvi = round(float(np.mean(veg_ndvi_pixels)), 3)
                veg_median_ndvi = round(float(np.median(veg_ndvi_pixels)), 3)
                veg_min_ndvi = round(float(np.min(veg_ndvi_pixels)), 3)
                veg_max_ndvi = round(float(np.max(veg_ndvi_pixels)), 3)
                veg_std_ndvi = round(float(np.std(veg_ndvi_pixels)), 3)
                veg_mean_ndmi = round(float(np.mean(veg_ndmi_pixels)), 3)
            else:
                veg_mean_ndvi = veg_median_ndvi = veg_min_ndvi = veg_max_ndvi = veg_std_ndvi = veg_mean_ndmi = None

            # Bare Soil Metrics (Class 5)
            if n_soil > 0:
                s_b04 = (b04_raw[soil_mask] * scale) + offset
                s_b08 = (b08_raw[soil_mask] * scale) + offset
                soil_ndvi_pixels = np.clip((s_b08 - s_b04) / (s_b08 + s_b04 + 1e-8), -1.0, 1.0)
                bare_soil_mean_ndvi = round(float(np.mean(soil_ndvi_pixels)), 3)
            else:
                bare_soil_mean_ndvi = None

            # Combined Surface Metrics (Classes 4+5+6, for multi-surface reference)
            if n_valid_surface > 0:
                c_b04 = (b04_raw[valid_surface_mask] * scale) + offset
                c_b08 = (b08_raw[valid_surface_mask] * scale) + offset
                c_b11 = (b11_raw[valid_surface_mask] * scale) + offset

                surf_ndvi_pixels = np.clip((c_b08 - c_b04) / (c_b08 + c_b04 + 1e-8), -1.0, 1.0)
                surf_ndmi_pixels = np.clip((c_b08 - c_b11) / (c_b08 + c_b11 + 1e-8), -1.0, 1.0)

                surface_mean_ndvi = round(float(np.mean(surf_ndvi_pixels)), 3)
                surface_mean_ndmi = round(float(np.mean(surf_ndmi_pixels)), 3)
            else:
                surface_mean_ndvi = surface_mean_ndmi = None

            # Set primary canopy indices to pure vegetation (Class 4) if present, else surface
            mean_ndvi = veg_mean_ndvi if veg_mean_ndvi is not None else surface_mean_ndvi
            median_ndvi = veg_median_ndvi if veg_median_ndvi is not None else surface_mean_ndvi
            min_ndvi = veg_min_ndvi if veg_min_ndvi is not None else None
            max_ndvi = veg_max_ndvi if veg_max_ndvi is not None else None
            std_ndvi = veg_std_ndvi if veg_std_ndvi is not None else 0.0
            mean_ndmi = veg_mean_ndmi if veg_mean_ndmi is not None else surface_mean_ndmi

            # 8. Spatial Discretization Accounting
            raster_discretized_area_ha = round(total_pixels * 0.01, 3)
            discretization_delta_ha = round(raster_discretized_area_ha - farm_area_ha, 3)

            # 9. Quality Status Classification
            is_small_farm = (farm_area_ha < 0.5) or (n_valid_surface < 5)

            if n_valid_surface == 0:
                quality = "NO_USABLE_OBSERVATION"
                notes = "Zero valid surface pixels inside parcel boundary."
            elif cloud_pct > 50.0:
                quality = "CLOUD_OBSTRUCTED"
                notes = f"Observation obstructed by clouds ({cloud_pct}% cloud masked)."
            elif valid_surface_coverage_pct < 50.0:
                quality = "LOW_VALID_PIXEL_COVERAGE"
                notes = f"Low valid surface coverage ({valid_surface_coverage_pct}% of parcel)."
            elif n_veg < 5:
                quality = "INSUFFICIENT_VEGETATION_PIXELS"
                notes = f"Insufficient vegetation canopy pixels ({n_veg} pixels); {n_soil} bare soil pixels detected."
            elif is_small_farm:
                quality = "SMALL_FARM_WARNING"
                notes = f"Farm parcel ({farm_area_ha:.2f} ha, {n_valid_surface} pixels) is subject to 10m Sentinel-2 boundary edge effects."
            elif (n_cloud + n_other) > 0:
                quality = "VALID_OBSERVATION_WITH_MASKED_PIXELS"
                notes = f"Valid observation with {n_veg} vegetation canopy pixels ({veg_coverage_pct}%) and {n_soil} bare soil pixels ({soil_coverage_pct}%); {n_cloud + n_other} boundary/shadow pixels masked."
            else:
                quality = "VALID_OBSERVATION"
                notes = f"100% cloud-free observation with {n_veg} vegetation canopy pixels."

            meta_tag = (
                f"[veg_px: {n_veg}, soil_px: {n_soil}, water_px: {n_water}, "
                f"veg_ndvi: {veg_mean_ndvi}, veg_ndmi: {veg_mean_ndmi}, soil_ndvi: {bare_soil_mean_ndvi}, "
                f"poly_ha: {farm_area_ha}, raster_ha: {raster_discretized_area_ha}, rad: {conv_status}]"
            )
            notes = f"{notes} {meta_tag}"

            dt_str = props.get("datetime")
            obs_dt = (
                datetime.fromisoformat(dt_str.replace("Z", "+00:00")).replace(tzinfo=None)
                if dt_str
                else (observation_date or datetime.utcnow())
            )

            # Persist derived raster maps if farm_id is provided
            if farm_id:
                classes_dict = {
                    "vegetation_pixels": n_veg,
                    "bare_soil_pixels": n_soil,
                    "water_pixels": n_water,
                    "cloud_masked_pixels": n_cloud,
                    "other_masked_pixels": n_other,
                }
                try:
                    save_derived_raster_maps(
                        farm_id=str(farm_id),
                        product_id=feature.get("id", "S2B_43QDA_20261104_0_L2A"),
                        obs_date=obs_dt,
                        b04_raw=b04_raw,
                        b08_raw=b08_raw,
                        b11_raw=b11_raw,
                        scl=scl,
                        farm_mask=farm_mask,
                        transform=transform_b08,
                        crs=str(raster_crs),
                        scale=scale,
                        offset=offset,
                        classes=classes_dict,
                    )
                except Exception as ex:
                    logger.warning("Failed to save derived raster maps: %s", ex)

            return {
                "observation_date": obs_dt,
                "product_id": feature.get("id", "S2B_43QDA_20261104_0_L2A"),
                "tile_id": "43QDA",
                "sensor": "Sentinel-2 L2A",
                "processing_baseline": f"N{props.get('s2:processing_baseline', '05.13').replace('.', '')}",
                "product_cloud_coverage_percent": round(float(props.get("eo:cloud_cover", 0.0)), 2),
                "mean_ndvi": mean_ndvi,
                "median_ndvi": median_ndvi,
                "min_ndvi": min_ndvi,
                "max_ndvi": max_ndvi,
                "std_ndvi": std_ndvi,
                "mean_ndmi": mean_ndmi,
                "surface_mean_ndvi": surface_mean_ndvi,
                "surface_mean_ndmi": surface_mean_ndmi,
                "vegetation_pixel_count": n_veg,
                "bare_soil_pixel_count": n_soil,
                "water_pixel_count": n_water,
                "vegetation_coverage_percent": veg_coverage_pct,
                "bare_soil_coverage_percent": soil_coverage_pct,
                "water_coverage_percent": water_coverage_pct,
                "vegetation_mean_ndvi": veg_mean_ndvi,
                "vegetation_mean_ndmi": veg_mean_ndmi,
                "bare_soil_mean_ndvi": bare_soil_mean_ndvi,
                "valid_pixel_count": n_valid_surface,
                "total_pixel_count": total_pixels,
                "farm_coverage_percent": valid_surface_coverage_pct,
                "cloud_masked_percent": cloud_pct,
                "boundary_masked_percent": other_pct,
                "polygon_area_hectares": farm_area_ha,
                "raster_discretized_area_hectares": raster_discretized_area_ha,
                "discretization_delta_hectares": discretization_delta_ha,
                "spatial_resolution_meters": 10.0,
                "b11_native_resolution_meters": 20.0,
                "b08_native_resolution_meters": 10.0,
                "target_grid_meters": 10.0,
                "resampling_method": "bilinear",
                "resampling_notes": "Resampled 20m SWIR (B11) to 10m grid (Bilinear). Note: Resampling does not create native 10m information.",
                "scl_resampling_method": "nearest_neighbour",
                "quality_status": quality,
                "quality_notes": notes,
                "is_small_farm_warning": is_small_farm,
                "copernicus_provider_status": "LIVE_SENTINEL_2_L2A_RASTER",
                "radiometric_conversion_provenance": conv_status,
                "data_attribution": "Copernicus Sentinel data [2026], processed by ESA, hosted on AWS by Element 84.",
                "raster_crs": raster_crs,
                "asset_urls": {
                    "b04": b04_url,
                    "b08": b08_url,
                    "b11": b11_url,
                    "scl": scl_url,
                },
            }
        except Exception as e:
            logger.error("Error in fetch_live_raster_indices: %s", e, exc_info=True)
            return None

    def compute_polygon_indices(
        self,
        polygon_geojson: Dict[str, Any],
        farm_area_ha: float,
        observation_date: Optional[datetime] = None,
        use_live_raster: bool = True,
        farm_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Calculates NDVI, NDMI, and spatial quality statistics for a farm polygon.
        If use_live_raster=True, attempts real live raster retrieval and clipping.
        If live raster retrieval fails or is unavailable, fails closed:
        returns quality_status="NO_USABLE_OBSERVATION" and copernicus_provider_status="PROVIDER_UNAVAILABLE"
        without generating fake records, hash-based simulation, or synthetic rasters.
        """
        if use_live_raster:
            live_res = self.fetch_live_raster_indices(
                polygon_geojson=polygon_geojson,
                farm_area_ha=farm_area_ha,
                observation_date=observation_date,
                farm_id=farm_id,
            )
            if live_res is not None:
                return live_res

        # Fail-closed retrieval: when live Sentinel-2 retrieval fails or no usable scene is found,
        # return quality_status="NO_USABLE_OBSERVATION" and copernicus_provider_status="PROVIDER_UNAVAILABLE",
        # without generating or persisting fake records or synthetic rasters.
        obs_date = observation_date or datetime.utcnow()
        return {
            "observation_date": obs_date,
            "product_id": None,
            "tile_id": None,
            "sensor": "Sentinel-2 L2A",
            "processing_baseline": None,
            "mean_ndvi": None,
            "median_ndvi": None,
            "min_ndvi": None,
            "max_ndvi": None,
            "std_ndvi": None,
            "mean_ndmi": None,
            "surface_mean_ndvi": None,
            "surface_mean_ndmi": None,
            "valid_pixel_count": 0,
            "total_pixel_count": 0,
            "farm_coverage_percent": 0.0,
            "cloud_masked_percent": 0.0,
            "spatial_resolution_meters": 10.0,
            "b11_native_resolution_meters": 20.0,
            "b08_native_resolution_meters": 10.0,
            "target_grid_meters": 10.0,
            "resampling_method": "bilinear",
            "resampling_notes": "Resampled 20m SWIR (B11) to 10m grid (Bilinear). Note: Resampling does not create native 10m information.",
            "scl_resampling_method": "nearest_neighbour",
            "quality_status": "NO_USABLE_OBSERVATION",
            "quality_notes": "Live Sentinel-2 observation unavailable or failed retrieval. No synthetic data generated.",
            "is_small_farm_warning": False,
            "copernicus_provider_status": "PROVIDER_UNAVAILABLE",
            "radiometric_conversion_provenance": "NONE",
            "data_attribution": "Copernicus Sentinel data [2026], processed by ESA, hosted on AWS by Element 84.",
        }


copernicus_client = CopernicusClient()
