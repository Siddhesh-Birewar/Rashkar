import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:latlong2/latlong.dart';
import 'package:cropnet_mobile/core/router/app_router.dart';
import 'package:cropnet_mobile/core/router/farm_state.dart';
import 'package:cropnet_mobile/core/router/route_names.dart';
import 'package:cropnet_mobile/core/router/route_paths.dart';
import 'package:cropnet_mobile/main.dart';

void main() {
  setUp(() {
    FarmRepository.instance.resetToDefault();
  });

  void setDesktopViewport(WidgetTester tester) {
    tester.view.physicalSize = const Size(1280, 900);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
  }

  group('Route Paths & Name Constants Verification', () {
    test('Mandatory route paths are correctly structured', () {
      expect(RoutePaths.home, '/');
      expect(RoutePaths.soilTesting, '/soil-testing');
      expect(RoutePaths.cropRecommendation, '/crop-recommendation');
      expect(RoutePaths.weather, '/weather');
      expect(RoutePaths.advisory, '/advisory');
      expect(RoutePaths.history, '/history');
    });

    test('Detail and sub-route parameter paths helper methods work as expected', () {
      expect(RoutePaths.farmDetailPath('farm-123'), '/farms/farm-123');
      expect(RoutePaths.soilDetailPath('farm-123'), '/soil-testing/farm-123');
      expect(RoutePaths.weatherDetailPath('farm-123'), '/weather/farm-123');
      expect(RoutePaths.cropDetailPath('crop-sugarcane'), '/crop-recommendation/crop-sugarcane');
    });

    test('Route names are distinctly defined', () {
      final names = [
        RouteNames.home,
        RouteNames.soilTesting,
        RouteNames.cropRecommendation,
        RouteNames.weather,
        RouteNames.advisory,
        RouteNames.history,
        RouteNames.farmNew,
        RouteNames.farmDetail,
        RouteNames.soilDetail,
        RouteNames.weatherDetail,
        RouteNames.cropDetail,
        RouteNames.about,
      ];
      final uniqueNames = names.toSet();
      expect(uniqueNames.length, names.length);
    });
  });

  group('FarmRepository Reactive State Tests', () {
    test('Default demo farm is initialized', () {
      final repo = FarmRepository.instance;
      expect(repo.farms.isNotEmpty, true);
      final demoFarm = repo.getFarmById('demo-baramati-1');
      expect(demoFarm, isNotNull);
      expect(demoFarm!.name, 'Baramati Pilot Plot');
      expect(demoFarm.taluka, 'Baramati');
    });

    test('Adding and deleting farms updates state reactively', () {
      final repo = FarmRepository.instance;
      final initialCount = repo.farms.length;

      final newFarm = FarmItem(
        id: 'test-farm-indapur',
        name: 'Indapur Test Plot',
        taluka: 'Indapur',
        polygonPoints: [
          const LatLng(18.11, 75.01),
          const LatLng(18.11, 75.02),
          const LatLng(18.12, 75.02),
        ],
        areaHectares: 5.5,
        areaAcres: 13.59,
        centroid: const LatLng(18.113, 75.016),
        createdAt: DateTime.now(),
      );

      bool listenerNotified = false;
      void listener() => listenerNotified = true;
      repo.addListener(listener);

      repo.addFarm(newFarm);
      expect(repo.farms.length, initialCount + 1);
      expect(repo.getFarmById('test-farm-indapur'), isNotNull);
      expect(listenerNotified, true);

      listenerNotified = false;
      repo.deleteFarm('test-farm-indapur');
      expect(repo.farms.length, initialCount);
      expect(repo.getFarmById('test-farm-indapur'), isNull);
      expect(listenerNotified, true);

      repo.removeListener(listener);
    });
  });

  group('GoRouter Deep Linking & Widget Integration Tests', () {
    testWidgets('Renders Dashboard at initial / route', (tester) async {
      setDesktopViewport(tester);
      final router = createCropNetRouter(initialLocation: RoutePaths.home);
      await tester.pumpWidget(CropNetApp(routerConfig: router));
      await tester.pumpAndSettle();

      expect(find.text('My Registered Farms'), findsOneWidget);
      expect(find.text('Baramati Pilot Plot'), findsOneWidget);
    });

    testWidgets('Deep links directly to /soil-testing without crashing', (tester) async {
      setDesktopViewport(tester);
      final router = createCropNetRouter(initialLocation: RoutePaths.soilTesting);
      await tester.pumpWidget(CropNetApp(routerConfig: router));
      await tester.pumpAndSettle();

      expect(find.text('Soil Intelligence'), findsOneWidget);
      expect(find.textContaining('Map-Derived Estimates: Values are derived from digital geospatial soil models'), findsOneWidget);
      expect(find.text('Baramati Pilot Plot'), findsOneWidget);
    });

    testWidgets('Deep links directly to /crop-recommendation', (tester) async {
      setDesktopViewport(tester);
      final router = createCropNetRouter(initialLocation: RoutePaths.cropRecommendation);
      await tester.pumpWidget(CropNetApp(routerConfig: router));
      await tester.pumpAndSettle();

      expect(find.text('Crop Knowledge Base'), findsOneWidget);
      expect(find.text('Sugarcane'), findsAtLeastNWidgets(1));
    });

    testWidgets('Deep links directly to /weather', (tester) async {
      setDesktopViewport(tester);
      final router = createCropNetRouter(initialLocation: RoutePaths.weather);
      await tester.pumpWidget(CropNetApp(routerConfig: router));
      await tester.pumpAndSettle();

      expect(find.text('Weather & Climate Intelligence'), findsOneWidget);
      expect(find.text('Baramati Pilot Plot'), findsOneWidget);
    });

    testWidgets('Deep links directly to /advisory with Qwen dialogue guardrails', (tester) async {
      setDesktopViewport(tester);
      final router = createCropNetRouter(initialLocation: RoutePaths.advisory);
      await tester.pumpWidget(CropNetApp(routerConfig: router));
      await tester.pumpAndSettle();

      expect(find.text('AI Dialogue & Advisory'), findsOneWidget);
      expect(find.textContaining('Qwen3:8B Agronomic Dialogue'), findsOneWidget);
      expect(find.textContaining('Namaste! Welcome to CropNet AI Agronomic Advisory'), findsOneWidget);
    });

    testWidgets('Deep links directly to /history', (tester) async {
      setDesktopViewport(tester);
      final router = createCropNetRouter(initialLocation: RoutePaths.history);
      await tester.pumpWidget(CropNetApp(routerConfig: router));
      await tester.pumpAndSettle();

      expect(find.text('Assessment History'), findsOneWidget);
      expect(find.text('Total Runs'), findsOneWidget);
      expect(find.text('Soil Profiles'), findsOneWidget);
      expect(find.textContaining('Baramati Pilot Plot (Baramati)'), findsAtLeastNWidgets(1));
    });

    testWidgets('Deep links to farm soil intelligence sub-route /soil-testing/demo-baramati-1', (tester) async {
      setDesktopViewport(tester);
      final router = createCropNetRouter(initialLocation: '/soil-testing/demo-baramati-1');
      await tester.pumpWidget(CropNetApp(routerConfig: router));
      await tester.pumpAndSettle();

      expect(find.text('Baramati Pilot Plot — Soil Intelligence'), findsOneWidget);
      expect(find.textContaining('Baramati, Pune, Maharashtra'), findsOneWidget);
      expect(find.text('Soil pH (H2O)'), findsOneWidget);
      expect(find.text('7.3 pH'), findsOneWidget);
    });

    testWidgets('Deep links to crop detail sub-route /crop-recommendation/sugarcane', (tester) async {
      setDesktopViewport(tester);
      final router = createCropNetRouter(initialLocation: '/crop-recommendation/sugarcane');
      await tester.pumpWidget(CropNetApp(routerConfig: router));
      await tester.pumpAndSettle();

      expect(find.text('Sugarcane'), findsAtLeastNWidgets(1));
      expect(find.text('Saccharum officinarum L.'), findsOneWidget);
    });

    testWidgets('Gracefully handles invalid route /invalid-unknown-url with error screen', (tester) async {
      setDesktopViewport(tester);
      final router = createCropNetRouter(initialLocation: '/invalid-unknown-url');
      await tester.pumpWidget(CropNetApp(routerConfig: router));
      await tester.pumpAndSettle();

      expect(find.text('Page Not Found — CropNet AI'), findsOneWidget);
      expect(find.text('Route or Page Not Found'), findsOneWidget);
      expect(find.text('Return to Dashboard'), findsOneWidget);

      // Tap return to dashboard
      await tester.tap(find.text('Return to Dashboard'));
      await tester.pumpAndSettle();

      expect(find.text('My Registered Farms'), findsOneWidget);
    });

    testWidgets('Gracefully handles missing farm ID in subroute /soil-testing/non-existent-farm', (tester) async {
      setDesktopViewport(tester);
      final router = createCropNetRouter(initialLocation: '/soil-testing/non-existent-farm');
      await tester.pumpWidget(CropNetApp(routerConfig: router));
      await tester.pumpAndSettle();

      expect(find.text('Route or Page Not Found'), findsOneWidget);
      expect(find.textContaining('non-existent-farm'), findsAtLeastNWidgets(1));
    });

    testWidgets('Navigation switches branches seamlessly', (tester) async {
      setDesktopViewport(tester);
      final router = createCropNetRouter(initialLocation: RoutePaths.home);
      await tester.pumpWidget(CropNetApp(routerConfig: router));
      await tester.pumpAndSettle();

      // Initially at Home
      expect(find.text('My Registered Farms'), findsOneWidget);

      // Switch to Soil branch
      await tester.tap(find.text('Soil').first);
      await tester.pumpAndSettle();
      expect(find.text('Soil Intelligence'), findsOneWidget);

      // Switch to Advisory branch
      await tester.tap(find.text('Advisory').first);
      await tester.pumpAndSettle();
      expect(find.text('AI Dialogue & Advisory'), findsOneWidget);

      // Switch to History branch
      await tester.tap(find.text('History').first);
      await tester.pumpAndSettle();
      expect(find.text('Assessment History'), findsOneWidget);

      // Switch back to Farms branch
      await tester.tap(find.text('Farms').first);
      await tester.pumpAndSettle();
      expect(find.text('My Registered Farms'), findsOneWidget);
    });
  });
}
