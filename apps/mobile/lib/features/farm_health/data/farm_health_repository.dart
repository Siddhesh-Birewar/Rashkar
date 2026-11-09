import 'dart:async';
import '../../../core/network/api_client.dart';
import '../../../core/network/api_constants.dart';
import '../models/farm_health_models.dart';

/// Repository responsible for retrieving the Unified Farm Health Snapshot
/// from the backend endpoint `GET /api/v1/farms/{farmId}/health-snapshot`.
///
/// Features robust in-memory local caching, automatic offline fallback with
/// freshness metadata, and an offline action queue for diagnostic follow-ups.
class FarmHealthRepository {
  final ApiClient _client;

  // Local snapshot memory cache
  final Map<String, FarmHealthSnapshotResponse> _cache = {};
  final Map<String, DateTime> _cacheTimestamps = {};

  // Offline action queue (e.g. pending diagnostic follow-up answers)
  final List<Map<String, dynamic>> _pendingActions = [];

  static FarmHealthRepository? _instance;
  static FarmHealthRepository get instance => _instance ??= FarmHealthRepository();

  FarmHealthRepository({ApiClient? client}) : _client = client ?? ApiClient();

  /// Check whether a cached snapshot is available for [farmId].
  bool hasCachedSnapshot(String farmId) => _cache.containsKey(farmId);

  /// Directly retrieve cached snapshot for [farmId] if present.
  FarmHealthSnapshotResponse? getCachedSnapshot(String farmId) {
    final cached = _cache[farmId];
    if (cached == null) return null;
    return cached.copyWith(
      isFromCache: true,
      cachedAt: _cacheTimestamps[farmId],
    );
  }

  /// Manually populate or update cache for a farm.
  void setCachedSnapshot(String farmId, FarmHealthSnapshotResponse snapshot) {
    _cache[farmId] = snapshot;
    _cacheTimestamps[farmId] = DateTime.now();
  }

  /// Clears cache for a specific farm or all farms.
  void clearCache([String? farmId]) {
    if (farmId != null) {
      _cache.remove(farmId);
      _cacheTimestamps.remove(farmId);
    } else {
      _cache.clear();
      _cacheTimestamps.clear();
    }
  }

  /// Queue a diagnostic follow-up action for offline synchronization.
  void queueFollowUpAction(String farmId, String decisionId, Map<String, dynamic> answers) {
    _pendingActions.add({
      'action': 'follow_up_submission',
      'farm_id': farmId,
      'decision_id': decisionId,
      'answers': answers,
      'queued_at': DateTime.now().toIso8601String(),
    });
  }

  /// Retrieve all pending queued offline actions.
  List<Map<String, dynamic>> getPendingActions() => List.unmodifiable(_pendingActions);

  /// Clear the pending offline action queue.
  void clearPendingActions() => _pendingActions.clear();

  /// Fetches the Unified Farm Health Snapshot for [farmId].
  ///
  /// Set [forceRefresh] to true to bypass backend cache and recalculate.
  /// Set [targetSeason] to evaluate crop context for a specific agricultural season.
  ///
  /// If the network request fails and a previously fetched snapshot exists in the
  /// local cache, returns the cached snapshot with [isFromCache] = true and [cachedAt].
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

    try {
      final response = await _client.get(endpoint);
      final json = response as Map<String, dynamic>;
      final liveSnapshot = FarmHealthSnapshotResponse.fromJson(json);

      // Update local memory cache on successful remote retrieval
      _cache[farmId] = liveSnapshot;
      _cacheTimestamps[farmId] = DateTime.now();

      return liveSnapshot;
    } catch (e) {
      // Offline fallback: if cache exists, return it with cache metadata
      if (_cache.containsKey(farmId)) {
        final cached = _cache[farmId]!;
        return cached.copyWith(
          isFromCache: true,
          cachedAt: _cacheTimestamps[farmId] ?? DateTime.now(),
        );
      }
      rethrow;
    }
  }
}
