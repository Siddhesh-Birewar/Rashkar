/// CropNet AI — Meteorological and Agro-Climatic Models
///
/// Matches FastAPI schemas in `services/api/app/schemas/weather.py`.
library;

/// Real-time observed meteorological data for a farm centroid.
class CurrentWeatherObservation {
  final String farmId;
  final String source;
  final String dataType;
  final DateTime observationTime;
  final DateTime retrievalTime;
  final double temperatureC;
  final double feelsLikeC;
  final double temperatureMinC;
  final double temperatureMaxC;
  final double humidityPercent;
  final double windSpeedMs;
  final double? windDirectionDeg;
  final double precipitationMm;
  final String weatherCondition;
  final String weatherDescription;
  final String weatherIcon;
  final bool isCached;
  final int? cacheAgeSeconds;

  const CurrentWeatherObservation({
    required this.farmId,
    this.source = 'OpenWeather',
    this.dataType = 'observed',
    required this.observationTime,
    required this.retrievalTime,
    required this.temperatureC,
    required this.feelsLikeC,
    required this.temperatureMinC,
    required this.temperatureMaxC,
    required this.humidityPercent,
    required this.windSpeedMs,
    this.windDirectionDeg,
    this.precipitationMm = 0.0,
    required this.weatherCondition,
    required this.weatherDescription,
    required this.weatherIcon,
    this.isCached = false,
    this.cacheAgeSeconds,
  });

  factory CurrentWeatherObservation.fromJson(Map<String, dynamic> json) {
    return CurrentWeatherObservation(
      farmId: json['farm_id'] as String,
      source: json['source'] as String? ?? 'OpenWeather',
      dataType: json['data_type'] as String? ?? 'observed',
      observationTime: DateTime.parse(json['observation_time'] as String),
      retrievalTime: json['retrieval_time'] != null
          ? DateTime.parse(json['retrieval_time'] as String)
          : DateTime.now(),
      temperatureC: (json['temperature_c'] as num).toDouble(),
      feelsLikeC: (json['feels_like_c'] as num).toDouble(),
      temperatureMinC: (json['temperature_min_c'] as num).toDouble(),
      temperatureMaxC: (json['temperature_max_c'] as num).toDouble(),
      humidityPercent: (json['humidity_percent'] as num).toDouble(),
      windSpeedMs: (json['wind_speed_ms'] as num).toDouble(),
      windDirectionDeg: (json['wind_direction_deg'] as num?)?.toDouble(),
      precipitationMm: (json['precipitation_mm'] as num?)?.toDouble() ?? 0.0,
      weatherCondition: json['weather_condition'] as String,
      weatherDescription: json['weather_description'] as String,
      weatherIcon: json['weather_icon'] as String,
      isCached: json['is_cached'] as bool? ?? false,
      cacheAgeSeconds: json['cache_age_seconds'] as int?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'farm_id': farmId,
      'source': source,
      'data_type': dataType,
      'observation_time': observationTime.toIso8601String(),
      'retrieval_time': retrievalTime.toIso8601String(),
      'temperature_c': temperatureC,
      'feels_like_c': feelsLikeC,
      'temperature_min_c': temperatureMinC,
      'temperature_max_c': temperatureMaxC,
      'humidity_percent': humidityPercent,
      'wind_speed_ms': windSpeedMs,
      if (windDirectionDeg != null) 'wind_direction_deg': windDirectionDeg,
      'precipitation_mm': precipitationMm,
      'weather_condition': weatherCondition,
      'weather_description': weatherDescription,
      'weather_icon': weatherIcon,
      'is_cached': isCached,
      if (cacheAgeSeconds != null) 'cache_age_seconds': cacheAgeSeconds,
    };
  }
}

/// 3-hour interval weather forecast point.
class WeatherForecastPoint {
  final DateTime forecastTime;
  final double temperatureC;
  final double tempMinC;
  final double tempMaxC;
  final double humidityPercent;
  final double windSpeedMs;
  final double precipitationProbabilityPct;
  final double precipitationMm;
  final String weatherCondition;
  final String weatherDescription;
  final String weatherIcon;

  const WeatherForecastPoint({
    required this.forecastTime,
    required this.temperatureC,
    required this.tempMinC,
    required this.tempMaxC,
    required this.humidityPercent,
    required this.windSpeedMs,
    required this.precipitationProbabilityPct,
    required this.precipitationMm,
    required this.weatherCondition,
    required this.weatherDescription,
    required this.weatherIcon,
  });

