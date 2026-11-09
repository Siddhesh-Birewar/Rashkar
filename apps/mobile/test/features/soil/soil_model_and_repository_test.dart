import 'dart:convert';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

import 'package:cropnet_mobile/core/network/api_client.dart';
import 'package:cropnet_mobile/features/soil/data/soil_repository.dart';
import 'package:cropnet_mobile/features/soil/models/soil_models.dart';

void main() {
  group('Soil Models & Repository Tests', () {
    final sampleSoilProfileJson = {
      'profile_id': 'soil-prof-baramati-001',
      'farm_id': 'farm-baramati-001',
      'created_at': '2026-03-01T12:00:00Z',
      'version': 1,
      'taluka': 'Baramati',
      'district': 'Pune',
      'state': 'Maharashtra',
      'is_map_derived': true,
      'disclaimer':
          'This soil profile is estimated from geospatial soil models and regional maps. It is not a physical laboratory soil test.',
      'source_dataset': 'ISRIC SoilGrids 2.0',
      'dataset_version': '2.0.0',
      'spatial_resolution': '250m',
      'depth_interval': '0-5cm',
      'spatial_representativeness_warning':
          'Parcel area is 4.25 ha, which is smaller than 250m raster grid cell.',
      'soil_texture_class': 'Clay',
      'ph': {
        'parameter_key': 'ph',
        'display_name': 'Soil pH (0-5cm)',
        'value': 7.29,
        'unit': 'pH',
        'source': 'ISRIC SoilGrids 2.0',
        'dataset_version': '2.0.0',
        'depth_interval': '0-5cm',
        'spatial_resolution': '250m',
        'vintage_year': 2020,
        'uncertainty': 0.35,
        'verification_status': 'map_derived_estimate',
        'availability_status': 'available',
        'farm_coverage_percent': 100.0,
      },
      'total_nitrogen': {
        'parameter_key': 'total_nitrogen',
        'display_name': 'Total Nitrogen (0-5cm)',
        'value': 1.25,
        'unit': 'g/kg',
        'source': 'ISRIC SoilGrids 2.0',
        'dataset_version': '2.0.0',
        'depth_interval': '0-5cm',
        'spatial_resolution': '250m',
        'vintage_year': 2020,
        'verification_status': 'map_derived_estimate',
        'availability_status': 'available',
        'farm_coverage_percent': 100.0,
        'scientific_note':
            'IMPORTANT: Total Nitrogen is NOT available mineral nitrogen (NH4+/NO3-).',
      },
      'available_nitrogen': null, // Strictly unverified
      'available_phosphorus': null,
      'available_potassium': null,
      'mapped_soil_zones': [
        {
          'zone_id': 'zone-1',
          'zone_name': 'Deccan Deep Vertisol',
          'area_fraction': 1.0,
          'description': 'Montmorillonitic shrink-swell clay',
        }
      ],
      'additional_parameters': {},
      'total_requested_parameters': 11,
      'available_parameters_count': 7,
      'data_completeness_ratio': 0.636,
    };

    test('UnifiedSoilProfile deserializes correctly and enforces unverified available NPK as null', () {
      final profile = UnifiedSoilProfile.fromJson(sampleSoilProfileJson);

      expect(profile.profileId, 'soil-prof-baramati-001');
      expect(profile.taluka, 'Baramati');
      expect(profile.isMapDerived, true);
      expect(profile.soilTextureClass, 'Clay');
      expect(profile.ph?.value, 7.29);
      expect(profile.totalNitrogen?.value, 1.25);

      // Scientific Guardrail Verification
      expect(profile.availableNitrogen, isNull);
      expect(profile.availablePhosphorus, isNull);
      expect(profile.availablePotassium, isNull);
      expect(profile.mappedSoilZones.length, 1);
      expect(profile.mappedSoilZones.first.zoneName, 'Deccan Deep Vertisol');
    });

    test('SoilRepository.analyseFarmSoil calls endpoint and returns parsed profile', () async {
      final mockClient = MockClient((request) async {
        expect(request.method, 'POST');
        expect(request.url.path, '/api/v1/farms/farm-123/soil/analyse');
        return http.Response(
          jsonEncode(sampleSoilProfileJson),
          200,
          headers: {'content-type': 'application/json; charset=utf-8'},
        );
      });

      final repo = SoilRepository(client: ApiClient(httpClient: mockClient));
      final profile = await repo.analyseFarmSoil('farm-123', forceRefresh: false, depth: '0-5cm');

      expect(profile.farmId, 'farm-baramati-001');
      expect(profile.ph?.value, 7.29);
    });

    test('SoilRepository.listSoilProviders parses provider capabilities', () async {
      final mockClient = MockClient((request) async {
        expect(request.method, 'GET');
        expect(request.url.path, '/api/v1/soil/providers');
        return http.Response(
          jsonEncode([
            {
              'provider_name': 'ISRIC SoilGrids',
              'dataset_version': '2.0.0',
              'spatial_resolution_or_scale': '250m',
              'supported_depth_intervals': ['0-5cm', '5-15cm'],
              'vintage_year': 2020,
              'licensing': 'CC BY 4.0',
              'attribution_statement': 'ISRIC — World Soil Information',
              'is_operational': true,
              'status_message': 'Operational',
              'available_properties': ['ph', 'soc', 'clay_percent'],
              'provides_uncertainty': true,
              'requires_credentials': false,
            }
          ]),
          200,
          headers: {'content-type': 'application/json; charset=utf-8'},
        );
      });

      final repo = SoilRepository(client: ApiClient(httpClient: mockClient));
      final providers = await repo.listSoilProviders();

      expect(providers.length, 1);
      expect(providers.first.providerName, 'ISRIC SoilGrids');
      expect(providers.first.isOperational, true);
    });

    test('SoilRepository.listSoilLayers parses layer metadata catalogue', () async {
      final mockClient = MockClient((request) async {
        expect(request.method, 'GET');
        expect(request.url.path, '/api/v1/soil/layers');
        return http.Response(
          jsonEncode([
            {
              'parameter_key': 'ph',
              'display_name': 'Soil pH (H2O)',
              'unit': 'pH',
              'source': 'ISRIC SoilGrids 2.0',
              'dataset_version': '2.0.0',
              'spatial_resolution': '250m',
              'supported_depth_intervals': ['0-5cm', '5-15cm'],
              'is_derived': false,
              'scientific_note': 'Soil pH in H2O',
            }
          ]),
          200,
          headers: {'content-type': 'application/json; charset=utf-8'},
        );
      });

      final repo = SoilRepository(client: ApiClient(httpClient: mockClient));
      final layers = await repo.listSoilLayers();

      expect(layers.length, 1);
      expect(layers.first.parameterKey, 'ph');
      expect(layers.first.unit, 'pH');
    });
  });
}
