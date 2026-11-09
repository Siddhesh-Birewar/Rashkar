import 'package:flutter/material.dart';

Map<String, dynamic>? _asStringMap(dynamic val) {
  if (val == null) return null;
  if (val is Map<String, dynamic>) return val;
  if (val is Map) return val.cast<String, dynamic>();
  return null;
}

/// Data availability states as defined in the Phase 5.9A Farm Health Snapshot Contract.
enum DataAvailabilityState {
  available,
  partiallyAvailable,
  notAvailable,
  stale,
  insufficientEvidence;

  static DataAvailabilityState fromString(String? val) {
    if (val == null) return DataAvailabilityState.notAvailable;
    switch (val.toUpperCase().replaceAll('-', '_')) {
      case 'AVAILABLE':
        return DataAvailabilityState.available;
      case 'PARTIALLY_AVAILABLE':
        return DataAvailabilityState.partiallyAvailable;
      case 'STALE':
        return DataAvailabilityState.stale;
      case 'INSUFFICIENT_EVIDENCE':
        return DataAvailabilityState.insufficientEvidence;
      case 'NOT_AVAILABLE':
      default:
        return DataAvailabilityState.notAvailable;
    }
  }

  String toApiString() {
    switch (this) {
      case DataAvailabilityState.available:
        return 'AVAILABLE';
      case DataAvailabilityState.partiallyAvailable:
        return 'PARTIALLY_AVAILABLE';
      case DataAvailabilityState.stale:
        return 'STALE';
      case DataAvailabilityState.insufficientEvidence:
        return 'INSUFFICIENT_EVIDENCE';
      case DataAvailabilityState.notAvailable:
        return 'NOT_AVAILABLE';
    }
  }

  String get displayName {
    switch (this) {
      case DataAvailabilityState.available:
        return 'Available';
      case DataAvailabilityState.partiallyAvailable:
        return 'Partially Available';
      case DataAvailabilityState.stale:
        return 'Stale';
      case DataAvailabilityState.insufficientEvidence:
        return 'Insufficient Evidence';
      case DataAvailabilityState.notAvailable:
        return 'Not Available';
    }
  }

  Color get color {
    switch (this) {
      case DataAvailabilityState.available:
        return const Color(0xFF2E7D32); // Green
      case DataAvailabilityState.partiallyAvailable:
        return const Color(0xFFF57C00); // Orange
      case DataAvailabilityState.stale:
        return const Color(0xFFD97706); // Amber
      case DataAvailabilityState.insufficientEvidence:
        return const Color(0xFFC62828); // Red
      case DataAvailabilityState.notAvailable:
        return const Color(0xFF757575); // Grey
    }
  }

  Color get backgroundColor {
    switch (this) {
      case DataAvailabilityState.available:
        return const Color(0xFFE8F5E9);
      case DataAvailabilityState.partiallyAvailable:
        return const Color(0xFFFFF3E0);
      case DataAvailabilityState.stale:
        return const Color(0xFFFEF3C7);
      case DataAvailabilityState.insufficientEvidence:
        return const Color(0xFFFFEBEE);
      case DataAvailabilityState.notAvailable:
        return const Color(0xFFF5F5F5);
    }
  }

  IconData get icon {
    switch (this) {
      case DataAvailabilityState.available:
        return Icons.check_circle_rounded;
      case DataAvailabilityState.partiallyAvailable:
        return Icons.warning_amber_rounded;
      case DataAvailabilityState.stale:
        return Icons.history_rounded;
      case DataAvailabilityState.insufficientEvidence:
        return Icons.error_outline_rounded;
      case DataAvailabilityState.notAvailable:
        return Icons.remove_circle_outline_rounded;
    }
  }
}

/// Categorical overview of evidence availability across all 5 evaluated domains.
class OverallEvidenceOverview {
  final int domainsAvailable;
  final int domainsPartiallyAvailable;
  final int domainsStale;
  final int domainsNotAvailable;
  final int domainsInsufficientEvidence;
  final int totalDomains;
  final String actionableSummary;

  const OverallEvidenceOverview({
    required this.domainsAvailable,
    required this.domainsPartiallyAvailable,
    required this.domainsStale,
    required this.domainsNotAvailable,
    required this.domainsInsufficientEvidence,
    this.totalDomains = 5,
    required this.actionableSummary,
  });

  factory OverallEvidenceOverview.fromJson(Map<String, dynamic> json) {
    return OverallEvidenceOverview(
      domainsAvailable: (json['domains_available'] as num?)?.toInt() ?? 0,
      domainsPartiallyAvailable: (json['domains_partially_available'] as num?)?.toInt() ?? 0,
      domainsStale: (json['domains_stale'] as num?)?.toInt() ?? 0,
      domainsNotAvailable: (json['domains_not_available'] as num?)?.toInt() ?? 0,
      domainsInsufficientEvidence: (json['domains_insufficient_evidence'] as num?)?.toInt() ?? 0,
      totalDomains: (json['total_domains'] as num?)?.toInt() ?? 5,
      actionableSummary: json['actionable_summary'] as String? ?? 'No summary available.',
    );
  }

  Map<String, dynamic> toJson() => {
    'domains_available': domainsAvailable,
    'domains_partially_available': domainsPartiallyAvailable,
    'domains_stale': domainsStale,
    'domains_not_available': domainsNotAvailable,
    'domains_insufficient_evidence': domainsInsufficientEvidence,
    'total_domains': totalDomains,
    'actionable_summary': actionableSummary,
  };
}

/// Key chemical and physical soil indicators.
class SoilKeyIndicators {
  final double? soilPh;
  final double? organicCarbonPct;
  final double? electricalConductivityDsM;
  final double? availableNitrogenKgHa;
  final double? availablePhosphorusKgHa;
  final double? availablePotassiumKgHa;
  final String? soilTexture;
  final double? cationExchangeCapacity;

