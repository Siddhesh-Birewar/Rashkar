import '../../farm/models/farm_models.dart';

/// Verification status for soil observations.
enum VerificationStatus {
  mapDerivedEstimate('map_derived_estimate'),
  regionalEstimate('regional_estimate'),
  notAvailable('not_available'),
  laboratoryVerified('laboratory_verified');

  final String value;
  const VerificationStatus(this.value);

  static VerificationStatus fromString(String? val) {
    return VerificationStatus.values.firstWhere(
      (e) => e.value == val,
      orElse: () => VerificationStatus.mapDerivedEstimate,
    );
  }
}

/// Availability classification of soil data.
enum ParameterAvailability {
  available('available'),
  partialCoverage('partial_coverage'),
  notAvailable('not_available'),
  sourceUnavailable('source_unavailable'),
  stale('stale');

  final String value;
  const ParameterAvailability(this.value);

  static ParameterAvailability fromString(String? val) {
    return ParameterAvailability.values.firstWhere(
      (e) => e.value == val,
      orElse: () => ParameterAvailability.available,
    );
  }
}

/// Standard model for an individual soil parameter observation with full scientific provenance.
class SoilParameterObservation {
  final String parameterKey;
  final String displayName;
  final double? value;
  final String unit;
  final String source;
  final String datasetVersion;
  final String depthInterval;
  final String spatialResolution;
  final int? vintageYear;
  final double? uncertainty;
  final VerificationStatus verificationStatus;
  final ParameterAvailability availabilityStatus;
  final double farmCoveragePercent;
  final String? scientificNote;

  const SoilParameterObservation({
    required this.parameterKey,
    required this.displayName,
    this.value,
    required this.unit,
    required this.source,
    required this.datasetVersion,
    required this.depthInterval,
    required this.spatialResolution,
    this.vintageYear,
    this.uncertainty,
    this.verificationStatus = VerificationStatus.mapDerivedEstimate,
    this.availabilityStatus = ParameterAvailability.available,
    this.farmCoveragePercent = 100.0,
    this.scientificNote,
  });

  factory SoilParameterObservation.fromJson(Map<String, dynamic> json) {
    return SoilParameterObservation(
      parameterKey: json['parameter_key'] as String,
      displayName: json['display_name'] as String,
      value: (json['value'] as num?)?.toDouble(),
      unit: json['unit'] as String,
      source: json['source'] as String,
      datasetVersion: json['dataset_version'] as String,
      depthInterval: json['depth_interval'] as String,
      spatialResolution: json['spatial_resolution'] as String,
      vintageYear: json['vintage_year'] as int?,
      uncertainty: (json['uncertainty'] as num?)?.toDouble(),
      verificationStatus: VerificationStatus.fromString(json['verification_status'] as String?),
      availabilityStatus: ParameterAvailability.fromString(json['availability_status'] as String?),
      farmCoveragePercent: (json['farm_coverage_percent'] as num?)?.toDouble() ?? 100.0,
      scientificNote: json['scientific_note'] as String?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'parameter_key': parameterKey,
      'display_name': displayName,
      'value': value,
      'unit': unit,
      'source': source,
      'dataset_version': datasetVersion,
      'depth_interval': depthInterval,
      'spatial_resolution': spatialResolution,
      if (vintageYear != null) 'vintage_year': vintageYear,
      if (uncertainty != null) 'uncertainty': uncertainty,
      'verification_status': verificationStatus.value,
      'availability_status': availabilityStatus.value,
      'farm_coverage_percent': farmCoveragePercent,
      if (scientificNote != null) 'scientific_note': scientificNote,
    };
  }
}

/// Mapped soil zone / sub-polygon intersecting a farm boundary.
class MappedSoilZone {
  final String zoneId;
  final String zoneName;
  final double areaFraction;
  final String? description;

  const MappedSoilZone({
    required this.zoneId,
    required this.zoneName,
    required this.areaFraction,
    this.description,
  });

