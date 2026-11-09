/// CropNet AI — Crop Knowledge Base Models
///
/// Matches FastAPI schemas in `services/api/app/schemas/crop.py`.
library;

class AgriculturalKnowledgeSource {
  final String id;
  final String organization;
  final String publicationTitle;
  final int? publicationYear;
  final String? documentUrlOrRef;
  final String? sectionOrPages;
  final String evidenceQuality;
  final DateTime lastVerifiedDate;

  const AgriculturalKnowledgeSource({
    required this.id,
    required this.organization,
    required this.publicationTitle,
    this.publicationYear,
    this.documentUrlOrRef,
    this.sectionOrPages,
    required this.evidenceQuality,
    required this.lastVerifiedDate,
  });

  factory AgriculturalKnowledgeSource.fromJson(Map<String, dynamic> json) {
    return AgriculturalKnowledgeSource(
      id: json['id'] as String,
      organization: json['organization'] as String,
      publicationTitle: json['publication_title'] as String,
      publicationYear: json['publication_year'] as int?,
      documentUrlOrRef: json['document_url_or_ref'] as String?,
      sectionOrPages: json['section_or_pages'] as String?,
      evidenceQuality: json['evidence_quality'] as String,
      lastVerifiedDate: DateTime.parse(json['last_verified_date'] as String),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'organization': organization,
      'publication_title': publicationTitle,
      if (publicationYear != null) 'publication_year': publicationYear,
      if (documentUrlOrRef != null) 'document_url_or_ref': documentUrlOrRef,
      if (sectionOrPages != null) 'section_or_pages': sectionOrPages,
      'evidence_quality': evidenceQuality,
      'last_verified_date': lastVerifiedDate.toIso8601String(),
    };
  }
}

class CropSoilRequirements {
  final List<String> preferredTextures;
  final List<String> acceptableTextures;
  final double? phOptimumMin;
  final double? phOptimumMax;
  final double? phBestSuitedMin;
  final double? phBestSuitedMax;
  final double? phTolerableMin;
  final double? phTolerableMax;
  final String? phContextNotes;
  final List<String>? bestSuitedSoilTextures;
  final String drainageRequirement;
  final String salinitySensitivity;
  final double minSoilDepthCm;
  final double? optimumOrganicCarbonGKg;
  final String? waterHoldingCapacityPref;
  final String? evidenceStatus;
  final List<String>? unverifiedParameters;
  final String? sourceId;

  const CropSoilRequirements({
    required this.preferredTextures,
    required this.acceptableTextures,
    this.phOptimumMin,
    this.phOptimumMax,
    this.phBestSuitedMin,
    this.phBestSuitedMax,
    this.phTolerableMin,
    this.phTolerableMax,
    this.phContextNotes,
    this.bestSuitedSoilTextures,
    required this.drainageRequirement,
    required this.salinitySensitivity,
    required this.minSoilDepthCm,
    this.optimumOrganicCarbonGKg,
    this.waterHoldingCapacityPref,
    this.evidenceStatus = 'derived',
    this.unverifiedParameters,
    this.sourceId,
  });

