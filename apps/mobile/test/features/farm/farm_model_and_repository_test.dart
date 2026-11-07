import 'dart:convert';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

import 'package:cropnet_mobile/core/network/api_client.dart';
import 'package:cropnet_mobile/features/farm/data/farm_repository.dart';
import 'package:cropnet_mobile/features/farm/models/farm_models.dart';

void main() {
  group('Farm Models & Repository Tests', () {
    const samplePolygon = GeoJsonPolygon(
      type: 'Polygon',
      coordinates: [
        [
          [74.52, 18.17],
          [74.54, 18.17],
          [74.54, 18.19],
          [74.52, 18.19],
          [74.52, 18.17],
        ]
      ],
    );

    final sampleFarmJson = {
      'id': 'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
      'owner_id': '00000000-0000-0000-0000-000000000001',
      'name': 'Baramati Test Plot A',
      'village': 'Malegaon Khurd',
      'taluka': 'Baramati',
      'district': 'Pune',
      'state': 'Maharashtra',
      'irrigation_type': 'irrigated',
      'water_source': 'well',
      'geometry': samplePolygon.toJson(),
      'calculated_area_hectares': 4.25,
      'calculated_area_acres': 10.5,
      'centroid_latitude': 18.18,
      'centroid_longitude': 74.53,
      'latitude': 18.18,
      'longitude': 74.53,
      'created_at': '2026-03-01T10:00:00Z',
      'updated_at': '2026-03-01T10:00:00Z',
    };

    test('Farm model serializes and deserializes accurately matching FastAPI schema', () {
      final farm = Farm.fromJson(sampleFarmJson);

      expect(farm.id, 'a1b2c3d4-e5f6-7890-abcd-ef1234567890');
      expect(farm.name, 'Baramati Test Plot A');
      expect(farm.taluka, 'Baramati');
      expect(farm.calculatedAreaHectares, 4.25);
      expect(farm.centroidLatitude, 18.18);
      expect(farm.geometry.coordinates.first.length, 5);

      final serialized = farm.toJson();
      expect(serialized['id'], farm.id);
      expect(serialized['taluka'], 'Baramati');
      expect(serialized['calculated_area_hectares'], 4.25);
    });

    test('FarmCreate serialization produces valid GeoJSON polygon payload', () {
      const create = FarmCreate(
        name: 'New Farm',
        taluka: 'Indapur',
        geometry: samplePolygon,
      );

      final json = create.toJson();
      expect(json['name'], 'New Farm');
      expect(json['taluka'], 'Indapur');
      expect(json['geometry']['type'], 'Polygon');
      expect(json['geometry']['coordinates'], isNotEmpty);
    });

    test('FarmRepository.createFarm sends POST and deserializes Farm response', () async {
      final mockClient = MockClient((request) async {
        expect(request.method, 'POST');
        expect(request.url.path, '/api/v1/farms');
        return http.Response(jsonEncode(sampleFarmJson), 201);
      });

      final repo = FarmRepository(client: ApiClient(httpClient: mockClient));
      final farm = await repo.createFarm(const FarmCreate(
        name: 'Baramati Test Plot A',
        taluka: 'Baramati',
        geometry: samplePolygon,
      ));

      expect(farm.id, 'a1b2c3d4-e5f6-7890-abcd-ef1234567890');
      expect(farm.taluka, 'Baramati');
    });

    test('FarmRepository.listFarms retrieves user farms list', () async {
      final mockClient = MockClient((request) async {
        expect(request.method, 'GET');
        expect(request.url.path, '/api/v1/farms');
        return http.Response(jsonEncode([sampleFarmJson]), 200);
      });

      final repo = FarmRepository(client: ApiClient(httpClient: mockClient));
      final farms = await repo.listFarms();

      expect(farms.length, 1);
      expect(farms.first.name, 'Baramati Test Plot A');
    });

    test('FarmRepository.deleteFarm sends DELETE request cleanly', () async {
      final mockClient = MockClient((request) async {
        expect(request.method, 'DELETE');
        expect(request.url.path, '/api/v1/farms/a1b2c3d4-e5f6-7890-abcd-ef1234567890');
        return http.Response('', 204);
      });

      final repo = FarmRepository(client: ApiClient(httpClient: mockClient));
      await repo.deleteFarm('a1b2c3d4-e5f6-7890-abcd-ef1234567890');
    });
  });
}
