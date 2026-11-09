/// Agri Intelligence models — Crop Doctor + Heat Risk.
library;

class CropDoctorResult {
  final String crop;
  final String diagnosis;
  final double confidence;
  final bool isHealthy;
  final List<String> advice;
  final String? disclaimer;

  const CropDoctorResult({
    required this.crop,
    required this.diagnosis,
    required this.confidence,
    required this.isHealthy,
    required this.advice,
    this.disclaimer,
  });

  factory CropDoctorResult.fromJson(Map<String, dynamic> json) {
    return CropDoctorResult(
      crop: json['crop'] as String? ?? 'Unknown',
      diagnosis: json['diagnosis'] as String? ?? 'Unknown',
      confidence: (json['confidence_percent'] as num?)?.toDouble() ?? 0.0,
      isHealthy: json['is_healthy'] as bool? ?? false,
      advice: (json['actionable_advice'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          const [],
      disclaimer: json['disclaimer'] as String?,
    );
  }
}

class CropHeatResult {
  final String cropCode;
  final String stageName;
  final double criticalTmax;
  final double forecastTmax;
  final double forecastTmin;
  final double hoursAboveCritical;
  final bool warmNightHazard;
  final double gdd;
  final String riskCategory;
  final String riskLabel;
  final String explanation;
  final String evidenceCitation;

  const CropHeatResult({
    required this.cropCode,
    required this.stageName,
    required this.criticalTmax,
    required this.forecastTmax,
    required this.forecastTmin,
    required this.hoursAboveCritical,
    required this.warmNightHazard,
    required this.gdd,
    required this.riskCategory,
    required this.riskLabel,
    required this.explanation,
    required this.evidenceCitation,
  });

  factory CropHeatResult.fromJson(Map<String, dynamic> json) {
    return CropHeatResult(
      cropCode: json['crop_code'] as String? ?? '',
      stageName: json['growth_stage_name'] as String? ?? '',
      criticalTmax: (json['critical_tmax_c'] as num?)?.toDouble() ?? 0.0,
      forecastTmax: (json['forecast_tmax_c'] as num?)?.toDouble() ?? 0.0,
      forecastTmin: (json['forecast_tmin_c'] as num?)?.toDouble() ?? 0.0,
      hoursAboveCritical: (json['hours_above_critical'] as num?)?.toDouble() ?? 0.0,
      warmNightHazard: json['warm_night_hazard'] as bool? ?? false,
      gdd: (json['cumulative_gdd'] as num?)?.toDouble() ?? 0.0,
      riskCategory: json['risk_category'] as String? ?? 'UNKNOWN',
      riskLabel: json['risk_label'] as String? ?? '',
      explanation: json['explanation'] as String? ?? '',
      evidenceCitation: json['evidence_citation'] as String? ?? '',
    );
  }
}

class WorkerHeatResult {
  final double wbgt;
  final double wbgtEffective;
  final double threshold;
  final String hazardLevel;
  final bool exceedsThreshold;
  final String workRestCycle;
  final double? heatIndex;
  final double? utci;
  final String recommendation;

  const WorkerHeatResult({
    required this.wbgt,
    required this.wbgtEffective,
    required this.threshold,
    required this.hazardLevel,
    required this.exceedsThreshold,
    required this.workRestCycle,
    this.heatIndex,
    this.utci,
    required this.recommendation,
  });

  factory WorkerHeatResult.fromJson(Map<String, dynamic> json) {
    return WorkerHeatResult(
      wbgt: (json['wbgt_c'] as num?)?.toDouble() ?? 0.0,
      wbgtEffective: (json['wbgt_effective_c'] as num?)?.toDouble() ?? 0.0,
      threshold: (json['threshold_c'] as num?)?.toDouble() ?? 0.0,
      hazardLevel: json['hazard_level'] as String? ?? 'UNKNOWN',
      exceedsThreshold: json['exceeds_threshold'] as bool? ?? false,
      workRestCycle: json['work_rest_cycle'] as String? ?? '',
      heatIndex: (json['heat_index_c'] as num?)?.toDouble(),
      utci: (json['utci_c'] as num?)?.toDouble(),
      recommendation: json['recommendation'] as String? ?? '',
    );
  }
}

class FarmHeatRiskResult {
  final String farmName;
  final String cropCommonName;
  final String stageName;
  final String riskCategory;
  final String riskLabel;
  final double tmax;
  final double tmin;
  final double hoursAbove;
  final bool warmNight;
  final List<Map<String, dynamic>> dailyOutlook;
  final List<Map<String, dynamic>> interventions;
  final List<String> limitations;
  final String provenance;
  final String weatherSource;

  const FarmHeatRiskResult({
    required this.farmName,
    required this.cropCommonName,
    required this.stageName,
    required this.riskCategory,
    required this.riskLabel,
    required this.tmax,
    required this.tmin,
    required this.hoursAbove,
    required this.warmNight,
    required this.dailyOutlook,
    required this.interventions,
    required this.limitations,
    required this.provenance,
    required this.weatherSource,
  });

  factory FarmHeatRiskResult.fromJson(Map<String, dynamic> json) {
    return FarmHeatRiskResult(
      farmName: json['farm_name'] as String? ?? '',
      cropCommonName: json['crop_common_name'] as String? ?? '',
      stageName: json['growth_stage_name'] as String? ?? '',
      riskCategory: json['risk_category'] as String? ?? 'UNKNOWN',
      riskLabel: json['risk_label'] as String? ?? '',
      tmax: (json['forecast_tmax_c'] as num?)?.toDouble() ?? 0,
      tmin: (json['forecast_tmin_c'] as num?)?.toDouble() ?? 0,
      hoursAbove: (json['hours_above_critical'] as num?)?.toDouble() ?? 0,
      warmNight: json['warm_night_hazard'] as bool? ?? false,
      dailyOutlook: (json['daily_outlook'] as List<dynamic>?)
              ?.map((e) => Map<String, dynamic>.from(e as Map))
              .toList() ??
          const [],
      interventions: (json['interventions'] as List<dynamic>?)
              ?.map((e) => Map<String, dynamic>.from(e as Map))
              .toList() ??
          const [],
      limitations: (json['limitations'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          const [],
      provenance: json['provenance'] as String? ?? '',
      weatherSource: json['weather_source'] as String? ?? '',
    );
  }
}