  factory MappedSoilZone.fromJson(Map<String, dynamic> json) {
    return MappedSoilZone(
      zoneId: json['zone_id'] as String,
      zoneName: json['zone_name'] as String,
      areaFraction: (json['area_fraction'] as num).toDouble(),
      description: json['description'] as String?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'zone_id': zoneId,
      'zone_name': zoneName,
      'area_fraction': areaFraction,
      if (description != null) 'description': description,
    };
  }
}

/// Unified Soil Profile snapshot consumed by crop recommendation engine.
class UnifiedSoilProfile {
  final String profileId;
  final String farmId;
  final DateTime createdAt;
  final int version;
  final String? taluka;
  final String district;
  final String state;
  final bool isMapDerived;
  final String disclaimer;
  final String sourceDataset;
  final String datasetVersion;
  final String spatialResolution;
  final String depthInterval;
  final String? spatialRepresentativenessWarning;
  final String? soilTextureClass;

  // Primary parameters
  final SoilParameterObservation? ph;
  final SoilParameterObservation? organicCarbon;
  final SoilParameterObservation? sandPercent;
  final SoilParameterObservation? siltPercent;
  final SoilParameterObservation? clayPercent;
  final SoilParameterObservation? totalNitrogen;
  final SoilParameterObservation? cationExchangeCapacity;

  // Nutrients with strict unverified protection
  final SoilParameterObservation? availableNitrogen;
  final SoilParameterObservation? availablePhosphorus;
  final SoilParameterObservation? availablePotassium;

  final List<MappedSoilZone> mappedSoilZones;
  final Map<String, SoilParameterObservation> additionalParameters;

  final int totalRequestedParameters;
  final int availableParametersCount;
  final double dataCompletenessRatio;

  const UnifiedSoilProfile({
    required this.profileId,
    required this.farmId,
    required this.createdAt,
    this.version = 1,
    this.taluka,
    this.district = 'Pune',
    this.state = 'Maharashtra',
    this.isMapDerived = true,
    required this.disclaimer,
    this.sourceDataset = 'ISRIC SoilGrids 2.0',
    this.datasetVersion = '2.0.0',
    this.spatialResolution = '250m',
    this.depthInterval = '0-5cm',
    this.spatialRepresentativenessWarning,
    this.soilTextureClass,
    this.ph,
    this.organicCarbon,
    this.sandPercent,
    this.siltPercent,
    this.clayPercent,
    this.totalNitrogen,
    this.cationExchangeCapacity,
    this.availableNitrogen,
    this.availablePhosphorus,
    this.availablePotassium,
    this.mappedSoilZones = const [],
    this.additionalParameters = const {},
    this.totalRequestedParameters = 0,
    this.availableParametersCount = 0,
    this.dataCompletenessRatio = 0.0,
  });

