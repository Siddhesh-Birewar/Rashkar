import 'package:flutter/foundation.dart';

class SatelliteObservation {
  final String id;
  final String farmId;
  final DateTime observationDate;
  final String productId;
  final String? tileId;
  final String sensor;
  final double? meanNdvi;
  final double? medianNdvi;
  final double? minNdvi;
  final double? maxNdvi;
  final double? stdNdvi;
  final double? meanNdmi;
  final int validPixelCount;
  final int totalPixelCount;
  final double farmCoveragePercent;
  final double cloudMaskedPercent;
  final double spatialResolutionMeters;
  final String qualityStatus;
  final String? qualityNotes;
  final bool isSmallFarmWarning;
  final DateTime createdAt;

  SatelliteObservation({
    required this.id,
    required this.farmId,
    required this.observationDate,
    required this.productId,
    this.tileId,
    required this.sensor,
    this.meanNdvi,
    this.medianNdvi,
    this.minNdvi,
    this.maxNdvi,
    this.stdNdvi,
    this.meanNdmi,
    required this.validPixelCount,
    required this.totalPixelCount,
    required this.farmCoveragePercent,
    required this.cloudMaskedPercent,
    required this.spatialResolutionMeters,
    required this.qualityStatus,
    this.qualityNotes,
    required this.isSmallFarmWarning,
    required this.createdAt,
  });

  factory SatelliteObservation.fromJson(Map<String, dynamic> json) {
    return SatelliteObservation(
      id: json['id'] as String? ?? '',
      farmId: json['farm_id'] as String? ?? '',
      observationDate: json['observation_date'] != null
          ? DateTime.tryParse(json['observation_date'] as String) ?? DateTime.now()
          : DateTime.now(),
      productId: json['product_id'] as String? ?? '',
      tileId: json['tile_id'] as String?,
      sensor: json['sensor'] as String? ?? 'Sentinel-2 L2A',
      meanNdvi: (json['mean_ndvi'] as num?)?.toDouble(),
      medianNdvi: (json['median_ndvi'] as num?)?.toDouble(),
      minNdvi: (json['min_ndvi'] as num?)?.toDouble(),
      maxNdvi: (json['max_ndvi'] as num?)?.toDouble(),
      stdNdvi: (json['std_ndvi'] as num?)?.toDouble(),
      meanNdmi: (json['mean_ndmi'] as num?)?.toDouble(),
      validPixelCount: json['valid_pixel_count'] as int? ?? 0,
      totalPixelCount: json['total_pixel_count'] as int? ?? 0,
      farmCoveragePercent: (json['farm_coverage_percent'] as num?)?.toDouble() ?? 100.0,
      cloudMaskedPercent: (json['cloud_masked_percent'] as num?)?.toDouble() ?? 0.0,
      spatialResolutionMeters: (json['spatial_resolution_meters'] as num?)?.toDouble() ?? 10.0,
      qualityStatus: json['quality_status'] as String? ?? 'VALID_OBSERVATION',
      qualityNotes: json['quality_notes'] as String?,
      isSmallFarmWarning: json['is_small_farm_warning'] as bool? ?? false,
      createdAt: json['created_at'] != null
          ? DateTime.tryParse(json['created_at'] as String) ?? DateTime.now()
          : DateTime.now(),
    );
  }
}

class VegetationTimeSeriesPoint {
  final DateTime date;
  final double? meanNdvi;
  final double? medianNdvi;
  final double? meanNdmi;
  final int validPixels;
  final double cloudMaskedPercent;
  final String qualityStatus;

  VegetationTimeSeriesPoint({
    required this.date,
    this.meanNdvi,
    this.medianNdvi,
    this.meanNdmi,
    required this.validPixels,
    required this.cloudMaskedPercent,
    required this.qualityStatus,
  });

  factory VegetationTimeSeriesPoint.fromJson(Map<String, dynamic> json) {
    return VegetationTimeSeriesPoint(
      date: json['date'] != null
          ? DateTime.tryParse(json['date'] as String) ?? DateTime.now()
          : DateTime.now(),
      meanNdvi: (json['mean_ndvi'] as num?)?.toDouble(),
      medianNdvi: (json['median_ndvi'] as num?)?.toDouble(),
      meanNdmi: (json['mean_ndmi'] as num?)?.toDouble(),
      validPixels: json['valid_pixels'] as int? ?? 0,
      cloudMaskedPercent: (json['cloud_masked_percent'] as num?)?.toDouble() ?? 0.0,
      qualityStatus: json['quality_status'] as String? ?? 'VALID_OBSERVATION',
    );
  }
}

class VegetationTimeSeriesData {
  final String farmId;
  final double farmAreaHectares;
  final bool isSmallFarm;
  final int totalObservations;
  final List<VegetationTimeSeriesPoint> series;
  final String vegetationInterpretation;
  final String scientificDisclaimer;

  VegetationTimeSeriesData({
    required this.farmId,
    required this.farmAreaHectares,
    required this.isSmallFarm,
    required this.totalObservations,
    required this.series,
    required this.vegetationInterpretation,
    required this.scientificDisclaimer,
  });

  factory VegetationTimeSeriesData.fromJson(Map<String, dynamic> json) {
    return VegetationTimeSeriesData(
      farmId: json['farm_id'] as String? ?? '',
      farmAreaHectares: (json['farm_area_hectares'] as num?)?.toDouble() ?? 1.0,
      isSmallFarm: json['is_small_farm_warning'] as bool? ?? (json['is_small_farm'] as bool? ?? false),
      totalObservations: json['total_observations'] as int? ?? 0,
      series: (json['series'] as List<dynamic>?)
              ?.map((e) => VegetationTimeSeriesPoint.fromJson(e as Map<String, dynamic>))
              .toList() ??
          [],
      vegetationInterpretation: json['vegetation_interpretation'] as String? ?? '',
      scientificDisclaimer: json['scientific_disclaimer'] as String? ?? '',
    );
  }
}
