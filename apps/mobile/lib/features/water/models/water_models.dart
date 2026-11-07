enum WaterSourceType {
  borewell,
  openWell,
  canal,
  river,
  reservoir,
  farmPond,
  rainwaterHarvesting,
  other;

  static WaterSourceType fromString(String val) {
    switch (val.toLowerCase().replaceAll('_', '')) {
      case 'borewell':
        return WaterSourceType.borewell;
      case 'openwell':
        return WaterSourceType.openWell;
      case 'canal':
        return WaterSourceType.canal;
      case 'river':
        return WaterSourceType.river;
      case 'reservoir':
        return WaterSourceType.reservoir;
      case 'farmpond':
        return WaterSourceType.farmPond;
      case 'rainwaterharvesting':
        return WaterSourceType.rainwaterHarvesting;
      default:
        return WaterSourceType.other;
    }
  }

  String get displayName {
    switch (this) {
      case WaterSourceType.borewell:
        return 'Borewell';
      case WaterSourceType.openWell:
        return 'Open Well';
      case WaterSourceType.canal:
        return 'Canal';
      case WaterSourceType.river:
        return 'River';
      case WaterSourceType.reservoir:
        return 'Reservoir / Dam';
      case WaterSourceType.farmPond:
        return 'Farm Pond (Shet Tale)';
      case WaterSourceType.rainwaterHarvesting:
        return 'Rainwater Harvesting';
      case WaterSourceType.other:
        return 'Other Source';
    }
  }

  String toApiString() {
    switch (this) {
      case WaterSourceType.borewell:
        return 'borewell';
      case WaterSourceType.openWell:
        return 'open_well';
      case WaterSourceType.canal:
        return 'canal';
      case WaterSourceType.river:
        return 'river';
      case WaterSourceType.reservoir:
        return 'reservoir';
      case WaterSourceType.farmPond:
        return 'farm_pond';
      case WaterSourceType.rainwaterHarvesting:
        return 'rainwater_harvesting';
      case WaterSourceType.other:
        return 'other';
    }
  }
}

class WaterSource {
  final String id;
  final String farmId;
  final WaterSourceType sourceType;
  final String name;
  final String? locationDescription;
  final double? latitude;
  final double? longitude;
  final String seasonalAvailability;
  final String reliability;
  final double? dailyAvailableHours;
  final String irrigationMethod;
  final double? measuredCapacityLph;
  final String capacityProvenance;
  final bool isActive;
  final DateTime createdAt;

  WaterSource({
    required this.id,
    required this.farmId,
    required this.sourceType,
    required this.name,
    this.locationDescription,
    this.latitude,
    this.longitude,
    required this.seasonalAvailability,
    required this.reliability,
    this.dailyAvailableHours,
    required this.irrigationMethod,
    this.measuredCapacityLph,
    required this.capacityProvenance,
    required this.isActive,
    required this.createdAt,
  });

  factory WaterSource.fromJson(Map<String, dynamic> json) {
    return WaterSource(
      id: json['id'] as String? ?? '',
      farmId: json['farm_id'] as String? ?? '',
      sourceType: WaterSourceType.fromString(json['source_type'] as String? ?? 'other'),
      name: json['name'] as String? ?? '',
      locationDescription: json['location_description'] as String?,
      latitude: (json['latitude'] as num?)?.toDouble(),
      longitude: (json['longitude'] as num?)?.toDouble(),
      seasonalAvailability: json['seasonal_availability'] as String? ?? 'perennial',
      reliability: json['reliability'] as String? ?? 'reliable',
      dailyAvailableHours: (json['daily_available_hours'] as num?)?.toDouble(),
      irrigationMethod: json['irrigation_method'] as String? ?? 'drip',
      measuredCapacityLph: (json['measured_capacity_lph'] as num?)?.toDouble(),
      capacityProvenance: json['capacity_provenance'] as String? ?? 'FARMER_REPORTED',
      isActive: json['is_active'] as bool? ?? true,
      createdAt: json['created_at'] != null
          ? DateTime.tryParse(json['created_at'] as String) ?? DateTime.now()
          : DateTime.now(),
    );
  }
}

