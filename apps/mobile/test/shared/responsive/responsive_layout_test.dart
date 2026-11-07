import 'package:cropnet_mobile/shared/responsive/responsive_layout.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('ResponsiveLayout Widget Tests', () {
    testWidgets('renders mobile builder when screen width < 600', (tester) async {
      tester.view.physicalSize = const Size(400, 800);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);

      await tester.pumpWidget(
        MaterialApp(
          home: ResponsiveLayout(
            mobile: (context, constraints) => const Text('Mobile Content'),
            tablet: (context, constraints) => const Text('Tablet Content'),
            desktop: (context, constraints) => const Text('Desktop Content'),
          ),
        ),
      );

      expect(find.text('Mobile Content'), findsOneWidget);
      expect(find.text('Tablet Content'), findsNothing);
      expect(find.text('Desktop Content'), findsNothing);
    });

    testWidgets('renders tablet builder when screen width is 600 - 1024', (tester) async {
      tester.view.physicalSize = const Size(768, 1024);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);

      await tester.pumpWidget(
        MaterialApp(
          home: ResponsiveLayout(
            mobile: (context, constraints) => const Text('Mobile Content'),
            tablet: (context, constraints) => const Text('Tablet Content'),
            desktop: (context, constraints) => const Text('Desktop Content'),
          ),
        ),
      );

      expect(find.text('Mobile Content'), findsNothing);
      expect(find.text('Tablet Content'), findsOneWidget);
      expect(find.text('Desktop Content'), findsNothing);
    });

    testWidgets('renders desktop builder when screen width > 1024', (tester) async {
      tester.view.physicalSize = const Size(1280, 800);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);

      await tester.pumpWidget(
        MaterialApp(
          home: ResponsiveLayout(
            mobile: (context, constraints) => const Text('Mobile Content'),
            tablet: (context, constraints) => const Text('Tablet Content'),
            desktop: (context, constraints) => const Text('Desktop Content'),
          ),
        ),
      );

      expect(find.text('Mobile Content'), findsNothing);
      expect(find.text('Tablet Content'), findsNothing);
      expect(find.text('Desktop Content'), findsOneWidget);
    });

    testWidgets('falls back to mobile on tablet when tablet is not provided', (tester) async {
      tester.view.physicalSize = const Size(768, 1024);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);

      await tester.pumpWidget(
        MaterialApp(
          home: ResponsiveLayout(
            mobile: (context, constraints) => const Text('Fallback Mobile Content'),
            desktop: (context, constraints) => const Text('Desktop Content'),
          ),
        ),
      );

      expect(find.text('Fallback Mobile Content'), findsOneWidget);
      expect(find.text('Desktop Content'), findsNothing);
    });

    testWidgets('falls back to tablet on desktop when desktop is not provided', (tester) async {
      tester.view.physicalSize = const Size(1440, 900);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);

      await tester.pumpWidget(
        MaterialApp(
          home: ResponsiveLayout(
            mobile: (context, constraints) => const Text('Mobile Content'),
            tablet: (context, constraints) => const Text('Fallback Tablet Content'),
          ),
        ),
      );

      expect(find.text('Fallback Tablet Content'), findsOneWidget);
      expect(find.text('Mobile Content'), findsNothing);
    });

    testWidgets('ResponsiveLayout.value constructor renders widgets directly', (tester) async {
      tester.view.physicalSize = const Size(400, 800);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);

      await tester.pumpWidget(
        MaterialApp(
          home: ResponsiveLayout.value(
            mobile: const Text('Value Mobile'),
            desktop: const Text('Value Desktop'),
          ),
        ),
      );

      expect(find.text('Value Mobile'), findsOneWidget);
      expect(find.text('Value Desktop'), findsNothing);
    });

    testWidgets('ResponsiveLayout with useConstraints evaluates local width', (tester) async {
      tester.view.physicalSize = const Size(1280, 800); // Desktop screen
      tester.view.devicePixelRatio = 1.0;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);

      await tester.pumpWidget(
        MaterialApp(
          home: Center(
            child: SizedBox(
              width: 500, // Constrained to mobile width
              child: ResponsiveLayout(
                useConstraints: true,
                mobile: (context, constraints) => const Text('Local Mobile'),
                desktop: (context, constraints) => const Text('Local Desktop'),
              ),
            ),
          ),
        ),
      );

      expect(find.text('Local Mobile'), findsOneWidget);
      expect(find.text('Local Desktop'), findsNothing);
    });
  });

  group('ResponsiveBuilder Widget Tests', () {
    testWidgets('provides complete ResponsiveSizingInformation to builder', (tester) async {
      tester.view.physicalSize = const Size(800, 600);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);

      late ResponsiveSizingInformation capturedInfo;

      await tester.pumpWidget(
        MaterialApp(
          home: ResponsiveBuilder(
            builder: (context, sizingInfo) {
              capturedInfo = sizingInfo;
              return Text('Breakpoint: ${sizingInfo.breakpoint.name}');
            },
          ),
        ),
      );

      expect(find.text('Breakpoint: tablet'), findsOneWidget);
      expect(capturedInfo.isMobile, isFalse);
      expect(capturedInfo.isTablet, isTrue);
      expect(capturedInfo.isDesktop, isFalse);
      expect(capturedInfo.screenSize.width, 800.0);
      expect(capturedInfo.screenSize.height, 600.0);
    });
  });
}
