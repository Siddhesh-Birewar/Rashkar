import 'dart:convert';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

import 'package:cropnet_mobile/core/network/api_client.dart';
import 'package:cropnet_mobile/features/weather/data/weather_repository.dart';
import 'package:cropnet_mobile/features/weather/models/weather_models.dart';

void main() {
  group('Weather Models & Repository Tests', () {
    final sampleCurrentWeatherJson = {
      'farm_id': 'farm-baramati-001',
      'source': 'OpenWeather',
      'data_type': 'observed',
      'observation_time': '2026-03-01T14:30:00Z',
      'retrieval_time': '2026-03-01T14:35:00Z',
      'temperature_c': 31.5,
      'feels_like_c': 30.8,
      'temperature_min_c': 20.0,
      'temperature_max_c': 34.0,
      'humidity_percent': 38.0,
      'wind_speed_ms': 4.2,
      'wind_direction_deg': 240.0,
      'precipitation_mm': 0.0,
      'weather_condition': 'Clear',
      'weather_description': 'clear sky',
      'weather_icon': '01d',
      'is_cached': false,
      'cache_age_seconds': 0,
    };

    final sampleForecastJson = {
      'farm_id': 'farm-baramati-001',
      'source': 'OpenWeather',
      'data_type': 'forecast',
      'retrieval_time': '2026-03-01T14:35:00Z',
      'forecast_period': '5 days (3-hour resolution)',
      'daily_summaries': [
        {
          'date': '2026-03-01',
          'day_name': 'Sunday',
          'temp_min_c': 20.5,
          'temp_max_c': 34.2,
          'humidity_percent': 35.0,
          'weather_condition': 'Clear',
          'weather_description': 'clear sky',
          'weather_icon': '01d',
          'total_rain_mm': 0.0,
          'max_pop_pct': 0.0,
        }
      ],
      'hourly_points': [
        {
          'forecast_time': '2026-03-01T15:00:00Z',
          'temperature_c': 32.0,
          'temp_min_c': 31.0,
          'temp_max_c': 33.0,
          'humidity_percent': 34.0,
          'wind_speed_ms': 4.5,
          'precipitation_probability_pct': 0.0,
          'precipitation_mm': 0.0,
          'weather_condition': 'Clear',
          'weather_description': 'clear sky',
          'weather_icon': '01d',
        }
      ],
      'is_cached': false,
    };

    final sampleClimateSummaryJson = {
      'farm_id': 'farm-baramati-001',
      'source': 'NASA POWER',
      'data_type': 'historical_reanalysis',
      'period_description': '30-year Meteorological Climatology (1991–2020)',
      'retrieval_time': '2026-03-01T14:35:00Z',
      'annual_rainfall_mm': 550.0,
      'monsoon_rainfall_mm': 420.0,
      'monsoon_share_percent': 76.4,
      'wet_season_months': ['June', 'July', 'August', 'September'],
      'dry_season_months': ['December', 'January', 'February', 'March'],
      'mean_temperature_c': 26.2,
      'min_temperature_c': 12.5,
      'max_temperature_c': 40.5,
      'temperature_range_c': 28.0,
      'rainfall_variability_index': 0.28,
      'potential_water_stress_indicator': 'Moderate Water Stress in Summer',
      'monthly_climate': [
        {
          'month_num': 7,
          'month_name': 'July',
          'rainfall_mm': 145.0,
          'mean_temp_c': 26.5,
          'min_temp_c': 22.0,
          'max_temp_c': 31.0,
        }
      ],
      'agricultural_seasons': [
        {
          'season_name': 'Kharif',
          'period_months': 'June – October',
          'total_rainfall_mm': 420.0,
          'mean_temperature_c': 27.0,
          'water_stress_status': 'Adequate Rainfed Moisture',
          'description': 'Monsoon season with favorable rainfed conditions',
        }
      ],
      'is_cached': false,
      'disclaimer': 'Climate summaries are derived from NASA POWER satellite reanalysis.',
    };

    test('CurrentWeatherObservation deserializes correctly', () {
      final weather = CurrentWeatherObservation.fromJson(sampleCurrentWeatherJson);

      expect(weather.farmId, 'farm-baramati-001');
      expect(weather.temperatureC, 31.5);
      expect(weather.humidityPercent, 38.0);
      expect(weather.weatherCondition, 'Clear');
      expect(weather.isCached, false);
    });

    test('FarmWeatherForecastResponse parses daily summaries and hourly points', () {
      final forecast = FarmWeatherForecastResponse.fromJson(sampleForecastJson);

      expect(forecast.farmId, 'farm-baramati-001');
      expect(forecast.dailySummaries.length, 1);
      expect(forecast.dailySummaries.first.dayName, 'Sunday');
      expect(forecast.hourlyPoints.length, 1);
      expect(forecast.hourlyPoints.first.temperatureC, 32.0);
    });

    test('SeasonalClimateSummary parses 30-year agro-climatic normals', () {
      final climate = SeasonalClimateSummary.fromJson(sampleClimateSummaryJson);

      expect(climate.farmId, 'farm-baramati-001');
      expect(climate.annualRainfallMm, 550.0);
      expect(climate.monsoonSharePercent, 76.4);
      expect(climate.monthlyClimate.first.monthName, 'July');
      expect(climate.agriculturalSeasons.first.seasonName, 'Kharif');
      expect(climate.agriculturalSeasons.first.waterStressStatus, 'Adequate Rainfed Moisture');
    });

    test('WeatherRepository.getCurrentWeather calls farm weather endpoint', () async {
      final mockClient = MockClient((request) async {
        expect(request.url.path, '/api/v1/farms/farm-baramati-001/weather/current');
        return http.Response(
          jsonEncode(sampleCurrentWeatherJson),
          200,
          headers: {'content-type': 'application/json; charset=utf-8'},
        );
      });

      final repo = WeatherRepository(client: ApiClient(httpClient: mockClient));
      final current = await repo.getCurrentWeather('farm-baramati-001');

      expect(current.farmId, 'farm-baramati-001');
      expect(current.temperatureC, 31.5);
    });

    test('WeatherRepository.getWeatherForecast calls forecast endpoint', () async {
      final mockClient = MockClient((request) async {
        expect(request.url.path, '/api/v1/farms/farm-baramati-001/weather/forecast');
        return http.Response(
          jsonEncode(sampleForecastJson),
          200,
          headers: {'content-type': 'application/json; charset=utf-8'},
        );
      });

      final repo = WeatherRepository(client: ApiClient(httpClient: mockClient));
      final forecast = await repo.getWeatherForecast('farm-baramati-001');

      expect(forecast.dailySummaries.first.maxPopPct, 0.0);
    });

    test('WeatherRepository.getClimateSummary calls climate-summary endpoint', () async {
      final mockClient = MockClient((request) async {
        expect(request.url.path, '/api/v1/farms/farm-baramati-001/weather/climate-summary');
        return http.Response(
          jsonEncode(sampleClimateSummaryJson),
          200,
          headers: {'content-type': 'application/json; charset=utf-8'},
        );
      });

      final repo = WeatherRepository(client: ApiClient(httpClient: mockClient));
      final climate = await repo.getClimateSummary('farm-baramati-001');

      expect(climate.annualRainfallMm, 550.0);
    });
  });
}
