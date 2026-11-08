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

  // SCL Class-Segregated Counts & Coverage
  final int? vegetationPixelCount;
  final int? bareSoilPixelCount;
  final int? waterPixelCount;
  final double? vegetationCoveragePercent;
  final double? bareSoilCoveragePercent;
  final double? waterCoveragePercent;

  // Pure Class-4 Canopy & Class-5 Soil Metrics
  final double? vegetationMeanNdvi;
  final double? vegetationMeanNdmi;
  final double? bareSoilMeanNdvi;

  // Spatial Discretization & Lineage Provenance
  final double? polygonAreaHectares;
  final double? rasterDiscretizedAreaHectares;
  final String? radiometricConversionProvenance;
  final String dataAttribution;

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
    this.vegetationPixelCount,
    this.bareSoilPixelCount,
    this.waterPixelCount,
    this.vegetationCoveragePercent,
    this.bareSoilCoveragePercent,
    this.waterCoveragePercent,
    this.vegetationMeanNdvi,
    this.vegetationMeanNdmi,
    this.bareSoilMeanNdvi,
    this.polygonAreaHectares,
    this.rasterDiscretizedAreaHectares,
    this.radiometricConversionProvenance,
    this.dataAttribution = 'Copernicus Sentinel data [2026], processed by ESA, hosted on AWS by Element 84.',
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
      vegetationPixelCount: json['vegetation_pixel_count'] as int?,
      bareSoilPixelCount: json['bare_soil_pixel_count'] as int?,
      waterPixelCount: json['water_pixel_count'] as int?,
      vegetationCoveragePercent: (json['vegetation_coverage_percent'] as num?)?.toDouble(),
      bareSoilCoveragePercent: (json['bare_soil_coverage_percent'] as num?)?.toDouble(),
      waterCoveragePercent: (json['water_coverage_percent'] as num?)?.toDouble(),
      vegetationMeanNdvi: (json['vegetation_mean_ndvi'] as num?)?.toDouble(),
      vegetationMeanNdmi: (json['vegetation_mean_ndmi'] as num?)?.toDouble(),
      bareSoilMeanNdvi: (json['bare_soil_mean_ndvi'] as num?)?.toDouble(),
      polygonAreaHectares: (json['polygon_area_hectares'] as num?)?.toDouble(),
      rasterDiscretizedAreaHectares: (json['raster_discretized_area_hectares'] as num?)?.toDouble(),
      radiometricConversionProvenance: json['radiometric_conversion_provenance'] as String?,
      dataAttribution: json['data_attribution'] as String? ??
          'Copernicus Sentinel data [2026], processed by ESA, hosted on AWS by Element 84.',
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

  final int? vegetationPixelCount;
  final int? bareSoilPixelCount;
  final double? vegetationCoveragePercent;
  final double? bareSoilCoveragePercent;
  final double? vegetationMeanNdvi;
  final double? vegetationMeanNdmi;

  VegetationTimeSeriesPoint({
    required this.date,
    this.meanNdvi,
    this.medianNdvi,
    this.meanNdmi,
    required this.validPixels,
    required this.cloudMaskedPercent,
    required this.qualityStatus,
    this.vegetationPixelCount,
    this.bareSoilPixelCount,
    this.vegetationCoveragePercent,
    this.bareSoilCoveragePercent,
    this.vegetationMeanNdvi,
    this.vegetationMeanNdmi,
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
      vegetationPixelCount: json['vegetation_pixel_count'] as int?,
      bareSoilPixelCount: json['bare_soil_pixel_count'] as int?,
      vegetationCoveragePercent: (json['vegetation_coverage_percent'] as num?)?.toDouble(),
      bareSoilCoveragePercent: (json['bare_soil_coverage_percent'] as num?)?.toDouble(),
      vegetationMeanNdvi: (json['vegetation_mean_ndvi'] as num?)?.toDouble(),
      vegetationMeanNdmi: (json['vegetation_mean_ndmi'] as num?)?.toDouble(),
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

class SatelliteSpatialMetadata {
  final String farmId;
  final String productId;
  final DateTime observationDate;
  final List<double> bounds; // [min_lon, min_lat, max_lon, max_lat]
  final int width;
  final int height;
  final double spatialResolutionMeters;
  final double b11NativeResolutionMeters;
  final int vegetationPixelCount;
  final int bareSoilPixelCount;
  final int waterPixelCount;
  final int cloudMaskedPixelCount;
  final int boundaryMaskedPixelCount;
  final int totalPixelCount;
  final String ndviMapUrl;
  final String ndmiMapUrl;
  final String sclMapUrl;
  final String scientificDisclosure;

  SatelliteSpatialMetadata({
    required this.farmId,
    required this.productId,
    required this.observationDate,
    required this.bounds,
    required this.width,
    required this.height,
    required this.spatialResolutionMeters,
    required this.b11NativeResolutionMeters,
    required this.vegetationPixelCount,
    required this.bareSoilPixelCount,
    required this.waterPixelCount,
    required this.cloudMaskedPixelCount,
    required this.boundaryMaskedPixelCount,
    required this.totalPixelCount,
    required this.ndviMapUrl,
    required this.ndmiMapUrl,
    required this.sclMapUrl,
    required this.scientificDisclosure,
  });

  factory SatelliteSpatialMetadata.fromJson(Map<String, dynamic> json) {
    return SatelliteSpatialMetadata(
      farmId: json['farm_id'] as String? ?? '',
      productId: json['product_id'] as String? ?? '',
      observationDate: json['observation_date'] != null
          ? DateTime.tryParse(json['observation_date'] as String) ?? DateTime.now()
          : DateTime.now(),
      bounds: (json['bounds'] as List<dynamic>?)?.map((e) => (e as num).toDouble()).toList() ?? [0.0, 0.0, 0.0, 0.0],
      width: json['width'] as int? ?? 40,
      height: json['height'] as int? ?? 40,
      spatialResolutionMeters: (json['spatial_resolution_meters'] as num?)?.toDouble() ?? 10.0,
      b11NativeResolutionMeters: (json['b11_native_resolution_meters'] as num?)?.toDouble() ?? 20.0,
      vegetationPixelCount: json['vegetation_pixel_count'] as int? ?? 0,
      bareSoilPixelCount: json['bare_soil_pixel_count'] as int? ?? 0,
      waterPixelCount: json['water_pixel_count'] as int? ?? 0,
      cloudMaskedPixelCount: json['cloud_masked_pixel_count'] as int? ?? 0,
      boundaryMaskedPixelCount: json['boundary_masked_pixel_count'] as int? ?? 0,
      totalPixelCount: json['total_pixel_count'] as int? ?? 0,
      ndviMapUrl: json['ndvi_map_url'] as String? ?? '',
      ndmiMapUrl: json['ndmi_map_url'] as String? ?? '',
      sclMapUrl: json['scl_map_url'] as String? ?? '',
      scientificDisclosure: json['scientific_disclosure'] as String? ?? '',
    );
  }
}
