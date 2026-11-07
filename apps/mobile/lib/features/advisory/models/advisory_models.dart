/// CropNet AI — Deterministic Agricultural Reasoning & Advisory Models
///
/// Matches FastAPI schemas in `services/api/app/schemas/agriculture_intelligence.py`.
library;

/// Standardized machine-readable agronomic outcomes.
enum DecisionState {
  verifiedSuitable('VERIFIED_SUITABLE'),
  regionalScreeningOnly('REGIONAL_SCREENING_ONLY'),
  conditionallySuitablePendingData('CONDITIONALLY_SUITABLE_PENDING_DATA'),
  requiresRegionalValidation('REQUIRES_REGIONAL_VALIDATION'),
  unsuitableVerifiedConstraint('UNSUITABLE_VERIFIED_CONSTRAINT'),
  abstainInsufficientEvidence('ABSTAIN_INSUFFICIENT_EVIDENCE');

  final String value;
  const DecisionState(this.value);

  static DecisionState fromString(String? val) {
    return DecisionState.values.firstWhere(
      (e) => e.value == val,
      orElse: () => DecisionState.abstainInsufficientEvidence,
    );
  }
}

/// Canonical 4-tier evidence gating classifications.
enum EvidenceTier {
  verified('VERIFIED'),
  conditionallySupported('CONDITIONALLY_SUPPORTED'),
  unverifiedBibliographic('UNVERIFIED_BIBLIOGRAPHIC'),
  unsupported('UNSUPPORTED');

  final String value;
  const EvidenceTier(this.value);

  static EvidenceTier fromString(String? val) {
    return EvidenceTier.values.firstWhere(
      (e) => e.value == val,
      orElse: () => EvidenceTier.unsupported,
    );
  }
}

/// Standardized rule enforcement levels for agricultural reasoning.
enum EnforcementLevel {
  verifiedHardConstraint('VERIFIED_HARD_CONSTRAINT'),
  conditionalConstraint('CONDITIONAL_CONSTRAINT'),
  advisoryOnly('ADVISORY_ONLY'),
  unverified('UNVERIFIED'),
  unsupported('UNSUPPORTED');

  final String value;
  const EnforcementLevel(this.value);

  static EnforcementLevel fromString(String? val) {
    return EnforcementLevel.values.firstWhere(
      (e) => e.value == val,
      orElse: () => EnforcementLevel.advisoryOnly,
    );
  }
}

/// Provenance distinction for soil input data.
enum SoilDataProvenance {
  laboratoryMeasured('laboratory_measured'),
  spatiallyEstimatedIsric('spatially_estimated_isric'),
  userReported('user_reported'),
  unknown('unknown');

  final String value;
  const SoilDataProvenance(this.value);

  static SoilDataProvenance fromString(String? val) {
    return SoilDataProvenance.values.firstWhere(
      (e) => e.value == val,
      orElse: () => SoilDataProvenance.unknown,
    );
  }
}

/// Structured farm context input for deterministic agricultural reasoning.
class FarmContextInput {
  final String? farmId;
  final double? latitude;
  final double? longitude;
  final String? taluka;
  final String district;

  // Soil chemical and physical parameters
  final double? soilPh;
  final double? soilOrganicCarbonPct;
  final String? soilTexture;
  final double? soilDepthCm;
  final String? drainage;
  final String? waterTableDepth;
  final double? waterTableDepthM;
  final int? standingWaterDays;
  final double? electricalConductivityDsM;

  // Nutrient availability (Strict separation of Total vs Available N)
  final double? availableNitrogenKgHa;
  final double? totalNitrogenPct;
  final double? availablePhosphorusKgHa;
  final double? availablePotassiumKgHa;

  // Soil provenance
  final SoilDataProvenance soilDataProvenance;
  final String? soilMeasurementDate;

