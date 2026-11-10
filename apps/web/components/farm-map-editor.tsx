"use client";

import React, { useEffect, useRef, useState, useCallback } from "react";
import L from "leaflet";
import {
  Layers,
  Locate,
  RotateCcw,
  Trash2,
  AlertCircle,
  CheckCircle2,
  Compass,
  MapPin,
  Loader2,
  Info,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  calculateGeodesicAreaHectares,
  formatAreaPreview,
  TALUKA_CENTERS,
  type LatLngPoint,
} from "@/lib/geo-utils";

export interface FarmMapEditorProps {
  initialPoints?: [number, number][];
  defaultTaluka?: string;
  onChange?: (points: [number, number][], areaPreview: { hectares: number; acres: number }) => void;
  height?: string;
  readOnly?: boolean;
}

type MapLayerType = "satellite" | "streets";

export function FarmMapEditor({
  initialPoints = [],
  defaultTaluka = "Baramati",
  onChange,
  height = "h-[440px] sm:h-[500px]",
  readOnly = false,
}: FarmMapEditorProps) {
  const mapContainerRef = useRef<HTMLDivElement | null>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const tileLayerRef = useRef<L.TileLayer | null>(null);
  const markersRef = useRef<L.Marker[]>([]);
  const polylineRef = useRef<L.Polyline | null>(null);
  const polygonRef = useRef<L.Polygon | null>(null);

  const [points, setPoints] = useState<[number, number][]>(initialPoints);
  const [mapLayer, setMapLayer] = useState<MapLayerType>("satellite");
  const [isLocating, setIsLocating] = useState(false);
  const [gpsStatus, setGpsStatus] = useState<string | null>(null);
  const [tileError, setTileError] = useState(false);

  // Read MapTiler API Key from browser environment variable
  const maptilerApiKey = process.env.NEXT_PUBLIC_MAPTILER_API_KEY || "";

  // Geodesic area calculation for preview
  const areaPreview = formatAreaPreview(calculateGeodesicAreaHectares(points));

  // Determine center based on initial points or default taluka
  const defaultCenter = TALUKA_CENTERS[defaultTaluka] || TALUKA_CENTERS["Baramati"];
  const initialCenter = initialPoints.length > 0 ? initialPoints[0] : defaultCenter;

  // Notify parent of changes
  const notifyChange = useCallback(
    (newPoints: [number, number][]) => {
      setPoints(newPoints);
      if (onChange) {
        const ha = calculateGeodesicAreaHectares(newPoints);
        const acres = ha * 2.47105;
        onChange(newPoints, { hectares: ha, acres });
      }
    },
    [onChange]
  );

  // Custom vertex marker icon
  const createVertexIcon = (index: number) => {
    return L.divIcon({
      className: "custom-farm-vertex",
      html: `
        <div style="
          display: flex;
          align-items: center;
          justify-content: center;
          width: 26px;
          height: 26px;
          background: #1b5e20;
          color: #ffffff;
          font-weight: 800;
          font-size: 11px;
          border: 2.5px solid #ffffff;
          border-radius: 50%;
          box-shadow: 0 3px 8px rgba(0, 0, 0, 0.4);
          cursor: grab;
          user-select: none;
        ">${index + 1}</div>
      `,
      iconSize: [26, 26],
      iconAnchor: [13, 13],
    });
  };

  // Helper to get tile URL
  const getTileUrl = useCallback(
    (type: MapLayerType) => {
      if (!maptilerApiKey) {
        // Graceful fallback to OpenStreetMap if key is not configured
        return {
          url: "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
          attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        };
      }

      if (type === "satellite") {
        return {
          url: `https://api.maptiler.com/maps/satellite/{z}/{x}/{y}.jpg?key=${maptilerApiKey}`,
          attribution: '&copy; <a href="https://www.maptiler.com/">MapTiler</a> &copy; OpenStreetMap',
        };
      } else {
        return {
          url: `https://api.maptiler.com/maps/streets-v2/{z}/{x}/{y}.png?key=${maptilerApiKey}`,
          attribution: '&copy; <a href="https://www.maptiler.com/">MapTiler</a> &copy; OpenStreetMap',
        };
      }
    },
    [maptilerApiKey]
  );

  // Initialize Map
  useEffect(() => {
    if (!mapContainerRef.current || mapInstanceRef.current) return;

    const map = L.map(mapContainerRef.current, {
      center: initialCenter,
      zoom: initialPoints.length > 0 ? 16 : 14,
      zoomControl: false,
    });

    // Add zoom control to bottom right for thumb-friendly mobile layout
    L.control
      .zoom({
        position: "bottomright",
      })
      .addTo(map);

    const tileConfig = getTileUrl("satellite");
    const tileLayer = L.tileLayer(tileConfig.url, {
      maxZoom: 20,
      attribution: tileConfig.attribution,
    }).addTo(map);

    tileLayer.on("tileerror", () => {
      setTileError(true);
    });

    tileLayerRef.current = tileLayer;
    mapInstanceRef.current = map;

    // Map click handler to add new polygon points
    if (!readOnly) {
      map.on("click", (e: L.LeafletMouseEvent) => {
        const newCoord: [number, number] = [
          Number(e.latlng.lat.toFixed(7)),
          Number(e.latlng.lng.toFixed(7)),
        ];

        setPoints((prev) => {
          const updated = [...prev, newCoord];
          if (onChange) {
            const ha = calculateGeodesicAreaHectares(updated);
            onChange(updated, { hectares: ha, acres: ha * 2.47105 });
          }
          return updated;
        });
      });
    }

    return () => {
      map.remove();
      mapInstanceRef.current = null;
    };
  }, [readOnly, getTileUrl, initialCenter, initialPoints.length, onChange]);

  // Update tile layer when switching between satellite and streets
  useEffect(() => {
    if (!mapInstanceRef.current || !tileLayerRef.current) return;

    const map = mapInstanceRef.current;
    map.removeLayer(tileLayerRef.current);

    const tileConfig = getTileUrl(mapLayer);
    const newTileLayer = L.tileLayer(tileConfig.url, {
      maxZoom: 20,
      attribution: tileConfig.attribution,
    }).addTo(map);

    newTileLayer.on("tileerror", () => {
      setTileError(true);
    });

    tileLayerRef.current = newTileLayer;
  }, [mapLayer, getTileUrl]);

  // Update markers and polygon overlay whenever `points` change
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map) return;

    // Clear existing vertex markers
    markersRef.current.forEach((marker) => marker.remove());
    markersRef.current = [];

    // Clear existing polyline and polygon
    if (polylineRef.current) {
      polylineRef.current.remove();
      polylineRef.current = null;
    }
    if (polygonRef.current) {
      polygonRef.current.remove();
      polygonRef.current = null;
    }

    if (points.length === 0) return;

    // Create draggable markers for each vertex
    points.forEach((point, idx) => {
      const marker = L.marker(point, {
        icon: createVertexIcon(idx),
        draggable: !readOnly,
      }).addTo(map);

      if (!readOnly) {
        marker.on("drag", (e: any) => {
          const newLatLng = e.target.getLatLng();
          setPoints((currentPoints) => {
            const next = [...currentPoints];
            next[idx] = [
              Number(newLatLng.lat.toFixed(7)),
              Number(newLatLng.lng.toFixed(7)),
            ];
            if (onChange) {
              const ha = calculateGeodesicAreaHectares(next);
              onChange(next, { hectares: ha, acres: ha * 2.47105 });
            }
            return next;
          });
        });

        marker.bindTooltip(`Corner #${idx + 1} (drag to adjust)`, {
          direction: "top",
          offset: [0, -14],
        });
      }

      markersRef.current.push(marker);
    });

    // Draw boundary line / polygon
    if (points.length >= 3) {
      // Form closed polygon
      const polygon = L.polygon(points, {
        color: "#1b5e20",
        weight: 3,
        opacity: 0.9,
        fillColor: "#2e7d32",
        fillOpacity: 0.35,
      }).addTo(map);

      polygonRef.current = polygon;
    } else if (points.length === 2) {
      // Connect line between 2 points
      const polyline = L.polyline(points, {
        color: "#1b5e20",
        weight: 3,
        opacity: 0.8,
        dashArray: "6, 8",
      }).addTo(map);

      polylineRef.current = polyline;
    }
  }, [points, readOnly, onChange]);

  // Initial bounds fitting
  useEffect(() => {
    if (!mapInstanceRef.current || points.length < 3) return;
    try {
      const bounds = L.latLngBounds(points);
      mapInstanceRef.current.fitBounds(bounds, {
        padding: [45, 45],
        maxZoom: 18,
      });
    } catch {
      // Ignore fitBounds errors on empty points
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // GPS Location Handler
  const handleLocateGPS = () => {
    if (!navigator.geolocation) {
      setGpsStatus("Geolocation is not supported by your browser.");
      return;
    }

    setIsLocating(true);
    setGpsStatus(null);

    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setIsLocating(false);
        const { latitude, longitude } = pos.coords;
        if (mapInstanceRef.current) {
          mapInstanceRef.current.flyTo([latitude, longitude], 17, {
            duration: 1.5,
          });
        }
        setGpsStatus(`GPS detected: ${latitude.toFixed(4)}, ${longitude.toFixed(4)}`);
        setTimeout(() => setGpsStatus(null), 4000);
      },
      (err) => {
        setIsLocating(false);
        let msg = "Could not detect GPS location.";
        if (err.code === err.PERMISSION_DENIED) {
          msg = "GPS permission was denied. Centering on taluka instead.";
        } else if (err.code === err.TIMEOUT) {
          msg = "GPS location request timed out.";
        }
        setGpsStatus(msg);

        // Fallback to taluka center
        const fallback = TALUKA_CENTERS[defaultTaluka] || TALUKA_CENTERS["Baramati"];
        if (mapInstanceRef.current) {
          mapInstanceRef.current.flyTo(fallback, 14, { duration: 1.2 });
        }
        setTimeout(() => setGpsStatus(null), 5000);
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 30000 }
    );
  };

  // Undo Last Vertex
  const handleUndo = () => {
    if (points.length === 0) return;
    const next = points.slice(0, -1);
    notifyChange(next);
  };

  // Clear / Reset All Vertices
  const handleClear = () => {
    if (points.length >= 3) {
      if (!window.confirm("Are you sure you want to clear the entire farm boundary?")) {
        return;
      }
    }
    notifyChange([]);
  };

  // Pan to Taluka Center
  const handleTalukaJump = (talukaName: string) => {
    const center = TALUKA_CENTERS[talukaName];
    if (center && mapInstanceRef.current) {
      mapInstanceRef.current.flyTo(center, 15, { duration: 1.2 });
    }
  };

  return (
    <div className="relative flex flex-col overflow-hidden rounded-2xl border border-line bg-canvas shadow-sm">
      {/* ── Top Bar: Status & Area Preview ── */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-line bg-white/95 px-4 py-3 backdrop-blur">
        <div className="flex items-center gap-2">
          <span className="grid size-8 place-items-center rounded-xl bg-forest/10 text-forest">
            <Compass size={17} />
          </span>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-ink">
                {points.length === 0
                  ? "Tap map to mark parcel corners"
                  : points.length === 1
                  ? "Corner 1 placed"
                  : points.length === 2
                  ? "2 corners placed (need 1 more)"
                  : `Parcel Enclosed (${points.length} corners)`}
              </span>
              <Badge
                variant={points.length >= 3 ? "default" : "outline"}
                className={points.length >= 3 ? "bg-leaf text-white border-0" : ""}
              >
                {points.length} {points.length === 1 ? "corner" : "corners"}
              </Badge>
            </div>
            <p className="text-[11px] text-muted">
              {points.length >= 3 ? (
                <>
                  Estimated live preview:{" "}
                  <strong className="text-ink">{areaPreview.summary}</strong>
                </>
              ) : (
                "Click on boundaries, bunds, or fence lines"
              )}
            </p>
          </div>
        </div>

        {/* Layer & Taluka Shortcuts */}
        <div className="flex items-center gap-1.5">
          <Button
            type="button"
            variant="outline"
            size="sm"
            className="h-8 gap-1.5 text-xs"
            onClick={() => setMapLayer(mapLayer === "satellite" ? "streets" : "satellite")}
            title="Toggle between Satellite Imagery and Street Map"
          >
            <Layers size={14} className="text-leaf" />
            <span className="capitalize">{mapLayer === "satellite" ? "Satellite" : "Street"}</span>
          </Button>

          <Button
            type="button"
            variant="outline"
            size="sm"
            className="h-8 gap-1.5 text-xs"
            onClick={handleLocateGPS}
            disabled={isLocating}
            title="Detect GPS Current Location"
          >
            {isLocating ? (
              <Loader2 size={14} className="animate-spin text-leaf" />
            ) : (
              <Locate size={14} className="text-leaf" />
            )}
            <span className="hidden sm:inline">GPS</span>
          </Button>
        </div>
      </div>

      {/* GPS Status Alert */}
      {gpsStatus && (
        <div className="flex items-center gap-2 bg-amber-50 px-4 py-2 text-xs text-amber-900 border-b border-amber-200">
          <Info size={14} className="shrink-0 text-amber-600" />
          <span>{gpsStatus}</span>
        </div>
      )}

      {/* Map Tile Key Notice */}
      {!maptilerApiKey && (
        <div className="flex items-center gap-2 bg-sky-50 px-4 py-1.5 text-[11px] text-sky-900 border-b border-sky-200">
          <Info size={13} className="shrink-0 text-sky-600" />
          <span>
            Using OpenStreetMap base tiles. Configure <code>NEXT_PUBLIC_MAPTILER_API_KEY</code> for high-resolution satellite imagery.
          </span>
        </div>
      )}

      {/* ── Interactive Leaflet Map Container ── */}
      <div className={`relative w-full ${height} bg-[#142318]`}>
        <div ref={mapContainerRef} className="h-full w-full z-0" />

        {/* Floating Quick Action Overlay (Bottom Left) */}
        {!readOnly && (
          <div className="absolute bottom-4 left-4 z-10 flex flex-wrap gap-2">
            <Button
              type="button"
              variant="secondary"
              size="sm"
              onClick={handleUndo}
              disabled={points.length === 0}
              className="h-8 bg-white/95 text-xs text-ink shadow-md backdrop-blur hover:bg-white"
            >
              <RotateCcw size={14} /> Undo Point
            </Button>

            <Button
              type="button"
              variant="secondary"
              size="sm"
              onClick={handleClear}
              disabled={points.length === 0}
              className="h-8 bg-white/95 text-xs text-red-700 shadow-md backdrop-blur hover:bg-red-50"
            >
              <Trash2 size={14} /> Clear Boundary
            </Button>
          </div>
        )}

        {/* Floating Center on Taluka Selector (Top Left) */}
        <div className="absolute top-3 left-3 z-10 flex items-center gap-1 rounded-xl bg-white/90 p-1 shadow-md backdrop-blur border border-line text-xs">
          <MapPin size={13} className="ml-1.5 text-leaf shrink-0" />
          <span className="text-[11px] font-semibold text-muted pr-1">Jump to:</span>
          {["Baramati", "Indapur", "Maval", "Mulshi"].map((t) => (
            <button
              key={t}
              type="button"
              onClick={() => handleTalukaJump(t)}
              className="rounded-lg px-2 py-1 text-[11px] font-medium text-ink transition hover:bg-[#e8f5e9] hover:text-leaf active:bg-[#c8e6c9]"
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      {/* ── Bottom Info Legend ── */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-t border-line bg-canvas px-4 py-2.5 text-[11px] text-muted">
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1">
            <span className="inline-block size-2 rounded-full bg-leaf" />
            <span>Green ring: Farm Polygon</span>
          </span>
          <span className="hidden sm:inline text-line">•</span>
          <span className="hidden sm:inline">Drag any numbered marker to fine-tune corners</span>
        </div>

        <div className="text-[10px] text-muted/80">
          Authoritative PostGIS geometry validated upon save
        </div>
      </div>
    </div>
  );
}
export default FarmMapEditor;