  factory CropSoilRequirements.fromJson(Map<String, dynamic> json) {
    return CropSoilRequirements(
      preferredTextures: (json['preferred_textures'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          [],
      acceptableTextures: (json['acceptable_textures'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          [],
      phOptimumMin: (json['ph_optimum_min'] as num?)?.toDouble(),
      phOptimumMax: (json['ph_optimum_max'] as num?)?.toDouble(),
      phBestSuitedMin: (json['ph_best_suited_min'] as num?)?.toDouble(),
      phBestSuitedMax: (json['ph_best_suited_max'] as num?)?.toDouble(),
      phTolerableMin: (json['ph_tolerable_min'] as num?)?.toDouble(),
      phTolerableMax: (json['ph_tolerable_max'] as num?)?.toDouble(),
      phContextNotes: json['ph_context_notes'] as String?,
      bestSuitedSoilTextures: (json['best_suited_soil_textures'] as List<dynamic>?)
          ?.map((e) => e.toString())
          .toList(),
      drainageRequirement: json['drainage_requirement'] as String? ?? 'well-drained',
      salinitySensitivity: json['salinity_sensitivity'] as String? ?? 'sensitive',
      minSoilDepthCm: (json['min_soil_depth_cm'] as num?)?.toDouble() ?? 30.0,
      optimumOrganicCarbonGKg: (json['optimum_organic_carbon_g_kg'] as num?)?.toDouble(),
      waterHoldingCapacityPref: json['water_holding_capacity_pref'] as String?,
      evidenceStatus: json['evidence_status'] as String? ?? 'derived',
      unverifiedParameters: (json['unverified_parameters'] as List<dynamic>?)
          ?.map((e) => e.toString())
          .toList(),
      sourceId: json['source_id'] as String?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'preferred_textures': preferredTextures,
      'acceptable_textures': acceptableTextures,
      if (phOptimumMin != null) 'ph_optimum_min': phOptimumMin,
      if (phOptimumMax != null) 'ph_optimum_max': phOptimumMax,
      if (phBestSuitedMin != null) 'ph_best_suited_min': phBestSuitedMin,
      if (phBestSuitedMax != null) 'ph_best_suited_max': phBestSuitedMax,
      if (phTolerableMin != null) 'ph_tolerable_min': phTolerableMin,
      if (phTolerableMax != null) 'ph_tolerable_max': phTolerableMax,
      if (phContextNotes != null) 'ph_context_notes': phContextNotes,
      if (bestSuitedSoilTextures != null) 'best_suited_soil_textures': bestSuitedSoilTextures,
      'drainage_requirement': drainageRequirement,
      'salinity_sensitivity': salinitySensitivity,
      'min_soil_depth_cm': minSoilDepthCm,
      if (optimumOrganicCarbonGKg != null)
        'optimum_organic_carbon_g_kg': optimumOrganicCarbonGKg,
      if (waterHoldingCapacityPref != null)
        'water_holding_capacity_pref': waterHoldingCapacityPref,
      if (evidenceStatus != null) 'evidence_status': evidenceStatus,
      if (unverifiedParameters != null)
        'unverified_parameters': unverifiedParameters,
      if (sourceId != null) 'source_id': sourceId,
    };
  }
}

class CropClimateRequirements {
  final double tempOptimumMinC;
  final double tempOptimumMaxC;
  final double? tempTolerableMinC;
  final double? tempTolerableMaxC;
  final double? tempReproductiveMaxC;
  final double? tempReproductiveMinMeanC;
  final double? annualRainfallMinMm;
  final double? annualRainfallMaxMm;
  final String? humidityPreference;
  final String frostSensitivity;
  final String heatSensitivity;
  final String? thermalThresholdContext;
  final String? solarRadiationRequirement;
  final String? evidenceStatus;
  final String? sourceId;

  const CropClimateRequirements({
    required this.tempOptimumMinC,
    required this.tempOptimumMaxC,
    this.tempTolerableMinC,
    this.tempTolerableMaxC,
    this.tempReproductiveMaxC,
    this.tempReproductiveMinMeanC,
    this.annualRainfallMinMm,
    this.annualRainfallMaxMm,
    this.humidityPreference,
    required this.frostSensitivity,
    required this.heatSensitivity,
    this.thermalThresholdContext,
    this.solarRadiationRequirement,
    this.evidenceStatus = 'derived',
    this.sourceId,
  });

  factory CropClimateRequirements.fromJson(Map<String, dynamic> json) {
    return CropClimateRequirements(
      tempOptimumMinC: (json['temp_optimum_min_c'] as num).toDouble(),
      tempOptimumMaxC: (json['temp_optimum_max_c'] as num).toDouble(),
      tempTolerableMinC: (json['temp_tolerable_min_c'] as num?)?.toDouble(),
      tempTolerableMaxC: (json['temp_tolerable_max_c'] as num?)?.toDouble(),
      tempReproductiveMaxC: (json['temp_reproductive_max_c'] as num?)?.toDouble(),
      tempReproductiveMinMeanC: (json['temp_reproductive_min_mean_c'] as num?)?.toDouble(),
      annualRainfallMinMm: (json['annual_rainfall_min_mm'] as num?)?.toDouble(),
      annualRainfallMaxMm: (json['annual_rainfall_max_mm'] as num?)?.toDouble(),
      humidityPreference: json['humidity_preference'] as String?,
      frostSensitivity: json['frost_sensitivity'] as String? ?? 'sensitive',
      heatSensitivity: json['heat_sensitivity'] as String? ?? 'moderate',
      thermalThresholdContext: json['thermal_threshold_context'] as String?,
      solarRadiationRequirement: json['solar_radiation_requirement'] as String?,
      evidenceStatus: json['evidence_status'] as String? ?? 'derived',
      sourceId: json['source_id'] as String?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'temp_optimum_min_c': tempOptimumMinC,
      'temp_optimum_max_c': tempOptimumMaxC,
      if (tempTolerableMinC != null) 'temp_tolerable_min_c': tempTolerableMinC,
      if (tempTolerableMaxC != null) 'temp_tolerable_max_c': tempTolerableMaxC,
      if (tempReproductiveMaxC != null)
        'temp_reproductive_max_c': tempReproductiveMaxC,
      if (tempReproductiveMinMeanC != null)
        'temp_reproductive_min_mean_c': tempReproductiveMinMeanC,
      if (annualRainfallMinMm != null)
        'annual_rainfall_min_mm': annualRainfallMinMm,
      if (annualRainfallMaxMm != null)
        'annual_rainfall_max_mm': annualRainfallMaxMm,
      if (humidityPreference != null)
        'humidity_preference': humidityPreference,
      'frost_sensitivity': frostSensitivity,
      'heat_sensitivity': heatSensitivity,
      if (thermalThresholdContext != null)
        'thermal_threshold_context': thermalThresholdContext,
      if (solarRadiationRequirement != null)
        'solar_radiation_requirement': solarRadiationRequirement,
      if (evidenceStatus != null) 'evidence_status': evidenceStatus,
      if (sourceId != null) 'source_id': sourceId,
    };
  }
}

class CropSeasonRequirement {
  final String seasonName;
  final bool isPrimarySeason;
  final String plantingWindowMaharashtra;
  final String harvestingWindowMaharashtra;
  final int durationDaysMin;
  final int durationDaysMax;
  final Map<String, String>? plantingCalendarByRegion;
  final String? sourceId;

  const CropSeasonRequirement({
    required this.seasonName,
    required this.isPrimarySeason,
    required this.plantingWindowMaharashtra,
    required this.harvestingWindowMaharashtra,
    required this.durationDaysMin,
    required this.durationDaysMax,
    this.plantingCalendarByRegion,
    this.sourceId,
  });

  factory CropSeasonRequirement.fromJson(Map<String, dynamic> json) {
    Map<String, String>? regionCalendar;
    if (json['planting_calendar_by_region'] is Map) {
      regionCalendar = (json['planting_calendar_by_region'] as Map<String, dynamic>)
          .map((k, v) => MapEntry(k, v.toString()));
    }

    return CropSeasonRequirement(
      seasonName: json['season_name'] as String,
      isPrimarySeason: json['is_primary_season'] as bool? ?? false,
      plantingWindowMaharashtra: json['planting_window_maharashtra'] as String,
      harvestingWindowMaharashtra: json['harvesting_window_maharashtra'] as String,
      durationDaysMin: json['duration_days_min'] as int,
      durationDaysMax: json['duration_days_max'] as int,
      plantingCalendarByRegion: regionCalendar,
      sourceId: json['source_id'] as String?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'season_name': seasonName,
      'is_primary_season': isPrimarySeason,
      'planting_window_maharashtra': plantingWindowMaharashtra,
      'harvesting_window_maharashtra': harvestingWindowMaharashtra,
      'duration_days_min': durationDaysMin,
      'duration_days_max': durationDaysMax,
      if (plantingCalendarByRegion != null)
        'planting_calendar_by_region': plantingCalendarByRegion,
      if (sourceId != null) 'source_id': sourceId,
    };
  }
}

class CropWaterRequirements {
  final double? annualWaterRequirementMmMin;
  final double? annualWaterRequirementMmMax;
  final bool rainfedSuitable;
  final String irrigationDependency;
  final List<String> criticalGrowthStages;
  final Map<String, dynamic>? dailyWaterTable;
  final List<Map<String, dynamic>>? irrigationStagesDetail;
  final String? evidenceStatus;
  final String waterloggingSensitivity;
  final String droughtSensitivity;
  final String? sourceId;

  const CropWaterRequirements({
    this.annualWaterRequirementMmMin,
    this.annualWaterRequirementMmMax,
    required this.rainfedSuitable,
    required this.irrigationDependency,
    required this.criticalGrowthStages,
    this.dailyWaterTable,
    this.irrigationStagesDetail,
    this.evidenceStatus = 'derived',
    required this.waterloggingSensitivity,
    required this.droughtSensitivity,
    this.sourceId,
  });

  factory CropWaterRequirements.fromJson(Map<String, dynamic> json) {
    return CropWaterRequirements(
      annualWaterRequirementMmMin: (json['annual_water_requirement_mm_min'] as num?)?.toDouble(),
      annualWaterRequirementMmMax: (json['annual_water_requirement_mm_max'] as num?)?.toDouble(),
      rainfedSuitable: json['rainfed_suitable'] as bool? ?? false,
      irrigationDependency: json['irrigation_dependency'] as String? ?? 'moderate',
      criticalGrowthStages: (json['critical_growth_stages'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          [],
      dailyWaterTable: json['daily_water_table'] as Map<String, dynamic>?,
      irrigationStagesDetail: (json['irrigation_stages_detail'] as List<dynamic>?)
          ?.map((e) => e as Map<String, dynamic>)
          .toList(),
      evidenceStatus: json['evidence_status'] as String? ?? 'derived',
      waterloggingSensitivity: json['waterlogging_sensitivity'] as String? ?? 'moderate',
      droughtSensitivity: json['drought_sensitivity'] as String? ?? 'moderate',
      sourceId: json['source_id'] as String?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      if (annualWaterRequirementMmMin != null)
        'annual_water_requirement_mm_min': annualWaterRequirementMmMin,
      if (annualWaterRequirementMmMax != null)
        'annual_water_requirement_mm_max': annualWaterRequirementMmMax,
      'rainfed_suitable': rainfedSuitable,
      'irrigation_dependency': irrigationDependency,
      'critical_growth_stages': criticalGrowthStages,
      if (dailyWaterTable != null) 'daily_water_table': dailyWaterTable,
      if (irrigationStagesDetail != null)
        'irrigation_stages_detail': irrigationStagesDetail,
      if (evidenceStatus != null) 'evidence_status': evidenceStatus,
      'waterlogging_sensitivity': waterloggingSensitivity,
      'drought_sensitivity': droughtSensitivity,
      if (sourceId != null) 'source_id': sourceId,
    };
  }
}

class CropRegionalSuitability {
  final String taluka;
  final String district;
  final String suitabilityStatus;
  final String agronomicRationale;
  final List<String>? limitingFactors;
  final String? evidenceStatus;
  final String? sourceId;

  const CropRegionalSuitability({
    required this.taluka,
    required this.district,
    required this.suitabilityStatus,
    required this.agronomicRationale,
    this.limitingFactors,
    this.evidenceStatus = 'regional_screening',
    this.sourceId,
  });

  factory CropRegionalSuitability.fromJson(Map<String, dynamic> json) {
    return CropRegionalSuitability(
      taluka: json['taluka'] as String,
      district: json['district'] as String? ?? 'Pune',
      suitabilityStatus: json['suitability_status'] as String,
      agronomicRationale: json['agronomic_rationale'] as String,
      limitingFactors: (json['limiting_factors'] as List<dynamic>?)
          ?.map((e) => e.toString())
          .toList(),
      evidenceStatus: json['evidence_status'] as String? ?? 'regional_screening',
      sourceId: json['source_id'] as String?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'taluka': taluka,
      'district': district,
      'suitability_status': suitabilityStatus,
      'agronomic_rationale': agronomicRationale,
      if (limitingFactors != null) 'limiting_factors': limitingFactors,
      if (evidenceStatus != null) 'evidence_status': evidenceStatus,
      if (sourceId != null) 'source_id': sourceId,
    };
  }
}

class CropCatalogSummary {
  final String id;
  final String commonName;
  final String scientificName;
  final String? marathiName;
  final String? hindiName;
  final String category;
  final String cropType;
  final int? typicalDurationDaysMin;
  final int? typicalDurationDaysMax;
  final List<String>? recommendedVarieties;
  final String? primarySourceOrg;
  final bool degradedMode;
  final String dataSourceMode;

  const CropCatalogSummary({
    required this.id,
    required this.commonName,
    required this.scientificName,
    this.marathiName,
    this.hindiName,
    required this.category,
    required this.cropType,
    this.typicalDurationDaysMin,
    this.typicalDurationDaysMax,
    this.recommendedVarieties,
    this.primarySourceOrg,
    this.degradedMode = false,
    this.dataSourceMode = 'database',
  });

  factory CropCatalogSummary.fromJson(Map<String, dynamic> json) {
    return CropCatalogSummary(
      id: json['id'] as String,
      commonName: json['common_name'] as String,
      scientificName: json['scientific_name'] as String,
      marathiName: json['marathi_name'] as String?,
      hindiName: json['hindi_name'] as String?,
      category: json['category'] as String,
      cropType: json['crop_type'] as String,
      typicalDurationDaysMin: json['typical_duration_days_min'] as int?,
      typicalDurationDaysMax: json['typical_duration_days_max'] as int?,
      recommendedVarieties: (json['recommended_varieties'] as List<dynamic>?)
          ?.map((e) => e.toString())
          .toList(),
      primarySourceOrg: json['primary_source_org'] as String?,
      degradedMode: json['degraded_mode'] as bool? ?? false,
      dataSourceMode: json['data_source_mode'] as String? ?? 'database',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'common_name': commonName,
      'scientific_name': scientificName,
      if (marathiName != null) 'marathi_name': marathiName,
      if (hindiName != null) 'hindi_name': hindiName,
      'category': category,
      'crop_type': cropType,
      if (typicalDurationDaysMin != null)
        'typical_duration_days_min': typicalDurationDaysMin,
      if (typicalDurationDaysMax != null)
        'typical_duration_days_max': typicalDurationDaysMax,
      if (recommendedVarieties != null)
        'recommended_varieties': recommendedVarieties,
      if (primarySourceOrg != null) 'primary_source_org': primarySourceOrg,
      'degraded_mode': degradedMode,
      'data_source_mode': dataSourceMode,
    };
  }
}

class CropFullProfile {
  final String id;
  final String commonName;
  final String scientificName;
  final String? marathiName;
  final String? hindiName;
  final String category;
  final String cropType;
  final int? typicalDurationDaysMin;
  final int? typicalDurationDaysMax;
  final List<String> recommendedVarieties;
  final CropSoilRequirements? soil;
  final CropClimateRequirements? climate;
  final List<CropSeasonRequirement> seasons;
  final CropWaterRequirements? water;
  final List<CropRegionalSuitability> regionalSuitability;
  final List<AgriculturalKnowledgeSource> sources;
  final bool degradedMode;
  final String dataSourceMode;
  final String? degradedWarning;

  const CropFullProfile({
    required this.id,
    required this.commonName,
    required this.scientificName,
    this.marathiName,
    this.hindiName,
    required this.category,
    required this.cropType,
    this.typicalDurationDaysMin,
    this.typicalDurationDaysMax,
    this.recommendedVarieties = const [],
    this.soil,
    this.climate,
    this.seasons = const [],
    this.water,
    this.regionalSuitability = const [],
    this.sources = const [],
    this.degradedMode = false,
    this.dataSourceMode = 'database',
    this.degradedWarning,
  });

  factory CropFullProfile.fromJson(Map<String, dynamic> json) {
    return CropFullProfile(
      id: json['id'] as String,
      commonName: json['common_name'] as String,
      scientificName: json['scientific_name'] as String,
      marathiName: json['marathi_name'] as String?,
      hindiName: json['hindi_name'] as String?,
      category: json['category'] as String,
      cropType: json['crop_type'] as String,
      typicalDurationDaysMin: json['typical_duration_days_min'] as int?,
      typicalDurationDaysMax: json['typical_duration_days_max'] as int?,
      recommendedVarieties: (json['recommended_varieties'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          [],
      soil: json['soil'] != null
          ? CropSoilRequirements.fromJson(json['soil'] as Map<String, dynamic>)
          : null,
      climate: json['climate'] != null
          ? CropClimateRequirements.fromJson(json['climate'] as Map<String, dynamic>)
          : null,
      seasons: (json['seasons'] as List<dynamic>?)
              ?.map((e) => CropSeasonRequirement.fromJson(e as Map<String, dynamic>))
              .toList() ??
          [],
      water: json['water'] != null
          ? CropWaterRequirements.fromJson(json['water'] as Map<String, dynamic>)
          : null,
      regionalSuitability: (json['regional_suitability'] as List<dynamic>?)
              ?.map((e) => CropRegionalSuitability.fromJson(e as Map<String, dynamic>))
              .toList() ??
          [],
      sources: (json['sources'] as List<dynamic>?)
              ?.map((e) =>
                  AgriculturalKnowledgeSource.fromJson(e as Map<String, dynamic>))
              .toList() ??
          [],
      degradedMode: json['degraded_mode'] as bool? ?? false,
      dataSourceMode: json['data_source_mode'] as String? ?? 'database',
      degradedWarning: json['degraded_warning'] as String?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'common_name': commonName,
      'scientific_name': scientificName,
      if (marathiName != null) 'marathi_name': marathiName,
      if (hindiName != null) 'hindi_name': hindiName,
      'category': category,
      'crop_type': cropType,
      if (typicalDurationDaysMin != null)
        'typical_duration_days_min': typicalDurationDaysMin,
      if (typicalDurationDaysMax != null)
        'typical_duration_days_max': typicalDurationDaysMax,
      'recommended_varieties': recommendedVarieties,
      if (soil != null) 'soil': soil!.toJson(),
      if (climate != null) 'climate': climate!.toJson(),
      'seasons': seasons.map((s) => s.toJson()).toList(),
      if (water != null) 'water': water!.toJson(),
      'regional_suitability': regionalSuitability.map((r) => r.toJson()).toList(),
      'sources': sources.map((s) => s.toJson()).toList(),
      'degraded_mode': degradedMode,
      'data_source_mode': dataSourceMode,
      if (degradedWarning != null) 'degraded_warning': degradedWarning,
    };
  }
}

class MaharashtraSeasonCalendar {
  final String seasonName;
  final String marathiName;
  final String periodMonths;
  final List<String> primaryCrops;
  final String rainfallDependency;
  final String description;

  const MaharashtraSeasonCalendar({
    required this.seasonName,
    required this.marathiName,
    required this.periodMonths,
    required this.primaryCrops,
    required this.rainfallDependency,
    required this.description,
  });

  factory MaharashtraSeasonCalendar.fromJson(Map<String, dynamic> json) {
    return MaharashtraSeasonCalendar(
      seasonName: json['season_name'] as String,
      marathiName: json['marathi_name'] as String,
      periodMonths: json['period_months'] as String,
      primaryCrops: (json['primary_crops'] as List<dynamic>)
          .map((e) => e.toString())
          .toList(),
      rainfallDependency: json['rainfall_dependency'] as String,
      description: json['description'] as String,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'season_name': seasonName,
      'marathi_name': marathiName,
      'period_months': periodMonths,
      'primary_crops': primaryCrops,
      'rainfall_dependency': rainfallDependency,
      'description': description,
    };
  }
}