  factory WeatherForecastPoint.fromJson(Map<String, dynamic> json) {
    return WeatherForecastPoint(
      forecastTime: DateTime.parse(json['forecast_time'] as String),
      temperatureC: (json['temperature_c'] as num).toDouble(),
      tempMinC: (json['temp_min_c'] as num).toDouble(),
      tempMaxC: (json['temp_max_c'] as num).toDouble(),
      humidityPercent: (json['humidity_percent'] as num).toDouble(),
      windSpeedMs: (json['wind_speed_ms'] as num).toDouble(),
      precipitationProbabilityPct: (json['precipitation_probability_pct'] as num).toDouble(),
      precipitationMm: (json['precipitation_mm'] as num).toDouble(),
      weatherCondition: json['weather_condition'] as String,
      weatherDescription: json['weather_description'] as String,
      weatherIcon: json['weather_icon'] as String,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'forecast_time': forecastTime.toIso8601String(),
      'temperature_c': temperatureC,
      'temp_min_c': tempMinC,
      'temp_max_c': tempMaxC,
      'humidity_percent': humidityPercent,
      'wind_speed_ms': windSpeedMs,
      'precipitation_probability_pct': precipitationProbabilityPct,
      'precipitation_mm': precipitationMm,
      'weather_condition': weatherCondition,
      'weather_description': weatherDescription,
      'weather_icon': weatherIcon,
    };
  }
}

/// Aggregated daily weather summary.
class DailyForecastSummary {
  final String date;
  final String dayName;
  final double tempMinC;
  final double tempMaxC;
  final double humidityPercent;
  final String weatherCondition;
  final String weatherDescription;
  final String weatherIcon;
  final double totalRainMm;
  final double maxPopPct;

  const DailyForecastSummary({
    required this.date,
    required this.dayName,
    required this.tempMinC,
    required this.tempMaxC,
    required this.humidityPercent,
    required this.weatherCondition,
    required this.weatherDescription,
    required this.weatherIcon,
    required this.totalRainMm,
    required this.maxPopPct,
  });

  factory DailyForecastSummary.fromJson(Map<String, dynamic> json) {
    return DailyForecastSummary(
      date: json['date'] as String,
      dayName: json['day_name'] as String,
      tempMinC: (json['temp_min_c'] as num).toDouble(),
      tempMaxC: (json['temp_max_c'] as num).toDouble(),
      humidityPercent: (json['humidity_percent'] as num).toDouble(),
      weatherCondition: json['weather_condition'] as String,
      weatherDescription: json['weather_description'] as String,
      weatherIcon: json['weather_icon'] as String,
      totalRainMm: (json['total_rain_mm'] as num).toDouble(),
      maxPopPct: (json['max_pop_pct'] as num).toDouble(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'date': date,
      'day_name': dayName,
      'temp_min_c': tempMinC,
      'temp_max_c': tempMaxC,
      'humidity_percent': humidityPercent,
      'weather_condition': weatherCondition,
      'weather_description': weatherDescription,
      'weather_icon': weatherIcon,
      'total_rain_mm': totalRainMm,
      'max_pop_pct': maxPopPct,
    };
  }
}

/// Short-term meteorological forecast response.
class FarmWeatherForecastResponse {
  final String farmId;
  final String source;
  final String dataType;
  final DateTime retrievalTime;
  final String forecastPeriod;
  final List<DailyForecastSummary> dailySummaries;
  final List<WeatherForecastPoint> hourlyPoints;
  final bool isCached;

  const FarmWeatherForecastResponse({
    required this.farmId,
    this.source = 'OpenWeather',
    this.dataType = 'forecast',
    required this.retrievalTime,
    this.forecastPeriod = '5 days (3-hour resolution)',
    required this.dailySummaries,
    required this.hourlyPoints,
    this.isCached = false,
  });

  factory FarmWeatherForecastResponse.fromJson(Map<String, dynamic> json) {
    return FarmWeatherForecastResponse(
      farmId: json['farm_id'] as String,
      source: json['source'] as String? ?? 'OpenWeather',
      dataType: json['data_type'] as String? ?? 'forecast',
      retrievalTime: json['retrieval_time'] != null
          ? DateTime.parse(json['retrieval_time'] as String)
          : DateTime.now(),
      forecastPeriod: json['forecast_period'] as String? ?? '5 days (3-hour resolution)',
      dailySummaries: (json['daily_summaries'] as List<dynamic>?)
              ?.map((e) => DailyForecastSummary.fromJson(e as Map<String, dynamic>))
              .toList() ??
          [],
      hourlyPoints: (json['hourly_points'] as List<dynamic>?)
              ?.map((e) => WeatherForecastPoint.fromJson(e as Map<String, dynamic>))
              .toList() ??
          [],
      isCached: json['is_cached'] as bool? ?? false,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'farm_id': farmId,
      'source': source,
      'data_type': dataType,
      'retrieval_time': retrievalTime.toIso8601String(),
      'forecast_period': forecastPeriod,
      'daily_summaries': dailySummaries.map((d) => d.toJson()).toList(),
      'hourly_points': hourlyPoints.map((h) => h.toJson()).toList(),
      'is_cached': isCached,
    };
  }
}

/// Monthly climatological average point from 30-year normals.
class MonthlyClimatePoint {
  final int monthNum;
  final String monthName;
  final double rainfallMm;
  final double meanTempC;
  final double minTempC;
  final double maxTempC;

