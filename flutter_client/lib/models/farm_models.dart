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

class YieldAssessment {
  final String farmId;
  final String cropCode;
  final String cropStageCode;
  final String cropStageNameEn;
  final String? cropStageNameMr;
  final int das;
  final List<RiskDimensionItem> risks;
  final Map<String, dynamic> baseline;

  YieldAssessment({
    required this.farmId,
    required this.cropCode,
    required this.cropStageCode,
    required this.cropStageNameEn,
    this.cropStageNameMr,
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
      cropStageNameMr: stage['stage_name_mr'] ?? stage['stage_name_en'],
      das: stage['days_after_sowing'] ?? 45,
      risks: rawRisks.map((r) => RiskDimensionItem.fromJson(r)).toList(),
      baseline: json['yield_baseline'] ?? {},
    );
  }
}

class WorkerHeatResponse {
  final String hazardLevel;
  final double wbgtSunC;
  final double wbgtShadeC;
  final double airTempC;
  final double rhPct;
  final String advice;
  final String methodology;

  WorkerHeatResponse({
    required this.hazardLevel,
    required this.wbgtSunC,
    required this.wbgtShadeC,
    required this.airTempC,
    required this.rhPct,
    required this.advice,
    required this.methodology,
  });

  factory WorkerHeatResponse.fromJson(Map<String, dynamic> json) {
    final metrics = json['heat_metrics'] ?? {};
    return WorkerHeatResponse(
      hazardLevel: json['hazard_level'] ?? 'moderate',
      wbgtSunC: (metrics['estimated_wbgt_sun_c'] as num?)?.toDouble() ?? 28.5,
      wbgtShadeC: (metrics['estimated_wbgt_shade_c'] as num?)?.toDouble() ?? 26.0,
      airTempC: (metrics['air_temp_c'] as num?)?.toDouble() ?? 33.0,
      rhPct: (metrics['relative_humidity_pct'] as num?)?.toDouble() ?? 55.0,
      advice: json['plain_language_advice'] ?? 'Drink water frequently and take rest in shade during peak afternoon.',
      methodology: json['methodology'] ?? 'Liljegren_et_al_2008_energy_balance',
    );
  }
}

class CropHeatAssessment {
  final String cropCode;
  final String stageCode;
  final double maxForecastTempC;
  final double criticalThresholdC;
  final int exceedanceHours;
  final String riskLevel;
  final String citation;

  CropHeatAssessment({
    required this.cropCode,
    required this.stageCode,
    required this.maxForecastTempC,
    required this.criticalThresholdC,
    required this.exceedanceHours,
    required this.riskLevel,
    required this.citation,
  });

  factory CropHeatAssessment.fromJson(Map<String, dynamic> json) {
    return CropHeatAssessment(
      cropCode: json['crop_code'] ?? 'soybean',
      stageCode: json['stage_code'] ?? 'flowering',
      maxForecastTempC: (json['max_forecast_temp_c'] as num?)?.toDouble() ?? 36.5,
      criticalThresholdC: (json['critical_threshold_c'] as num?)?.toDouble() ?? 38.0,
      exceedanceHours: json['exceedance_hours'] ?? 0,
      riskLevel: json['risk_level'] ?? 'low',
      citation: json['evidence_citation'] ?? 'MPKV Rahuri Package of Practices',
    );
  }
}

class IncomeOpportunity {
  final String opportunityId;
  final String title;
  final String category;
  final List<String> targetCrops;
  final List<String> requiredResources;
  final double minInvestmentInr;
  final double maxInvestmentInr;
  final int paybackPeriodMonths;
  final double potentialAnnualProfitInr;
  final String riskLevel;
  final String summary;
  final List<String> keyAssumptions;
  final List<String> keyRisks;
  final String sourceAttribution;

  IncomeOpportunity({
    required this.opportunityId,
    required this.title,
    required this.category,
    required this.targetCrops,
    required this.requiredResources,
    required this.minInvestmentInr,
    required this.maxInvestmentInr,
    required this.paybackPeriodMonths,
    required this.potentialAnnualProfitInr,
    required this.riskLevel,
    required this.summary,
    required this.keyAssumptions,
    required this.keyRisks,
    required this.sourceAttribution,
  });

  factory IncomeOpportunity.fromJson(Map<String, dynamic> json) {
    return IncomeOpportunity(
      opportunityId: json['opportunity_id'] ?? '',
      title: json['title'] ?? '',
      category: json['category'] ?? '',
      targetCrops: List<String>.from(json['target_crops'] ?? []),
      requiredResources: List<String>.from(json['required_resources'] ?? []),
      minInvestmentInr: (json['min_investment_inr'] as num?)?.toDouble() ?? 0.0,
      maxInvestmentInr: (json['max_investment_inr'] as num?)?.toDouble() ?? 0.0,
      paybackPeriodMonths: json['payback_period_months'] ?? 6,
      potentialAnnualProfitInr: (json['potential_annual_profit_inr'] as num?)?.toDouble() ?? 0.0,
      riskLevel: json['risk_level'] ?? 'moderate',
      summary: json['summary'] ?? '',
      keyAssumptions: List<String>.from(json['key_assumptions'] ?? []),
      keyRisks: List<String>.from(json['key_risks'] ?? []),
      sourceAttribution: json['source_attribution'] ?? '',
    );
  }
}

class IncomeScenario {
  final String opportunityId;
  final String opportunityTitle;
  final double customBudgetInr;
  final double calculatedCapexInr;
  final double calculatedOpexAnnualInr;
  final double calculatedGrossRevenueInr;
  final double calculatedNetProfitAnnualInr;
  final double calculatedBreakEvenMonths;
  final List<String> assumptionsApplied;
  final List<String> risksToMonitor;
  final String sourceAttribution;
  final String disclaimer;

  IncomeScenario({
    required this.opportunityId,
    required this.opportunityTitle,
    required this.customBudgetInr,
    required this.calculatedCapexInr,
    required this.calculatedOpexAnnualInr,
    required this.calculatedGrossRevenueInr,
    required this.calculatedNetProfitAnnualInr,
    required this.calculatedBreakEvenMonths,
    required this.assumptionsApplied,
    required this.risksToMonitor,
    required this.sourceAttribution,
    required this.disclaimer,
  });

  factory IncomeScenario.fromJson(Map<String, dynamic> json) {
    return IncomeScenario(
      opportunityId: json['opportunity_id'] ?? '',
      opportunityTitle: json['opportunity_title'] ?? '',
      customBudgetInr: (json['custom_budget_inr'] as num?)?.toDouble() ?? 0.0,
      calculatedCapexInr: (json['calculated_capex_inr'] as num?)?.toDouble() ?? 0.0,
      calculatedOpexAnnualInr: (json['calculated_opex_annual_inr'] as num?)?.toDouble() ?? 0.0,
      calculatedGrossRevenueInr: (json['calculated_gross_revenue_inr'] as num?)?.toDouble() ?? 0.0,
      calculatedNetProfitAnnualInr: (json['calculated_net_profit_annual_inr'] as num?)?.toDouble() ?? 0.0,
      calculatedBreakEvenMonths: (json['calculated_break_even_months'] as num?)?.toDouble() ?? 0.0,
      assumptionsApplied: List<String>.from(json['assumptions_applied'] ?? []),
      risksToMonitor: List<String>.from(json['risks_to_monitor'] ?? []),
      sourceAttribution: json['source_attribution'] ?? '',
      disclaimer: json['disclaimer'] ?? '',
    );
  }
}

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