  // Hydrology & Irrigation
  final bool? irrigationAvailable;
  final String? irrigationSource;
  final String? irrigationCapacity;
  final String? alternativeSummerIrrigation;
  final bool? irrigationWaterSalinityTested;
  final double? irrigationWaterEcDsM;

  // Orchard & Bahar Specifics (Pomegranate)
  final int? treeAgeYears;
  final String? targetBahar;
  final String? waterScarcityPeriod;

  // Cropping context & Season
  final String? previousCrop;
  final String? targetSeason;
  final int? targetYear;
  final String? proposedSowingDate;
  final double? actualRecordedRainMm;
  final bool? monsoonArrived;

  // Real-time weather & forecast
  final double? forecastMaxTempC;
  final double? forecastMinTempC;
  final double? reproductiveTempMaxC;
  final double? reproductiveTempMeanC;
  final double? sowingWindowRainMm;
  final double? forecastRainMm48h;
  final String? growthStage;
  final int? daysAfterSowing;

  // Targeted query parameters
  final List<String>? targetCrops;
  final String? userQuery;
  final String language;

  const FarmContextInput({
    this.farmId,
    this.latitude,
    this.longitude,
    this.taluka,
    this.district = 'Pune',
    this.soilPh,
    this.soilOrganicCarbonPct,
    this.soilTexture,
    this.soilDepthCm,
    this.drainage,
    this.waterTableDepth,
    this.waterTableDepthM,
    this.standingWaterDays,
    this.electricalConductivityDsM,
    this.availableNitrogenKgHa,
    this.totalNitrogenPct,
    this.availablePhosphorusKgHa,
    this.availablePotassiumKgHa,
    this.soilDataProvenance = SoilDataProvenance.unknown,
    this.soilMeasurementDate,
    this.irrigationAvailable,
    this.irrigationSource,
    this.irrigationCapacity,
    this.alternativeSummerIrrigation,
    this.irrigationWaterSalinityTested,
    this.irrigationWaterEcDsM,
    this.treeAgeYears,
    this.targetBahar,
    this.waterScarcityPeriod,
    this.previousCrop,
    this.targetSeason,
    this.targetYear,
    this.proposedSowingDate,
    this.actualRecordedRainMm,
    this.monsoonArrived,
    this.forecastMaxTempC,
    this.forecastMinTempC,
    this.reproductiveTempMaxC,
    this.reproductiveTempMeanC,
    this.sowingWindowRainMm,
    this.forecastRainMm48h,
    this.growthStage,
    this.daysAfterSowing,
    this.targetCrops,
    this.userQuery,
    this.language = 'en',
  });

