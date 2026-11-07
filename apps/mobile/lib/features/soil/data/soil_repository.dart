import '../../../core/network/api_client.dart';
import '../../../core/network/api_constants.dart';
import '../models/soil_models.dart';

/// Repository for Soil Intelligence and GIS Raster Extraction.
///
/// Communicates with FastAPI `/api/v1/soil` and `/api/v1/farms/{id}/soil` endpoints.
class SoilRepository {
  final ApiClient _client;

  SoilRepository({ApiClient? client}) : _client = client ?? ApiClient();

  /// Trigger or retrieve soil analysis for a registered farm.
  Future<UnifiedSoilProfile> analyseFarmSoil(
    String farmId, {
    bool forceRefresh = false,
    String depth = '0-5cm',
  }) async {
    final request = SoilAnalyseRequest(forceRefresh: forceRefresh, depth: depth);
    return _client.post<UnifiedSoilProfile>(
      ApiConstants.farmSoilAnalyse(farmId),
      body: request.toJson(),
      fromJson: (json) => UnifiedSoilProfile.fromJson(Map<String, dynamic>.from(json as Map)),
    );
  }

  /// Retrieve the latest soil intelligence profile for a registered farm.
  Future<UnifiedSoilProfile> getFarmSoilProfile(String farmId, {String? depth}) async {
    final params = depth != null ? {'depth': depth} : null;
    return _client.get<UnifiedSoilProfile>(
      ApiConstants.farmSoil(farmId),
      queryParameters: params,
      fromJson: (json) => UnifiedSoilProfile.fromJson(Map<String, dynamic>.from(json as Map)),
    );
  }

  /// Retrieve full historical soil intelligence runs for a farm.
  Future<List<UnifiedSoilProfile>> getFarmSoilHistory(String farmId) async {
    return _client.get<List<UnifiedSoilProfile>>(
      ApiConstants.farmSoilHistory(farmId),
      fromJson: (json) {
        final list = json as List<dynamic>;
        return list.map((item) => UnifiedSoilProfile.fromJson(Map<String, dynamic>.from(item as Map))).toList();
      },
    );
  }

  /// Generate a soil profile snapshot for a registered farm boundary.
  Future<UnifiedSoilProfile> generateSoilProfileForFarm(String farmId) async {
    return _client.post<UnifiedSoilProfile>(
      ApiConstants.soilFarmProfile(farmId),
      fromJson: (json) => UnifiedSoilProfile.fromJson(Map<String, dynamic>.from(json as Map)),
    );
  }

  /// Extract soil parameters directly for an ad-hoc polygon.
  Future<UnifiedSoilProfile> extractAdHocPolygon(PolygonSoilExtractRequest payload) async {
    return _client.post<UnifiedSoilProfile>(
      ApiConstants.soilExtractPolygon,
      body: payload.toJson(),
      fromJson: (json) => UnifiedSoilProfile.fromJson(Map<String, dynamic>.from(json as Map)),
    );
  }

  /// List all supported soil data providers and their operational capabilities.
  Future<List<ProviderCapability>> listSoilProviders() async {
    return _client.get<List<ProviderCapability>>(
      ApiConstants.soilProviders,
      fromJson: (json) {
        final list = json as List<dynamic>;
        return list.map((item) => ProviderCapability.fromJson(Map<String, dynamic>.from(item as Map))).toList();
      },
    );
  }

  /// Metadata catalogue of all operational and derived soil layers.
  Future<List<SoilLayerInfo>> listSoilLayers() async {
    return _client.get<List<SoilLayerInfo>>(
      ApiConstants.soilLayers,
      fromJson: (json) {
        final list = json as List<dynamic>;
        return list.map((item) => SoilLayerInfo.fromJson(Map<String, dynamic>.from(item as Map))).toList();
      },
    );
  }

  /// Retrieve verified pilot coverage matrix for Maharashtra pilot regions.
  Future<Map<String, dynamic>> getPilotCoverageMatrix() async {
    return _client.get<Map<String, dynamic>>(
      ApiConstants.soilPilotCoverage,
      fromJson: (json) => Map<String, dynamic>.from(json as Map),
    );
  }
}
