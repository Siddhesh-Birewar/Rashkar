"""Live Open-Meteo weather adapter with 10-minute coordinate TTL cache and zero fabrication."""

from datetime import datetime
import threading
import time
from typing import Any, Dict, List, Optional, Tuple
import httpx
from sqlalchemy.orm import Session

try:
    from cropnet.services.api.app.models.weather import FarmClimateSummaryModel
except ImportError:
    from app.models.weather import FarmClimateSummaryModel

from ..timezone import IST_ZONE, UTC_ZONE, now_ist


OPEN_METEO_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
WEATHER_CACHE_TTL_SECONDS = 600  # 10 minutes
WEATHER_PROVIDER_NAME = "Open-Meteo High-Res Forecast"

_CACHE_LOCK = threading.Lock()
_FORECAST_CACHE: Dict[Tuple[float, float, int, int], Tuple[float, Dict[str, Any]]] = {}


def clear_weather_cache() -> None:
    """Clear the in-memory Open-Meteo coordinate cache (useful in tests)."""
    with _CACHE_LOCK:
        _FORECAST_CACHE.clear()


def _parse_ist_timestamp(ts_str: str) -> Tuple[str, str]:
    """Parse Open-Meteo Asia/Kolkata timestamp string into IST and UTC ISO strings."""
    try:
        dt = datetime.fromisoformat(ts_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=IST_ZONE)
        else:
            dt = dt.astimezone(IST_ZONE)
        return dt.isoformat(), dt.astimezone(UTC_ZONE).isoformat()
    except Exception:
        return ts_str, ts_str


def fetch_open_meteo_forecast(
    lat: float,
    lon: float,
    past_days: int = 10,
    forecast_days: int = 7,
) -> Dict[str, Any]:
    """
    Fetch live hourly and daily meteorological data from Open-Meteo in Asia/Kolkata timezone.
    Uses a 10-minute coordinate TTL cache. Raises on HTTP/network/schema failure (never fabricates).
    """
    cache_key = (round(float(lat), 3), round(float(lon), 3), int(past_days), int(forecast_days))
    now_mono = time.monotonic()

    with _CACHE_LOCK:
        cached = _FORECAST_CACHE.get(cache_key)
        if cached and now_mono < cached[0]:
            return cached[1]

    params = {
        "latitude": round(float(lat), 4),
        "longitude": round(float(lon), 4),
        "hourly": (
            "temperature_2m,relative_humidity_2m,wind_speed_10m,"
            "shortwave_radiation,direct_normal_irradiance,precipitation"
        ),
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
        "past_days": int(past_days),
        "forecast_days": int(forecast_days),
        "timezone": "Asia/Kolkata",
    }

    with httpx.Client(timeout=6.0) as client:
        resp = client.get(OPEN_METEO_FORECAST_URL, params=params)
        resp.raise_for_status()
        payload = resp.json()

    if not isinstance(payload, dict) or ("hourly" not in payload and "daily" not in payload):
        raise ValueError("Open-Meteo response missing 'hourly' and 'daily' sections.")

    with _CACHE_LOCK:
        _FORECAST_CACHE[cache_key] = (now_mono + WEATHER_CACHE_TTL_SECONDS, payload)

    return payload


def _build_hourly_points(
    raw: Dict[str, Any],
    max_points: int,
    start_from_current_ist_hour: bool = True,
) -> List[Dict[str, Any]]:
    hourly = raw.get("hourly") or {}
    times = hourly.get("time") or []
    temps = hourly.get("temperature_2m") or []
    rhs = hourly.get("relative_humidity_2m") or []
    winds = hourly.get("wind_speed_10m") or []
    solars = (
        hourly.get("shortwave_radiation")
        or hourly.get("direct_normal_irradiance")
        or []
    )
    if not times:
        return []

    wind_unit = str((raw.get("hourly_units") or {}).get("wind_speed_10m", "km/h")).lower()
    wind_is_ms = wind_unit in ("m/s", "ms")

    start_idx = 0
    if start_from_current_ist_hour:
        current_hour_str = now_ist().strftime("%Y-%m-%dT%H:00")
        for idx, t_str in enumerate(times):
            if str(t_str) >= current_hour_str:
                start_idx = idx
                break

    points: List[Dict[str, Any]] = []
    end_idx = min(len(times), start_idx + max_points)
    for idx in range(start_idx, end_idx):
        ta_val = temps[idx] if idx < len(temps) else None
        rh_val = rhs[idx] if idx < len(rhs) else None
        w_val = winds[idx] if idx < len(winds) else None
        sw_val = solars[idx] if idx < len(solars) else None

        if w_val is not None:
            wind_ms = round(float(w_val) if wind_is_ms else float(w_val) / 3.6, 2)
        else:
            wind_ms = None

        ts_ist, ts_utc = _parse_ist_timestamp(str(times[idx]))
        points.append(
            {
                "air_temp_c": float(ta_val) if ta_val is not None else None,
                "relative_humidity_pct": float(rh_val) if rh_val is not None else None,
                "wind_speed_ms": wind_ms,
                "solar_irradiance_wm2": float(sw_val) if sw_val is not None else None,
                "timestamp_ist": ts_ist,
                "timestamp_utc": ts_utc,
            }
        )
    return points