  factory UnifiedSoilProfile.fromJson(Map<String, dynamic> json) {
    SoilParameterObservation? parseParam(String key) {
      if (json[key] is Map) {
        return SoilParameterObservation.fromJson(Map<String, dynamic>.from(json[key] as Map));
      }
      return null;
    }

    final zones = (json['mapped_soil_zones'] as List<dynamic>?)
            ?.map((e) => MappedSoilZone.fromJson(Map<String, dynamic>.from(e as Map)))
            .toList() ??
        [];

    final additional = <String, SoilParameterObservation>{};
    if (json['additional_parameters'] is Map) {
      final map = json['additional_parameters'] as Map;
      for (final entry in map.entries) {
        if (entry.value is Map) {
          additional[entry.key.toString()] = SoilParameterObservation.fromJson(
            Map<String, dynamic>.from(entry.value as Map),
          );
        }
      }
    }

    return UnifiedSoilProfile(
      profileId: json['profile_id'] as String,
      farmId: json['farm_id'] as String,
      createdAt: json['created_at'] != null
          ? DateTime.parse(json['created_at'] as String)
          : DateTime.now(),
      version: json['version'] as int? ?? 1,
      taluka: json['taluka'] as String?,
      district: json['district'] as String? ?? 'Pune',
      state: json['state'] as String? ?? 'Maharashtra',
      isMapDerived: json['is_map_derived'] as bool? ?? true,
      disclaimer: json['disclaimer'] as String? ?? '',
      sourceDataset: json['source_dataset'] as String? ?? 'ISRIC SoilGrids 2.0',
      datasetVersion: json['dataset_version'] as String? ?? '2.0.0',
      spatialResolution: json['spatial_resolution'] as String? ?? '250m',
      depthInterval: json['depth_interval'] as String? ?? '0-5cm',
      spatialRepresentativenessWarning: json['spatial_representativeness_warning'] as String?,
      soilTextureClass: json['soil_texture_class'] as String?,
      ph: parseParam('ph'),
      organicCarbon: parseParam('organic_carbon'),
      sandPercent: parseParam('sand_percent'),
      siltPercent: parseParam('silt_percent'),
      clayPercent: parseParam('clay_percent'),
      totalNitrogen: parseParam('total_nitrogen'),
      cationExchangeCapacity: parseParam('cation_exchange_capacity'),
      availableNitrogen: parseParam('available_nitrogen'),
      availablePhosphorus: parseParam('available_phosphorus'),
      availablePotassium: parseParam('available_potassium'),
      mappedSoilZones: zones,
      additionalParameters: additional,
      totalRequestedParameters: json['total_requested_parameters'] as int? ?? 0,
      availableParametersCount: json['available_parameters_count'] as int? ?? 0,
      dataCompletenessRatio: (json['data_completeness_ratio'] as num?)?.toDouble() ?? 0.0,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'profile_id': profileId,
      'farm_id': farmId,
      'created_at': createdAt.toIso8601String(),
      'version': version,
      if (taluka != null) 'taluka': taluka,
      'district': district,
      'state': state,
      'is_map_derived': isMapDerived,
      'disclaimer': disclaimer,
      'source_dataset': sourceDataset,
      'dataset_version': datasetVersion,
      'spatial_resolution': spatialResolution,
      'depth_interval': depthInterval,
      if (spatialRepresentativenessWarning != null)
        'spatial_representativeness_warning': spatialRepresentativenessWarning,
      if (soilTextureClass != null) 'soil_texture_class': soilTextureClass,
      if (ph != null) 'ph': ph!.toJson(),
      if (organicCarbon != null) 'organic_carbon': organicCarbon!.toJson(),
      if (sandPercent != null) 'sand_percent': sandPercent!.toJson(),
      if (siltPercent != null) 'silt_percent': siltPercent!.toJson(),
      if (clayPercent != null) 'clay_percent': clayPercent!.toJson(),
      if (totalNitrogen != null) 'total_nitrogen': totalNitrogen!.toJson(),
      if (cationExchangeCapacity != null)
        'cation_exchange_capacity': cationExchangeCapacity!.toJson(),
      if (availableNitrogen != null) 'available_nitrogen': availableNitrogen!.toJson(),
      if (availablePhosphorus != null) 'available_phosphorus': availablePhosphorus!.toJson(),
      if (availablePotassium != null) 'available_potassium': availablePotassium!.toJson(),
      'mapped_soil_zones': mappedSoilZones.map((z) => z.toJson()).toList(),
      'additional_parameters':
          additionalParameters.map((k, v) => MapEntry(k, v.toJson())),
      'total_requested_parameters': totalRequestedParameters,
      'available_parameters_count': availableParametersCount,
      'data_completeness_ratio': dataCompletenessRatio,
    };
  }
}

/// Request to trigger soil analysis.
class SoilAnalyseRequest {
  final bool forceRefresh;
  final String depth;

  const SoilAnalyseRequest({
    this.forceRefresh = false,
    this.depth = '0-5cm',
  });

  Map<String, dynamic> toJson() {
    return {
      'force_refresh': forceRefresh,
      'depth': depth,
    };
  }
}

/// GIS Soil Layer catalogue item.
class SoilLayerInfo {
  final String parameterKey;
  final String displayName;
  final String unit;
  final String source;
  final String datasetVersion;
  final String spatialResolution;
  final List<String> supportedDepthIntervals;
  final bool isDerived;
  final String? scientificNote;

