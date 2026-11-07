import '../../../core/network/api_client.dart';
import '../../../core/network/api_constants.dart';
import '../models/weather_models.dart';

/// Repository for Farm Meteorological and Agro-Climatic Intelligence.
///
/// Communicates with FastAPI `/api/v1/farms/{id}/weather` endpoints.
class WeatherRepository {
  final ApiClient _client;

  WeatherRepository({ApiClient? client}) : _client = client ?? ApiClient();

  /// Retrieve real-time observed meteorological data for the farm centroid.
  Future<CurrentWeatherObservation> getCurrentWeather(
    String farmId, {
    bool forceRefresh = false,
  }) async {
    final queryParams = forceRefresh ? {'force_refresh': 'true'} : null;
    return _client.get<CurrentWeatherObservation>(
      ApiConstants.farmWeatherCurrent(farmId),
      queryParameters: queryParams,
      fromJson: (json) => CurrentWeatherObservation.fromJson(json as Map<String, dynamic>),
    );
  }

  /// Retrieve 5-day / 3-hour meteorological forecast for the farm centroid.
  Future<FarmWeatherForecastResponse> getWeatherForecast(
    String farmId, {
    bool forceRefresh = false,
  }) async {
    final queryParams = forceRefresh ? {'force_refresh': 'true'} : null;
    return _client.get<FarmWeatherForecastResponse>(
      ApiConstants.farmWeatherForecast(farmId),
      queryParameters: queryParams,
      fromJson: (json) => FarmWeatherForecastResponse.fromJson(json as Map<String, dynamic>),
    );
  }

  /// Retrieve historical weather observation snapshots stored for this farm.
  Future<List<HistoricalWeatherRecord>> getWeatherHistory(
    String farmId, {
    int limit = 50,
  }) async {
    return _client.get<List<HistoricalWeatherRecord>>(
      ApiConstants.farmWeatherHistory(farmId),
      queryParameters: {'limit': limit.toString()},
      fromJson: (json) {
        final list = json as List<dynamic>;
        return list
            .map((item) => HistoricalWeatherRecord.fromJson(item as Map<String, dynamic>))
            .toList();
      },
    );
  }

  /// Retrieve 30-year agro-climate summary and seasonal indicators from NASA POWER.
  Future<SeasonalClimateSummary> getClimateSummary(
    String farmId, {
    bool forceRefresh = false,
  }) async {
    final queryParams = forceRefresh ? {'force_refresh': 'true'} : null;
    return _client.get<SeasonalClimateSummary>(
      ApiConstants.farmClimateSummary(farmId),
      queryParameters: queryParams,
      fromJson: (json) => SeasonalClimateSummary.fromJson(json as Map<String, dynamic>),
    );
  }
}