class WaterCalculatedIndices {
  final double? sar;
  final String sarStatus;
  final double? rsc;
  final String rscStatus;
  final Map<String, dynamic> inputsUsed;
  final List<String> calculationNotes;

  WaterCalculatedIndices({
    this.sar,
    required this.sarStatus,
    this.rsc,
    required this.rscStatus,
    required this.inputsUsed,
    required this.calculationNotes,
  });

  factory WaterCalculatedIndices.fromJson(Map<String, dynamic> json) {
    return WaterCalculatedIndices(
      sar: (json['sar'] as num?)?.toDouble(),
      sarStatus: json['sar_status'] as String? ?? 'UNAVAILABLE',
      rsc: (json['rsc'] as num?)?.toDouble(),
      rscStatus: json['rsc_status'] as String? ?? 'UNAVAILABLE',
      inputsUsed: (json['inputs_used'] as Map<String, dynamic>?) ?? {},
      calculationNotes: (json['calculation_notes'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          [],
    );
  }
}

class WaterMeasurement {
  final String id;
  final String parameterKey;
  final String originalParameterName;
  final double? originalValue;
  final String originalUnit;
  final double? normalizedValue;
  final String? normalizedUnit;
  final String verificationStatus;
  final double? farmerCorrectedValue;
  final String? farmerNotes;
  final String provenance;

  WaterMeasurement({
    required this.id,
    required this.parameterKey,
    required this.originalParameterName,
    this.originalValue,
    required this.originalUnit,
    this.normalizedValue,
    this.normalizedUnit,
    required this.verificationStatus,
    this.farmerCorrectedValue,
    this.farmerNotes,
    required this.provenance,
  });

  factory WaterMeasurement.fromJson(Map<String, dynamic> json) {
    return WaterMeasurement(
      id: json['id'] as String? ?? '',
      parameterKey: json['parameter_key'] as String? ?? '',
      originalParameterName: json['original_parameter_name'] as String? ?? '',
      originalValue: (json['original_value'] as num?)?.toDouble(),
      originalUnit: json['original_unit'] as String? ?? '',
      normalizedValue: (json['normalized_value'] as num?)?.toDouble(),
      normalizedUnit: json['normalized_unit'] as String?,
      verificationStatus: json['verification_status'] as String? ?? 'EXTRACTED_UNVERIFIED',
      farmerCorrectedValue: (json['farmer_corrected_value'] as num?)?.toDouble(),
      farmerNotes: json['farmer_notes'] as String?,
      provenance: json['provenance'] as String? ?? 'LAB_REPORT',
    );
  }
}

class WaterReportSummary {
  final String id;
  final String farmId;
  final String? waterSourceId;
  final String originalFilename;
  final int? fileSizeBytes;
  final String? laboratoryName;
  final DateTime? reportDate;
  final String extractionStatus;
  final String reviewStatus;
  final int measurementCount;
  final DateTime uploadTimestamp;

  WaterReportSummary({
    required this.id,
    required this.farmId,
    this.waterSourceId,
    required this.originalFilename,
    this.fileSizeBytes,
    this.laboratoryName,
    this.reportDate,
    required this.extractionStatus,
    required this.reviewStatus,
    required this.measurementCount,
    required this.uploadTimestamp,
  });

  factory WaterReportSummary.fromJson(Map<String, dynamic> json) {
    return WaterReportSummary(
      id: json['id'] as String? ?? '',
      farmId: json['farm_id'] as String? ?? '',
      waterSourceId: json['water_source_id'] as String?,
      originalFilename: json['original_filename'] as String? ?? 'report.pdf',
      fileSizeBytes: json['file_size_bytes'] as int?,
      laboratoryName: json['laboratory_name'] as String?,
      reportDate: json['report_date'] != null ? DateTime.tryParse(json['report_date'] as String) : null,
      extractionStatus: json['extraction_status'] as String? ?? 'UPLOADED',
      reviewStatus: json['review_status'] as String? ?? 'NEEDS_REVIEW',
      measurementCount: json['measurement_count'] as int? ?? 0,
      uploadTimestamp: json['upload_timestamp'] != null
          ? DateTime.tryParse(json['upload_timestamp'] as String) ?? DateTime.now()
          : DateTime.now(),
    );
  }
}

class WaterRuleEvaluation {
  final String parameterKey;
  final String parameterName;
  final double observedValue;
  final String observedUnit;
  final String hazardLevel;
  final String hazardTitle;
  final String ruleId;
  final String sourceCitation;
  final String applicableStandard;
  final String managementGuidance;
  final String scopeAndLimitations;

  WaterRuleEvaluation({
    required this.parameterKey,
    required this.parameterName,
    required this.observedValue,
    required this.observedUnit,
    required this.hazardLevel,
    required this.hazardTitle,
    required this.ruleId,
    required this.sourceCitation,
    required this.applicableStandard,
    required this.managementGuidance,
    required this.scopeAndLimitations,
  });

  factory WaterRuleEvaluation.fromJson(Map<String, dynamic> json) {
    return WaterRuleEvaluation(
      parameterKey: json['parameter_key'] as String? ?? '',
      parameterName: json['parameter_name'] as String? ?? '',
      observedValue: (json['observed_value'] as num?)?.toDouble() ?? 0.0,
      observedUnit: json['observed_unit'] as String? ?? '',
      hazardLevel: json['hazard_level'] as String? ?? 'LOW',
      hazardTitle: json['hazard_title'] as String? ?? '',
      ruleId: json['rule_id'] as String? ?? '',
      sourceCitation: json['source_citation'] as String? ?? '',
      applicableStandard: json['applicable_standard'] as String? ?? '',
      managementGuidance: json['management_guidance'] as String? ?? '',
      scopeAndLimitations: json['scope_and_limitations'] as String? ?? '',
    );
  }
}

class WaterQualityEvaluation {
  final String farmId;
  final String? waterSourceId;
  final List<WaterRuleEvaluation> evaluations;
  final WaterCalculatedIndices calculatedIndices;
  final String soilDrainageCaution;
  final Map<String, dynamic> cropSensitivityOverview;
  final Map<String, dynamic>? regionalCgwbContext;
  final String disclaimer;

  WaterQualityEvaluation({
    required this.farmId,
    this.waterSourceId,
    required this.evaluations,
    required this.calculatedIndices,
    required this.soilDrainageCaution,
    required this.cropSensitivityOverview,
    this.regionalCgwbContext,
    required this.disclaimer,
  });

  factory WaterQualityEvaluation.fromJson(Map<String, dynamic> json) {
    return WaterQualityEvaluation(
      farmId: json['farm_id'] as String? ?? '',
      waterSourceId: json['water_source_id'] as String?,
      evaluations: (json['evaluations'] as List<dynamic>?)
              ?.map((e) => WaterRuleEvaluation.fromJson(e as Map<String, dynamic>))
              .toList() ??
          [],
      calculatedIndices: WaterCalculatedIndices.fromJson(
        (json['calculated_indices'] as Map<String, dynamic>?) ?? {},
      ),
      soilDrainageCaution: json['soil_drainage_caution'] as String? ?? '',
      cropSensitivityOverview:
          (json['crop_sensitivity_overview'] as Map<String, dynamic>?) ?? {},
      regionalCgwbContext: json['regional_cgwb_context'] as Map<String, dynamic>?,
      disclaimer: json['disclaimer'] as String? ?? '',
    );
  }
}
