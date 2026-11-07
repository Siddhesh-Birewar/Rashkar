/// CropNet AI — Backend API Endpoints & Configuration Constants
///
/// Verified against FastAPI backend at `services/api/app/main.py` and `app/api/v1/router.py`.
class ApiConstants {
  ApiConstants._();

  /// Default API base URL.
  /// Configurable at compile-time via `--dart-define=API_BASE_URL=...`
  /// or at runtime via [ApiClient] constructor.
  static const String defaultBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://localhost:8000',
  );

  /// API V1 prefix
  static const String apiV1Prefix = '/api/v1';

  /// Development User ID header used in non-production environments
  static const String devUserIdHeader = 'X-Dev-User-Id';
  static const String defaultDevUserId = '00000000-0000-0000-0000-000000000001';

  // --- Health Endpoints ---
  static const String health = '$apiV1Prefix/health';

  // --- Farm Endpoints ---
  static const String farms = '$apiV1Prefix/farms';
  static String farmById(String farmId) => '$apiV1Prefix/farms/$farmId';
  static String farmSoilAnalyse(String farmId) => '$apiV1Prefix/farms/$farmId/soil/analyse';
  static String farmSoil(String farmId) => '$apiV1Prefix/farms/$farmId/soil';
  static String farmSoilHistory(String farmId) => '$apiV1Prefix/farms/$farmId/soil/history';

  // --- Weather Endpoints (nested under farms) ---
  static String farmWeatherCurrent(String farmId) => '$apiV1Prefix/farms/$farmId/weather/current';
  static String farmWeatherForecast(String farmId) => '$apiV1Prefix/farms/$farmId/weather/forecast';
  static String farmWeatherHistory(String farmId) => '$apiV1Prefix/farms/$farmId/weather/history';
  static String farmClimateSummary(String farmId) => '$apiV1Prefix/farms/$farmId/weather/climate-summary';

  // --- Soil Global Endpoints ---
  static const String soilProviders = '$apiV1Prefix/soil/providers';
  static const String soilLayers = '$apiV1Prefix/soil/layers';
  static const String soilPilotCoverage = '$apiV1Prefix/soil/pilot-coverage';
  static String soilFarmProfile(String farmId) => '$apiV1Prefix/soil/farms/$farmId/profile';
  static const String soilExtractPolygon = '$apiV1Prefix/soil/extract-polygon';

  // --- Crop Knowledge Base Endpoints ---
  static const String crops = '$apiV1Prefix/crops';
  static String cropById(String cropId) => '$apiV1Prefix/crops/$cropId';
  static String cropRequirements(String cropId) => '$apiV1Prefix/crops/$cropId/requirements';
  static String cropSources(String cropId) => '$apiV1Prefix/crops/$cropId/sources';
  static const String cropsSeed = '$apiV1Prefix/crops/seed';

  // --- Agriculture Reference & Intelligence Endpoints ---
  static const String agricultureSeasons = '$apiV1Prefix/agriculture/seasons';
  static const String agricultureEvaluateFarm = '$apiV1Prefix/agriculture/evaluate-farm';
  static String agricultureDecision(String decisionId) => '$apiV1Prefix/agriculture/decision/$decisionId';
  static const String agricultureFollowUp = '$apiV1Prefix/agriculture/follow-up';
  static const String agricultureExplainDecision = '$apiV1Prefix/agriculture/explain-decision';
  static const String agricultureConversation = '$apiV1Prefix/agriculture/conversation';
}
