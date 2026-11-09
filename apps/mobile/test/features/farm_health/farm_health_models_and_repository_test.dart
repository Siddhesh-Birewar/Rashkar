import 'dart:convert';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

import 'package:cropnet_mobile/core/network/api_client.dart';
import 'package:cropnet_mobile/core/network/api_exception.dart';
import 'package:cropnet_mobile/features/farm_health/data/farm_health_repository.dart';
import 'package:cropnet_mobile/features/farm_health/models/farm_health_models.dart';

void main() {
  group('DataAvailabilityState Enum Tests', () {
    test('parses canonical state strings correctly', () {
      expect(DataAvailabilityState.fromString('AVAILABLE'), DataAvailabilityState.available);
      expect(DataAvailabilityState.fromString('PARTIALLY_AVAILABLE'), DataAvailabilityState.partiallyAvailable);
      expect(DataAvailabilityState.fromString('partially-available'), DataAvailabilityState.partiallyAvailable);
      expect(DataAvailabilityState.fromString('STALE'), DataAvailabilityState.stale);
      expect(DataAvailabilityState.fromString('INSUFFICIENT_EVIDENCE'), DataAvailabilityState.insufficientEvidence);
      expect(DataAvailabilityState.fromString('NOT_AVAILABLE'), DataAvailabilityState.notAvailable);
      expect(DataAvailabilityState.fromString(null), DataAvailabilityState.notAvailable);
      expect(DataAvailabilityState.fromString('UNKNOWN_STATE'), DataAvailabilityState.notAvailable);
    });

    test('serializes back to canonical API strings', () {
      expect(DataAvailabilityState.available.toApiString(), 'AVAILABLE');
      expect(DataAvailabilityState.partiallyAvailable.toApiString(), 'PARTIALLY_AVAILABLE');
      expect(DataAvailabilityState.stale.toApiString(), 'STALE');
      expect(DataAvailabilityState.insufficientEvidence.toApiString(), 'INSUFFICIENT_EVIDENCE');
      expect(DataAvailabilityState.notAvailable.toApiString(), 'NOT_AVAILABLE');
    });
  });

  group('FarmHealthSnapshotResponse — Contract Examples Tests', () {
    test('Example A: Full Evidence Farm parses completely with all 5 domains', () {
      final json = {
        'contract_version': '1.0',
        'farm_id': '94a1f16e-bf0d-4d3f-9bd3-d63a57189818',
        'farm_name': 'Baramati Model Farm',
        'owner_id': '00000000-0000-0000-0000-000000000001',
        'taluka': 'Baramati',
        'district': 'Pune',
        'state': 'Maharashtra',
        'calculated_area_hectares': 2.5,
        'calculated_area_acres': 6.18,
        'snapshot_timestamp': '2026-11-08T11:45:00Z',
        'overall_evidence_overview': {
          'domains_available': 5,
          'domains_partially_available': 0,
          'domains_stale': 0,
          'domains_not_available': 0,
          'domains_insufficient_evidence': 0,
          'total_domains': 5,
          'actionable_summary': 'Complete actionable evidence available across all 5 domains.',
        },
        'soil': {
          'availability_state': 'AVAILABLE',
          'last_updated': '2026-10-15T09:30:00Z',
          'data_age_days': 24,
          'provenance': 'MIXED_DUAL_SOURCE',
          'laboratory_name': 'KVK Baramati Soil Testing Laboratory',
          'sample_depth': '0-15 cm',
          'key_indicators': {
            'soil_ph': 7.6,
            'organic_carbon_pct': 0.58,
            'electrical_conductivity_ds_m': 0.45,
            'available_nitrogen_kg_ha': 210.0,
            'available_phosphorus_kg_ha': 18.5,
            'available_potassium_kg_ha': 340.0,
            'soil_texture': 'Clay Loam',
            'cation_exchange_capacity': 38.2,
          },
          'missing_critical_parameters': [],
          'agronomic_notes': ['Farmer-confirmed physical laboratory test.'],
        },
        'water': {
          'availability_state': 'AVAILABLE',
          'last_updated': '2026-09-20T14:15:00Z',
          'data_age_days': 49,
          'registered_sources_count': 1,
          'sources': [
            {
              'source_id': 'wsrc-001',
              'source_type': 'borewell',
              'name': 'North Field Borewell',
              'seasonal_availability': 'perennial',
              'reliability': 'reliable',
              'irrigation_method': 'drip',
              'measured_capacity_lph': 12000.0,
              'capacity_provenance': 'MEASURED',
            }
          ],
          'laboratory_name': 'Agricultural Water Testing Laboratory, Pune',
          'key_indicators': {
            'ph': 7.6,
            'electrical_conductivity_ds_m': 1.85,
            'tds_mg_l': 1184.0,
            'sar': 3.01,
            'sar_status': 'AVAILABLE',
            'rsc_meq_l': -1.9,
            'rsc_status': 'AVAILABLE',
            'chloride_meq_l': 4.8,
            'boron_mg_l': 0.65,
          },
          'institutional_evaluations': [
            {
              'parameter_key': 'electrical_conductivity',
              'parameter_name': 'Electrical Conductivity (EC)',
              'hazard_level': 'MEDIUM',
              'hazard_title': 'Medium Salinity (Class 2)',
              'standard_applied': 'BIS IS 11624:2019',
              'management_guidance': 'Leaching fraction required for salt-sensitive crops.',
            }
          ],
          'missing_critical_parameters': [],
        },
        'satellite': {
          'availability_state': 'AVAILABLE',
          'observation_date': '2026-11-04T05:43:53Z',
          'observation_age_days': 4,
          'sensor': 'Sentinel-2 L2A',
          'product_id': 'S2B_MSIL2A_20261104',
          'canopy_ndvi': 0.68,
          'canopy_ndmi': 0.22,
          'composite_mean_ndvi': 0.52,
          'bare_soil_mean_ndvi': 0.28,
          'vegetation_coverage_percent': 68.4,
          'bare_soil_coverage_percent': 31.6,
          'cloud_masked_percent': 0.0,
          'valid_pixel_count': 250,
          'quality_status': 'VALID_OBSERVATION',
          'is_small_farm_warning': false,
          'agronomic_interpretation': 'Active photosynthetic canopy covering 68.4% of parcel.',
          'scientific_disclaimer': 'Sentinel-2 NDVI and NDMI reflect surface optical reflectance.',
        },
        'weather': {
          'availability_state': 'AVAILABLE',
          'last_updated': '2026-11-08T11:30:00Z',
          'current_weather': {
            'observation_time': '2026-11-08T11:20:00Z',
            'temperature_c': 28.4,
            'humidity_percent': 48.0,
            'precipitation_mm': 0.0,
            'wind_speed_ms': 3.1,
            'weather_condition': 'Clear',
            'weather_description': 'clear sky',
          },
          'forecast': {
            'forecast_days_count': 5,
            'next_48h_rain_expected_mm': 0.0,
            'temp_min_c': 17.5,
            'temp_max_c': 31.0,
            'weather_alerts': [],
          },
          'climate_normals': {
            'annual_rainfall_mm': 560.0,
            'monsoon_rainfall_mm': 440.0,
            'mean_temperature_c': 24.5,
            'potential_water_stress_indicator': 'Moderate seasonal winter dry spell',
          },
        },
        'crop_context': {
          'availability_state': 'AVAILABLE',
          'evaluated_at': '2026-11-08T10:00:00Z',
          'target_season': 'Rabi 2026-27',
          'taluka_resolved': 'Baramati',
          'evaluated_crops_count': 10,
          'suitable_crops': [
            {
              'crop_id': 'wheat',
              'common_name': 'Wheat',
              'marathi_name': 'गहू',
              'decision_state': 'VERIFIED_SUITABLE',
              'limiting_factors': [],
              'irrigation_guidance': 'Crown root initiation irrigation critical at 21 DAS.',
            }
          ],
          'conditionally_suitable_crops': [],
          'disqualified_crops': [],
          'abstain_crops': [],
          'top_limiting_factors': [],
          'pending_followup_questions_count': 0,
        },
        'governance_notice': 'CropNet AI provides independent, evidence-gated agricultural domain summaries. No universal health score is computed.',
      };

      final snapshot = FarmHealthSnapshotResponse.fromJson(json);

      expect(snapshot.farmName, 'Baramati Model Farm');
      expect(snapshot.calculatedAreaHectares, 2.5);
      expect(snapshot.overallEvidenceOverview.domainsAvailable, 5);
      expect(snapshot.overallEvidenceOverview.domainsNotAvailable, 0);
      expect(snapshot.soil.availabilityState, DataAvailabilityState.available);
      expect(snapshot.soil.keyIndicators.soilPh, 7.6);
      expect(snapshot.water.availabilityState, DataAvailabilityState.available);
      expect(snapshot.water.keyIndicators.sar, 3.01);
      expect(snapshot.satellite.canopyNdvi, 0.68);
      expect(snapshot.weather.currentWeather.temperatureC, 28.4);
      expect(snapshot.cropContext.suitableCrops.first.commonName, 'Wheat');

      // Verify timeline items generation
      final timeline = snapshot.buildTimelineItems();
      expect(timeline.isNotEmpty, isTrue);
      expect(timeline.first.timestamp.isAfter(timeline.last.timestamp) || timeline.first.timestamp == timeline.last.timestamp, isTrue);
    });

    test('Example B: Missing Evidence Farm (New Parcel) safely handles nulls without default numbers', () {
      final json = {
        'contract_version': '1.0',
        'farm_id': 'e4b2d189-9a74-4b5c-897b-3d6e5c9f1a23',
        'farm_name': 'New Registered Parcel',
        'owner_id': '00000000-0000-0000-0000-000000000001',
        'taluka': 'Indapur',
        'district': 'Pune',
        'state': 'Maharashtra',
        'calculated_area_hectares': 1.2,
        'calculated_area_acres': 2.97,
        'snapshot_timestamp': '2026-11-08T11:45:00Z',
        'overall_evidence_overview': {
          'domains_available': 0,
          'domains_partially_available': 0,
          'domains_stale': 0,
          'domains_not_available': 5,
          'domains_insufficient_evidence': 0,
          'total_domains': 5,
          'actionable_summary': 'Zero evidence recorded for this farm.',
        },
        'soil': {
          'availability_state': 'NOT_AVAILABLE',
          'last_updated': null,
          'data_age_days': null,
          'provenance': null,
          'laboratory_name': null,
          'sample_depth': null,
          'key_indicators': {
            'soil_ph': null,
            'organic_carbon_pct': null,
            'electrical_conductivity_ds_m': null,
            'available_nitrogen_kg_ha': null,
            'available_phosphorus_kg_ha': null,
            'available_potassium_kg_ha': null,
            'soil_texture': null,
            'cation_exchange_capacity': null,
          },
          'missing_critical_parameters': ['soil_ph', 'organic_carbon', 'nitrogen'],
          'agronomic_notes': ['No soil profile has been generated or uploaded.'],
        },
        'water': {
          'availability_state': 'NOT_AVAILABLE',
          'last_updated': null,
          'data_age_days': null,
          'registered_sources_count': 0,
          'sources': [],
          'laboratory_name': null,
          'key_indicators': {
            'ph': null,
            'electrical_conductivity_ds_m': null,
            'sar': null,
            'sar_status': 'UNAVAILABLE',
            'rsc_meq_l': null,
            'rsc_status': 'UNAVAILABLE',
          },
          'institutional_evaluations': [],
          'missing_critical_parameters': ['water_source', 'electrical_conductivity'],
        },
        'satellite': {
          'availability_state': 'NOT_AVAILABLE',
          'observation_date': null,
          'canopy_ndvi': null,
          'canopy_ndmi': null,
          'valid_pixel_count': 0,
        },
        'weather': {
          'availability_state': 'NOT_AVAILABLE',
          'last_updated': null,
          'current_weather': {},
          'forecast': {},
          'climate_normals': {},
        },
        'crop_context': {
          'availability_state': 'NOT_AVAILABLE',
          'evaluated_crops_count': 0,
          'suitable_crops': [],
        },
      };

      final snapshot = FarmHealthSnapshotResponse.fromJson(json);

      expect(snapshot.overallEvidenceOverview.domainsNotAvailable, 5);
      expect(snapshot.soil.availabilityState, DataAvailabilityState.notAvailable);
      expect(snapshot.soil.keyIndicators.soilPh, isNull);
      expect(snapshot.water.availabilityState, DataAvailabilityState.notAvailable);
      expect(snapshot.water.keyIndicators.sar, isNull);
      expect(snapshot.satellite.canopyNdvi, isNull);
      expect(snapshot.satellite.validPixelCount, 0);
      expect(snapshot.cropContext.suitableCrops, isEmpty);
    });

    test('Example C: Stale Evidence Farm marks STALE status and reports ages', () {
      final json = {
        'contract_version': '1.0',
        'farm_id': 'c8d2e3f4-5678-4abc-9def-0123456789ab',
        'farm_name': 'Sangamner Pomegranate Orchard',
        'owner_id': '00000000-0000-0000-0000-000000000001',
        'taluka': 'Sangamner',
        'district': 'Ahmednagar',
        'state': 'Maharashtra',
        'calculated_area_hectares': 3.1,
        'calculated_area_acres': 7.66,
        'snapshot_timestamp': '2026-11-08T11:45:00Z',
        'overall_evidence_overview': {
          'domains_available': 0,
          'domains_partially_available': 0,
          'domains_stale': 5,
          'domains_not_available': 0,
          'domains_insufficient_evidence': 0,
          'total_domains': 5,
          'actionable_summary': 'All recorded farm evidence is stale.',
        },
        'soil': {
          'availability_state': 'STALE',
          'last_updated': '2022-08-10T10:00:00Z',
          'data_age_days': 1551,
          'key_indicators': {'soil_ph': 8.1},
        },
        'water': {
          'availability_state': 'STALE',
          'last_updated': '2025-06-15T11:30:00Z',
          'data_age_days': 511,
          'registered_sources_count': 1,
          'key_indicators': {'electrical_conductivity_ds_m': 2.2},
        },
        'satellite': {
          'availability_state': 'STALE',
          'observation_date': '2026-09-12T05:40:02Z',
          'observation_age_days': 57,
          'canopy_ndvi': 0.44,
        },
        'weather': {
          'availability_state': 'STALE',
          'last_updated': '2026-11-08T06:00:00Z',
        },
        'crop_context': {
          'availability_state': 'STALE',
          'evaluated_at': '2025-07-01T08:00:00Z',
          'suitable_crops': [],
        },
      };

      final snapshot = FarmHealthSnapshotResponse.fromJson(json);

      expect(snapshot.overallEvidenceOverview.domainsStale, 5);
      expect(snapshot.soil.availabilityState, DataAvailabilityState.stale);
      expect(snapshot.soil.dataAgeDays, 1551);
      expect(snapshot.water.availabilityState, DataAvailabilityState.stale);
      expect(snapshot.water.dataAgeDays, 511);
      expect(snapshot.satellite.availabilityState, DataAvailabilityState.stale);
      expect(snapshot.satellite.observationAgeDays, 57);
    });
  });

  group('FarmHealthRepository Tests', () {
    test('fetches health snapshot successfully on HTTP 200', () async {
      final mockData = {
        'contract_version': '1.0',
        'farm_id': 'farm-123',
        'farm_name': 'Baramati Agro Farm',
        'owner_id': 'user-1',
        'taluka': 'Baramati',
        'district': 'Pune',
        'state': 'Maharashtra',
        'calculated_area_hectares': 2.0,
        'calculated_area_acres': 4.94,
        'snapshot_timestamp': '2026-11-08T11:45:00Z',
        'overall_evidence_overview': {
          'domains_available': 5,
          'domains_partially_available': 0,
          'domains_stale': 0,
          'domains_not_available': 0,
          'domains_insufficient_evidence': 0,
          'total_domains': 5,
          'actionable_summary': 'All evidence available.',
        },
        'soil': {'availability_state': 'AVAILABLE', 'key_indicators': {'soil_ph': 7.4}},
        'water': {'availability_state': 'AVAILABLE', 'registered_sources_count': 1, 'key_indicators': {'ph': 7.5}},
        'satellite': {'availability_state': 'AVAILABLE', 'canopy_ndvi': 0.65},
        'weather': {'availability_state': 'AVAILABLE', 'current_weather': {'temperature_c': 28.0}},
        'crop_context': {'availability_state': 'AVAILABLE', 'evaluated_crops_count': 5},
      };

      final mockClient = MockClient((request) async {
        expect(request.url.path, '/api/v1/farms/farm-123/health-snapshot');
        return http.Response(jsonEncode(mockData), 200, headers: {'content-type': 'application/json'});
      });

      final apiClient = ApiClient(httpClient: mockClient);
      final repo = FarmHealthRepository(client: apiClient);

      final snapshot = await repo.getFarmHealthSnapshot('farm-123');
      expect(snapshot.farmName, 'Baramati Agro Farm');
      expect(snapshot.soil.keyIndicators.soilPh, 7.4);
    });

    test('propagates force_refresh and target_season query parameters', () async {
      final mockClient = MockClient((request) async {
        expect(request.url.queryParameters['force_refresh'], 'true');
        expect(request.url.queryParameters['target_season'], 'Rabi 2026-27');

        final mockData = {
          'farm_id': 'farm-123',
          'farm_name': 'Test Farm',
          'owner_id': 'user-1',
          'taluka': 'Baramati',
          'district': 'Pune',
          'state': 'Maharashtra',
          'calculated_area_hectares': 1.0,
          'calculated_area_acres': 2.47,
          'snapshot_timestamp': '2026-11-08T11:45:00Z',
          'overall_evidence_overview': {
            'domains_available': 5,
            'domains_partially_available': 0,
            'domains_stale': 0,
            'domains_not_available': 0,
            'domains_insufficient_evidence': 0,
            'total_domains': 5,
            'actionable_summary': 'Refreshed.',
          },
          'soil': {'availability_state': 'AVAILABLE'},
          'water': {'availability_state': 'AVAILABLE'},
          'satellite': {'availability_state': 'AVAILABLE'},
          'weather': {'availability_state': 'AVAILABLE'},
          'crop_context': {'availability_state': 'AVAILABLE'},
        };
        return http.Response(jsonEncode(mockData), 200, headers: {'content-type': 'application/json'});
      });

      final apiClient = ApiClient(httpClient: mockClient);
      final repo = FarmHealthRepository(client: apiClient);

      final snapshot = await repo.getFarmHealthSnapshot(
        'farm-123',
        forceRefresh: true,
        targetSeason: 'Rabi 2026-27',
      );
      expect(snapshot.farmName, 'Test Farm');
    });

    test('throws ForbiddenException on HTTP 403 unauthorized access', () async {
      final mockClient = MockClient((request) async {
        return http.Response(
          jsonEncode({'detail': 'You do not have permission to access this farm'}),
          403,
          headers: {'content-type': 'application/json'},
        );
      });

      final apiClient = ApiClient(httpClient: mockClient);
      final repo = FarmHealthRepository(client: apiClient);

      expect(
        () => repo.getFarmHealthSnapshot('farm-other-user'),
        throwsA(isA<ForbiddenException>()),
      );
    });

    test('throws NotFoundException on HTTP 404 missing farm', () async {
      final mockClient = MockClient((request) async {
        return http.Response(
          jsonEncode({'detail': 'Farm farm-999 not found'}),
          404,
          headers: {'content-type': 'application/json'},
        );
      });

      final apiClient = ApiClient(httpClient: mockClient);
      final repo = FarmHealthRepository(client: apiClient);

      expect(
        () => repo.getFarmHealthSnapshot('farm-999'),
        throwsA(isA<NotFoundException>()),
      );
    });
  });
}