  const SoilKeyIndicators({
    this.soilPh,
    this.organicCarbonPct,
    this.electricalConductivityDsM,
    this.availableNitrogenKgHa,
    this.availablePhosphorusKgHa,
    this.availablePotassiumKgHa,
    this.soilTexture,
    this.cationExchangeCapacity,
  });

  factory SoilKeyIndicators.fromJson(Map<String, dynamic>? json) {
    if (json == null) return const SoilKeyIndicators();
    return SoilKeyIndicators(
      soilPh: (json['soil_ph'] as num?)?.toDouble(),
      organicCarbonPct: (json['organic_carbon_pct'] as num?)?.toDouble(),
      electricalConductivityDsM: (json['electrical_conductivity_ds_m'] as num?)?.toDouble(),
      availableNitrogenKgHa: (json['available_nitrogen_kg_ha'] as num?)?.toDouble(),
      availablePhosphorusKgHa: (json['available_phosphorus_kg_ha'] as num?)?.toDouble(),
      availablePotassiumKgHa: (json['available_potassium_kg_ha'] as num?)?.toDouble(),
      soilTexture: json['soil_texture'] as String?,
      cationExchangeCapacity: (json['cation_exchange_capacity'] as num?)?.toDouble(),
    );
  }

  Map<String, dynamic> toJson() => {
    'soil_ph': soilPh,
    'organic_carbon_pct': organicCarbonPct,
    'electrical_conductivity_ds_m': electricalConductivityDsM,
    'available_nitrogen_kg_ha': availableNitrogenKgHa,
    'available_phosphorus_kg_ha': availablePhosphorusKgHa,
    'available_potassium_kg_ha': availablePotassiumKgHa,
    'soil_texture': soilTexture,
    'cation_exchange_capacity': cationExchangeCapacity,
  };
}

/// Domain summary for Soil Intelligence.
class SoilDomainSummary {
  final DataAvailabilityState availabilityState;
  final DateTime? lastUpdated;
  final int? dataAgeDays;
  final String? provenance;
  final String? laboratoryName;
  final String? sampleDepth;
  final SoilKeyIndicators keyIndicators;
  final List<String> missingCriticalParameters;
  final List<String> agronomicNotes;

  const SoilDomainSummary({
    required this.availabilityState,
    this.lastUpdated,
    this.dataAgeDays,
    this.provenance,
    this.laboratoryName,
    this.sampleDepth,
    this.keyIndicators = const SoilKeyIndicators(),
    this.missingCriticalParameters = const [],
    this.agronomicNotes = const [],
  });