def get_worker_hourly_forecast(lat: float, lon: float) -> Dict[str, Any]:
    """Return 0-6h+ hourly forecast slice formatted for WorkerHeatEngine."""
    try:
        raw = fetch_open_meteo_forecast(lat, lon, past_days=0, forecast_days=2)
    except Exception as exc:
        return {
            "status": "WEATHER_UNAVAILABLE",
            "error": f"Open-Meteo request failed: {exc}",
            "hourly": [],
        }

    hourly_points = _build_hourly_points(raw, max_points=12, start_from_current_ist_hour=True)
    valid_points = [
        p
        for p in hourly_points
        if p.get("air_temp_c") is not None and p.get("relative_humidity_pct") is not None
    ]
    if not valid_points:
        return {
            "status": "WEATHER_UNAVAILABLE",
            "error": "Open-Meteo hourly temperature/humidity values unavailable.",
            "hourly": [],
        }

    return {
        "status": "OK",
        "provider": WEATHER_PROVIDER_NAME,
        "elevation_m": raw.get("elevation"),
        "hourly": valid_points,
    }


def get_crop_heat_forecast(lat: float, lon: float) -> Dict[str, Any]:
    """Return hourly (next 24h) and 4+ daily forecast payload formatted for CropHeatEngine."""
    try:
        raw = fetch_open_meteo_forecast(lat, lon, past_days=0, forecast_days=7)
    except Exception as exc:
        return {
            "status": "WEATHER_UNAVAILABLE",
            "error": f"Open-Meteo request failed: {exc}",
        }

    hourly_points = _build_hourly_points(raw, max_points=24, start_from_current_ist_hour=True)
    valid_hourly = [p for p in hourly_points if p.get("air_temp_c") is not None]

    daily = raw.get("daily") or {}
    d_times = daily.get("time") or []
    d_tmax = daily.get("temperature_2m_max") or []
    d_tmin = daily.get("temperature_2m_min") or []
    d_precip = daily.get("precipitation_sum") or []

    today_str = now_ist().strftime("%Y-%m-%d")
    d_start = 0
    for idx, d_str in enumerate(d_times):
        if str(d_str) >= today_str:
            d_start = idx
            break

    daily_points: List[Dict[str, Any]] = []
    for idx in range(d_start, len(d_times)):
        tmax_val = d_tmax[idx] if idx < len(d_tmax) else None
        tmin_val = d_tmin[idx] if idx < len(d_tmin) else None
        if tmax_val is None:
            continue
        precip_val = d_precip[idx] if idx < len(d_precip) else None
        daily_points.append(
            {
                "date": str(d_times[idx]),
                "tmax_c": float(tmax_val),
                "tmin_c": float(tmin_val) if tmin_val is not None else None,
                "precipitation_mm": float(precip_val) if precip_val is not None else 0.0,
            }
        )

    if not valid_hourly and not daily_points:
        return {
            "status": "WEATHER_UNAVAILABLE",
            "error": "Open-Meteo forecast missing both hourly and daily temperature arrays.",
        }

    if valid_hourly:
        peak_pt = max(valid_hourly, key=lambda p: float(p["air_temp_c"]))
        tmax_c = round(float(peak_pt["air_temp_c"]), 1)
        tmin_c = round(min(float(p["air_temp_c"]) for p in valid_hourly), 1)
        rh_pct = peak_pt.get("relative_humidity_pct")
    else:
        tmax_c = round(float(daily_points[0]["tmax_c"]), 1)
        tmin_c = (
            round(float(daily_points[0]["tmin_c"]), 1)
            if daily_points[0].get("tmin_c") is not None
            else None
        )
        rh_pct = None

    if tmax_c is None or (not valid_hourly and tmin_c is None):
        return {
            "status": "WEATHER_UNAVAILABLE",
            "error": "Open-Meteo forecast missing required tmax/tmin temperatures.",
        }

    return {
        "status": "OK",
        "provider": WEATHER_PROVIDER_NAME,
        "elevation_m": raw.get("elevation"),
        "hourly_points": valid_hourly,
        "daily_points": daily_points,
        "tmax_c": tmax_c,
        "tmin_c": tmin_c,
        "relative_humidity_pct": float(rh_pct) if rh_pct is not None else None,
    }