  const MonthlyClimatePoint({
    required this.monthNum,
    required this.monthName,
    required this.rainfallMm,
    required this.meanTempC,
    required this.minTempC,
    required this.maxTempC,
  });

  factory MonthlyClimatePoint.fromJson(Map<String, dynamic> json) {
    return MonthlyClimatePoint(
      monthNum: json['month_num'] as int,
      monthName: json['month_name'] as String,
      rainfallMm: (json['rainfall_mm'] as num).toDouble(),
      meanTempC: (json['mean_temp_c'] as num).toDouble(),
      minTempC: (json['min_temp_c'] as num).toDouble(),
      maxTempC: (json['max_temp_c'] as num).toDouble(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'month_num': monthNum,
      'month_name': monthName,
      'rainfall_mm': rainfallMm,
      'mean_temp_c': meanTempC,
      'min_temp_c': minTempC,
      'max_temp_c': maxTempC,
    };
  }
}

/// Deterministic agro-climatic seasonal classification.
class AgriculturalSeasonSummary {
  final String seasonName;
  final String periodMonths;
  final double totalRainfallMm;
  final double meanTemperatureC;
  final String waterStressStatus;
  final String description;

  const AgriculturalSeasonSummary({
    required this.seasonName,
    required this.periodMonths,
    required this.totalRainfallMm,
    required this.meanTemperatureC,
    required this.waterStressStatus,
    required this.description,
  });

  factory AgriculturalSeasonSummary.fromJson(Map<String, dynamic> json) {
    return AgriculturalSeasonSummary(
      seasonName: json['season_name'] as String,
      periodMonths: json['period_months'] as String,
      totalRainfallMm: (json['total_rainfall_mm'] as num).toDouble(),
      meanTemperatureC: (json['mean_temperature_c'] as num).toDouble(),
      waterStressStatus: json['water_stress_status'] as String,
      description: json['description'] as String,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'season_name': seasonName,
      'period_months': periodMonths,
      'total_rainfall_mm': totalRainfallMm,
      'mean_temperature_c': meanTemperatureC,
      'water_stress_status': waterStressStatus,
      'description': description,
    };
  }
}

/// Farm-specific 30-year agro-climate summary from NASA POWER.
class SeasonalClimateSummary {
  final String farmId;
  final String source;
  final String dataType;
  final String periodDescription;
  final DateTime retrievalTime;
  final double annualRainfallMm;
  final double monsoonRainfallMm;
  final double monsoonSharePercent;
  final List<String> wetSeasonMonths;
  final List<String> drySeasonMonths;
  final double meanTemperatureC;
  final double minTemperatureC;
  final double maxTemperatureC;
  final double temperatureRangeC;
  final double rainfallVariabilityIndex;
  final String potentialWaterStressIndicator;
  final List<MonthlyClimatePoint> monthlyClimate;
  final List<AgriculturalSeasonSummary> agriculturalSeasons;
  final bool isCached;
  final String disclaimer;

  const SeasonalClimateSummary({
    required this.farmId,
    this.source = 'NASA POWER',
    this.dataType = 'historical_reanalysis',
    this.periodDescription = '30-year Meteorological Climatology (1991–2020)',
    required this.retrievalTime,
    required this.annualRainfallMm,
    required this.monsoonRainfallMm,
    required this.monsoonSharePercent,
    required this.wetSeasonMonths,
    required this.drySeasonMonths,
    required this.meanTemperatureC,
    required this.minTemperatureC,
    required this.maxTemperatureC,
    required this.temperatureRangeC,
    required this.rainfallVariabilityIndex,
    required this.potentialWaterStressIndicator,
    required this.monthlyClimate,
    required this.agriculturalSeasons,
    this.isCached = false,
    this.disclaimer =
        'Climate summaries are derived from NASA POWER satellite reanalysis (0.5° x 0.5° grid).',
  });

