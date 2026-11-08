import 'dart:async';
import '../../../core/network/api_client.dart';
import '../../../core/network/api_constants.dart';
import '../models/farm_health_models.dart';

/// Repository responsible for retrieving the Unified Farm Health Snapshot
/// from the backend endpoint `GET /api/v1/farms/{farmId}/health-snapshot`.
class FarmHealthRepository {
  final ApiClient _client;

  static FarmHealthRepository? _instance;
  static FarmHealthRepository get instance => _instance ??= FarmHealthRepository();

  FarmHealthRepository({ApiClient? client}) : _client = client ?? ApiClient();

  /// Fetches the live Unified Farm Health Snapshot for [farmId].
  ///
  /// Set [forceRefresh] to true to bypass backend cache and recalculate.
  /// Set [targetSeason] to evaluate crop context for a specific agricultural season.
  Future<FarmHealthSnapshotResponse> getFarmHealthSnapshot(
    String farmId, {
    bool forceRefresh = false,
    String? targetSeason,
  }) async {
    final endpoint = ApiConstants.farmHealthSnapshot(
      farmId,
      forceRefresh: forceRefresh,
      targetSeason: targetSeason,
    );

    final response = await _client.get(endpoint);
    final json = response as Map<String, dynamic>;
    return FarmHealthSnapshotResponse.fromJson(json);
  }
}
