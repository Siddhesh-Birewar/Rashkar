/**
 * CropNet AI — Geospatial Utilities for Farm Polygon Mapping.
 *
 * Implements WGS84 spherical geodesic area calculations, GeoJSON EPSG:4326 conversions,
 * centroid calculations, and geometry validation.
 *
 * Note: Frontend area calculations serve as live previews for the farmer. Authoritative
 * calculations are performed by PostGIS / PyProj on the FastAPI backend upon registration.
 */

import type { GeoJSONPolygon } from "./api/types";

export interface LatLngPoint {
  lat: number;
  lng: number;
}

/**
 * Taluka center coordinates (Pune District Pilot Region)
 * Format: [latitude, longitude]
 */
export const TALUKA_CENTERS: Record<string, [number, number]> = {
  Baramati: [18.1506, 74.5772],
  Indapur: [18.1150, 75.0200],
  Maval: [18.7520, 73.5350],
  Mulshi: [18.5050, 73.5120],
  Haveli: [18.5204, 73.8567],
  Shirur: [18.8256, 74.3789],
  Daund: [18.4638, 74.5794],
};

/**
 * Calculates geodesic area on WGS84 sphere in hectares.
 * @param coords Array of [lat, lng] coordinates
 */
export function calculateGeodesicAreaHectares(coords: [number, number][]): number {
  if (!coords || coords.length < 3) return 0.0;

  const earthRadius = 6378137.0; // meters (WGS84 equatorial radius)
  let area = 0.0;

  for (let i = 0; i < coords.length; i++) {
    const p1 = coords[i];
    const p2 = coords[(i + 1) % coords.length];

    const radLat1 = (p1[0] * Math.PI) / 180.0;
    const radLat2 = (p2[0] * Math.PI) / 180.0;
    const radLonDiff = ((p2[1] - p1[1]) * Math.PI) / 180.0;

    area += radLonDiff * (2.0 + Math.sin(radLat1) + Math.sin(radLat2));
  }

  area = Math.abs((area * earthRadius * earthRadius) / 4.0);
  return area / 10000.0; // convert square meters to hectares
}

/**
 * Converts hectares to acres using the standard international factor (1 ha = 2.47105 acres).
 */
export function hectaresToAcres(hectares: number): number {
  return hectares * 2.47105;
}

/**
 * Formats area into a human-readable preview object.
 */
export function formatAreaPreview(hectares: number): {
  hectares: number;
  acres: number;
  haText: string;
  acresText: string;
  summary: string;
} {
  const acres = hectaresToAcres(hectares);
  const haText = hectares < 0.01 ? "< 0.01 ha" : `${hectares.toFixed(2)} ha`;
  const acresText = acres < 0.01 ? "< 0.01 ac" : `${acres.toFixed(2)} acres`;
  const summary = `${haText} (${acresText})`;

  return {
    hectares,
    acres,
    haText,
    acresText,
    summary,
  };
}

/**
 * Converts internal [lat, lng] point array into a valid GeoJSON Polygon (EPSG:4326).
 * GeoJSON standard requires [longitude, latitude] coordinate pairs and a closed ring
 * (first and last coordinate must be identical).
 */
export function latLngsToGeoJSONPolygon(latLngs: [number, number][]): GeoJSONPolygon {
  if (latLngs.length < 3) {
    throw new Error("A polygon requires at least 3 points to form a closed ring.");
  }

  // Convert [lat, lng] -> [lng, lat]
  const ring: [number, number][] = latLngs.map(([lat, lng]) => [
    Number(lng.toFixed(7)),
    Number(lat.toFixed(7)),
  ]);

  // Ensure closed ring (first coordinate equals last)
  const first = ring[0];
  const last = ring[ring.length - 1];
  if (first[0] !== last[0] || first[1] !== last[1]) {
    ring.push([first[0], first[1]]);
  }

  return {
    type: "Polygon",
    coordinates: [ring],
  };
}

/**
 * Converts a GeoJSON Polygon into an array of [lat, lng] coordinates for Leaflet display.
 * Strips the redundant closing point if present.
 */
export function geoJSONPolygonToLatLngs(geojson?: GeoJSONPolygon | null): [number, number][] {
  if (!geojson || !geojson.coordinates || !geojson.coordinates[0]) {
    return [];
  }

  const ring = geojson.coordinates[0];
  if (!Array.isArray(ring) || ring.length === 0) {
    return [];
  }

  const points: [number, number][] = ring.map(([lng, lat]) => [lat, lng]);

  // Remove redundant closing point if present
  if (points.length >= 4) {
    const first = points[0];
    const last = points[points.length - 1];
    if (Math.abs(first[0] - last[0]) < 1e-6 && Math.abs(first[1] - last[1]) < 1e-6) {
      points.pop();
    }
  }

  return points;
}

/**
 * Computes average centroid [lat, lng] of a collection of points.
 */
export function calculateCentroid(points: [number, number][], fallback: [number, number] = [18.1506, 74.5772]): [number, number] {
  if (!points || points.length === 0) return fallback;

  let sumLat = 0;
  let sumLng = 0;

  for (const [lat, lng] of points) {
    sumLat += lat;
    sumLng += lng;
  }

  return [
    Number((sumLat / points.length).toFixed(6)),
    Number((sumLng / points.length).toFixed(6)),
  ];
}

/**
 * Validates polygon points before submission to backend API.
 */
export function validateFarmPolygon(points: [number, number][]): {
  isValid: boolean;
  error?: string;
} {
  if (!points || points.length < 3) {
    return {
      isValid: false,
      error: `Farm boundary requires at least 3 points (currently has ${points?.length || 0}). Tap on the map to place parcel corners.`,
    };
  }

  // Check latitude/longitude ranges
  for (let i = 0; i < points.length; i++) {
    const [lat, lng] = points[i];
    if (isNaN(lat) || isNaN(lng)) {
      return { isValid: false, error: `Point ${i + 1} has invalid numerical coordinates.` };
    }
    if (lat < -90 || lat > 90) {
      return { isValid: false, error: `Point ${i + 1} latitude (${lat}) is out of bounds [-90, 90].` };
    }
    if (lng < -180 || lng > 180) {
      return { isValid: false, error: `Point ${i + 1} longitude (${lng}) is out of bounds [-180, 180].` };
    }
  }

  // Check for minimum area
  const ha = calculateGeodesicAreaHectares(points);
  if (ha <= 0.0001) {
    return {
      isValid: false,
      error: "Boundary has near-zero area. Please spread out the polygon points around the field perimeter.",
    };
  }

  return { isValid: true };
}