  factory SeasonalClimateSummary.fromJson(Map<String, dynamic> json) {
    return SeasonalClimateSummary(
      farmId: json['farm_id'] as String,
      source: json['source'] as String? ?? 'NASA POWER',
      dataType: json['data_type'] as String? ?? 'historical_reanalysis',
      periodDescription: json['period_description'] as String? ??
          '30-year Meteorological Climatology (1991–2020)',
      retrievalTime: json['retrieval_time'] != null
          ? DateTime.parse(json['retrieval_time'] as String)
          : DateTime.now(),
      annualRainfallMm: (json['annual_rainfall_mm'] as num).toDouble(),
      monsoonRainfallMm: (json['monsoon_rainfall_mm'] as num).toDouble(),
      monsoonSharePercent: (json['monsoon_share_percent'] as num).toDouble(),
      wetSeasonMonths: (json['wet_season_months'] as List<dynamic>)
          .map((e) => e.toString())
          .toList(),
      drySeasonMonths: (json['dry_season_months'] as List<dynamic>)
          .map((e) => e.toString())
          .toList(),
      meanTemperatureC: (json['mean_temperature_c'] as num).toDouble(),
      minTemperatureC: (json['min_temperature_c'] as num).toDouble(),
      maxTemperatureC: (json['max_temperature_c'] as num).toDouble(),
      temperatureRangeC: (json['temperature_range_c'] as num).toDouble(),
      rainfallVariabilityIndex:
          (json['rainfall_variability_index'] as num).toDouble(),
      potentialWaterStressIndicator:
          json['potential_water_stress_indicator'] as String,
      monthlyClimate: (json['monthly_climate'] as List<dynamic>?)
              ?.map((e) => MonthlyClimatePoint.fromJson(e as Map<String, dynamic>))
              .toList() ??
          [],
      agriculturalSeasons: (json['agricultural_seasons'] as List<dynamic>?)
              ?.map((e) =>
                  AgriculturalSeasonSummary.fromJson(e as Map<String, dynamic>))
              .toList() ??
          [],
      isCached: json['is_cached'] as bool? ?? false,
      disclaimer: json['disclaimer'] as String? ?? '',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'farm_id': farmId,
      'source': source,
      'data_type': dataType,
      'period_description': periodDescription,
      'retrieval_time': retrievalTime.toIso8601String(),
      'annual_rainfall_mm': annualRainfallMm,
      'monsoon_rainfall_mm': monsoonRainfallMm,
      'monsoon_share_percent': monsoonSharePercent,
      'wet_season_months': wetSeasonMonths,
      'dry_season_months': drySeasonMonths,
      'mean_temperature_c': meanTemperatureC,
      'min_temperature_c': minTemperatureC,
      'max_temperature_c': maxTemperatureC,
      'temperature_range_c': temperatureRangeC,
      'rainfall_variability_index': rainfallVariabilityIndex,
      'potential_water_stress_indicator': potentialWaterStressIndicator,
      'monthly_climate': monthlyClimate.map((m) => m.toJson()).toList(),
      'agricultural_seasons': agriculturalSeasons.map((a) => a.toJson()).toList(),
      'is_cached': isCached,
      'disclaimer': disclaimer,
    };
  }
}

/// Stored historical observation or snapshot record.
class HistoricalWeatherRecord {
  final String id;
  final String farmId;
  final String snapshotType;
  final String source;
  final DateTime observationTime;
  final double? temperature;
  final double? humidity;
  final double? windSpeed;
  final double? precipitationMm;
  final String? weatherCondition;
  final DateTime createdAt;

  const HistoricalWeatherRecord({
    required this.id,
    required this.farmId,
    required this.snapshotType,
    required this.source,
    required this.observationTime,
    this.temperature,
    this.humidity,
    this.windSpeed,
    this.precipitationMm,
    this.weatherCondition,
    required this.createdAt,
  });

  factory HistoricalWeatherRecord.fromJson(Map<String, dynamic> json) {
    return HistoricalWeatherRecord(
      id: json['id'] as String,
      farmId: json['farm_id'] as String,
      snapshotType: json['snapshot_type'] as String,
      source: json['source'] as String,
      observationTime: DateTime.parse(json['observation_time'] as String),
      temperature: (json['temperature'] as num?)?.toDouble(),
      humidity: (json['humidity'] as num?)?.toDouble(),
      windSpeed: (json['wind_speed'] as num?)?.toDouble(),
      precipitationMm: (json['precipitation_mm'] as num?)?.toDouble(),
      weatherCondition: json['weather_condition'] as String?,
      createdAt: DateTime.parse(json['created_at'] as String),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'farm_id': farmId,
      'snapshot_type': snapshotType,
      'source': source,
      'observation_time': observationTime.toIso8601String(),
      if (temperature != null) 'temperature': temperature,
      if (humidity != null) 'humidity': humidity,
      if (windSpeed != null) 'wind_speed': windSpeed,
      if (precipitationMm != null) 'precipitation_mm': precipitationMm,
      if (weatherCondition != null) 'weather_condition': weatherCondition,
      'created_at': createdAt.toIso8601String(),
    };
  }
}