  factory FarmContextInput.fromJson(Map<String, dynamic> json) {
    return FarmContextInput(
      farmId: json['farm_id'] as String?,
      latitude: (json['latitude'] as num?)?.toDouble(),
      longitude: (json['longitude'] as num?)?.toDouble(),
      taluka: json['taluka'] as String?,
      district: json['district'] as String? ?? 'Pune',
      soilPh: (json['soil_ph'] as num?)?.toDouble(),
      soilOrganicCarbonPct: (json['soil_organic_carbon_pct'] as num?)?.toDouble(),
      soilTexture: json['soil_texture'] as String?,
      soilDepthCm: (json['soil_depth_cm'] as num?)?.toDouble(),
      drainage: json['drainage'] as String?,
      waterTableDepth: json['water_table_depth'] as String?,
      waterTableDepthM: (json['water_table_depth_m'] as num?)?.toDouble(),
      standingWaterDays: json['standing_water_days'] as int?,
      electricalConductivityDsM:
          (json['electrical_conductivity_ds_m'] as num?)?.toDouble(),
      availableNitrogenKgHa:
          (json['available_nitrogen_kg_ha'] as num?)?.toDouble(),
      totalNitrogenPct: (json['total_nitrogen_pct'] as num?)?.toDouble(),
      availablePhosphorusKgHa:
          (json['available_phosphorus_kg_ha'] as num?)?.toDouble(),
      availablePotassiumKgHa:
          (json['available_potassium_kg_ha'] as num?)?.toDouble(),
      soilDataProvenance:
          SoilDataProvenance.fromString(json['soil_data_provenance'] as String?),
      soilMeasurementDate: json['soil_measurement_date'] as String?,
      irrigationAvailable: json['irrigation_available'] as bool?,
      irrigationSource: json['irrigation_source'] as String?,
      irrigationCapacity: json['irrigation_capacity'] as String?,
      alternativeSummerIrrigation:
          json['alternative_summer_irrigation'] as String?,
      irrigationWaterSalinityTested:
          json['irrigation_water_salinity_tested'] as bool?,
      irrigationWaterEcDsM:
          (json['irrigation_water_ec_ds_m'] as num?)?.toDouble(),
      treeAgeYears: json['tree_age_years'] as int?,
      targetBahar: json['target_bahar'] as String?,
      waterScarcityPeriod: json['water_scarcity_period'] as String?,
      previousCrop: json['previous_crop'] as String?,
      targetSeason: json['target_season'] as String?,
      targetYear: json['target_year'] as int?,
      proposedSowingDate: json['proposed_sowing_date'] as String?,
      actualRecordedRainMm:
          (json['actual_recorded_rain_mm'] as num?)?.toDouble(),
      monsoonArrived: json['monsoon_arrived'] as bool?,
      forecastMaxTempC: (json['forecast_max_temp_c'] as num?)?.toDouble(),
      forecastMinTempC: (json['forecast_min_temp_c'] as num?)?.toDouble(),
      reproductiveTempMaxC:
          (json['reproductive_temp_max_c'] as num?)?.toDouble(),
      reproductiveTempMeanC:
          (json['reproductive_temp_mean_c'] as num?)?.toDouble(),
      sowingWindowRainMm:
          (json['sowing_window_rain_mm'] as num?)?.toDouble(),
      forecastRainMm48h:
          (json['forecast_rain_mm_48h'] as num?)?.toDouble(),
      growthStage: json['growth_stage'] as String?,
      daysAfterSowing: json['days_after_sowing'] as int?,
      targetCrops: (json['target_crops'] as List<dynamic>?)
          ?.map((e) => e.toString())
          .toList(),
      userQuery: json['user_query'] as String?,
      language: json['language'] as String? ?? 'en',
    );
  }

