import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:latlong2/latlong.dart';

import 'package:cropnet_mobile/core/network/api_client.dart';
import 'package:cropnet_mobile/core/router/farm_resolution.dart';
import 'package:cropnet_mobile/core/router/farm_state.dart';
import 'package:cropnet_mobile/features/farm/data/farm_repository.dart' as data;
import 'package:cropnet_mobile/main.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  FarmItem buildTestFarm({String id = 'farm-101', String name = 'Baramati KVK Test Farm'}) {
    return FarmItem(
      id: id,
      name: name,
      taluka: 'Baramati',
      district: 'Pune',
      irrigationType: 'irrigated',
      waterSource: 'canal',
      polygonPoints: [
        const LatLng(18.18, 74.53),
        const LatLng(18.19, 74.53),
        const LatLng(18.19, 74.54),
        const LatLng(18.18, 74.54),
      ],
      areaHectares: 4.5,
      areaAcres: 11.1,
      centroid: const LatLng(18.185, 74.535),
      createdAt: DateTime.now(),
    );
  }

  Map<String, dynamic> buildRawFarmJson({String id = 'farm-101', String name = 'Baramati KVK Test Farm'}) {
    return {
      'id': id,
      'owner_id': '00000000-0000-0000-0000-000000000001',
      'name': name,
      'taluka': 'Baramati',
      'district': 'Pune',
      'state': 'Maharashtra',
      'irrigation_type': 'irrigated',
      'water_source': 'canal',
      'calculated_area_hectares': 4.5,
      'calculated_area_acres': 11.1,
      'centroid_latitude': 18.185,
      'centroid_longitude': 74.535,
      'latitude': 18.185,
      'longitude': 74.535,
      'geometry': {
        'type': 'Polygon',
        'coordinates': [
          [
            [74.53, 18.18],
            [74.53, 18.19],
            [74.54, 18.19],
            [74.54, 18.18],
            [74.53, 18.18],
          ]
        ]
      },
      'created_at': DateTime.now().toIso8601String(),
      'updated_at': DateTime.now().toIso8601String(),
    };
  }

  group('FarmRouteResolver Widget & Async Resolution Tests', () {
    testWidgets('Renders child immediately when farm already in memory', (tester) async {
      final repo = FarmRepository.instance;
      repo.resetToDefault();
      final localFarm = buildTestFarm(id: 'farm-local-1', name: 'Memory Farm');
      repo.addFarm(localFarm);

      await tester.pumpWidget(
        MaterialApp(
          home: FarmRouteResolver(
            farmId: 'farm-local-1',
            featureName: 'Soil Intelligence',
            builder: (context, farm) => Text('Resolved Farm: ${farm.name}'),
          ),
        ),
      );

      expect(find.text('Resolved Farm: Memory Farm'), findsOneWidget);
      expect(find.byType(CircularProgressIndicator), findsNothing);
    });

    testWidgets('Asynchronously fetches missing farm from backend API and renders child', (tester) async {
      final mockClient = MockClient((request) async {
        if (request.url.path == '/api/v1/farms/farm-remote-2') {
          return http.Response(
            jsonEncode(buildRawFarmJson(id: 'farm-remote-2', name: 'Remote Fetched Farm')),
            200,
            headers: {'content-type': 'application/json'},
          );
        }
        return http.Response('{"detail":"Not found"}', 404);
      });

      final apiClient = ApiClient(httpClient: mockClient);
      final dataRepo = data.FarmRepository(client: apiClient);
      FarmRepository.instance.resetToDefault(dataRepo: dataRepo);

      await tester.pumpWidget(
        MaterialApp(
          home: FarmRouteResolver(
            farmId: 'farm-remote-2',
            featureName: 'Soil Intelligence',
            builder: (context, farm) => Text('Resolved Farm: ${farm.name}'),
          ),
        ),
      );

      // Loading state shown initially
      expect(find.text('Resolving soil intelligence details...'), findsOneWidget);

      await tester.pumpAndSettle();

      // Successfully resolved and rendered child
      expect(find.text('Resolved Farm: Remote Fetched Farm'), findsOneWidget);
      expect(FarmRepository.instance.getFarmById('farm-remote-2'), isNotNull);
    });

    testWidgets('Shows dedicated Farm No Longer Available screen when API returns 404', (tester) async {
      final mockClient = MockClient((request) async {
        return http.Response(jsonEncode({'detail': 'Farm not found'}), 404, headers: {'content-type': 'application/json'});
      });

      final apiClient = ApiClient(httpClient: mockClient);
      final dataRepo = data.FarmRepository(client: apiClient);
      FarmRepository.instance.resetToDefault(dataRepo: dataRepo);

      await tester.pumpWidget(
        const MaterialApp(
          home: FarmRouteResolver(
            farmId: '472a042d-deleted-farm',
            featureName: 'Soil Intelligence',
            builder: _dummyBuilder,
          ),
        ),
      );

      await tester.pumpAndSettle();

      expect(find.text('Farm No Longer Available'), findsOneWidget);
      expect(find.text('Return to Dashboard'), findsOneWidget);
      expect(find.text('Select Another Farm'), findsOneWidget);
      expect(find.text('Resolved Farm'), findsNothing);
    });

    testWidgets('Shows Access Restricted screen when API returns 403 Forbidden', (tester) async {
      final mockClient = MockClient((request) async {
        return http.Response(jsonEncode({'detail': 'You do not have permission to access this farm'}), 403, headers: {'content-type': 'application/json'});
      });

      final apiClient = ApiClient(httpClient: mockClient);
      final dataRepo = data.FarmRepository(client: apiClient);
      FarmRepository.instance.resetToDefault(dataRepo: dataRepo);

      await tester.pumpWidget(
        const MaterialApp(
          home: FarmRouteResolver(
            farmId: 'farm-other-user',
            featureName: 'Soil Intelligence',
            builder: _dummyBuilder,
          ),
        ),
      );

      await tester.pumpAndSettle();

      expect(find.text('Access Restricted'), findsOneWidget);
      expect(find.text('Return to My Farms'), findsOneWidget);
      expect(find.byIcon(Icons.lock_outline), findsOneWidget);
    });

    testWidgets('Shows Connection Error screen with Retry when network failure occurs', (tester) async {
      final mockClient = MockClient((request) async {
        throw http.ClientException('Connection refused');
      });

      final apiClient = ApiClient(httpClient: mockClient);
      final dataRepo = data.FarmRepository(client: apiClient);
      FarmRepository.instance.resetToDefault(dataRepo: dataRepo);

      await tester.pumpWidget(
        const MaterialApp(
          home: FarmRouteResolver(
            farmId: 'farm-net-fail',
            featureName: 'Soil Intelligence',
            builder: _dummyBuilder,
          ),
        ),
      );

      await tester.pumpAndSettle();

      expect(find.text('Unable to Connect to CropNet'), findsOneWidget);
      expect(find.text('Retry Connection'), findsOneWidget);
      expect(find.text('Go to Dashboard'), findsOneWidget);
    });
  });
}

Widget _dummyBuilder(BuildContext context, FarmItem farm) {
  return Text('Resolved Farm: ${farm.name}');
}
