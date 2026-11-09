import '../../../core/network/api_client.dart';
import '../../../core/network/api_constants.dart';
import '../models/farm_models.dart';

/// Repository for Farm Registration and Boundary Management.
///
/// Communicates with FastAPI `/api/v1/farms` endpoints.
class FarmRepository {
  final ApiClient _client;

  FarmRepository({ApiClient? client}) : _client = client ?? ApiClient();

  /// Register a new farm with validated polygon boundary.
  Future<Farm> createFarm(FarmCreate payload) async {
    return _client.post<Farm>(
      ApiConstants.farms,
      body: payload.toJson(),
      fromJson: (json) => Farm.fromJson(json as Map<String, dynamic>),
    );
  }

  /// List all farms belonging to the authenticated user.
  Future<List<Farm>> listFarms() async {
    return _client.get<List<Farm>>(
      ApiConstants.farms,
      fromJson: (json) {
        final list = json as List<dynamic>;
        return list.map((item) => Farm.fromJson(item as Map<String, dynamic>)).toList();
      },
    );
  }

  /// Retrieve farm by ID.
  Future<Farm> getFarm(String farmId) async {
    return _client.get<Farm>(
      ApiConstants.farmById(farmId),
      fromJson: (json) => Farm.fromJson(json as Map<String, dynamic>),
    );
  }

  /// Update farm details or boundary geometry.
  Future<Farm> updateFarm(String farmId, FarmUpdate payload) async {
    return _client.put<Farm>(
      ApiConstants.farmById(farmId),
      body: payload.toJson(),
      fromJson: (json) => Farm.fromJson(json as Map<String, dynamic>),
    );
  }

  /// Delete farm by ID.
  Future<void> deleteFarm(String farmId) async {
    await _client.delete<void>(
      ApiConstants.farmById(farmId),
    );
  }
}