  Map<String, dynamic> toJson() {
    final map = <String, dynamic>{
      'district': district,
      'soil_data_provenance': soilDataProvenance.value,
      'language': language,
    };
    if (farmId != null) map['farm_id'] = farmId;
    if (latitude != null) map['latitude'] = latitude;
    if (longitude != null) map['longitude'] = longitude;
    if (taluka != null) map['taluka'] = taluka;
    if (soilPh != null) map['soil_ph'] = soilPh;
    if (soilOrganicCarbonPct != null) {
      map['soil_organic_carbon_pct'] = soilOrganicCarbonPct;
    }
    if (soilTexture != null) map['soil_texture'] = soilTexture;
    if (soilDepthCm != null) map['soil_depth_cm'] = soilDepthCm;
    if (drainage != null) map['drainage'] = drainage;
    if (waterTableDepth != null) map['water_table_depth'] = waterTableDepth;
    if (waterTableDepthM != null) map['water_table_depth_m'] = waterTableDepthM;
    if (standingWaterDays != null) map['standing_water_days'] = standingWaterDays;
    if (electricalConductivityDsM != null) {
      map['electrical_conductivity_ds_m'] = electricalConductivityDsM;
    }
    if (availableNitrogenKgHa != null) {
      map['available_nitrogen_kg_ha'] = availableNitrogenKgHa;
    }
    if (totalNitrogenPct != null) map['total_nitrogen_pct'] = totalNitrogenPct;
    if (availablePhosphorusKgHa != null) {
      map['available_phosphorus_kg_ha'] = availablePhosphorusKgHa;
    }
    if (availablePotassiumKgHa != null) {
      map['available_potassium_kg_ha'] = availablePotassiumKgHa;
    }
    if (soilMeasurementDate != null) {
      map['soil_measurement_date'] = soilMeasurementDate;
    }
    if (irrigationAvailable != null) {
      map['irrigation_available'] = irrigationAvailable;
    }
    if (irrigationSource != null) map['irrigation_source'] = irrigationSource;
    if (irrigationCapacity != null) {
      map['irrigation_capacity'] = irrigationCapacity;
    }
    if (alternativeSummerIrrigation != null) {
      map['alternative_summer_irrigation'] = alternativeSummerIrrigation;
    }
    if (irrigationWaterSalinityTested != null) {
      map['irrigation_water_salinity_tested'] = irrigationWaterSalinityTested;
    }
    if (irrigationWaterEcDsM != null) {
      map['irrigation_water_ec_ds_m'] = irrigationWaterEcDsM;
    }
    if (treeAgeYears != null) map['tree_age_years'] = treeAgeYears;
    if (targetBahar != null) map['target_bahar'] = targetBahar;
    if (waterScarcityPeriod != null) {
      map['water_scarcity_period'] = waterScarcityPeriod;
    }
    if (previousCrop != null) map['previous_crop'] = previousCrop;
    if (targetSeason != null) map['target_season'] = targetSeason;
    if (targetYear != null) map['target_year'] = targetYear;
    if (proposedSowingDate != null) {
      map['proposed_sowing_date'] = proposedSowingDate;
    }
    if (actualRecordedRainMm != null) {
      map['actual_recorded_rain_mm'] = actualRecordedRainMm;
    }
    if (monsoonArrived != null) map['monsoon_arrived'] = monsoonArrived;
    if (forecastMaxTempC != null) map['forecast_max_temp_c'] = forecastMaxTempC;
    if (forecastMinTempC != null) map['forecast_min_temp_c'] = forecastMinTempC;
    if (reproductiveTempMaxC != null) {
      map['reproductive_temp_max_c'] = reproductiveTempMaxC;
    }
    if (reproductiveTempMeanC != null) {
      map['reproductive_temp_mean_c'] = reproductiveTempMeanC;
    }
    if (sowingWindowRainMm != null) {
      map['sowing_window_rain_mm'] = sowingWindowRainMm;
    }
    if (forecastRainMm48h != null) {
      map['forecast_rain_mm_48h'] = forecastRainMm48h;
    }
    if (growthStage != null) map['growth_stage'] = growthStage;
    if (daysAfterSowing != null) map['days_after_sowing'] = daysAfterSowing;
    if (targetCrops != null) map['target_crops'] = targetCrops;
    if (userQuery != null) map['user_query'] = userQuery;
    return map;
  }
}

/// Granular citation metadata for transparency and provenance.
class CitationMetadata {
  final String sourceId;
  final String organization;
  final String publicationTitle;
  final int? publicationYear;
  final String? sectionOrPages;
  final EvidenceTier evidenceTier;

  const CitationMetadata({
    required this.sourceId,
    required this.organization,
    required this.publicationTitle,
    this.publicationYear,
    this.sectionOrPages,
    required this.evidenceTier,
  });

  factory CitationMetadata.fromJson(Map<String, dynamic> json) {
    return CitationMetadata(
      sourceId: json['source_id'] as String,
      organization: json['organization'] as String,
      publicationTitle: json['publication_title'] as String,
      publicationYear: json['publication_year'] as int?,
      sectionOrPages: json['section_or_pages'] as String?,
      evidenceTier: EvidenceTier.fromString(json['evidence_tier'] as String?),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'source_id': sourceId,
      'organization': organization,
      'publication_title': publicationTitle,
      if (publicationYear != null) 'publication_year': publicationYear,
      if (sectionOrPages != null) 'section_or_pages': sectionOrPages,
      'evidence_tier': evidenceTier.value,
    };
  }
}

