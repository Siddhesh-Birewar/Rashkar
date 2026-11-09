import 'dart:convert';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

import 'package:cropnet_mobile/core/network/api_client.dart';
import 'package:cropnet_mobile/core/network/api_exception.dart';
import 'package:cropnet_mobile/features/farm_health/data/farm_health_repository.dart';
import 'package:cropnet_mobile/features/farm_health/models/farm_health_models.dart';

void main() {
  const farmId = '94a1f16e-bf0d-4d3f-9bd3-d63a57189818';

  final sampleSnapshotJson = {
    'contract_version': '1.0',
    'farm_id': farmId,
    'farm_name': 'Baramati Pilot Grape Vineyard',
    'owner_id': '00000000-0000-0000-0000-000000000001',
    'taluka': 'Baramati',
    'district': 'Pune',
    'state': 'Maharashtra',
    'calculated_area_hectares': 18.74,
    'calculated_area_acres': 46.3,
    'snapshot_timestamp': '2026-11-08T14:00:00Z',
    'overall_evidence_overview': {
      'domains_available': 4,
      'domains_partially_available': 1,
      'domains_stale': 0,
      'domains_not_available': 0,
      'domains_insufficient_evidence': 0,
      'total_domains': 5,
      'actionable_summary': 'Healthy evidence profile available.',
    },
    'soil': {
      'availability_state': 'PARTIALLY_AVAILABLE',
      'provenance': 'SPATIALLY_ESTIMATED_ISRIC',
      'key_indicators': {
        'soil_ph': 7.3,
        'organic_carbon_pct': 1.62,
        'soil_texture': 'Clay',
        'cation_exchange_capacity': 37.7,
      },
      'missing_critical_parameters': ['available_nitrogen'],
      'agronomic_notes': [],
    },
    'water': {
      'availability_state': 'AVAILABLE',
      'provenance': 'LABORATORY_MEASURED',
      'registered_sources_count': 2,
      'laboratory_name': 'District Agricultural Water Testing Laboratory',
      'key_indicators': {
        'electrical_conductivity_ds_m': 1.15,
        'sar': 4.2,
        'rsc_meq_l': -0.8,
        'boron_mg_l': 0.4,
      },
      'sources': [],
      'institutional_evaluations': [],
      'missing_critical_parameters': [],
    },
    'satellite': {
      'availability_state': 'AVAILABLE',
      'provenance': 'COPERNICUS_SENTINEL_2_L2A',
      'canopy_ndvi': 0.64,
      'canopy_ndmi': 0.217,
      'vegetation_coverage_percent': 57.6,
      'valid_pixel_count': 1874,
      'raster_maps': {},
    },
    'weather': {
      'availability_state': 'AVAILABLE',
      'current_weather': {
        'source': 'OPENWEATHER_OBSERVATION',
        'provenance': 'OPENWEATHER_OBSERVATION',
        'temperature_c': 25.4,
      },
      'forecast': {
        'provenance': 'OPENWEATHER_FORECAST',
        'forecast_days_count': 5,
      },
      'climate_normals': {
        'provenance': 'NASA_POWER_CLIMATOLOGY',
        'monsoon_rainfall_mm': 480.0,
      },
    },
    'crop_context': {
      'availability_state': 'AVAILABLE',
      'provenance': 'CROP_DECISION_ENGINE',
      'evaluated_crops_count': 3,
      'suitable_crops': [],
      'conditionally_suitable_crops': [],
      'disqualified_crops': [],
      'abstain_crops': [],
      'top_limiting_factors': [],
      'pending_followup_questions_count': 0,
    },
    'governance_notice':
        'CropNet AI provides independent, evidence-gated agricultural domain summaries. In accordance with institutional agricultural guidelines, no universal health score is computed.',
  };

  group('FarmHealthRepository Offline Resilience Tests', () {
    test('Successful network fetch stores snapshot in memory cache', () async {
      final mockClient = MockClient((request) async {
        return http.Response(
          jsonEncode(sampleSnapshotJson),
          200,
          headers: {'content-type': 'application/json'},
        );
      });

      final apiClient = ApiClient(httpClient: mockClient);
      final repo = FarmHealthRepository(client: apiClient);

      // Verify cache initially empty
      expect(repo.hasCachedSnapshot(farmId), isFalse);

      // Fetch snapshot
      final snapshot = await repo.getFarmHealthSnapshot(farmId);
      expect(snapshot.isFromCache, isFalse);
      expect(snapshot.farmName, 'Baramati Pilot Grape Vineyard');

      // Verify memory cache populated
      expect(repo.hasCachedSnapshot(farmId), isTrue);
      final cached = repo.getCachedSnapshot(farmId);
      expect(cached, isNotNull);
      expect(cached!.isFromCache, isTrue);
      expect(cached.cachedAt, isNotNull);
    });

    test('Network failure falls back to cached snapshot with offline metadata', () async {
      int requestCount = 0;
      final mockClient = MockClient((request) async {
        requestCount++;
        if (requestCount == 1) {
          // First request: Online 200 OK
          return http.Response(
            jsonEncode(sampleSnapshotJson),
            200,
            headers: {'content-type': 'application/json'},
          );
        } else {
          // Second request: Network outage / Offline socket failure
          throw http.ClientException('Network is unreachable / SocketException');
        }
      });

      final apiClient = ApiClient(httpClient: mockClient);
      final repo = FarmHealthRepository(client: apiClient);

      // 1. Initial online retrieval
      final liveSnapshot = await repo.getFarmHealthSnapshot(farmId);
      expect(liveSnapshot.isFromCache, isFalse);

      // 2. Subsequent offline retrieval -> Graceful fallback to cache
      final offlineSnapshot = await repo.getFarmHealthSnapshot(farmId);
      expect(offlineSnapshot.isFromCache, isTrue);
      expect(offlineSnapshot.cachedAt, isNotNull);
      expect(offlineSnapshot.farmId, farmId);
      expect(offlineSnapshot.soil.provenance, 'SPATIALLY_ESTIMATED_ISRIC');
      expect(offlineSnapshot.water.provenance, 'LABORATORY_MEASURED');
      expect(offlineSnapshot.satellite.provenance, 'COPERNICUS_SENTINEL_2_L2A');
    });

    test('Network failure with NO prior cache rethrows exception', () async {
      final mockClient = MockClient((request) async {
        throw http.ClientException('No Internet Connection');
      });

      final apiClient = ApiClient(httpClient: mockClient);
      final repo = FarmHealthRepository(client: apiClient);

      expect(
        () async => await repo.getFarmHealthSnapshot('unknown-farm-parcel'),
        throwsA(isA<NetworkException>()),
      );
    });

    test('Offline Action Queue stores and retrieves pending follow-up submissions', () {
      final repo = FarmHealthRepository();
      expect(repo.getPendingActions(), isEmpty);

      // Queue an action while offline
      repo.queueFollowUpAction(
        farmId,
        'decision-eval-401',
        {'irrigation_frequency_days': 7, 'soil_salinity_observed': false},
      );

      final actions = repo.getPendingActions();
      expect(actions.length, 1);
      expect(actions.first['action'], 'follow_up_submission');
      expect(actions.first['farm_id'], farmId);
      expect(actions.first['decision_id'], 'decision-eval-401');
      expect(actions.first['answers']['irrigation_frequency_days'], 7);

      // Clear queue after synchronization
      repo.clearPendingActions();
      expect(repo.getPendingActions(), isEmpty);
    });

    test('Cache clearing removes cached snapshot for specified farm or all farms', () {
      final repo = FarmHealthRepository();
      final snapshot = FarmHealthSnapshotResponse.fromJson(sampleSnapshotJson);

      repo.setCachedSnapshot(farmId, snapshot);
      expect(repo.hasCachedSnapshot(farmId), isTrue);

      // Clear specific farm
      repo.clearCache(farmId);
      expect(repo.hasCachedSnapshot(farmId), isFalse);

      // Clear all
      repo.setCachedSnapshot(farmId, snapshot);
      repo.clearCache();
      expect(repo.hasCachedSnapshot(farmId), isFalse);
    });
  });

  group('FarmHealthSnapshotResponse Cache Serialization Tests', () {
    test('isFromCache and cachedAt round-trip through JSON correctly', () {
      final now = DateTime.now();
      final base = FarmHealthSnapshotResponse.fromJson(sampleSnapshotJson);

      final cachedSnapshot = base.copyWith(isFromCache: true, cachedAt: now);
      final serialized = cachedSnapshot.toJson();

      expect(serialized['is_from_cache'], isTrue);
      expect(serialized['cached_at'], isNotNull);

      final roundTrip = FarmHealthSnapshotResponse.fromJson(serialized);
      expect(roundTrip.isFromCache, isTrue);
      expect(roundTrip.cachedAt?.toIso8601String(), now.toIso8601String());
    });
  });
}
