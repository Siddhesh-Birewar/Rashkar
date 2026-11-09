class FarmSummary {
  final String farmerId;
  final String farmerName;
  final String farmId;
  final String farmName;
  final String locationDisplay;
  final double latitude;
  final double longitude;
  final double? totalAreaAcres;
  final String? activeCropCode;
  final String? activeCropName;
  final String? sowingDate;
  final int? daysAfterSowing;
  final String? estimatedStageCode;
  final String? estimatedStageName;
  final double? plantedAreaAcres;
  final String? irrigationType;
  final Map<String, dynamic> weatherSummary;
  final String dataLastUpdated;
  final bool isDataStale;
  final Map<String, dynamic>? soilSummary;
  final List<Map<String, dynamic>> activeAlerts;

  FarmSummary({
    required this.farmerId,
    required this.farmerName,
    required this.farmId,
    required this.farmName,
    required this.locationDisplay,
    required this.latitude,
    required this.longitude,
    this.totalAreaAcres,
    this.activeCropCode,
    this.activeCropName,
    this.sowingDate,
    this.daysAfterSowing,
    this.estimatedStageCode,
    this.estimatedStageName,
    this.plantedAreaAcres,
    this.irrigationType,
    required this.weatherSummary,
    required this.dataLastUpdated,
    required this.isDataStale,
    this.soilSummary,
    required this.activeAlerts,
  });

  factory FarmSummary.fromJson(Map<String, dynamic> json) {
    return FarmSummary(
      farmerId: json['farmer_id'] ?? '',
      farmerName: json['farmer_name'] ?? 'Farmer',
      farmId: json['farm_id'] ?? '',
      farmName: json['farm_name'] ?? 'My Farm',
      locationDisplay: json['location_display'] ?? '',
      latitude: (json['latitude'] as num?)?.toDouble() ?? 18.15,
      longitude: (json['longitude'] as num?)?.toDouble() ?? 74.57,
      totalAreaAcres: (json['total_area_acres'] as num?)?.toDouble(),
      activeCropCode: json['active_crop_code'],
      activeCropName: json['active_crop_name'],
      sowingDate: json['sowing_date'],
      daysAfterSowing: json['days_after_sowing'],
      estimatedStageCode: json['estimated_stage_code'],
      estimatedStageName: json['estimated_stage_name'],
      plantedAreaAcres: (json['planted_area_acres'] as num?)?.toDouble(),
      irrigationType: json['irrigation_type'],
      weatherSummary: Map<String, dynamic>.from(json['weather_summary'] ?? {}),
      dataLastUpdated: json['data_last_updated'] ?? 'Recently',
      isDataStale: json['is_data_stale'] ?? false,
      soilSummary: json['soil_summary'] != null ? Map<String, dynamic>.from(json['soil_summary']) : null,
      activeAlerts: List<Map<String, dynamic>>.from(json['active_alerts'] ?? []),
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

class SoilSuitabilityAnalysis {
  final String soilTexture;
  final double soilPh;
  final String phStatus;
  final double organicCarbonPct;
  final double cationExchangeCapacity;
  final double availableWaterCapacityMmM;
  final double effectiveRootingDepthCm;
  final double climateNormalRainfallMm;
  final String suitabilityVerdict;
  final String dataProvenance;

  SoilSuitabilityAnalysis({
    required this.soilTexture,
    required this.soilPh,
    required this.phStatus,
    required this.organicCarbonPct,
    required this.cationExchangeCapacity,
    required this.availableWaterCapacityMmM,
    required this.effectiveRootingDepthCm,
    required this.climateNormalRainfallMm,
    required this.suitabilityVerdict,
    required this.dataProvenance,
  });

  factory SoilSuitabilityAnalysis.fromJson(Map<String, dynamic> json) {
    return SoilSuitabilityAnalysis(
      soilTexture: json['soil_texture'] ?? 'Medium Black Vertisol',
      soilPh: (json['soil_ph'] as num?)?.toDouble() ?? 7.8,
      phStatus: json['ph_status'] ?? 'Optimal',
      organicCarbonPct: (json['organic_carbon_pct'] as num?)?.toDouble() ?? 0.65,
      cationExchangeCapacity: (json['cation_exchange_capacity'] as num?)?.toDouble() ?? 38.5,
      availableWaterCapacityMmM: (json['available_water_capacity_mm_m'] as num?)?.toDouble() ?? 145.0,
      effectiveRootingDepthCm: (json['effective_rooting_depth_cm'] as num?)?.toDouble() ?? 90.0,
      climateNormalRainfallMm: (json['climate_normal_rainfall_mm'] as num?)?.toDouble() ?? 680.0,
      suitabilityVerdict: json['suitability_verdict'] ?? 'Suitable',
      dataProvenance: json['data_provenance'] ?? 'CropNet Soil Adapter',
    );
  }
}

class ActionableRecommendationItem {
  final String recommendationId;
  final String title;
  final String description;
  final String whyRecommended;
  final String supportingData;
  final String evidenceSource;
  final String urgency;
  final String limitations;

  ActionableRecommendationItem({
    required this.recommendationId,
    required this.title,
    required this.description,
    required this.whyRecommended,
    required this.supportingData,
    required this.evidenceSource,
    required this.urgency,
    required this.limitations,
  });

  factory ActionableRecommendationItem.fromJson(Map<String, dynamic> json) {
    return ActionableRecommendationItem(
      recommendationId: json['recommendation_id'] ?? '',
      title: json['title'] ?? '',
      description: json['description'] ?? '',
      whyRecommended: json['why_recommended'] ?? '',
      supportingData: json['supporting_data'] ?? '',
      evidenceSource: json['evidence_source'] ?? '',
      urgency: json['urgency'] ?? 'Preventative',
      limitations: json['limitations'] ?? '',
    );
  }
}

class YieldAssessment {
  final String farmId;
  final String farmName;
  final String plotId;
  final String cropCode;
  final String cropName;
  final String sowingDate;
  final int daysAfterSowing;
  final double totalAreaAcres;
  final String irrigationType;
  final String locationDisplay;
  final String generatedAtUtc;
  final String timezone;
  final Map<String, dynamic> baseline;
  final SoilSuitabilityAnalysis? suitabilityAnalysis;
  final List<RiskDimensionItem> risks;
  final Map<String, dynamic> mlPredictionGate;
  final List<ActionableRecommendationItem> recommendations;
  final String farmerNarrativeExplanation;

  // Compatibility getters
  String get cropStageCode => cropCode;
  String get cropStageNameEn => 'Stage (DAS $daysAfterSowing)';
  String get cropStageNameMr => 'अवस्था';
  int get das => daysAfterSowing;

  YieldAssessment({
    required this.farmId,
    this.farmName = 'My Farm',
    this.plotId = 'plot_1',
    required this.cropCode,
    this.cropName = 'Crop',
    this.sowingDate = '',
    required this.daysAfterSowing,
    this.totalAreaAcres = 2.5,
    this.irrigationType = 'Rainfed',
    this.locationDisplay = 'Maharashtra',
    this.generatedAtUtc = '',
    this.timezone = 'Asia/Kolkata',
    required this.baseline,
    this.suitabilityAnalysis,
    required this.risks,
    this.mlPredictionGate = const {},
    this.recommendations = const [],
    this.farmerNarrativeExplanation = '',
  });

  factory YieldAssessment.fromJson(Map<String, dynamic> json) {
    final stage = json['crop_stage'] ?? {};
    final rawRisks = json['risks'] as List? ?? [];
    final rawRecs = json['recommendations'] as List? ?? [];
    return YieldAssessment(
      farmId: json['farm_id'] ?? '',
      farmName: json['farm_name'] ?? 'My Farm',
      plotId: json['plot_id'] ?? 'plot_1',
      cropCode: json['crop_code'] ?? 'soybean',
      cropName: json['crop_name'] ?? (json['crop_code'] != null ? json['crop_code'].toString().toUpperCase() : 'Crop'),
      sowingDate: json['sowing_date'] ?? '',
      daysAfterSowing: stage['days_after_sowing'] ?? json['days_after_sowing'] ?? 45,
      totalAreaAcres: (json['total_area_acres'] as num?)?.toDouble() ?? 2.5,
      irrigationType: json['irrigation_type'] ?? 'Rainfed',
      locationDisplay: json['location_display'] ?? '',
      generatedAtUtc: json['generated_at_utc'] ?? '',
      timezone: json['timezone'] ?? 'Asia/Kolkata',
      baseline: json['yield_baseline'] ?? {},
      suitabilityAnalysis: json['suitability_analysis'] != null
          ? SoilSuitabilityAnalysis.fromJson(json['suitability_analysis'])
          : null,
      risks: rawRisks.map((r) => RiskDimensionItem.fromJson(r)).toList(),
      mlPredictionGate: Map<String, dynamic>.from(json['ml_prediction_gate'] ?? {}),
      recommendations: rawRecs.map((r) => ActionableRecommendationItem.fromJson(r)).toList(),
      farmerNarrativeExplanation: json['farmer_narrative_explanation'] ?? '',
    );
  }
}

// ==================== WORKER HEAT MODELS ====================

class WorkerHourlyProjection {
  final int forecastHourOffset;
  final String validTimeIst;
  final double airTempC;
  final double relativeHumidityPct;
  final double windSpeedMs;
  final double solarIrradianceWm2;
  final double wbgtEstimatedC;
  final double wbgtEffectiveC;
  final String hazardLevel;
  final bool exceedsScreeningThreshold;
  final double thresholdLimitC;
  final String trend;
  final String workRestCycle;
  final double? heatIndexC;
  final double? utciC;

  WorkerHourlyProjection({
    required this.forecastHourOffset,
    required this.validTimeIst,
    required this.airTempC,
    required this.relativeHumidityPct,
    required this.windSpeedMs,
    required this.solarIrradianceWm2,
    required this.wbgtEstimatedC,
    required this.wbgtEffectiveC,
    required this.hazardLevel,
    required this.exceedsScreeningThreshold,
    required this.thresholdLimitC,
    required this.trend,
    required this.workRestCycle,
    this.heatIndexC,
    this.utciC,
  });

  factory WorkerHourlyProjection.fromJson(Map<String, dynamic> json) {
    return WorkerHourlyProjection(
      forecastHourOffset: json['forecast_hour_offset'] ?? 0,
      validTimeIst: json['valid_time_ist'] ?? '',
      airTempC: (json['air_temp_c'] as num?)?.toDouble() ?? 32.0,
      relativeHumidityPct: (json['relative_humidity_pct'] as num?)?.toDouble() ?? 50.0,
      windSpeedMs: (json['wind_speed_ms'] as num?)?.toDouble() ?? 1.5,
      solarIrradianceWm2: (json['solar_irradiance_wm2'] as num?)?.toDouble() ?? 500.0,
      wbgtEstimatedC: (json['wbgt_estimated_c'] as num?)?.toDouble() ?? 27.5,
      wbgtEffectiveC: (json['wbgt_effective_c'] as num?)?.toDouble() ?? 27.5,
      hazardLevel: json['hazard_level'] ?? 'LOW',
      exceedsScreeningThreshold: json['exceeds_screening_threshold'] ?? false,
      thresholdLimitC: (json['threshold_limit_c'] as num?)?.toDouble() ?? 28.0,
      trend: json['trend'] ?? 'STEADY',
      workRestCycle: json['work_rest_cycle'] ?? 'Continuous work',
      heatIndexC: (json['heat_index_c'] as num?)?.toDouble(),
      utciC: (json['utci_c'] as num?)?.toDouble(),
    );
  }
}

class WorkerHeatResponse {
  final String sessionId;
  final String generatedAtIst;
  final String farmLocationDisplay;
  final String weatherSourceName;
  final String weatherRetrievalTimeIst;
  final String isObservedOrForecast;
  final double currentAirTempC;
  final double currentRelativeHumidityPct;
  final double currentDewPointC;
  final double currentWindSpeedMs;
  final double currentWindSpeedKmh;
  final double currentSolarRadiationWm2;
  final double currentWbgtEstimatedC;
  final double? currentHeatIndexC;
  final double? currentUtciC;
  final Map<String, dynamic> personalizedHeatStrainScore;
  final Map<String, dynamic> topographicDownscaling;
  final Map<String, dynamic> mlForecastMetadata;
  final String nextAssessmentRefreshIst;
  final String dataConfidence;

  final String peakRiskHourIst;
  final String peakRiskReason;
  final List<WorkerHourlyProjection> hourlyProjections;

  final String workloadCategory;
  final String clothingType;
  final double clothingCavC;
  final bool isAcclimatised;
  final String sunExposure;
  final double exposureDurationHours;
  final String currentHazardLevel;
  final String maxHazardLevelInWindow;
  final double maxWbgtEffectiveC;
  final double screeningThresholdC;

  final String categorySelectionReason;
  final List<String> mainContributingFactors;
  final String workloadInteractionExplanation;
  final String methodologyReference;
  final String methodologyStandardsVersion;
  final String thresholdMeaningExplanation;
  final String safetyGuaranteeDisclaimer;
  final Map<String, dynamic> technicalDetails;

  final String disclaimer;
  final List<String> safetyCautions;
  final Map<String, dynamic> hydrationGuidance;
  final List<String> beforeWorkGuidance;
  final List<String> duringWorkGuidance;
  final List<String> highRiskActions;
  final Map<String, dynamic> emergencyTriage;
  final Map<String, String> localEmergencyContacts;

  // Additional defect fix fields
  final String thresholdComparisonMessage;
  final double thresholdDifferenceC;
  final String thresholdComparisonState;
  final double plannedShiftDurationHours;
  final int forecastCoverageHours;
  final bool shiftExceedsForecastCoverage;
  final String? coverageLimitationWarning;
  final String spatialResolution;
  final String gridCoordinates;
  final String validTimeIst;

  // Compatibility getters
  String get hazardLevel => currentHazardLevel.toLowerCase();
  double get wbgtSunC => currentWbgtEstimatedC;
  double get wbgtShadeC => (currentWbgtEstimatedC - 2.8 > 0 ? (currentWbgtEstimatedC - 2.8) : currentWbgtEstimatedC);
  double get airTempC => currentAirTempC;
  double get rhPct => currentRelativeHumidityPct;
  String get advice => categorySelectionReason;
  String get methodology => methodologyReference;

  WorkerHeatResponse({
    this.sessionId = '',
    this.generatedAtIst = '',
    this.farmLocationDisplay = '',
    this.weatherSourceName = 'WMO Global NWP / IMD',
    this.weatherRetrievalTimeIst = '',
    this.isObservedOrForecast = 'Forecast (Operational WMO NWP)',
    required this.currentAirTempC,
    required this.currentRelativeHumidityPct,
    this.currentDewPointC = 20.0,
    this.currentWindSpeedMs = 1.8,
    this.currentWindSpeedKmh = 6.5,
    this.currentSolarRadiationWm2 = 600.0,
    required this.currentWbgtEstimatedC,
    this.currentHeatIndexC,
    this.currentUtciC,
    this.personalizedHeatStrainScore = const {},
    this.topographicDownscaling = const {},
    this.mlForecastMetadata = const {},
    this.nextAssessmentRefreshIst = '',
    this.dataConfidence = 'HIGH',
    this.peakRiskHourIst = '',
    this.peakRiskReason = '',
    this.hourlyProjections = const [],
    this.workloadCategory = 'moderate',
    this.clothingType = 'standard_work_clothes',
    this.clothingCavC = 0.0,
    this.isAcclimatised = true,
    this.sunExposure = 'direct_sun',
    this.exposureDurationHours = 3.0,
    required this.currentHazardLevel,
    this.maxHazardLevelInWindow = 'MODERATE',
    this.maxWbgtEffectiveC = 28.0,
    this.screeningThresholdC = 28.0,
    this.thresholdComparisonMessage = '',
    this.thresholdDifferenceC = 0.0,
    this.thresholdComparisonState = 'BELOW',
    this.plannedShiftDurationHours = 4.0,
    this.forecastCoverageHours = 6,
    this.shiftExceedsForecastCoverage = false,
    this.coverageLimitationWarning,
    this.spatialResolution = '0.1° (~11 km grid resolution)',
    this.gridCoordinates = 'Lat 18.15°N, Lon 74.58°E',
    this.validTimeIst = 'Next 6 Hours',
    this.categorySelectionReason = '',
    this.mainContributingFactors = const [],
    this.workloadInteractionExplanation = '',
    this.methodologyReference = 'Liljegren et al. (2008)',
    this.methodologyStandardsVersion = 'ACGIH 2023 TLVs & ISO 7243:2017 screening action limits',
    this.thresholdMeaningExplanation = '',
    this.safetyGuaranteeDisclaimer = '',
    this.technicalDetails = const {},
    this.disclaimer = '',
    this.safetyCautions = const [],
    this.hydrationGuidance = const {},
    this.beforeWorkGuidance = const [],
    this.duringWorkGuidance = const [],
    this.highRiskActions = const [],
    this.emergencyTriage = const {},
    this.localEmergencyContacts = const {},
  });

  factory WorkerHeatResponse.fromJson(Map<String, dynamic> json) {
    final rawProjections = json['hourly_projections'] as List? ?? [];
    return WorkerHeatResponse(
      sessionId: json['session_id'] ?? '',
      generatedAtIst: json['generated_at_ist'] ?? '',
      farmLocationDisplay: json['farm_location_display'] ?? '',
      weatherSourceName: json['weather_source_name'] ?? 'Operational WMO NWP',
      weatherRetrievalTimeIst: json['weather_retrieval_time_ist'] ?? '',
      isObservedOrForecast: json['is_observed_or_forecast'] ?? 'Forecast (Operational WMO NWP)',
      currentAirTempC: (json['current_air_temp_c'] as num?)?.toDouble() ?? 32.0,
      currentRelativeHumidityPct: (json['current_relative_humidity_pct'] as num?)?.toDouble() ?? 50.0,
      currentDewPointC: (json['current_dew_point_c'] as num?)?.toDouble() ?? 21.0,
      currentWindSpeedMs: (json['current_wind_speed_ms'] as num?)?.toDouble() ?? 1.8,
      currentWindSpeedKmh: (json['current_wind_speed_kmh'] as num?)?.toDouble() ?? 6.5,
      currentSolarRadiationWm2: (json['current_solar_radiation_wm2'] as num?)?.toDouble() ?? 600.0,
      currentWbgtEstimatedC: (json['current_wbgt_estimated_c'] as num?)?.toDouble() ?? 27.8,
      currentHeatIndexC: (json['current_heat_index_c'] as num?)?.toDouble(),
      currentUtciC: (json['current_utci_c'] as num?)?.toDouble(),
      personalizedHeatStrainScore: Map<String, dynamic>.from(json['personalized_heat_strain_score'] ?? {}),
      topographicDownscaling: Map<String, dynamic>.from(json['topographic_downscaling'] ?? {}),
      mlForecastMetadata: Map<String, dynamic>.from(json['ml_forecast_metadata'] ?? {}),
      nextAssessmentRefreshIst: json['next_assessment_refresh_ist'] ?? '',
      dataConfidence: json['data_confidence'] ?? 'HIGH',
      peakRiskHourIst: json['peak_risk_hour_ist'] ?? '',
      peakRiskReason: json['peak_risk_reason'] ?? '',
      hourlyProjections: rawProjections.map((p) => WorkerHourlyProjection.fromJson(p)).toList(),
      workloadCategory: json['workload_category'] ?? 'moderate',
      clothingType: json['clothing_type'] ?? 'standard_work_clothes',
      clothingCavC: (json['clothing_cav_c'] as num?)?.toDouble() ?? 0.0,
      isAcclimatised: json['is_acclimatised'] ?? true,
      sunExposure: json['sun_exposure'] ?? 'direct_sun',
      exposureDurationHours: (json['exposure_duration_hours'] as num?)?.toDouble() ?? 3.0,
      currentHazardLevel: json['current_hazard_level'] ?? 'LOW',
      maxHazardLevelInWindow: json['max_hazard_level_in_window'] ?? 'MODERATE',
      maxWbgtEffectiveC: (json['max_wbgt_effective_c'] as num?)?.toDouble() ?? 28.0,
      screeningThresholdC: (json['screening_threshold_c'] as num?)?.toDouble() ?? 28.0,
      thresholdComparisonMessage: json['threshold_comparison_message'] ?? '',
      thresholdDifferenceC: (json['threshold_difference_c'] as num?)?.toDouble() ?? 0.0,
      thresholdComparisonState: json['threshold_comparison_state'] ?? 'BELOW',
      plannedShiftDurationHours: (json['planned_shift_duration_hours'] as num?)?.toDouble() ?? (json['exposure_duration_hours'] as num?)?.toDouble() ?? 4.0,
      forecastCoverageHours: json['forecast_coverage_hours'] ?? 6,
      shiftExceedsForecastCoverage: json['shift_exceeds_forecast_coverage'] ?? false,
      coverageLimitationWarning: json['coverage_limitation_warning'],
      spatialResolution: json['spatial_resolution'] ?? '0.1° (~11 km grid resolution)',
      gridCoordinates: json['grid_coordinates'] ?? 'Lat 18.15°N, Lon 74.58°E',
      validTimeIst: json['valid_time_ist'] ?? 'Next 6 Hours',
      categorySelectionReason: json['category_selection_reason'] ?? '',
      mainContributingFactors: List<String>.from(json['main_contributing_factors'] ?? []),
      workloadInteractionExplanation: json['workload_interaction_explanation'] ?? '',
      methodologyReference: json['methodology_reference'] ?? 'Liljegren et al. (2008)',
      methodologyStandardsVersion: json['methodology_standards_version'] ?? 'ACGIH 2023 TLVs & ISO 7243:2017 screening action limits',
      thresholdMeaningExplanation: json['threshold_meaning_explanation'] ?? '',
      safetyGuaranteeDisclaimer: json['safety_guarantee_disclaimer'] ?? '',
      technicalDetails: Map<String, dynamic>.from(json['technical_details'] ?? {}),
      disclaimer: json['disclaimer'] ?? '',
      safetyCautions: List<String>.from(json['safety_cautions'] ?? []),
      hydrationGuidance: Map<String, dynamic>.from(json['hydration_guidance'] ?? {}),
      beforeWorkGuidance: List<String>.from(json['before_work_guidance'] ?? []),
      duringWorkGuidance: List<String>.from(json['during_work_guidance'] ?? []),
      highRiskActions: List<String>.from(json['high_risk_actions'] ?? []),
      emergencyTriage: Map<String, dynamic>.from(json['emergency_triage'] ?? {}),
      localEmergencyContacts: Map<String, String>.from(json['local_emergency_contacts'] ?? {}),
    );
  }
}

// ==================== CROP HEAT MODELS ====================

class CropDailyOutlook {
  final String date;
  final String dayLabel;
  final double tmaxC;
  final double tminC;
  final double hoursAboveCritical;
  final String riskCategory;
  final String explanation;

  CropDailyOutlook({
    required this.date,
    required this.dayLabel,
    required this.tmaxC,
    required this.tminC,
    required this.hoursAboveCritical,
    required this.riskCategory,
    required this.explanation,
  });

  factory CropDailyOutlook.fromJson(Map<String, dynamic> json) {
    return CropDailyOutlook(
      date: json['date'] ?? '',
      dayLabel: json['day_label'] ?? '',
      tmaxC: (json['tmax_c'] as num?)?.toDouble() ?? 35.0,
      tminC: (json['tmin_c'] as num?)?.toDouble() ?? 23.0,
      hoursAboveCritical: (json['hours_above_critical'] as num?)?.toDouble() ?? 0.0,
      riskCategory: json['risk_category'] ?? 'LOW',
      explanation: json['explanation'] ?? '',
    );
  }
}

class CropHeatIntervention {
  final String interventionId;
  final String titleEn;
  final String titleMr;
  final String descriptionEn;
  final String descriptionMr;
  final String whyAppropriate;
  final String evidenceCitation;
  final String category;
  final String? sourcePageOrTable;
  final String? agronomistReviewer;
  final String? applicationMethod;
  final String? applicationDose;
  final String? infrastructureRequirements;
  final String? triggerCondition;

  CropHeatIntervention({
    required this.interventionId,
    required this.titleEn,
    required this.titleMr,
    required this.descriptionEn,
    required this.descriptionMr,
    required this.whyAppropriate,
    required this.evidenceCitation,
    required this.category,
    this.sourcePageOrTable,
    this.agronomistReviewer,
    this.applicationMethod,
    this.applicationDose,
    this.infrastructureRequirements,
    this.triggerCondition,
  });

  factory CropHeatIntervention.fromJson(Map<String, dynamic> json) {
    return CropHeatIntervention(
      interventionId: json['intervention_id'] ?? '',
      titleEn: json['title_en'] ?? '',
      titleMr: json['title_mr'] ?? '',
      descriptionEn: json['description_en'] ?? '',
      descriptionMr: json['description_mr'] ?? '',
      whyAppropriate: json['why_appropriate'] ?? '',
      evidenceCitation: json['evidence_citation'] ?? '',
      category: json['category'] ?? 'VERIFIED_AGRONOMIC',
      sourcePageOrTable: json['source_page_or_table'],
      agronomistReviewer: json['agronomist_reviewer'],
      applicationMethod: json['application_method'],
      applicationDose: json['application_dose'],
      infrastructureRequirements: json['infrastructure_requirements'],
      triggerCondition: json['trigger_condition'],
    );
  }
}

class CropHeatAssessment {
  final String assessmentId;
  final String farmId;
  final String farmName;
  final String plotName;
  final String cropCode;
  final String cropCommonName;
  final String cropVariety;
  final String sowingDate;
  final int daysAfterSowing;
  final double cropAreaAcres;
  final String irrigationStatus;
  final String soilTexture;
  final String soilProvenanceLabel;
  final bool isSoilSynthetic;

  final bool isSeasonExpired;
  final String seasonStatus;
  final bool requiresSeasonUpdate;
  final String? seasonExpiryMessage;

  final String? growthStageCode;
  final String growthStageNameEn;
  final String growthStageNameMr;
  final List<Map<String, dynamic>> supportedStages;
  final String? farmerConfirmedStage;

  final double baseTempC;
  final double optimalTempMinC;
  final double optimalTempMaxC;
  final double criticalTmaxThresholdC;
  final double criticalTminThresholdC;
  final double tmaxForecastC;
  final double tminForecastC;
  final double hoursAboveCritical;
  final int consecutiveHotDays;
  final double daytimeExposureHours;
  final bool warmNightRespirationHazard;
  final double warmNightPenaltyScore;
  final double cumulativeHeatUnitsGdd;
  final String evidenceCitation;
  final String evidenceStatus;

  final List<CropDailyOutlook> dailyOutlook;
  final String daytimeHeatStressLevel;
  final String overallCropHeatRisk;
  final String physiologicalMechanism;
  final String stageBiologicalVulnerability;

  final List<CropHeatIntervention> recommendedInterventions;
  final List<Map<String, dynamic>> assessmentHistory;
  final Map<String, dynamic> personalizedCropVulnerabilityScore;
  final Map<String, dynamic> topographicDownscaling;

  // Compatibility getters
  String get stageCode => growthStageCode ?? 'unknown';
  double get maxForecastTempC => tmaxForecastC;
  double get criticalThresholdC => criticalTmaxThresholdC;
  int get exceedanceHours => hoursAboveCritical.round();
  String get riskLevel => overallCropHeatRisk.toLowerCase();
  String get citation => evidenceCitation;

  CropHeatAssessment({
    this.assessmentId = '',
    this.farmId = '',
    this.farmName = '',
    this.plotName = '',
    required this.cropCode,
    this.cropCommonName = '',
    this.cropVariety = 'Variety not recorded',
    this.sowingDate = '',
    this.daysAfterSowing = 45,
    this.cropAreaAcres = 2.5,
    this.irrigationStatus = 'Rainfed',
    this.soilTexture = 'Medium Black Vertisol',
    this.soilProvenanceLabel = 'CropNet Model Estimate (Unsampled Farm Coordinate)',
    this.isSoilSynthetic = true,
    this.isSeasonExpired = false,
    this.seasonStatus = 'ACTIVE',
    this.requiresSeasonUpdate = false,
    this.seasonExpiryMessage,
    this.growthStageCode,
    this.growthStageNameEn = '',
    this.growthStageNameMr = '',
    this.supportedStages = const [],
    this.farmerConfirmedStage,
    this.baseTempC = 10.0,
    this.optimalTempMinC = 24.0,
    this.optimalTempMaxC = 30.0,
    required this.criticalTmaxThresholdC,
    this.criticalTminThresholdC = 22.0,
    required this.tmaxForecastC,
    this.tminForecastC = 23.0,
    this.hoursAboveCritical = 0.0,
    this.consecutiveHotDays = 0,
    this.daytimeExposureHours = 0.0,
    this.warmNightRespirationHazard = false,
    this.warmNightPenaltyScore = 0.0,
    this.cumulativeHeatUnitsGdd = 15.0,
    required this.evidenceCitation,
    this.evidenceStatus = 'VERIFIED_PUBLISHED',
    this.dailyOutlook = const [],
    this.daytimeHeatStressLevel = 'low',
    required this.overallCropHeatRisk,
    this.physiologicalMechanism = '',
    this.stageBiologicalVulnerability = '',
    this.recommendedInterventions = const [],
    this.assessmentHistory = const [],
    this.personalizedCropVulnerabilityScore = const {},
    this.topographicDownscaling = const {},
  });

  factory CropHeatAssessment.fromJson(Map<String, dynamic> json) {
    final rawOutlook = json['daily_outlook'] as List? ?? json['four_day_outlook'] as List? ?? [];
    final rawInterventions = json['recommended_interventions'] as List? ?? json['field_recommendations'] as List? ?? [];
    final rawStages = json['supported_stages'] as List? ?? [];
    final rawHistory = json['assessment_history'] as List? ?? [];

    return CropHeatAssessment(
      assessmentId: json['assessment_id'] ?? '',
      farmId: json['farm_id'] ?? '',
      farmName: json['farm_name'] ?? '',
      plotName: json['plot_name'] ?? '',
      cropCode: json['crop_code'] ?? 'soybean',
      cropCommonName: json['crop_common_name'] ?? json['crop_code'] ?? 'Crop',
      cropVariety: json['crop_variety'] ?? 'Variety not recorded',
      sowingDate: json['sowing_date'] ?? '',
      daysAfterSowing: json['days_after_sowing'] ?? 45,
      cropAreaAcres: (json['crop_area_acres'] as num?)?.toDouble() ?? 2.5,
      irrigationStatus: json['irrigation_status'] ?? 'Rainfed',
      soilTexture: json['soil_texture'] ?? 'Medium Black Vertisol',
      soilProvenanceLabel: json['soil_provenance_label'] ?? 'CropNet Model Estimate (Unsampled Farm Coordinate)',
      isSoilSynthetic: json['is_soil_synthetic'] ?? true,
      isSeasonExpired: json['is_season_expired'] ?? false,
      seasonStatus: json['season_status'] ?? 'ACTIVE',
      requiresSeasonUpdate: json['requires_season_update'] ?? false,
      seasonExpiryMessage: json['season_expiry_message'],
      growthStageCode: json['growth_stage_code'] ?? json['stage_code'],
      growthStageNameEn: json['growth_stage_name_en'] ?? '',
      growthStageNameMr: json['growth_stage_name_mr'] ?? '',
      supportedStages: rawStages.map((s) {
        if (s is Map) {
          final m = Map<String, dynamic>.from(s);
          final rawCode = m['stage_code']?.toString().trim();
          final safeCode = (rawCode != null && rawCode.isNotEmpty && rawCode != 'null') ? rawCode : 'stage_unknown';
          final rawName = m['stage_name_en'] ?? m['stage_name'] ?? m['name'];
          final name = (rawName != null && rawName.toString().trim().isNotEmpty && rawName.toString().trim() != 'null')
              ? rawName.toString().trim()
              : (safeCode != 'stage_unknown' ? safeCode.replaceAll('stage_', '').replaceAll('_', ' ').toUpperCase() : 'Growth Stage');
          return <String, dynamic>{
            'stage_code': safeCode,
            'stage_name': name,
            'stage_name_en': name,
            'das_range': m['das_range']?.toString() ?? '',
            'crit_tmax': (m['crit_tmax'] as num?)?.toDouble() ?? 36.0,
          };
        }
        return <String, dynamic>{};
      }).where((m) => m.isNotEmpty).toList(),
      farmerConfirmedStage: json['farmer_confirmed_stage'],
      baseTempC: (json['base_temp_c'] as num?)?.toDouble() ?? 10.0,
      optimalTempMinC: (json['optimal_temp_min_c'] as num?)?.toDouble() ?? 24.0,
      optimalTempMaxC: (json['optimal_temp_max_c'] as num?)?.toDouble() ?? 30.0,
      criticalTmaxThresholdC: (json['critical_tmax_threshold_c'] as num?)?.toDouble() ?? 36.0,
      criticalTminThresholdC: (json['critical_tmin_threshold_c'] as num?)?.toDouble() ?? 22.0,
      tmaxForecastC: (json['tmax_forecast_c'] as num?)?.toDouble() ?? 34.0,
      tminForecastC: (json['tmin_forecast_c'] as num?)?.toDouble() ?? 23.0,
      hoursAboveCritical: (json['hours_above_critical'] as num?)?.toDouble() ?? 0.0,
      consecutiveHotDays: json['consecutive_hot_days'] ?? 0,
      daytimeExposureHours: (json['daytime_exposure_hours'] as num?)?.toDouble() ?? 0.0,
      warmNightRespirationHazard: json['warm_night_respiration_hazard'] ?? false,
      warmNightPenaltyScore: (json['warm_night_penalty_score'] as num?)?.toDouble() ?? 0.0,
      cumulativeHeatUnitsGdd: (json['cumulative_heat_units_gdd'] as num?)?.toDouble() ?? 15.0,
      evidenceCitation: json['evidence_citation'] ?? '',
      evidenceStatus: json['evidence_status'] ?? 'VERIFIED_PUBLISHED',
      dailyOutlook: rawOutlook.map((o) => CropDailyOutlook.fromJson(o)).toList(),
      daytimeHeatStressLevel: json['daytime_heat_stress_level'] ?? 'low',
      overallCropHeatRisk: json['overall_crop_heat_risk'] ?? 'low',
      physiologicalMechanism: json['physiological_mechanism'] ?? '',
      stageBiologicalVulnerability: json['stage_biological_vulnerability'] ?? '',
      recommendedInterventions: rawInterventions.map((i) => CropHeatIntervention.fromJson(i)).toList(),
      assessmentHistory: List<Map<String, dynamic>>.from(rawHistory),
      personalizedCropVulnerabilityScore: Map<String, dynamic>.from(json['personalized_crop_vulnerability_score'] ?? {}),
      topographicDownscaling: Map<String, dynamic>.from(json['topographic_downscaling'] ?? {}),
    );
  }
}

// ==================== INCOME DIVERSIFICATION MODELS ====================

class FarmerResourceProfile {
  final String farmId;
  final String farmerId;
  final double availableInvestmentInr;
  final double monthlyOperatingBudgetInr;
  final double? maxRiskCapitalInr;
  final bool willingToBorrow;
  final double? totalFarmAcres;
  final double? cultivatedAcres;
  final double availableLandAcres;
  final double unusedLandAcres;
  final bool fieldBundsAvailable;
  final bool hasAnimalShed;
  final bool hasStorageRoom;
  final bool hasShadedSpace;
  final String waterAvailability;
  final List<dynamic> waterMonthsAvailable;
  final double familyLaborHoursDay;
  final bool hiredLaborPossible;
  final String existingLivestock;
  final List<String> existingAssets;
  final List<String> cropByproducts;
  final bool byproductSurplusAvailable;
  final List<String> interests;
  final bool hasTransport;
  final bool hasFpoAccess;
  final double? distanceToApmcKm;
  final String riskTolerance;
  final String categoryPreference;
  final String? ageRange;
  final String workPreference;
  final String paybackHorizon;
  final String familyManagementRole;

  FarmerResourceProfile({
    required this.farmId,
    required this.farmerId,
    this.availableInvestmentInr = 0.0,
    this.monthlyOperatingBudgetInr = 0.0,
    this.maxRiskCapitalInr,
    this.willingToBorrow = false,
    this.totalFarmAcres,
    this.cultivatedAcres,
    this.availableLandAcres = 0.0,
    this.unusedLandAcres = 0.0,
    this.fieldBundsAvailable = true,
    this.hasAnimalShed = false,
    this.hasStorageRoom = false,
    this.hasShadedSpace = false,
    this.waterAvailability = 'seasonal_canal',
    this.waterMonthsAvailable = const [],
    this.familyLaborHoursDay = 2.0,
    this.hiredLaborPossible = false,
    this.existingLivestock = 'none',
    this.existingAssets = const [],
    this.cropByproducts = const [],
    this.byproductSurplusAvailable = true,
    this.interests = const [],
    this.hasTransport = false,
    this.hasFpoAccess = false,
    this.distanceToApmcKm,
    this.riskTolerance = 'moderate',
    this.categoryPreference = 'all',
    this.ageRange = '36_to_45',
    this.workPreference = 'active_physical',
    this.paybackHorizon = 'within_1_year',
    this.familyManagementRole = 'personal_direct',
  });

  bool get isZeroBudget => availableInvestmentInr <= 0.0 && monthlyOperatingBudgetInr <= 0.0;

  factory FarmerResourceProfile.fromJson(Map<String, dynamic> json) {
    return FarmerResourceProfile(
      farmId: json['farm_id'] ?? '',
      farmerId: json['farmer_id'] ?? '',
      availableInvestmentInr: (json['available_investment_inr'] as num?)?.toDouble() ?? 0.0,
      monthlyOperatingBudgetInr: (json['monthly_operating_budget_inr'] as num?)?.toDouble() ?? 0.0,
      maxRiskCapitalInr: (json['max_risk_capital_inr'] as num?)?.toDouble(),
      willingToBorrow: json['willing_to_borrow'] ?? false,
      totalFarmAcres: (json['total_farm_acres'] as num?)?.toDouble(),
      cultivatedAcres: (json['cultivated_acres'] as num?)?.toDouble(),
      availableLandAcres: (json['available_land_acres'] as num?)?.toDouble() ?? 0.0,
      unusedLandAcres: (json['unused_land_acres'] as num?)?.toDouble() ?? 0.0,
      fieldBundsAvailable: json['field_bunds_available'] ?? true,
      hasAnimalShed: json['has_animal_shed'] ?? false,
      hasStorageRoom: json['has_storage_room'] ?? false,
      hasShadedSpace: json['has_shaded_space'] ?? false,
      waterAvailability: json['water_availability'] ?? 'seasonal_canal',
      waterMonthsAvailable: List<dynamic>.from(json['water_months_available'] ?? []),
      familyLaborHoursDay: (json['family_labor_hours_day'] as num?)?.toDouble() ?? 2.0,
      hiredLaborPossible: json['hired_labor_possible'] ?? false,
      existingLivestock: json['existing_livestock'] ?? 'none',
      existingAssets: List<String>.from(json['existing_assets'] ?? []),
      cropByproducts: List<String>.from(json['crop_byproducts'] ?? []),
      byproductSurplusAvailable: json['byproduct_surplus_available'] ?? true,
      interests: List<String>.from(json['interests'] ?? []),
      hasTransport: json['has_transport'] ?? false,
      hasFpoAccess: json['has_fpo_access'] ?? false,
      distanceToApmcKm: (json['distance_to_apmc_km'] as num?)?.toDouble(),
      riskTolerance: json['risk_tolerance'] ?? 'moderate',
      categoryPreference: json['category_preference'] ?? 'all',
      ageRange: json['age_range'] ?? '36_to_45',
      workPreference: json['work_preference'] ?? 'active_physical',
      paybackHorizon: json['payback_horizon'] ?? 'within_1_year',
      familyManagementRole: json['family_management_role'] ?? 'personal_direct',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'farm_id': farmId,
      'farmer_id': farmerId,
      'available_investment_inr': availableInvestmentInr,
      'monthly_operating_budget_inr': monthlyOperatingBudgetInr,
      if (maxRiskCapitalInr != null) 'max_risk_capital_inr': maxRiskCapitalInr,
      'willing_to_borrow': willingToBorrow,
      if (totalFarmAcres != null) 'total_farm_acres': totalFarmAcres,
      if (cultivatedAcres != null) 'cultivated_acres': cultivatedAcres,
      'available_land_acres': availableLandAcres,
      'unused_land_acres': unusedLandAcres,
      'field_bunds_available': fieldBundsAvailable,
      'has_animal_shed': hasAnimalShed,
      'has_storage_room': hasStorageRoom,
      'has_shaded_space': hasShadedSpace,
      'water_availability': waterAvailability,
      'water_months_available': waterMonthsAvailable,
      'family_labor_hours_day': familyLaborHoursDay,
      'hired_labor_possible': hiredLaborPossible,
      'existing_livestock': existingLivestock,
      'existing_assets': existingAssets,
      'crop_byproducts': cropByproducts,
      'byproduct_surplus_available': byproductSurplusAvailable,
      'interests': interests,
      'has_transport': hasTransport,
      'has_fpo_access': hasFpoAccess,
      if (distanceToApmcKm != null) 'distance_to_apmc_km': distanceToApmcKm,
      'risk_tolerance': riskTolerance,
      'category_preference': categoryPreference,
      if (ageRange != null) 'age_range': ageRange,
      'work_preference': workPreference,
      'payback_horizon': paybackHorizon,
      'family_management_role': familyManagementRole,
    };
  }
}

class SavedIncomePlan {
  final String planId;
  final String farmId;
  final String opportunityId;
  final String opportunityTitle;
  final String category;
  final double plannedInvestmentInr;
  final double expectedAnnualIncomeInr;
  final double expectedAnnualSavingsInr;
  final double breakEvenMonths;
  final String status;
  final List<String> actionPlanSteps;
  final String notes;
  final String createdAt;

  SavedIncomePlan({
    required this.planId,
    required this.farmId,
    required this.opportunityId,
    required this.opportunityTitle,
    required this.category,
    required this.plannedInvestmentInr,
    required this.expectedAnnualIncomeInr,
    required this.expectedAnnualSavingsInr,
    required this.breakEvenMonths,
    this.status = 'active',
    this.actionPlanSteps = const [],
    this.notes = '',
    required this.createdAt,
  });

  factory SavedIncomePlan.fromJson(Map<String, dynamic> json) {
    return SavedIncomePlan(
      planId: json['plan_id'] ?? '',
      farmId: json['farm_id'] ?? '',
      opportunityId: json['opportunity_id'] ?? '',
      opportunityTitle: json['opportunity_title'] ?? '',
      category: json['category'] ?? '',
      plannedInvestmentInr: (json['planned_investment_inr'] as num?)?.toDouble() ?? 0.0,
      expectedAnnualIncomeInr: (json['expected_annual_income_inr'] as num?)?.toDouble() ?? 0.0,
      expectedAnnualSavingsInr: (json['expected_annual_savings_inr'] as num?)?.toDouble() ?? 0.0,
      breakEvenMonths: (json['break_even_months'] as num?)?.toDouble() ?? 0.0,
      status: json['status'] ?? 'active',
      actionPlanSteps: List<String>.from(json['action_plan_steps'] ?? []),
      notes: json['notes'] ?? '',
      createdAt: json['created_at'] ?? '',
    );
  }
}

class IncomeOpportunity {
  final String opportunityId;
  final String title;
  final String category;
  final bool isCostSaving;
  final String tagline;
  final List<String> targetCrops;
  final List<String> requiredResources;
  final double minInvestmentInr;
  final double maxInvestmentInr;
  final double workingCapitalRequiredInr;
  final double requiredLandAcres;
  final String requiredSpaceType;
  final String waterRequirement;
  final double dailyLaborHours;
  final int paybackPeriodMonths;
  final double potentialAnnualProfitInr;
  final double potentialAnnualSavingsInr;
  final String riskLevel;
  final String summary;
  final String marketCommodity;
  final String marketBenchmarkPrice;
  final String marketSource;
  final bool marketVerified;
  final List<String> keyAssumptions;
  final List<String> keyRisks;
  final String sourceAttribution;
  final String minimumViableUnitDescription;
  final int productionCycleDays;
  final int revenueDelayMonths;

  IncomeOpportunity({
    required this.opportunityId,
    required this.title,
    required this.category,
    this.isCostSaving = false,
    this.tagline = '',
    this.targetCrops = const [],
    this.requiredResources = const [],
    required this.minInvestmentInr,
    required this.maxInvestmentInr,
    this.workingCapitalRequiredInr = 0.0,
    this.requiredLandAcres = 0.25,
    this.requiredSpaceType = 'field',
    this.waterRequirement = 'low',
    this.dailyLaborHours = 2.0,
    required this.paybackPeriodMonths,
    required this.potentialAnnualProfitInr,
    this.potentialAnnualSavingsInr = 0.0,
    required this.riskLevel,
    required this.summary,
    this.marketCommodity = '',
    this.marketBenchmarkPrice = '',
    this.marketSource = '',
    this.marketVerified = true,
    required this.keyAssumptions,
    required this.keyRisks,
    required this.sourceAttribution,
    this.minimumViableUnitDescription = '',
    this.productionCycleDays = 90,
    this.revenueDelayMonths = 3,
  });

  factory IncomeOpportunity.fromJson(Map<String, dynamic> json) {
    return IncomeOpportunity(
      opportunityId: json['opportunity_id'] ?? '',
      title: json['title'] ?? '',
      category: json['category'] ?? '',
      isCostSaving: json['is_cost_saving'] ?? false,
      tagline: json['tagline'] ?? '',
      targetCrops: List<String>.from(json['target_crops'] ?? []),
      requiredResources: List<String>.from(json['required_resources'] ?? []),
      minInvestmentInr: (json['min_investment_inr'] as num?)?.toDouble() ?? 0.0,
      maxInvestmentInr: (json['max_investment_inr'] as num?)?.toDouble() ?? 0.0,
      workingCapitalRequiredInr: (json['working_capital_required_inr'] as num?)?.toDouble() ?? 0.0,
      requiredLandAcres: (json['required_land_acres'] as num?)?.toDouble() ?? 0.25,
      requiredSpaceType: json['required_space_type'] ?? 'field',
      waterRequirement: json['water_requirement'] ?? 'low',
      dailyLaborHours: (json['daily_labor_hours'] as num?)?.toDouble() ?? 2.0,
      paybackPeriodMonths: json['payback_period_months'] ?? 6,
      potentialAnnualProfitInr: (json['potential_annual_profit_inr'] as num?)?.toDouble() ?? 0.0,
      potentialAnnualSavingsInr: (json['potential_annual_savings_inr'] as num?)?.toDouble() ?? 0.0,
      riskLevel: json['risk_level'] ?? 'moderate',
      summary: json['summary'] ?? '',
      marketCommodity: json['market_commodity'] ?? '',
      marketBenchmarkPrice: json['market_benchmark_price'] ?? '',
      marketSource: json['market_source'] ?? '',
      marketVerified: json['market_verified'] ?? true,
      keyAssumptions: List<String>.from(json['key_assumptions'] ?? []),
      keyRisks: List<String>.from(json['key_risks'] ?? []),
      sourceAttribution: json['source_attribution'] ?? '',
      minimumViableUnitDescription: json['minimum_viable_unit_description'] ?? '',
      productionCycleDays: json['production_cycle_days'] ?? 90,
      revenueDelayMonths: json['revenue_delay_months'] ?? 3,
    );
  }
}

class ScoredOpportunityItem {
  final IncomeOpportunity opportunity;
  final int suitabilityScorePct;
  final bool isSuitable;
  final String suitabilityVerdict;
  final List<String> reasonsWhySuitable;
  final List<String> reasonsWhyUnsuitable;
  final String feasibilityStatus;
  final double capitalGapInr;
  final List<String> limitingFactors;
  final List<String> matchingResources;
  final double estimatedAnnualProfitInr;
  final double estimatedAnnualSavingsInr;
  final double paybackMonths;
  final String marketBenchmarkSummary;
  final String feasibilityCategory;
  final Map<String, String>? farmerSummaryQa;

  ScoredOpportunityItem({
    required this.opportunity,
    required this.suitabilityScorePct,
    required this.isSuitable,
    required this.suitabilityVerdict,
    required this.reasonsWhySuitable,
    required this.reasonsWhyUnsuitable,
    this.feasibilityStatus = 'FEASIBLE_NOW',
    this.capitalGapInr = 0.0,
    this.limitingFactors = const [],
    this.matchingResources = const [],
    this.estimatedAnnualProfitInr = 0.0,
    this.estimatedAnnualSavingsInr = 0.0,
    this.paybackMonths = 1.0,
    this.marketBenchmarkSummary = '',
    this.feasibilityCategory = 'CAN_TRY_WITH_WHAT_YOU_HAVE',
    this.farmerSummaryQa,
  });

  bool get isFeasible => isSuitable && (feasibilityStatus == 'FEASIBLE_NOW' || feasibilityStatus == 'HIGHLY_FEASIBLE' || feasibilityStatus == 'USES_EXISTING_RESOURCES');

  factory ScoredOpportunityItem.fromJson(Map<String, dynamic> json) {
    Map<String, String>? qaMap;
    if (json['farmer_summary_qa'] is Map) {
      qaMap = (json['farmer_summary_qa'] as Map).map((k, v) => MapEntry(k.toString(), v.toString()));
    }

    return ScoredOpportunityItem(
      opportunity: IncomeOpportunity.fromJson(json['opportunity'] ?? {}),
      suitabilityScorePct: json['suitability_score_pct'] ?? (json['suitability_score'] as num?)?.toInt() ?? 75,
      isSuitable: json['is_suitable'] ?? json['is_feasible'] ?? true,
      suitabilityVerdict: json['suitability_verdict'] ?? json['feasibility_status'] ?? 'Suitable',
      reasonsWhySuitable: List<String>.from(json['reasons_why_suitable'] ?? json['matching_resources'] ?? []),
      reasonsWhyUnsuitable: List<String>.from(json['reasons_why_unsuitable'] ?? json['limiting_factors'] ?? []),
      feasibilityStatus: json['feasibility_status'] ?? 'FEASIBLE_NOW',
      capitalGapInr: (json['capital_gap_inr'] as num?)?.toDouble() ?? 0.0,
      limitingFactors: List<String>.from(json['limiting_factors'] ?? []),
      matchingResources: List<String>.from(json['matching_resources'] ?? []),
      estimatedAnnualProfitInr: (json['estimated_annual_profit_inr'] as num?)?.toDouble() ?? 0.0,
      estimatedAnnualSavingsInr: (json['estimated_annual_savings_inr'] as num?)?.toDouble() ?? 0.0,
      paybackMonths: (json['payback_months'] as num?)?.toDouble() ?? 1.0,
      marketBenchmarkSummary: json['market_benchmark_summary'] ?? '',
      feasibilityCategory: json['feasibility_category'] ?? 'CAN_TRY_WITH_WHAT_YOU_HAVE',
      farmerSummaryQa: qaMap,
    );
  }
}

class DashboardIssue {
  final String issueId;
  final String domain;
  final String severity; // URGENT_ATTENTION, NEEDS_ATTENTION, KEEP_AN_EYE_ON, INFORMATION
  final String title;
  final String summary;
  final String recommendedAction;
  final String actionTargetRoute;
  final String actionButtonLabel;
  final Map<String, dynamic> evidence;

  DashboardIssue({
    required this.issueId,
    required this.domain,
    required this.severity,
    required this.title,
    required this.summary,
    required this.recommendedAction,
    required this.actionTargetRoute,
    required this.actionButtonLabel,
    this.evidence = const {},
  });

  factory DashboardIssue.fromJson(Map<String, dynamic> json) {
    return DashboardIssue(
      issueId: json['issue_id'] ?? '',
      domain: json['domain'] ?? '',
      severity: json['severity'] ?? 'INFORMATION',
      title: json['title'] ?? '',
      summary: json['summary'] ?? '',
      recommendedAction: json['recommended_action'] ?? '',
      actionTargetRoute: json['action_target_route'] ?? '/',
      actionButtonLabel: json['action_button_label'] ?? 'View Details',
      evidence: Map<String, dynamic>.from(json['evidence'] ?? {}),
    );
  }
}

class DashboardSummaryResponse {
  final String farmId;
  final String farmName;
  final bool hasUrgentIssues;
  final int totalIssuesCount;
  final List<DashboardIssue> issues;
  final String? positiveStatusSummary;
  final String assessedAt;

  DashboardSummaryResponse({
    required this.farmId,
    required this.farmName,
    required this.hasUrgentIssues,
    required this.totalIssuesCount,
    required this.issues,
    this.positiveStatusSummary,
    required this.assessedAt,
  });

  factory DashboardSummaryResponse.fromJson(Map<String, dynamic> json) {
    return DashboardSummaryResponse(
      farmId: json['farm_id'] ?? '',
      farmName: json['farm_name'] ?? 'My Farm',
      hasUrgentIssues: json['has_urgent_issues'] ?? false,
      totalIssuesCount: json['total_issues_count'] ?? 0,
      issues: (json['issues'] as List<dynamic>? ?? [])
          .map((i) => DashboardIssue.fromJson(i as Map<String, dynamic>))
          .toList(),
      positiveStatusSummary: json['positive_status_summary'],
      assessedAt: json['assessed_at'] ?? '',
    );
  }
}

class FinancialScenarioDetail {
  final String name;
  final String priceAssumption;
  final String costAssumption;
  final double grossAnnualRevenueInr;
  final double annualOpexInr;
  final double netAnnualProfitInr;
  final double breakEvenMonths;
  final List<double> monthlyNetCashFlowInr;

  FinancialScenarioDetail({
    required this.name,
    required this.priceAssumption,
    required this.costAssumption,
    required this.grossAnnualRevenueInr,
    required this.annualOpexInr,
    required this.netAnnualProfitInr,
    required this.breakEvenMonths,
    required this.monthlyNetCashFlowInr,
  });

  factory FinancialScenarioDetail.fromJson(Map<String, dynamic> json) {
    final rawFlows = json['monthly_net_cash_flow_inr'] as List? ?? [];
    return FinancialScenarioDetail(
      name: json['name'] ?? '',
      priceAssumption: json['price_assumption'] ?? '',
      costAssumption: json['cost_assumption'] ?? '',
      grossAnnualRevenueInr: (json['gross_annual_revenue_inr'] as num?)?.toDouble() ?? 0.0,
      annualOpexInr: (json['annual_opex_inr'] as num?)?.toDouble() ?? 0.0,
      netAnnualProfitInr: (json['net_annual_profit_inr'] as num?)?.toDouble() ?? 0.0,
      breakEvenMonths: (json['break_even_months'] as num?)?.toDouble() ?? 0.0,
      monthlyNetCashFlowInr: rawFlows.map((f) => (f as num).toDouble()).toList(),
    );
  }
}

class IncomeScenario {
  final String opportunityId;
  final String opportunityTitle;
  final String category;
  final double customBudgetInr;
  final double calculatedCapexInr;
  final double workingCapitalInr;
  final double totalInitialOutlayInr;
  final double calculatedGrossRevenueInr;
  final double calculatedOpexAnnualInr;
  final double calculatedNetProfitAnnualInr;
  final double calculatedBreakEvenMonths;
  final List<String> assumptionsApplied;
  final List<String> risksToMonitor;
  final String sourceAttribution;
  final String disclaimer;
  final Map<String, FinancialScenarioDetail> scenarios;
  final Map<String, dynamic> localMandiBenchmark;
  final Map<String, dynamic> sensitivityAnalysis;

  IncomeScenario({
    required this.opportunityId,
    required this.opportunityTitle,
    this.category = '',
    required this.customBudgetInr,
    required this.calculatedCapexInr,
    this.workingCapitalInr = 0.0,
    this.totalInitialOutlayInr = 0.0,
    required this.calculatedOpexAnnualInr,
    required this.calculatedGrossRevenueInr,
    required this.calculatedNetProfitAnnualInr,
    required this.calculatedBreakEvenMonths,
    required this.assumptionsApplied,
    required this.risksToMonitor,
    required this.sourceAttribution,
    required this.disclaimer,
    this.scenarios = const {},
    this.localMandiBenchmark = const {},
    this.sensitivityAnalysis = const {},
  });

  factory IncomeScenario.fromJson(Map<String, dynamic> json) {
    final rawScenarios = json['scenarios'] as Map<String, dynamic>? ?? {};
    final parsedScenarios = <String, FinancialScenarioDetail>{};
    rawScenarios.forEach((key, val) {
      if (val is Map<String, dynamic>) {
        parsedScenarios[key] = FinancialScenarioDetail.fromJson(val);
      }
    });

    return IncomeScenario(
      opportunityId: json['opportunity_id'] ?? '',
      opportunityTitle: json['opportunity_title'] ?? '',
      category: json['category'] ?? '',
      customBudgetInr: (json['custom_budget_inr'] as num?)?.toDouble() ?? 0.0,
      calculatedCapexInr: (json['calculated_capex_inr'] as num?)?.toDouble() ?? 0.0,
      workingCapitalInr: (json['working_capital_inr'] as num?)?.toDouble() ?? 0.0,
      totalInitialOutlayInr: (json['total_initial_outlay_inr'] as num?)?.toDouble() ?? 0.0,
      calculatedGrossRevenueInr: (json['calculated_gross_revenue_inr'] as num?)?.toDouble() ?? 0.0,
      calculatedOpexAnnualInr: (json['calculated_opex_annual_inr'] as num?)?.toDouble() ?? 0.0,
      calculatedNetProfitAnnualInr: (json['calculated_net_profit_annual_inr'] as num?)?.toDouble() ?? 0.0,
      calculatedBreakEvenMonths: (json['calculated_break_even_months'] as num?)?.toDouble() ?? 0.0,
      assumptionsApplied: List<String>.from(json['assumptions_applied'] ?? []),
      risksToMonitor: List<String>.from(json['risks_to_monitor'] ?? []),
      sourceAttribution: json['source_attribution'] ?? '',
      disclaimer: json['disclaimer'] ?? '',
      scenarios: parsedScenarios,
      localMandiBenchmark: Map<String, dynamic>.from(json['local_mandi_benchmark'] ?? {}),
      sensitivityAnalysis: Map<String, dynamic>.from(json['sensitivity_analysis'] ?? {}),
    );
  }
}

class OpportunityComparisonItem {
  final String opportunityId;
  final String title;
  final String category;
  final bool isCostSaving;
  final double initialInvestmentInr;
  final double workingCapitalInr;
  final double netAnnualProfitInr;
  final double annualSavingsInr;
  final double paybackMonths;
  final double landRequiredAcres;
  final String waterNeeds;
  final double dailyLaborHours;
  final String riskLevel;
  final String suitabilityVerdict;
  final String marketBenchmark;

  OpportunityComparisonItem({
    required this.opportunityId,
    required this.title,
    required this.category,
    this.isCostSaving = false,
    required this.initialInvestmentInr,
    this.workingCapitalInr = 0.0,
    required this.netAnnualProfitInr,
    this.annualSavingsInr = 0.0,
    required this.paybackMonths,
    required this.landRequiredAcres,
    required this.waterNeeds,
    required this.dailyLaborHours,
    required this.riskLevel,
    required this.suitabilityVerdict,
    this.marketBenchmark = '',
  });

  factory OpportunityComparisonItem.fromJson(Map<String, dynamic> json) {
    return OpportunityComparisonItem(
      opportunityId: json['opportunity_id'] ?? '',
      title: json['title'] ?? '',
      category: json['category'] ?? '',
      isCostSaving: json['is_cost_saving'] ?? false,
      initialInvestmentInr: (json['initial_investment_inr'] as num?)?.toDouble() ?? 0.0,
      workingCapitalInr: (json['working_capital_inr'] as num?)?.toDouble() ?? 0.0,
      netAnnualProfitInr: (json['net_annual_profit_inr'] as num?)?.toDouble() ?? 0.0,
      annualSavingsInr: (json['annual_savings_inr'] as num?)?.toDouble() ?? 0.0,
      paybackMonths: (json['payback_months'] as num?)?.toDouble() ?? 0.0,
      landRequiredAcres: (json['land_required_acres'] as num?)?.toDouble() ?? 0.0,
      waterNeeds: json['water_needs'] ?? '',
      dailyLaborHours: (json['daily_labor_hours'] as num?)?.toDouble() ?? 0.0,
      riskLevel: json['risk_level'] ?? '',
      suitabilityVerdict: json['suitability_verdict'] ?? '',
      marketBenchmark: json['market_benchmark'] ?? '',
    );
  }
}

// ==================== PMFBY & CHAT MODELS ====================

class CropLossCase {
  final String caseId;
  final String farmerId;
  final String farmId;
  final String cropCode;
  final String season;
  final String eventDate;
  final String perilType;
  final double damageEstimatePct;
  final double affectedAreaAcres;
  final List<String> photoUrls;
  final String dossierStatus;
  final Map<String, dynamic> weatherEvidenceSummary;
  final Map<String, dynamic> satelliteEvidenceSummary;
  final Map<String, dynamic> visionEvidenceSummary;
  final Map<String, dynamic> multimodalFusionSummary;
  final int slaTargetHours;
  final double slaRemainingHours;
  final String slaStatus;
  final String? reviewerDecision;
  final String? reviewerRationale;
  final String createdAt;
  final String disclaimer;

  CropLossCase({
    required this.caseId,
    required this.farmerId,
    required this.farmId,
    required this.cropCode,
    required this.season,
    required this.eventDate,
    required this.perilType,
    required this.damageEstimatePct,
    required this.affectedAreaAcres,
    required this.photoUrls,
    required this.dossierStatus,
    required this.weatherEvidenceSummary,
    this.satelliteEvidenceSummary = const {},
    this.visionEvidenceSummary = const {},
    this.multimodalFusionSummary = const {},
    this.slaTargetHours = 48,
    this.slaRemainingHours = 48.0,
    this.slaStatus = "within_sla",
    this.reviewerDecision,
    this.reviewerRationale,
    required this.createdAt,
    required this.disclaimer,
  });

  factory CropLossCase.fromJson(Map<String, dynamic> json) {
    return CropLossCase(
      caseId: json['case_id'] ?? '',
      farmerId: json['farmer_id'] ?? '',
      farmId: json['farm_id'] ?? '',
      cropCode: json['crop_code'] ?? '',
      season: json['season'] ?? 'kharif',
      eventDate: json['event_date'] ?? '',
      perilType: json['peril_type'] ?? '',
      damageEstimatePct: (json['damage_estimate_pct'] as num?)?.toDouble() ?? 0.0,
      affectedAreaAcres: (json['affected_area_acres'] as num?)?.toDouble() ?? 0.0,
      photoUrls: List<String>.from(json['photo_urls'] ?? []),
      dossierStatus: json['dossier_status'] ?? 'draft_saved',
      weatherEvidenceSummary: Map<String, dynamic>.from(json['weather_evidence_summary'] ?? {}),
      satelliteEvidenceSummary: Map<String, dynamic>.from(json['satellite_evidence_summary'] ?? {}),
      visionEvidenceSummary: Map<String, dynamic>.from(json['vision_evidence_summary'] ?? {}),
      multimodalFusionSummary: Map<String, dynamic>.from(json['multimodal_fusion_summary'] ?? {}),
      slaTargetHours: (json['sla_target_hours'] as num?)?.toInt() ?? 48,
      slaRemainingHours: (json['sla_remaining_hours'] as num?)?.toDouble() ?? 48.0,
      slaStatus: json['sla_status'] ?? 'within_sla',
      reviewerDecision: json['reviewer_decision'],
      reviewerRationale: json['reviewer_rationale'],
      createdAt: json['created_at'] ?? '',
      disclaimer: json['disclaimer'] ?? '',
    );
  }
}

class AssistantChatMessage {
  final String sender; // 'user' or 'assistant'
  final String text;
  final String? providerUsed;
  final List<Map<String, String>> citations;
  final DateTime timestamp;

  AssistantChatMessage({
    required this.sender,
    required this.text,
    this.providerUsed,
    this.citations = const [],
    required this.timestamp,
  });
}

class SoilIndicatorItem {
  final String key;
  final String displayName;
  final String valueDisplay;
  final String unit;
  final String status;
  final bool isEstimated;
  final String? scientificNote;

  SoilIndicatorItem({
    required this.key,
    required this.displayName,
    required this.valueDisplay,
    required this.unit,
    required this.status,
    required this.isEstimated,
    this.scientificNote,
  });

  factory SoilIndicatorItem.fromJson(Map<String, dynamic> json) {
    return SoilIndicatorItem(
      key: json['key'] ?? '',
      displayName: json['display_name'] ?? '',
      valueDisplay: json['value_display'] ?? '',
      unit: json['unit'] ?? '',
      status: json['status'] ?? 'normal',
      isEstimated: json['is_estimated'] ?? true,
      scientificNote: json['scientific_note'],
    );
  }
}

class CropNetSoilCardData {
  final String farmId;
  final String farmName;
  final String locationDisplay;
  final String textureSummary;
  final String reactionSummary;
  final String provenanceBadge;
  final bool isLabMeasured;
  final String lastUpdatedDisplay;
  final String depthInterval;
  final String disclaimer;
  final String unmeasuredNutrientsNotice;
  final List<SoilIndicatorItem> indicators;
  final Map<String, dynamic> technicalDetails;

  CropNetSoilCardData({
    required this.farmId,
    required this.farmName,
    required this.locationDisplay,
    required this.textureSummary,
    required this.reactionSummary,
    required this.provenanceBadge,
    required this.isLabMeasured,
    required this.lastUpdatedDisplay,
    required this.depthInterval,
    required this.disclaimer,
    required this.unmeasuredNutrientsNotice,
    required this.indicators,
    required this.technicalDetails,
  });

  factory CropNetSoilCardData.fromJson(Map<String, dynamic> json) {
    return CropNetSoilCardData(
      farmId: json['farm_id'] ?? '',
      farmName: json['farm_name'] ?? 'Demo Farm',
      locationDisplay: json['location_display'] ?? 'Maharashtra, India',
      textureSummary: json['texture_summary'] ?? 'Medium Black Vertisol (Clay)',
      reactionSummary: json['reaction_summary'] ?? 'Moderately Alkaline (pH 7.8)',
      provenanceBadge: json['provenance_badge'] ?? 'Location-Based Estimate (SoilGrids 250m)',
      isLabMeasured: json['is_lab_measured'] ?? false,
      lastUpdatedDisplay: json['last_updated_display'] ?? 'Recently',
      depthInterval: json['depth_interval'] ?? '0-5cm',
      disclaimer: json['disclaimer'] ?? 'Estimated from geospatial datasets.',
      unmeasuredNutrientsNotice: json['unmeasured_nutrients_notice'] ?? 'Available N-P-K: Physical Lab Test Required',
      indicators: (json['indicators'] as List<dynamic>?)
              ?.map((item) => SoilIndicatorItem.fromJson(Map<String, dynamic>.from(item)))
              .toList() ??
          [],
      technicalDetails: Map<String, dynamic>.from(json['technical_details'] ?? {}),
    );
  }
}