  factory SoilDomainSummary.fromJson(Map<String, dynamic>? json) {
    if (json == null) {
      return const SoilDomainSummary(availabilityState: DataAvailabilityState.notAvailable);
    }
    return SoilDomainSummary(
      availabilityState: DataAvailabilityState.fromString(json['availability_state'] as String?),
      lastUpdated: json['last_updated'] != null ? DateTime.tryParse(json['last_updated'] as String) : null,
      dataAgeDays: (json['data_age_days'] as num?)?.toInt(),
      provenance: json['provenance'] as String?,
      laboratoryName: json['laboratory_name'] as String?,
      sampleDepth: json['sample_depth'] as String?,
      keyIndicators: SoilKeyIndicators.fromJson(_asStringMap(json['key_indicators'])),
      missingCriticalParameters: (json['missing_critical_parameters'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          const [],
      agronomicNotes:
          (json['agronomic_notes'] as List<dynamic>?)?.map((e) => e.toString()).toList() ?? const [],
    );
  }

  Map<String, dynamic> toJson() => {
    'availability_state': availabilityState.toApiString(),
    'last_updated': lastUpdated?.toIso8601String(),
    'data_age_days': dataAgeDays,
    'provenance': provenance,
    'laboratory_name': laboratoryName,
    'sample_depth': sampleDepth,
    'key_indicators': keyIndicators.toJson(),
    'missing_critical_parameters': missingCriticalParameters,
    'agronomic_notes': agronomicNotes,
  };
}

/// Individual water source detail item.
class WaterSourceSummaryItem {
  final String sourceId;
  final String sourceType;
  final String name;
  final String seasonalAvailability;
  final String reliability;
  final String irrigationMethod;
  final double? measuredCapacityLph;
  final String capacityProvenance;

  const WaterSourceSummaryItem({
    required this.sourceId,
    required this.sourceType,
    required this.name,
    required this.seasonalAvailability,
    required this.reliability,
    required this.irrigationMethod,
    this.measuredCapacityLph,
    required this.capacityProvenance,
  });

  factory WaterSourceSummaryItem.fromJson(Map<String, dynamic> json) {
    return WaterSourceSummaryItem(
      sourceId: json['source_id'] as String? ?? '',
      sourceType: json['source_type'] as String? ?? 'other',
      name: json['name'] as String? ?? 'Water Source',
      seasonalAvailability: json['seasonal_availability'] as String? ?? 'perennial',
      reliability: json['reliability'] as String? ?? 'moderate',
      irrigationMethod: json['irrigation_method'] as String? ?? 'drip',
      measuredCapacityLph: (json['measured_capacity_lph'] as num?)?.toDouble(),
      capacityProvenance: json['capacity_provenance'] as String? ?? 'FARMER_REPORTED',
    );
  }

  Map<String, dynamic> toJson() => {
    'source_id': sourceId,
    'source_type': sourceType,
    'name': name,
    'seasonal_availability': seasonalAvailability,
    'reliability': reliability,
    'irrigation_method': irrigationMethod,
    'measured_capacity_lph': measuredCapacityLph,
    'capacity_provenance': capacityProvenance,
  };
}

/// Water quality key indicators.
class WaterKeyIndicators {
  final double? ph;
  final double? electricalConductivityDsM;
  final double? tdsMgL;
  final double? sar;
  final String? sarStatus;
  final double? rscMeqL;
  final String? rscStatus;
  final double? chlorideMeqL;
  final double? boronMgL;

  const WaterKeyIndicators({
    this.ph,
    this.electricalConductivityDsM,
    this.tdsMgL,
    this.sar,
    this.sarStatus,
    this.rscMeqL,
    this.rscStatus,
    this.chlorideMeqL,
    this.boronMgL,
  });

  factory WaterKeyIndicators.fromJson(Map<String, dynamic>? json) {
    if (json == null) return const WaterKeyIndicators();
    return WaterKeyIndicators(
      ph: (json['ph'] as num?)?.toDouble(),
      electricalConductivityDsM: (json['electrical_conductivity_ds_m'] as num?)?.toDouble(),
      tdsMgL: (json['tds_mg_l'] as num?)?.toDouble(),
      sar: (json['sar'] as num?)?.toDouble(),
      sarStatus: json['sar_status'] as String?,
      rscMeqL: (json['rsc_meq_l'] as num?)?.toDouble(),
      rscStatus: json['rsc_status'] as String?,
      chlorideMeqL: (json['chloride_meq_l'] as num?)?.toDouble(),
      boronMgL: (json['boron_mg_l'] as num?)?.toDouble(),
    );
  }

  Map<String, dynamic> toJson() => {
    'ph': ph,
    'electrical_conductivity_ds_m': electricalConductivityDsM,
    'tds_mg_l': tdsMgL,
    'sar': sar,
    'sar_status': sarStatus,
    'rsc_meq_l': rscMeqL,
    'rsc_status': rscStatus,
    'chloride_meq_l': chlorideMeqL,
    'boron_mg_l': boronMgL,
  };
}

/// Institutional water evaluation finding (e.g. BIS IS 11624:2019 or ICAR-CSSRI).
class WaterEvaluationFinding {
  final String parameterKey;
  final String parameterName;
  final String hazardLevel;
  final String hazardTitle;
  final String standardApplied;
  final String managementGuidance;

  const WaterEvaluationFinding({
    required this.parameterKey,
    required this.parameterName,
    required this.hazardLevel,
    required this.hazardTitle,
    required this.standardApplied,
    required this.managementGuidance,
  });

  factory WaterEvaluationFinding.fromJson(Map<String, dynamic> json) {
    return WaterEvaluationFinding(
      parameterKey: json['parameter_key'] as String? ?? '',
      parameterName: json['parameter_name'] as String? ?? '',
      hazardLevel: json['hazard_level'] as String? ?? 'UNVERIFIED',
      hazardTitle: json['hazard_title'] as String? ?? '',
      standardApplied: json['standard_applied'] as String? ?? '',
      managementGuidance: json['management_guidance'] as String? ?? '',
    );
  }

  Map<String, dynamic> toJson() => {
    'parameter_key': parameterKey,
    'parameter_name': parameterName,
    'hazard_level': hazardLevel,
    'hazard_title': hazardTitle,
    'standard_applied': standardApplied,
    'management_guidance': managementGuidance,
  };

  Color get hazardColor {
    switch (hazardLevel.toUpperCase()) {
      case 'SAFE':
        return const Color(0xFF2E7D32);
      case 'LOW':
        return const Color(0xFF558B2F);
      case 'MEDIUM':
        return const Color(0xFFF57C00);
      case 'HIGH':
        return const Color(0xFFE65100);
      case 'VERY_HIGH':
      case 'HAZARDOUS':
        return const Color(0xFFC62828);
      default:
        return const Color(0xFF757575);
    }
  }
}

/// Domain summary for Irrigation Water Intelligence.
class WaterDomainSummary {
  final DataAvailabilityState availabilityState;
  final DateTime? lastUpdated;
  final int? dataAgeDays;
  final String? provenance;
  final int registeredSourcesCount;
  final List<WaterSourceSummaryItem> sources;
  final String? laboratoryName;
  final WaterKeyIndicators keyIndicators;
  final List<WaterEvaluationFinding> institutionalEvaluations;
  final List<String> missingCriticalParameters;

  const WaterDomainSummary({
    required this.availabilityState,
    this.lastUpdated,
    this.dataAgeDays,
    this.provenance,
    this.registeredSourcesCount = 0,
    this.sources = const [],
    this.laboratoryName,
    this.keyIndicators = const WaterKeyIndicators(),
    this.institutionalEvaluations = const [],
    this.missingCriticalParameters = const [],
  });

  factory WaterDomainSummary.fromJson(Map<String, dynamic>? json) {
    if (json == null) {
      return const WaterDomainSummary(availabilityState: DataAvailabilityState.notAvailable);
    }
    return WaterDomainSummary(
      availabilityState: DataAvailabilityState.fromString(json['availability_state'] as String?),
      lastUpdated: json['last_updated'] != null ? DateTime.tryParse(json['last_updated'] as String) : null,
      dataAgeDays: (json['data_age_days'] as num?)?.toInt(),
      provenance: json['provenance'] as String?,
      registeredSourcesCount: (json['registered_sources_count'] as num?)?.toInt() ?? 0,
      sources: (json['sources'] as List<dynamic>?)
              ?.map((e) => WaterSourceSummaryItem.fromJson(_asStringMap(e) ?? const {}))
              .toList() ??
          const [],
      laboratoryName: json['laboratory_name'] as String?,
      keyIndicators: WaterKeyIndicators.fromJson(_asStringMap(json['key_indicators'])),
      institutionalEvaluations: (json['institutional_evaluations'] as List<dynamic>?)
              ?.map((e) => WaterEvaluationFinding.fromJson(_asStringMap(e) ?? const {}))
              .toList() ??
          const [],
      missingCriticalParameters: (json['missing_critical_parameters'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          const [],
    );
  }

  Map<String, dynamic> toJson() => {
    'availability_state': availabilityState.toApiString(),
    'last_updated': lastUpdated?.toIso8601String(),
    'data_age_days': dataAgeDays,
    'provenance': provenance,
    'registered_sources_count': registeredSourcesCount,
    'sources': sources.map((e) => e.toJson()).toList(),
    'laboratory_name': laboratoryName,
    'key_indicators': keyIndicators.toJson(),
    'institutional_evaluations': institutionalEvaluations.map((e) => e.toJson()).toList(),
    'missing_critical_parameters': missingCriticalParameters,
  };
}

/// Satellite raster map relative URLs.
class SatelliteRasterUrls {
  final String? ndviMapUrl;
  final String? ndmiMapUrl;
  final String? sclMapUrl;

  const SatelliteRasterUrls({
    this.ndviMapUrl,
    this.ndmiMapUrl,
    this.sclMapUrl,
  });

  factory SatelliteRasterUrls.fromJson(Map<String, dynamic>? json) {
    if (json == null) return const SatelliteRasterUrls();
    return SatelliteRasterUrls(
      ndviMapUrl: json['ndvi_map_url'] as String?,
      ndmiMapUrl: json['ndmi_map_url'] as String?,
      sclMapUrl: json['scl_map_url'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
    'ndvi_map_url': ndviMapUrl,
    'ndmi_map_url': ndmiMapUrl,
    'scl_map_url': sclMapUrl,
  };
}

/// Domain summary for Copernicus Sentinel-2 Satellite Vegetation.
class SatelliteDomainSummary {
  final DataAvailabilityState availabilityState;
  final DateTime? observationDate;
  final int? observationAgeDays;
  final String? provenance;
  final String? sensor;
  final String? productId;
  final double? canopyNdvi;
  final double? canopyNdmi;
  final double? compositeMeanNdvi;
  final double? bareSoilMeanNdvi;
  final double? vegetationCoveragePercent;
  final double? bareSoilCoveragePercent;
  final double? cloudMaskedPercent;
  final int validPixelCount;
  final String? qualityStatus;
  final bool isSmallFarmWarning;
  final SatelliteRasterUrls rasterMaps;
  final String? agronomicInterpretation;
  final String scientificDisclaimer;

  const SatelliteDomainSummary({
    required this.availabilityState,
    this.observationDate,
    this.observationAgeDays,
    this.provenance = 'COPERNICUS_SENTINEL_2_L2A',
    this.sensor = 'Sentinel-2 L2A',
    this.productId,
    this.canopyNdvi,
    this.canopyNdmi,
    this.compositeMeanNdvi,
    this.bareSoilMeanNdvi,
    this.vegetationCoveragePercent,
    this.bareSoilCoveragePercent,
    this.cloudMaskedPercent,
    this.validPixelCount = 0,
    this.qualityStatus,
    this.isSmallFarmWarning = false,
    this.rasterMaps = const SatelliteRasterUrls(),
    this.agronomicInterpretation,
    this.scientificDisclaimer =
        'Sentinel-2 NDVI and NDMI reflect surface optical reflectance (10m GSD). They are indirect canopy vigor indicators, NOT direct disease pathogen or yield diagnoses.',
  });

  factory SatelliteDomainSummary.fromJson(Map<String, dynamic>? json) {
    if (json == null) {
      return const SatelliteDomainSummary(availabilityState: DataAvailabilityState.notAvailable);
    }
    return SatelliteDomainSummary(
      availabilityState: DataAvailabilityState.fromString(json['availability_state'] as String?),
      observationDate: json['observation_date'] != null ? DateTime.tryParse(json['observation_date'] as String) : null,
      observationAgeDays: (json['observation_age_days'] as num?)?.toInt(),
      provenance: json['provenance'] as String? ?? 'COPERNICUS_SENTINEL_2_L2A',
      sensor: json['sensor'] as String? ?? 'Sentinel-2 L2A',
      productId: json['product_id'] as String?,
      canopyNdvi: (json['canopy_ndvi'] as num?)?.toDouble(),
      canopyNdmi: (json['canopy_ndmi'] as num?)?.toDouble(),
      compositeMeanNdvi: (json['composite_mean_ndvi'] as num?)?.toDouble(),
      bareSoilMeanNdvi: (json['bare_soil_mean_ndvi'] as num?)?.toDouble(),
      vegetationCoveragePercent: (json['vegetation_coverage_percent'] as num?)?.toDouble(),
      bareSoilCoveragePercent: (json['bare_soil_coverage_percent'] as num?)?.toDouble(),
      cloudMaskedPercent: (json['cloud_masked_percent'] as num?)?.toDouble(),
      validPixelCount: (json['valid_pixel_count'] as num?)?.toInt() ?? 0,
      qualityStatus: json['quality_status'] as String?,
      isSmallFarmWarning: json['is_small_farm_warning'] as bool? ?? false,
      rasterMaps: SatelliteRasterUrls.fromJson(_asStringMap(json['raster_maps'])),
      agronomicInterpretation: json['agronomic_interpretation'] as String?,
      scientificDisclaimer: json['scientific_disclaimer'] as String? ??
          'Sentinel-2 NDVI and NDMI reflect surface optical reflectance (10m GSD). They are indirect canopy vigor indicators, NOT direct disease pathogen or yield diagnoses.',
    );
  }

  Map<String, dynamic> toJson() => {
    'availability_state': availabilityState.toApiString(),
    'observation_date': observationDate?.toIso8601String(),
    'observation_age_days': observationAgeDays,
    'provenance': provenance,
    'sensor': sensor,
    'product_id': productId,
    'canopy_ndvi': canopyNdvi,
    'canopy_ndmi': canopyNdmi,
    'composite_mean_ndvi': compositeMeanNdvi,
    'bare_soil_mean_ndvi': bareSoilMeanNdvi,
    'vegetation_coverage_percent': vegetationCoveragePercent,
    'bare_soil_coverage_percent': bareSoilCoveragePercent,
    'cloud_masked_percent': cloudMaskedPercent,
    'valid_pixel_count': validPixelCount,
    'quality_status': qualityStatus,
    'is_small_farm_warning': isSmallFarmWarning,
    'raster_maps': rasterMaps.toJson(),
    'agronomic_interpretation': agronomicInterpretation,
    'scientific_disclaimer': scientificDisclaimer,
  };
}

/// Observed current weather parameters.
class CurrentWeatherSummary {
  final DateTime? observationTime;
  final String source;
  final String provenance;
  final double? temperatureC;
  final double? humidityPercent;
  final double? precipitationMm;
  final double? windSpeedMs;
  final String? weatherCondition;
  final String? weatherDescription;

  const CurrentWeatherSummary({
    this.observationTime,
    this.source = 'OPENWEATHER_OBSERVATION',
    this.provenance = 'OPENWEATHER_OBSERVATION',
    this.temperatureC,
    this.humidityPercent,
    this.precipitationMm,
    this.windSpeedMs,
    this.weatherCondition,
    this.weatherDescription,
  });

  factory CurrentWeatherSummary.fromJson(Map<String, dynamic>? json) {
    if (json == null) return const CurrentWeatherSummary();
    return CurrentWeatherSummary(
      observationTime:
          json['observation_time'] != null ? DateTime.tryParse(json['observation_time'] as String) : null,
      source: json['source'] as String? ?? 'OPENWEATHER_OBSERVATION',
      provenance: json['provenance'] as String? ?? 'OPENWEATHER_OBSERVATION',
      temperatureC: (json['temperature_c'] as num?)?.toDouble(),
      humidityPercent: (json['humidity_percent'] as num?)?.toDouble(),
      precipitationMm: (json['precipitation_mm'] as num?)?.toDouble(),
      windSpeedMs: (json['wind_speed_ms'] as num?)?.toDouble(),
      weatherCondition: json['weather_condition'] as String?,
      weatherDescription: json['weather_description'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
    'observation_time': observationTime?.toIso8601String(),
    'source': source,
    'provenance': provenance,
    'temperature_c': temperatureC,
    'humidity_percent': humidityPercent,
    'precipitation_mm': precipitationMm,
    'wind_speed_ms': windSpeedMs,
    'weather_condition': weatherCondition,
    'weather_description': weatherDescription,
  };
}

/// Weather forecast summary.
class ForecastSummary {
  final int forecastDaysCount;
  final String provenance;
  final double? next48hRainExpectedMm;
  final double? tempMinC;
  final double? tempMaxC;
  final List<String> weatherAlerts;

  const ForecastSummary({
    this.forecastDaysCount = 0,
    this.provenance = 'OPENWEATHER_FORECAST',
    this.next48hRainExpectedMm,
    this.tempMinC,
    this.tempMaxC,
    this.weatherAlerts = const [],
  });

  factory ForecastSummary.fromJson(Map<String, dynamic>? json) {
    if (json == null) return const ForecastSummary();
    return ForecastSummary(
      forecastDaysCount: (json['forecast_days_count'] as num?)?.toInt() ?? 0,
      provenance: json['provenance'] as String? ?? 'OPENWEATHER_FORECAST',
      next48hRainExpectedMm: (json['next_48h_rain_expected_mm'] as num?)?.toDouble(),
      tempMinC: (json['temp_min_c'] as num?)?.toDouble(),
      tempMaxC: (json['temp_max_c'] as num?)?.toDouble(),
      weatherAlerts:
          (json['weather_alerts'] as List<dynamic>?)?.map((e) => e.toString()).toList() ?? const [],
    );
  }

  Map<String, dynamic> toJson() => {
    'forecast_days_count': forecastDaysCount,
    'provenance': provenance,
    'next_48h_rain_expected_mm': next48hRainExpectedMm,
    'temp_min_c': tempMinC,
    'temp_max_c': tempMaxC,
    'weather_alerts': weatherAlerts,
  };
}

/// 30-year NASA POWER climatology normals.
class ClimateNormalsSummary {
  final double? annualRainfallMm;
  final double? monsoonRainfallMm;
  final double? meanTemperatureC;
  final String? potentialWaterStressIndicator;
  final String provenance;

  const ClimateNormalsSummary({
    this.annualRainfallMm,
    this.monsoonRainfallMm,
    this.meanTemperatureC,
    this.potentialWaterStressIndicator,
    this.provenance = 'NASA_POWER_CLIMATOLOGY',
  });

  factory ClimateNormalsSummary.fromJson(Map<String, dynamic>? json) {
    if (json == null) return const ClimateNormalsSummary();
    return ClimateNormalsSummary(
      annualRainfallMm: (json['annual_rainfall_mm'] as num?)?.toDouble(),
      monsoonRainfallMm: (json['monsoon_rainfall_mm'] as num?)?.toDouble(),
      meanTemperatureC: (json['mean_temperature_c'] as num?)?.toDouble(),
      potentialWaterStressIndicator: json['potential_water_stress_indicator'] as String?,
      provenance: json['provenance'] as String? ?? 'NASA_POWER_CLIMATOLOGY',
    );
  }

  Map<String, dynamic> toJson() => {
    'annual_rainfall_mm': annualRainfallMm,
    'monsoon_rainfall_mm': monsoonRainfallMm,
    'mean_temperature_c': meanTemperatureC,
    'potential_water_stress_indicator': potentialWaterStressIndicator,
    'provenance': provenance,
  };
}

/// Domain summary for Agro-meteorology and Climate.
class WeatherDomainSummary {
  final DataAvailabilityState availabilityState;
  final DateTime? lastUpdated;
  final CurrentWeatherSummary currentWeather;
  final ForecastSummary forecast;
  final ClimateNormalsSummary climateNormals;

  const WeatherDomainSummary({
    required this.availabilityState,
    this.lastUpdated,
    this.currentWeather = const CurrentWeatherSummary(),
    this.forecast = const ForecastSummary(),
    this.climateNormals = const ClimateNormalsSummary(),
  });

  factory WeatherDomainSummary.fromJson(Map<String, dynamic>? json) {
    if (json == null) {
      return const WeatherDomainSummary(availabilityState: DataAvailabilityState.notAvailable);
    }
    return WeatherDomainSummary(
      availabilityState: DataAvailabilityState.fromString(json['availability_state'] as String?),
      lastUpdated: json['last_updated'] != null ? DateTime.tryParse(json['last_updated'] as String) : null,
      currentWeather: CurrentWeatherSummary.fromJson(_asStringMap(json['current_weather'])),
      forecast: ForecastSummary.fromJson(_asStringMap(json['forecast'])),
      climateNormals: ClimateNormalsSummary.fromJson(_asStringMap(json['climate_normals'])),
    );
  }

  Map<String, dynamic> toJson() => {
    'availability_state': availabilityState.toApiString(),
    'last_updated': lastUpdated?.toIso8601String(),
    'current_weather': currentWeather.toJson(),
    'forecast': forecast.toJson(),
    'climate_normals': climateNormals.toJson(),
  };
}

/// Crop suitability evaluation item from deterministic decision engine.
class CropSuitabilityItem {
  final String cropId;
  final String commonName;
  final String? marathiName;
  final String decisionState;
  final List<String> limitingFactors;
  final String? irrigationGuidance;

  const CropSuitabilityItem({
    required this.cropId,
    required this.commonName,
    this.marathiName,
    required this.decisionState,
    this.limitingFactors = const [],
    this.irrigationGuidance,
  });

  factory CropSuitabilityItem.fromJson(Map<String, dynamic> json) {
    return CropSuitabilityItem(
      cropId: json['crop_id'] as String? ?? '',
      commonName: json['common_name'] as String? ?? '',
      marathiName: json['marathi_name'] as String?,
      decisionState: json['decision_state'] as String? ?? 'ABSTAIN_INSUFFICIENT_EVIDENCE',
      limitingFactors:
          (json['limiting_factors'] as List<dynamic>?)?.map((e) => e.toString()).toList() ?? const [],
      irrigationGuidance: json['irrigation_guidance'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
    'crop_id': cropId,
    'common_name': commonName,
    'marathi_name': marathiName,
    'decision_state': decisionState,
    'limiting_factors': limitingFactors,
    'irrigation_guidance': irrigationGuidance,
  };

  Color get decisionColor {
    switch (decisionState.toUpperCase()) {
      case 'VERIFIED_SUITABLE':
        return const Color(0xFF2E7D32);
      case 'CONDITIONALLY_SUITABLE_PENDING_DATA':
        return const Color(0xFFF57C00);
      case 'NOT_RECOMMENDED':
      case 'DISQUALIFIED':
        return const Color(0xFFC62828);
      default:
        return const Color(0xFF757575);
    }
  }
}

/// Domain summary for Deterministic Crop Context.
class CropContextDomainSummary {
  final DataAvailabilityState availabilityState;
  final String provenance;
  final DateTime? evaluatedAt;
  final String? targetSeason;
  final String? talukaResolved;
  final int evaluatedCropsCount;
  final List<CropSuitabilityItem> suitableCrops;
  final List<CropSuitabilityItem> conditionallySuitableCrops;
  final List<CropSuitabilityItem> disqualifiedCrops;
  final List<CropSuitabilityItem> abstainCrops;
  final List<String> topLimitingFactors;
  final int pendingFollowupQuestionsCount;

  const CropContextDomainSummary({
    required this.availabilityState,
    this.provenance = 'CROP_DECISION_ENGINE',
    this.evaluatedAt,
    this.targetSeason,
    this.talukaResolved,
    this.evaluatedCropsCount = 0,
    this.suitableCrops = const [],
    this.conditionallySuitableCrops = const [],
    this.disqualifiedCrops = const [],
    this.abstainCrops = const [],
    this.topLimitingFactors = const [],
    this.pendingFollowupQuestionsCount = 0,
  });

  factory CropContextDomainSummary.fromJson(Map<String, dynamic>? json) {
    if (json == null) {
      return const CropContextDomainSummary(availabilityState: DataAvailabilityState.notAvailable);
    }
    return CropContextDomainSummary(
      availabilityState: DataAvailabilityState.fromString(json['availability_state'] as String?),
      provenance: json['provenance'] as String? ?? 'CROP_DECISION_ENGINE',
      evaluatedAt: json['evaluated_at'] != null ? DateTime.tryParse(json['evaluated_at'] as String) : null,
      targetSeason: json['target_season'] as String?,
      talukaResolved: json['taluka_resolved'] as String?,
      evaluatedCropsCount: (json['evaluated_crops_count'] as num?)?.toInt() ?? 0,
      suitableCrops: (json['suitable_crops'] as List<dynamic>?)
              ?.map((e) => CropSuitabilityItem.fromJson(_asStringMap(e) ?? const {}))
              .toList() ??
          const [],
      conditionallySuitableCrops: (json['conditionally_suitable_crops'] as List<dynamic>?)
              ?.map((e) => CropSuitabilityItem.fromJson(_asStringMap(e) ?? const {}))
              .toList() ??
          const [],
      disqualifiedCrops: (json['disqualified_crops'] as List<dynamic>?)
              ?.map((e) => CropSuitabilityItem.fromJson(_asStringMap(e) ?? const {}))
              .toList() ??
          const [],
      abstainCrops: (json['abstain_crops'] as List<dynamic>?)
              ?.map((e) => CropSuitabilityItem.fromJson(_asStringMap(e) ?? const {}))
              .toList() ??
          const [],
      topLimitingFactors:
          (json['top_limiting_factors'] as List<dynamic>?)?.map((e) => e.toString()).toList() ?? const [],
      pendingFollowupQuestionsCount: (json['pending_followup_questions_count'] as num?)?.toInt() ?? 0,
    );
  }

  Map<String, dynamic> toJson() => {
    'availability_state': availabilityState.toApiString(),
    'provenance': provenance,
    'evaluated_at': evaluatedAt?.toIso8601String(),
    'target_season': targetSeason,
    'taluka_resolved': talukaResolved,
    'evaluated_crops_count': evaluatedCropsCount,
    'suitable_crops': suitableCrops.map((e) => e.toJson()).toList(),
    'conditionally_suitable_crops': conditionallySuitableCrops.map((e) => e.toJson()).toList(),
    'disqualified_crops': disqualifiedCrops.map((e) => e.toJson()).toList(),
    'abstain_crops': abstainCrops.map((e) => e.toJson()).toList(),
    'top_limiting_factors': topLimitingFactors,
    'pending_followup_questions_count': pendingFollowupQuestionsCount,
  };
}

/// Farm observation timeline item for Section 7.
class FarmObservationTimelineItem {
  final String id;
  final String title;
  final String description;
  final DateTime timestamp;
  final String domain; // soil, water, satellite, weather, crop, parcel
  final DataAvailabilityState state;
  final IconData icon;
  final Color color;
  final String? provenance;

  const FarmObservationTimelineItem({
    required this.id,
    required this.title,
    required this.description,
    required this.timestamp,
    required this.domain,
    required this.state,
    required this.icon,
    required this.color,
    this.provenance,
  });
}

/// Canonical Farm Health Snapshot Response matching Phase 5.9A contract.
class FarmHealthSnapshotResponse {
  final String contractVersion;
  final String farmId;
  final String farmName;
  final String ownerId;
  final String taluka;
  final String district;
  final String state;
  final double calculatedAreaHectares;
  final double calculatedAreaAcres;
  final DateTime snapshotTimestamp;
  final OverallEvidenceOverview overallEvidenceOverview;
  final SoilDomainSummary soil;
  final WaterDomainSummary water;
  final SatelliteDomainSummary satellite;
  final WeatherDomainSummary weather;
  final CropContextDomainSummary cropContext;
  final String governanceNotice;
  final bool isFromCache;
  final DateTime? cachedAt;

  const FarmHealthSnapshotResponse({
    this.contractVersion = '1.0',
    required this.farmId,
    required this.farmName,
    required this.ownerId,
    required this.taluka,
    required this.district,
    required this.state,
    required this.calculatedAreaHectares,
    required this.calculatedAreaAcres,
    required this.snapshotTimestamp,
    required this.overallEvidenceOverview,
    required this.soil,
    required this.water,
    required this.satellite,
    required this.weather,
    required this.cropContext,
    this.governanceNotice =
        'CropNet AI provides independent, evidence-gated agricultural domain summaries. In accordance with institutional agricultural guidelines, no universal health score is computed.',
    this.isFromCache = false,
    this.cachedAt,
  });

  factory FarmHealthSnapshotResponse.fromJson(Map<String, dynamic> json) {
    return FarmHealthSnapshotResponse(
      contractVersion: json['contract_version'] as String? ?? '1.0',
      farmId: json['farm_id'] as String? ?? '',
      farmName: json['farm_name'] as String? ?? 'Unnamed Farm',
      ownerId: json['owner_id'] as String? ?? '',
      taluka: json['taluka'] as String? ?? '',
      district: json['district'] as String? ?? '',
      state: json['state'] as String? ?? '',
      calculatedAreaHectares: (json['calculated_area_hectares'] as num?)?.toDouble() ?? 0.0,
      calculatedAreaAcres: (json['calculated_area_acres'] as num?)?.toDouble() ?? 0.0,
      snapshotTimestamp: json['snapshot_timestamp'] != null
          ? DateTime.tryParse(json['snapshot_timestamp'] as String) ?? DateTime.now()
          : DateTime.now(),
      overallEvidenceOverview: OverallEvidenceOverview.fromJson(
        _asStringMap(json['overall_evidence_overview']) ?? const {},
      ),
      soil: SoilDomainSummary.fromJson(_asStringMap(json['soil'])),
      water: WaterDomainSummary.fromJson(_asStringMap(json['water'])),
      satellite: SatelliteDomainSummary.fromJson(_asStringMap(json['satellite'])),
      weather: WeatherDomainSummary.fromJson(_asStringMap(json['weather'])),
      cropContext: CropContextDomainSummary.fromJson(_asStringMap(json['crop_context'])),
      governanceNotice: json['governance_notice'] as String? ??
          'CropNet AI provides independent, evidence-gated agricultural domain summaries. In accordance with institutional agricultural guidelines, no universal health score is computed.',
      isFromCache: json['is_from_cache'] as bool? ?? false,
      cachedAt: json['cached_at'] != null ? DateTime.tryParse(json['cached_at'] as String) : null,
    );
  }

  FarmHealthSnapshotResponse copyWith({
    String? contractVersion,
    String? farmId,
    String? farmName,
    String? ownerId,
    String? taluka,
    String? district,
    String? state,
    double? calculatedAreaHectares,
    double? calculatedAreaAcres,
    DateTime? snapshotTimestamp,
    OverallEvidenceOverview? overallEvidenceOverview,
    SoilDomainSummary? soil,
    WaterDomainSummary? water,
    SatelliteDomainSummary? satellite,
    WeatherDomainSummary? weather,
    CropContextDomainSummary? cropContext,
    String? governanceNotice,
    bool? isFromCache,
    DateTime? cachedAt,
  }) {
    return FarmHealthSnapshotResponse(
      contractVersion: contractVersion ?? this.contractVersion,
      farmId: farmId ?? this.farmId,
      farmName: farmName ?? this.farmName,
      ownerId: ownerId ?? this.ownerId,
      taluka: taluka ?? this.taluka,
      district: district ?? this.district,
      state: state ?? this.state,
      calculatedAreaHectares: calculatedAreaHectares ?? this.calculatedAreaHectares,
      calculatedAreaAcres: calculatedAreaAcres ?? this.calculatedAreaAcres,
      snapshotTimestamp: snapshotTimestamp ?? this.snapshotTimestamp,
      overallEvidenceOverview: overallEvidenceOverview ?? this.overallEvidenceOverview,
      soil: soil ?? this.soil,
      water: water ?? this.water,
      satellite: satellite ?? this.satellite,
      weather: weather ?? this.weather,
      cropContext: cropContext ?? this.cropContext,
      governanceNotice: governanceNotice ?? this.governanceNotice,
      isFromCache: isFromCache ?? this.isFromCache,
      cachedAt: cachedAt ?? this.cachedAt,
    );
  }

  Map<String, dynamic> toJson() => {
    'contract_version': contractVersion,
    'farm_id': farmId,
    'farm_name': farmName,
    'owner_id': ownerId,
    'taluka': taluka,
    'district': district,
    'state': state,
    'calculated_area_hectares': calculatedAreaHectares,
    'calculated_area_acres': calculatedAreaAcres,
    'snapshot_timestamp': snapshotTimestamp.toIso8601String(),
    'overall_evidence_overview': overallEvidenceOverview.toJson(),
    'soil': soil.toJson(),
    'water': water.toJson(),
    'satellite': satellite.toJson(),
    'weather': weather.toJson(),
    'crop_context': cropContext.toJson(),
    'governance_notice': governanceNotice,
    'is_from_cache': isFromCache,
    'cached_at': cachedAt?.toIso8601String(),
  };

  /// Generates the chronological farm observation timeline from domain timestamps.
  List<FarmObservationTimelineItem> buildTimelineItems() {
    final List<FarmObservationTimelineItem> items = [];

    // Soil observation
    if (soil.lastUpdated != null) {
      items.add(FarmObservationTimelineItem(
        id: 'timeline-soil',
        title: 'Soil Intelligence Update',
        description: soil.laboratoryName != null
            ? 'Lab report confirmed by ${soil.laboratoryName}. Status: ${soil.availabilityState.displayName}'
            : 'Soil profile extracted. Status: ${soil.availabilityState.displayName}',
        timestamp: soil.lastUpdated!,
        domain: 'soil',
        state: soil.availabilityState,
        icon: Icons.layers_rounded,
        color: const Color(0xFF8D6E63),
        provenance: soil.provenance,
      ));
    }

    // Water observation
    if (water.lastUpdated != null) {
      items.add(FarmObservationTimelineItem(
        id: 'timeline-water',
        title: 'Irrigation Water Quality Test',
        description:
            '${water.registeredSourcesCount} source(s) registered. Evaluated under BIS IS 11624:2019 / ICAR-CSSRI. Status: ${water.availabilityState.displayName}',
        timestamp: water.lastUpdated!,
        domain: 'water',
        state: water.availabilityState,
        icon: Icons.water_drop_rounded,
        color: const Color(0xFF0288D1),
        provenance: water.provenance ?? (water.laboratoryName != null ? 'LABORATORY_MEASURED' : 'FARMER_REPORTED'),
      ));
    }

    // Satellite observation
    if (satellite.observationDate != null) {
      items.add(FarmObservationTimelineItem(
        id: 'timeline-satellite',
        title: 'Copernicus Sentinel-2 Overpass',
        description: satellite.canopyNdvi != null
            ? 'Class 4 pure canopy NDVI: ${satellite.canopyNdvi!.toStringAsFixed(2)} | Coverage: ${(satellite.vegetationCoveragePercent ?? 0).toStringAsFixed(1)}%'
            : 'Satellite observation synced. Status: ${satellite.availabilityState.displayName}',
        timestamp: satellite.observationDate!,
        domain: 'satellite',
        state: satellite.availabilityState,
        icon: Icons.satellite_alt_rounded,
        color: const Color(0xFF388E3C),
        provenance: satellite.provenance ?? 'COPERNICUS_SENTINEL_2_L2A',
      ));
    }

    // Weather observation
    if (weather.lastUpdated != null) {
      items.add(FarmObservationTimelineItem(
        id: 'timeline-weather',
        title: 'Agro-Meteorology Collection',
        description: weather.currentWeather.temperatureC != null
            ? 'Observed: ${weather.currentWeather.temperatureC!.toStringAsFixed(1)}°C, ${weather.currentWeather.weatherCondition ?? "Normal"}. Forecast: ${weather.forecast.forecastDaysCount} days'
            : 'Weather snapshot updated. Status: ${weather.availabilityState.displayName}',
        timestamp: weather.lastUpdated!,
        domain: 'weather',
        state: weather.availabilityState,
        icon: Icons.cloud_queue_rounded,
        color: const Color(0xFF0288D1),
        provenance: '${weather.currentWeather.provenance} + ${weather.climateNormals.provenance}',
      ));
    }

    // Crop context evaluation
    if (cropContext.evaluatedAt != null) {
      items.add(FarmObservationTimelineItem(
        id: 'timeline-crop',
        title: 'Crop Feasibility Assessment',
        description:
            '${cropContext.evaluatedCropsCount} candidate crops evaluated for ${cropContext.targetSeason ?? "Active Season"}. (${cropContext.suitableCrops.length} verified suitable).',
        timestamp: cropContext.evaluatedAt!,
        domain: 'crop',
        state: cropContext.availabilityState,
        icon: Icons.agriculture_rounded,
        color: const Color(0xFF689F38),
        provenance: cropContext.provenance,
      ));
    }

    // Snapshot assembly event
    items.add(FarmObservationTimelineItem(
      id: 'timeline-snapshot',
      title: 'Unified Farm Health Snapshot',
      description: overallEvidenceOverview.actionableSummary,
      timestamp: snapshotTimestamp,
      domain: 'snapshot',
      state: soil.availabilityState == DataAvailabilityState.available &&
              water.availabilityState == DataAvailabilityState.available
          ? DataAvailabilityState.available
          : DataAvailabilityState.partiallyAvailable,
      icon: Icons.dashboard_customize_rounded,
      color: const Color(0xFF1B5E20),
      provenance: 'Unified Farm Health Aggregator',
    ));

    // Sort descending by timestamp
    items.sort((a, b) => b.timestamp.compareTo(a.timestamp));
    return items;
  }
}