  const SoilLayerInfo({
    required this.parameterKey,
    required this.displayName,
    required this.unit,
    required this.source,
    required this.datasetVersion,
    required this.spatialResolution,
    required this.supportedDepthIntervals,
    this.isDerived = false,
    this.scientificNote,
  });

  factory SoilLayerInfo.fromJson(Map<String, dynamic> json) {
    return SoilLayerInfo(
      parameterKey: json['parameter_key'] as String,
      displayName: json['display_name'] as String,
      unit: json['unit'] as String,
      source: json['source'] as String,
      datasetVersion: json['dataset_version'] as String,
      spatialResolution: json['spatial_resolution'] as String,
      supportedDepthIntervals: (json['supported_depth_intervals'] as List<dynamic>)
          .map((e) => e.toString())
          .toList(),
      isDerived: json['is_derived'] as bool? ?? false,
      scientificNote: json['scientific_note'] as String?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'parameter_key': parameterKey,
      'display_name': displayName,
      'unit': unit,
      'source': source,
      'dataset_version': datasetVersion,
      'spatial_resolution': spatialResolution,
      'supported_depth_intervals': supportedDepthIntervals,
      'is_derived': isDerived,
      if (scientificNote != null) 'scientific_note': scientificNote,
    };
  }
}

/// Capability report for an independent soil data provider.
class ProviderCapability {
  final String providerName;
  final String datasetVersion;
  final String spatialResolutionOrScale;
  final List<String> supportedDepthIntervals;
  final int? vintageYear;
  final String licensing;
  final String attributionStatement;
  final bool isOperational;
  final String statusMessage;
  final List<String> availableProperties;
  final bool providesUncertainty;
  final bool requiresCredentials;

  const ProviderCapability({
    required this.providerName,
    required this.datasetVersion,
    required this.spatialResolutionOrScale,
    required this.supportedDepthIntervals,
    this.vintageYear,
    required this.licensing,
    required this.attributionStatement,
    required this.isOperational,
    required this.statusMessage,
    required this.availableProperties,
    required this.providesUncertainty,
    required this.requiresCredentials,
  });

  factory ProviderCapability.fromJson(Map<String, dynamic> json) {
    return ProviderCapability(
      providerName: json['provider_name'] as String,
      datasetVersion: json['dataset_version'] as String,
      spatialResolutionOrScale: json['spatial_resolution_or_scale'] as String,
      supportedDepthIntervals: (json['supported_depth_intervals'] as List<dynamic>)
          .map((e) => e.toString())
          .toList(),
      vintageYear: json['vintage_year'] as int?,
      licensing: json['licensing'] as String,
      attributionStatement: json['attribution_statement'] as String,
      isOperational: json['is_operational'] as bool,
      statusMessage: json['status_message'] as String,
      availableProperties: (json['available_properties'] as List<dynamic>)
          .map((e) => e.toString())
          .toList(),
      providesUncertainty: json['provides_uncertainty'] as bool,
      requiresCredentials: json['requires_credentials'] as bool,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'provider_name': providerName,
      'dataset_version': datasetVersion,
      'spatial_resolution_or_scale': spatialResolutionOrScale,
      'supported_depth_intervals': supportedDepthIntervals,
      if (vintageYear != null) 'vintage_year': vintageYear,
      'licensing': licensing,
      'attribution_statement': attributionStatement,
      'is_operational': isOperational,
      'status_message': statusMessage,
      'available_properties': availableProperties,
      'provides_uncertainty': providesUncertainty,
      'requires_credentials': requiresCredentials,
    };
  }
}

/// Request to extract soil parameters for an ad-hoc polygon.
class PolygonSoilExtractRequest {
  final GeoJsonPolygon geometry;
  final String taluka;

  const PolygonSoilExtractRequest({
    required this.geometry,
    this.taluka = 'Baramati',
  });

  Map<String, dynamic> toJson() {
    return {
      'geometry': geometry.toJson(),
      'taluka': taluka,
    };
  }
}