/// Record of an individual deterministic rule evaluated for a candidate crop.
class AppliedRuleRecord {
  final String ruleId;
  final String domain;
  final String parameterChecked;
  final String ruleStatement;
  final bool conditionMet;
  final EvidenceTier evidenceTier;
  final CitationMetadata? citation;
  final String claimVerificationStatus;
  final String? sourceId;
  final String? documentTitle;
  final String? sectionOrPages;
  final String? supportingStatement;
  final String? applicabilityConditions;
  final EnforcementLevel enforcementLevel;
  final bool canTriggerDisqualification;

  const AppliedRuleRecord({
    required this.ruleId,
    required this.domain,
    required this.parameterChecked,
    required this.ruleStatement,
    required this.conditionMet,
    required this.evidenceTier,
    this.citation,
    this.claimVerificationStatus = 'VERIFIED',
    this.sourceId,
    this.documentTitle,
    this.sectionOrPages,
    this.supportingStatement,
    this.applicabilityConditions,
    this.enforcementLevel = EnforcementLevel.advisoryOnly,
    this.canTriggerDisqualification = false,
  });

  factory AppliedRuleRecord.fromJson(Map<String, dynamic> json) {
    return AppliedRuleRecord(
      ruleId: json['rule_id'] as String,
      domain: json['domain'] as String,
      parameterChecked: json['parameter_checked'] as String,
      ruleStatement: json['rule_statement'] as String,
      conditionMet: json['condition_met'] as bool,
      evidenceTier: EvidenceTier.fromString(json['evidence_tier'] as String?),
      citation: json['citation'] != null
          ? CitationMetadata.fromJson(json['citation'] as Map<String, dynamic>)
          : null,
      claimVerificationStatus:
          json['claim_verification_status'] as String? ?? 'VERIFIED',
      sourceId: json['source_id'] as String?,
      documentTitle: json['document_title'] as String?,
      sectionOrPages: json['section_or_pages'] as String?,
      supportingStatement: json['supporting_statement'] as String?,
      applicabilityConditions: json['applicability_conditions'] as String?,
      enforcementLevel:
          EnforcementLevel.fromString(json['enforcement_level'] as String?),
      canTriggerDisqualification:
          json['can_trigger_disqualification'] as bool? ?? false,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'rule_id': ruleId,
      'domain': domain,
      'parameter_checked': parameterChecked,
      'rule_statement': ruleStatement,
      'condition_met': conditionMet,
      'evidence_tier': evidenceTier.value,
      if (citation != null) 'citation': citation!.toJson(),
      'claim_verification_status': claimVerificationStatus,
      if (sourceId != null) 'source_id': sourceId,
      if (documentTitle != null) 'document_title': documentTitle,
      if (sectionOrPages != null) 'section_or_pages': sectionOrPages,
      if (supportingStatement != null)
        'supporting_statement': supportingStatement,
      if (applicabilityConditions != null)
        'applicability_conditions': applicabilityConditions,
      'enforcement_level': enforcementLevel.value,
      'can_trigger_disqualification': canTriggerDisqualification,
    };
  }
}

/// Detailed deterministic evaluation outcome for a single candidate crop.
class CropEvaluationOutcome {
  final String cropId;
  final String commonName;
  final String scientificName;
  final String? marathiName;
  final DecisionState decisionState;
  final bool isDisqualified;
  final List<String> limitingFactors;
  final List<String> reproductiveRiskWarnings;
  final Map<String, dynamic>? irrigationGuidance;
  final Map<String, dynamic>? pomegranateDailyWater;
  final List<String> missingInformation;
  final List<String> uncertaintyNotes;
  final List<AppliedRuleRecord> appliedRules;
  final List<CitationMetadata> citations;
  final String explanation;

