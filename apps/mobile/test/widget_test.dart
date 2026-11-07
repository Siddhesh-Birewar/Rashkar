import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:cropnet_mobile/main.dart';

void main() {
  testWidgets('CropNet AI app shell navigates to Soil Intelligence report correctly', (WidgetTester tester) async {
    tester.view.physicalSize = const Size(1280, 900);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    // 1. Pump the app shell
    await tester.pumpWidget(const CropNetApp());
    await tester.pumpAndSettle();

    // Verify My Registered Farms dashboard on initial load
    expect(find.text('My Registered Farms'), findsOneWidget);
    expect(find.text('Baramati Pilot Plot'), findsOneWidget);
    expect(find.text('Soil'), findsOneWidget);

    // 2. Switch to Soil tab
    await tester.tap(find.text('Soil'));
    await tester.pumpAndSettle();

    // Verify Soil Intelligence Screen
    expect(find.text('Soil Intelligence'), findsOneWidget);
    expect(find.textContaining('Map-Derived Estimates:'), findsOneWidget);
    expect(find.text('Baramati Pilot Plot'), findsOneWidget);

    // 3. Open Soil Intelligence Report for Baramati Pilot Plot
    await tester.tap(find.text('Baramati Pilot Plot'));
    await tester.pumpAndSettle();

    // Verify Soil Report Screen and Safeguards
    expect(find.text('Baramati Pilot Plot — Soil Intelligence'), findsOneWidget);
    expect(find.text('Soil pH (H2O)'), findsOneWidget);
    expect(find.text('Total Nitrogen (N)'), findsOneWidget);
    expect(find.textContaining('Available Nitrogen (N)'), findsOneWidget);
    expect(find.textContaining('Physical soil test required'), findsNWidgets(3));
  });
}
