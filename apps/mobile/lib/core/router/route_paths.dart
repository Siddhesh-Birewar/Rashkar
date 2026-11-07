/// Route path constants for CropNet AI navigation and URL synchronization.
abstract final class RoutePaths {
  /// Home / Dashboard (My Farms)
  static const String home = '/';

  /// Soil Testing & Metrics (Location-Based Soil Intelligence)
  static const String soilTesting = '/soil-testing';

  /// Crop Recommendation & Feasibility (Agricultural Crop Knowledge)
  static const String cropRecommendation = '/crop-recommendation';

  /// Agro-meteorology & Climate Intelligence
  static const String weather = '/weather';

  /// AI Dialogue & Advisory (Qwen3:8B Agronomic Dialogue)
  static const String advisory = '/advisory';

  /// Soil & Crop Assessment History
  static const String history = '/history';

  // --- Sub-routes & Detail Paths ---

  /// Register new farm
  static const String farmNew = '/farms/new';

  /// Farm boundary and details: /farms/:farmId
  static const String farmDetail = '/farms/:farmId';

  /// Farm soil intelligence report: /soil-testing/:farmId
  static const String soilDetail = '/soil-testing/:farmId';

  /// Farm weather & climate report: /weather/:farmId
  static const String weatherDetail = '/weather/:farmId';

  /// Crop feasibility & cultivation guide: /crop-recommendation/:cropId
  static const String cropDetail = '/crop-recommendation/:cropId';

  /// About CropNet AI
  static const String about = '/about';

  /// Authentication
  static const String login = '/login';
  static const String register = '/register';

  // --- Parameter Path Helper Methods ---

  static String farmDetailPath(String farmId) => '/farms/$farmId';
  static String soilDetailPath(String farmId) => '/soil-testing/$farmId';
  static String weatherDetailPath(String farmId) => '/weather/$farmId';
  static String cropDetailPath(String cropId) => '/crop-recommendation/$cropId';
}