def get_yield_weather_summary(
    farm_id: str,
    lat: float,
    lon: float,
    db: Session,
) -> Optional[Dict[str, Any]]:
    """
    Compute real dry-spell, 3-day rainfall, humidity, and Tmax metrics from Open-Meteo
    historical + forecast series. Returns None on failure so YieldRiskEngine returns
    WEATHER_UNAVAILABLE rather than fabricating 0 dry days.
    """
    try:
        raw = fetch_open_meteo_forecast(lat, lon, past_days=10, forecast_days=3)
    except Exception:
        return None

    daily = raw.get("daily") or {}
    d_times = daily.get("time") or []
    d_precip = daily.get("precipitation_sum") or []
    d_tmax = daily.get("temperature_2m_max") or []

    hourly = raw.get("hourly") or {}
    h_times = hourly.get("time") or []
    h_temps = hourly.get("temperature_2m") or []
    h_rhs = hourly.get("relative_humidity_2m") or []
    h_precip = hourly.get("precipitation") or []

    today_str = now_ist().strftime("%Y-%m-%d")

    past_precip: List[float] = []
    future_precip: List[float] = []
    recent_tmax_vals: List[float] = []

    for idx, d_str in enumerate(d_times):
        p_val = d_precip[idx] if idx < len(d_precip) else None
        t_val = d_tmax[idx] if idx < len(d_tmax) else None
        if str(d_str) <= today_str:
            if p_val is not None:
                past_precip.append(float(p_val))
        if str(d_str) >= today_str:
            if p_val is not None:
                future_precip.append(float(p_val))
            if t_val is not None:
                recent_tmax_vals.append(float(t_val))

    if not past_precip and d_precip:
        past_precip = [float(p) for p in d_precip if p is not None]
    if not future_precip and d_precip:
        future_precip = [float(p) for p in d_precip[-3:] if p is not None]
    if not recent_tmax_vals and d_tmax:
        recent_tmax_vals = [float(t) for t in d_tmax[-3:] if t is not None]

    # Consecutive dry days (< 2.5 mm/day) walking backwards from latest past/today observation
    consecutive_dry_days = 0
    for rain_mm in reversed(past_precip):
        if rain_mm < 2.5:
            consecutive_dry_days += 1
        else:
            break

    if future_precip:
        rolling_3d_rain_mm = sum(future_precip[:3])
    elif h_precip:
        rolling_3d_rain_mm = sum(float(p) for p in h_precip[-72:] if p is not None)
    else:
        return None

    if not past_precip and not future_precip:
        return None

    if recent_tmax_vals:
        tmax_recent_c = max(recent_tmax_vals[:3])
    else:
        valid_h_temps = [float(t) for t in h_temps if t is not None]
        if not valid_h_temps:
            return None
        tmax_recent_c = max(valid_h_temps[-48:])

    current_hour_str = now_ist().strftime("%Y-%m-%dT%H:00")
    h_start = 0
    for idx, ts in enumerate(h_times):
        if str(ts) >= current_hour_str:
            h_start = idx
            break
    rh_slice = [float(r) for r in h_rhs[h_start : h_start + 24] if r is not None]
    if not rh_slice:
        rh_slice = [float(r) for r in h_rhs[-24:] if r is not None]
    if not rh_slice:
        return None
    rh_recent_pct = sum(rh_slice) / len(rh_slice)

    climate_normal_rainfall_mm: Optional[float] = None
    if db is not None:
        climate_summary = (
            db.query(FarmClimateSummaryModel)
            .filter(FarmClimateSummaryModel.farm_id == str(farm_id))
            .order_by(FarmClimateSummaryModel.created_at.desc())
            .first()
        )
        if climate_summary is not None and climate_summary.annual_rainfall_mm is not None:
            climate_normal_rainfall_mm = float(climate_summary.annual_rainfall_mm)

    return {
        "consecutive_dry_days": int(consecutive_dry_days),
        "rolling_3d_rain_mm": round(float(rolling_3d_rain_mm), 1),
        "rh_recent_pct": round(float(rh_recent_pct), 1),
        "tmax_recent_c": round(float(tmax_recent_c), 1),
        "data_source": "Open-Meteo Historical + Forecast",
        "climate_normal_rainfall_mm": climate_normal_rainfall_mm,
    }


__all__ = [
    "fetch_open_meteo_forecast",
    "get_worker_hourly_forecast",
    "get_crop_heat_forecast",
    "get_yield_weather_summary",
    "clear_weather_cache",
]
