import 'package:cropnet_mobile/shared/widgets/responsive_scaffold.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  final testDestinations = [
    const ResponsiveScaffoldDestination(
      icon: Icon(Icons.map_outlined),
      selectedIcon: Icon(Icons.map),
      label: 'Farms',
    ),
    const ResponsiveScaffoldDestination(
      icon: Icon(Icons.terrain_outlined),
      selectedIcon: Icon(Icons.terrain),
      label: 'Soil',
    ),
    const ResponsiveScaffoldDestination(
      icon: Icon(Icons.wb_sunny_outlined),
      selectedIcon: Icon(Icons.wb_sunny),
      label: 'Weather',
    ),
  ];

  group('ResponsiveScaffold Widget Tests', () {
    testWidgets('renders bottom NavigationBar on mobile screens (< 600px)', (tester) async {
      tester.view.physicalSize = const Size(400, 800);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);

      int selectedIndex = 0;

      await tester.pumpWidget(
        MaterialApp(
          home: StatefulBuilder(
            builder: (context, setState) {
              return ResponsiveScaffold(
                currentIndex: selectedIndex,
                onNavigationIndexChanged: (idx) => setState(() => selectedIndex = idx),
                destinations: testDestinations,
                body: const Center(child: Text('Mobile Body')),
              );
            },
          ),
        ),
      );

      expect(find.byType(NavigationBar), findsOneWidget);
      expect(find.byType(NavigationRail), findsNothing);
      expect(find.text('Mobile Body'), findsOneWidget);
      expect(find.text('Farms'), findsOneWidget);
      expect(find.text('Soil'), findsOneWidget);

      // Tap 'Soil' destination
      await tester.tap(find.text('Soil'));
      await tester.pumpAndSettle();
      expect(selectedIndex, 1);
    });

    testWidgets('renders persistent side NavigationRail on tablet/desktop (>= 600px)', (tester) async {
      tester.view.physicalSize = const Size(1280, 800);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);

      int selectedIndex = 0;

      await tester.pumpWidget(
        MaterialApp(
          home: StatefulBuilder(
            builder: (context, setState) {
              return ResponsiveScaffold(
                currentIndex: selectedIndex,
                onNavigationIndexChanged: (idx) => setState(() => selectedIndex = idx),
                destinations: testDestinations,
                railLeading: const Text('CropNet Logo'),
                railTrailing: const Text('User Profile'),
                body: const Center(child: Text('Desktop Body')),
              );
            },
          ),
        ),
      );

      expect(find.byType(NavigationRail), findsOneWidget);
      expect(find.byType(NavigationBar), findsNothing);
      expect(find.text('Desktop Body'), findsOneWidget);
      expect(find.text('CropNet Logo'), findsOneWidget);
      expect(find.text('User Profile'), findsOneWidget);

      // Tap 'Weather' destination
      await tester.tap(find.text('Weather'));
      await tester.pumpAndSettle();
      expect(selectedIndex, 2);
    });

    testWidgets('respects explicit railExtended override', (tester) async {
      tester.view.physicalSize = const Size(1400, 900);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);

      await tester.pumpWidget(
        MaterialApp(
          home: ResponsiveScaffold(
            currentIndex: 0,
            railExtended: false,
            destinations: testDestinations,
            body: const Text('Content'),
          ),
        ),
      );

      final rail = tester.widget<NavigationRail>(find.byType(NavigationRail));
      expect(rail.extended, isFalse);
    });
  });
}
