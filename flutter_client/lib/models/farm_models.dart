class Farm {
  final String farmId;
  final String ownerId;
  final String farmName;
  final String district;
  final String taluka;
  final String village;
  final double latitude;
  final double longitude;

  Farm({
    required this.farmId,
    required this.ownerId,
    required this.farmName,
    required this.district,
    required this.taluka,
    required this.village,
    required this.latitude,
    required this.longitude,
  });

  factory Farm.fromJson(Map<String, dynamic> json) {
    return Farm(
      farmId: json['farm_id'] ?? '',
      ownerId: json['owner_id'] ?? '',
      farmName: json['farm_name'] ?? 'My Farm',
      district: json['district'] ?? 'Pune',
      taluka: json['taluka'] ?? 'Baramati',
      village: json['village'] ?? '',
      latitude: (json['latitude'] as num?)?.toDouble() ?? 18.15,
      longitude: (json['longitude'] as num?)?.toDouble() ?? 74.57,
    );
  }
}

class RiskDimensionItem {
  final String riskDimension;
  final String riskLevel;
  final String timeHorizon;
  final String impactSeverity;
  final String confidence;
  final List<String> drivers;
  final List<Map<String, dynamic>> recommendedActions;

  RiskDimensionItem({
    required this.riskDimension,
    required this.riskLevel,
    required this.timeHorizon,
    required this.impactSeverity,
    required this.confidence,
    required this.drivers,
    required this.recommendedActions,
  });

  factory RiskDimensionItem.fromJson(Map<String, dynamic> json) {
    return RiskDimensionItem(
      riskDimension: json['risk_dimension'] ?? '',
      riskLevel: json['risk_level'] ?? 'low',
      timeHorizon: json['time_horizon'] ?? '',
      impactSeverity: json['impact_severity'] ?? 'low',
      confidence: json['confidence'] ?? 'medium',
      drivers: List<String>.from(json['drivers'] ?? []),
      recommendedActions: List<Map<String, dynamic>>.from(json['recommended_actions'] ?? []),
    );
  }
}

class YieldAssessment {
  final String farmId;
  final String cropCode;
  final String cropStageCode;
  final String cropStageNameEn;
  final String cropStageNameMr;
  final int das;
  final List<RiskDimensionItem> risks;
  final Map<String, dynamic> baseline;

  YieldAssessment({
    required this.farmId,
    required this.cropCode,
    required this.cropStageCode,
    required this.cropStageNameEn,
    required this.cropStageNameMr,
    required this.das,
    required this.risks,
    required this.baseline,
  });

  factory YieldAssessment.fromJson(Map<String, dynamic> json) {
    final stage = json['crop_stage'] ?? {};
    final rawRisks = json['risks'] as List? ?? [];
    return YieldAssessment(
      farmId: json['farm_id'] ?? '',
      cropCode: json['crop_code'] ?? 'soybean',
      cropStageCode: stage['stage_code'] ?? 'VEGETATIVE',
      cropStageNameEn: stage['stage_name_en'] ?? 'Vegetative',
      cropStageNameMr: stage['stage_name_mr'] ?? 'शाकीय वाढ',
      das: stage['days_after_sowing'] ?? 45,
      risks: rawRisks.map((r) => RiskDimensionItem.fromJson(r)).toList(),
      baseline: json['yield_baseline'] ?? {},
    );
  }
}

class WorkerHeatProjection {
  final int hourOffset;
  final String timeIst;
  final double airTempC;
  final double rhPct;
  final double wbgtEffectiveC;
  final String hazardLevel;
  final bool exceedsScreening;

  WorkerHeatProjection({
    required this.hourOffset,
    required this.timeIst,
    required this.airTempC,
    required this.rhPct,
    required this.wbgtEffectiveC,
    required this.hazardLevel,
    required this.exceedsScreening,
  });

  factory WorkerHeatProjection.fromJson(Map<String, dynamic> json) {
    return WorkerHeatProjection(
      hourOffset: json['forecast_hour_offset'] ?? 0,
      timeIst: json['valid_time_ist'] ?? '',
      airTempC: (json['air_temp_c'] as num?)?.toDouble() ?? 32.0,
      rhPct: (json['relative_humidity_pct'] as num?)?.toDouble() ?? 50.0,
      wbgtEffectiveC: (json['wbgt_effective_c'] as num?)?.toDouble() ?? 28.0,
      hazardLevel: json['hazard_level'] ?? 'low',
      exceedsScreening: json['exceeds_screening_threshold'] ?? false,
    );
  }
}

class WorkerHeatResponse {
  final String currentHazardLevel;
  final String maxHazardLevel;
  final double maxWbgtEffectiveC;
  final double screeningThresholdC;
  final String disclaimer;
  final List<String> safetyCautions;
  final Map<String, dynamic> hydrationGuidance;
  final List<WorkerHeatProjection> projections;

  WorkerHeatResponse({
    required this.currentHazardLevel,
    required this.maxHazardLevel,
    required this.maxWbgtEffectiveC,
    required this.screeningThresholdC,
    required this.disclaimer,
    required this.safetyCautions,
    required this.hydrationGuidance,
    required this.projections,
  });

  factory WorkerHeatResponse.fromJson(Map<String, dynamic> json) {
    final rawProj = json['hourly_projections'] as List? ?? [];
    return WorkerHeatResponse(
      currentHazardLevel: json['current_hazard_level'] ?? 'low',
      maxHazardLevel: json['max_hazard_level_in_window'] ?? 'low',
      maxWbgtEffectiveC: (json['max_wbgt_effective_c'] as num?)?.toDouble() ?? 27.0,
      screeningThresholdC: (json['screening_threshold_c'] as num?)?.toDouble() ?? 28.0,
      disclaimer: json['disclaimer'] ?? '',
      safetyCautions: List<String>.from(json['safety_cautions'] ?? []),
      hydrationGuidance: json['hydration_guidance'] ?? {},
      projections: rawProj.map((p) => WorkerHeatProjection.fromJson(p)).toList(),
    );
  }
}