  const CropEvaluationOutcome({
    required this.cropId,
    required this.commonName,
    required this.scientificName,
    this.marathiName,
    required this.decisionState,
    this.isDisqualified = false,
    this.limitingFactors = const [],
    this.reproductiveRiskWarnings = const [],
    this.irrigationGuidance,
    this.pomegranateDailyWater,
    this.missingInformation = const [],
    this.uncertaintyNotes = const [],
    this.appliedRules = const [],
    this.citations = const [],
    required this.explanation,
  });

  factory CropEvaluationOutcome.fromJson(Map<String, dynamic> json) {
    return CropEvaluationOutcome(
      cropId: json['crop_id'] as String,
      commonName: json['common_name'] as String,
      scientificName: json['scientific_name'] as String,
      marathiName: json['marathi_name'] as String?,
      decisionState: DecisionState.fromString(json['decision_state'] as String?),
      isDisqualified: json['is_disqualified'] as bool? ?? false,
      limitingFactors: (json['limiting_factors'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          [],
      reproductiveRiskWarnings:
          (json['reproductive_risk_warnings'] as List<dynamic>?)
                  ?.map((e) => e.toString())
                  .toList() ??
              [],
      irrigationGuidance: json['irrigation_guidance'] as Map<String, dynamic>?,
      pomegranateDailyWater:
          json['pomegranate_daily_water'] as Map<String, dynamic>?,
      missingInformation: (json['missing_information'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          [],
      uncertaintyNotes: (json['uncertainty_notes'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          [],
      appliedRules: (json['applied_rules'] as List<dynamic>?)
              ?.map((e) => AppliedRuleRecord.fromJson(e as Map<String, dynamic>))
              .toList() ??
          [],
      citations: (json['citations'] as List<dynamic>?)
              ?.map((e) => CitationMetadata.fromJson(e as Map<String, dynamic>))
              .toList() ??
          [],
      explanation: json['explanation'] as String? ?? '',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'crop_id': cropId,
      'common_name': commonName,
      'scientific_name': scientificName,
      if (marathiName != null) 'marathi_name': marathiName,
      'decision_state': decisionState.value,
      'is_disqualified': isDisqualified,
      'limiting_factors': limitingFactors,
      'reproductive_risk_warnings': reproductiveRiskWarnings,
      if (irrigationGuidance != null)
        'irrigation_guidance': irrigationGuidance,
      if (pomegranateDailyWater != null)
        'pomegranate_daily_water': pomegranateDailyWater,
      'missing_information': missingInformation,
      'uncertainty_notes': uncertaintyNotes,
      'applied_rules': appliedRules.map((r) => r.toJson()).toList(),
      'citations': citations.map((c) => c.toJson()).toList(),
      'explanation': explanation,
    };
  }
}

/// Diagnostic follow-up question selected to resolve decision uncertainty.
class FollowUpQuestion {
  final String questionId;
  final String targetParameter;
  final int priority;
  final String questionTextEn;
  final String questionTextMr;
  final String questionType;
  final List<String>? options;
  final String agronomicRationale;

  const FollowUpQuestion({
    required this.questionId,
    required this.targetParameter,
    required this.priority,
    required this.questionTextEn,
    required this.questionTextMr,
    required this.questionType,
    this.options,
    required this.agronomicRationale,
  });

  factory FollowUpQuestion.fromJson(Map<String, dynamic> json) {
    return FollowUpQuestion(
      questionId: json['question_id'] as String,
      targetParameter: json['target_parameter'] as String,
      priority: json['priority'] as int,
      questionTextEn: json['question_text_en'] as String,
      questionTextMr: json['question_text_mr'] as String,
      questionType: json['question_type'] as String,
      options: (json['options'] as List<dynamic>?)
          ?.map((e) => e.toString())
          .toList(),
      agronomicRationale: json['agronomic_rationale'] as String,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'question_id': questionId,
      'target_parameter': targetParameter,
      'priority': priority,
      'question_text_en': questionTextEn,
      'question_text_mr': questionTextMr,
      'question_type': questionType,
      if (options != null) 'options': options,
      'agronomic_rationale': agronomicRationale,
    };
  }
}

/// Full response payload for deterministic agricultural farm evaluation.
class FarmEvaluationResponse {
  final String decisionId;
  final DateTime evaluatedAt;
  final String inputValidationStatus;
  final List<String> contradictionsDetected;
  final List<String> missingParametersFlagged;
  final String? talukaResolved;
  final String? targetSeason;
  final String language;
  final FarmContextInput? farmContext;
  final List<CropEvaluationOutcome> cropOutcomes;
  final List<FollowUpQuestion> followUpQuestions;
  final String governanceNotice;

  const FarmEvaluationResponse({
    required this.decisionId,
    required this.evaluatedAt,
    required this.inputValidationStatus,
    this.contradictionsDetected = const [],
    this.missingParametersFlagged = const [],
    this.talukaResolved,
    this.targetSeason,
    this.language = 'en',
    this.farmContext,
    this.cropOutcomes = const [],
    this.followUpQuestions = const [],
    this.governanceNotice =
        'CropNet AI evaluates biological and environmental feasibility.',
  });

  factory FarmEvaluationResponse.fromJson(Map<String, dynamic> json) {
    return FarmEvaluationResponse(
      decisionId: json['decision_id'] as String,
      evaluatedAt: DateTime.parse(json['evaluated_at'] as String),
      inputValidationStatus: json['input_validation_status'] as String,
      contradictionsDetected: (json['contradictions_detected'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          [],
      missingParametersFlagged:
          (json['missing_parameters_flagged'] as List<dynamic>?)
                  ?.map((e) => e.toString())
                  .toList() ??
              [],
      talukaResolved: json['taluka_resolved'] as String?,
      targetSeason: json['target_season'] as String?,
      language: json['language'] as String? ?? 'en',
      farmContext: json['farm_context'] != null
          ? FarmContextInput.fromJson(json['farm_context'] as Map<String, dynamic>)
          : null,
      cropOutcomes: (json['crop_outcomes'] as List<dynamic>?)
              ?.map((e) => CropEvaluationOutcome.fromJson(e as Map<String, dynamic>))
              .toList() ??
          [],
      followUpQuestions: (json['follow_up_questions'] as List<dynamic>?)
              ?.map((e) => FollowUpQuestion.fromJson(e as Map<String, dynamic>))
              .toList() ??
          [],
      governanceNotice: json['governance_notice'] as String? ?? '',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'decision_id': decisionId,
      'evaluated_at': evaluatedAt.toIso8601String(),
      'input_validation_status': inputValidationStatus,
      'contradictions_detected': contradictionsDetected,
      'missing_parameters_flagged': missingParametersFlagged,
      if (talukaResolved != null) 'taluka_resolved': talukaResolved,
      if (targetSeason != null) 'target_season': targetSeason,
      'language': language,
      if (farmContext != null) 'farm_context': farmContext!.toJson(),
      'crop_outcomes': cropOutcomes.map((c) => c.toJson()).toList(),
      'follow_up_questions': followUpQuestions.map((f) => f.toJson()).toList(),
      'governance_notice': governanceNotice,
    };
  }
}

/// Individual message in a bounded conversational dialogue.
class ConversationMessage {
  final String role;
  final String content;
  final DateTime? timestamp;

  const ConversationMessage({
    required this.role,
    required this.content,
    this.timestamp,
  });

  factory ConversationMessage.fromJson(Map<String, dynamic> json) {
    return ConversationMessage(
      role: json['role'] as String,
      content: json['content'] as String,
      timestamp: json['timestamp'] != null
          ? DateTime.parse(json['timestamp'] as String)
          : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'role': role,
      'content': content,
      if (timestamp != null) 'timestamp': timestamp!.toIso8601String(),
    };
  }
}

/// Request to explain a validated agricultural decision.
class ExplainDecisionRequest {
  final String decisionId;
  final String language;
  final String? focusCrop;

  const ExplainDecisionRequest({
    required this.decisionId,
    this.language = 'en',
    this.focusCrop,
  });

  Map<String, dynamic> toJson() {
    return {
      'decision_id': decisionId,
      'language': language,
      if (focusCrop != null) 'focus_crop': focusCrop,
    };
  }
}

/// Request for interactive dialogue grounded in a validated decision.
class ConversationRequest {
  final String decisionId;
  final String message;
  final String language;
  final List<ConversationMessage> history;
  final Map<String, dynamic>? submittedAnswers;

  const ConversationRequest({
    required this.decisionId,
    required this.message,
    this.language = 'en',
    this.history = const [],
    this.submittedAnswers,
  });

  Map<String, dynamic> toJson() {
    return {
      'decision_id': decisionId,
      'message': message,
      'language': language,
      'history': history.map((h) => h.toJson()).toList(),
      if (submittedAnswers != null) 'submitted_answers': submittedAnswers,
    };
  }
}

/// Natural language explanation response with strictly bound factual metadata.
class AgriculturalExplanationResponse {
  final String decisionId;
  final String language;
  final String explanationText;
  final String generationSource;
  final bool validationPassed;
  final List<String> validationWarnings;
  final Map<String, String> decisionStateSummary;
  final List<CitationMetadata> authoritativeCitations;
  final List<FollowUpQuestion> followUpQuestions;
  final String governanceNotice;

  const AgriculturalExplanationResponse({
    required this.decisionId,
    required this.language,
    required this.explanationText,
    required this.generationSource,
    required this.validationPassed,
    this.validationWarnings = const [],
    this.decisionStateSummary = const {},
    this.authoritativeCitations = const [],
    this.followUpQuestions = const [],
    this.governanceNotice =
        'CropNet AI explanations are strictly derived from validated deterministic agronomic decisions.',
  });

  factory AgriculturalExplanationResponse.fromJson(Map<String, dynamic> json) {
    final summary = <String, String>{};
    if (json['decision_state_summary'] is Map) {
      final map = json['decision_state_summary'] as Map<String, dynamic>;
      for (final e in map.entries) {
        summary[e.key] = e.value.toString();
      }
    }

    return AgriculturalExplanationResponse(
      decisionId: json['decision_id'] as String,
      language: json['language'] as String,
      explanationText: json['explanation_text'] as String,
      generationSource: json['generation_source'] as String,
      validationPassed: json['validation_passed'] as bool,
      validationWarnings: (json['validation_warnings'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          [],
      decisionStateSummary: summary,
      authoritativeCitations: (json['authoritative_citations'] as List<dynamic>?)
              ?.map((e) => CitationMetadata.fromJson(e as Map<String, dynamic>))
              .toList() ??
          [],
      followUpQuestions: (json['follow_up_questions'] as List<dynamic>?)
              ?.map((e) => FollowUpQuestion.fromJson(e as Map<String, dynamic>))
              .toList() ??
          [],
      governanceNotice: json['governance_notice'] as String? ?? '',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'decision_id': decisionId,
      'language': language,
      'explanation_text': explanationText,
      'generation_source': generationSource,
      'validation_passed': validationPassed,
      'validation_warnings': validationWarnings,
      'decision_state_summary': decisionStateSummary,
      'authoritative_citations':
          authoritativeCitations.map((c) => c.toJson()).toList(),
      'follow_up_questions': followUpQuestions.map((f) => f.toJson()).toList(),
      'governance_notice': governanceNotice,
    };
  }
}
