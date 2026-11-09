import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:rashkar_farmer/main.dart';
import 'package:rashkar_farmer/models/farm_models.dart';
import 'package:rashkar_farmer/services/api_service.dart';
import 'package:rashkar_farmer/services/app_state.dart';
import 'package:rashkar_farmer/screens/home_screen.dart';
import 'package:rashkar_farmer/screens/farm_registration_screen.dart';
import 'package:rashkar_farmer/screens/extra_income_screen.dart';
import 'package:rashkar_farmer/screens/crop_loss_screen.dart';
import 'package:rashkar_farmer/screens/ask_rashkar_screen.dart';
import 'package:rashkar_farmer/screens/heat_safety_screen.dart';

void main() {
  setUp(() {
    ApiService.mockMode = true;
  });

  testWidgets('Rashkar main app boots and renders navigation shell in clean starting state', (WidgetTester tester) async {
    AppState.instance.clearSession();
    await tester.pumpWidget(const RashkarFarmerApp());
    await tester.pumpAndSettle();

    expect(find.text('RASHKAR'), findsWidgets);
    expect(find.text('Home'), findsOneWidget);
    expect(find.text('My Crop'), findsWidgets);
    expect(find.text('Heat Safety'), findsWidgets);
    expect(find.text('Income'), findsOneWidget);
    expect(find.text('Ask Rashkar'), findsOneWidget);
    expect(find.text('Welcome to Rashkar'), findsOneWidget);
    expect(find.text('Register Your Farm'), findsOneWidget);
  });

  testWidgets('Home screen displays 4 primary action buttons when demo farm is loaded', (WidgetTester tester) async {
    await AppState.instance.loadDemoFarm();
    await tester.pumpWidget(const MaterialApp(home: HomeScreen()));
    await tester.pumpAndSettle();

    expect(find.text('WHAT WOULD YOU LIKE TO DO?'), findsOneWidget);
    expect(find.text('My Crop'), findsWidgets);
    expect(find.text('Heat Safety'), findsWidgets);
    expect(find.text('Extra Income'), findsWidgets);
    expect(find.text('Crop Loss'), findsWidgets);
    expect(find.text('Ask Rashkar AI Assistant'), findsWidgets);
  });

  testWidgets('Farm registration screen displays 5-step guided flow with dynamic catalog', (WidgetTester tester) async {
    await tester.pumpWidget(const MaterialApp(home: FarmRegistrationScreen()));
    await tester.pumpAndSettle();

    expect(find.text('Farm Setup Guide'), findsOneWidget);
    expect(find.text('Farmer Details'), findsOneWidget);
    expect(find.text('Farm Profile'), findsOneWidget);
    expect(find.text('CONTINUE'), findsWidgets);
  });

  testWidgets('Extra income screen renders budget and simulation actions', (WidgetTester tester) async {
    await tester.pumpWidget(const MaterialApp(home: ExtraIncomeScreen()));
    await tester.pumpAndSettle();

    expect(find.text('Extra Farm Income'), findsOneWidget);
    expect(find.text('Find Extra Income from Your Farm'), findsOneWidget);
  });

  testWidgets('Ask Rashkar chat screen renders prompt chips and input field', (WidgetTester tester) async {
    await tester.pumpWidget(const MaterialApp(home: AskRashkarScreen()));
    await tester.pumpAndSettle();

    expect(find.text('Ask Rashkar Assistant'), findsOneWidget);
    expect(find.text('Ask a question about your farm...'), findsOneWidget);
    expect(find.text('How is my crop doing today?'), findsOneWidget);
  });

  testWidgets('Crop loss screen renders tabs and form controls', (WidgetTester tester) async {
    await tester.pumpWidget(const MaterialApp(home: CropLossScreen()));
    await tester.pumpAndSettle();

    expect(find.text('Crop Loss Claim (PMFBY)'), findsOneWidget);
    expect(find.text('Report Loss'), findsOneWidget);
    expect(find.text('My Claims'), findsOneWidget);
    expect(find.text('Report Crop Damage'), findsOneWidget);
  });

  testWidgets('Heat safety screen renders crop stage chips with valid non-null names', (WidgetTester tester) async {
    await AppState.instance.loadDemoFarm();
    await tester.pumpWidget(const MaterialApp(home: HeatSafetyScreen()));
    await tester.pumpAndSettle();

    // Switch to Crop Heat tab
    final cropTabFinder = find.text('Crop Heat Risk');
    expect(cropTabFinder, findsOneWidget);
    await tester.tap(cropTabFinder);
    await tester.pumpAndSettle();

    expect(find.text('Confirm Crop Stage'), findsOneWidget);
    // Ensure no chip or text contains 'null'
    expect(find.textContaining('null ('), findsNothing);
    // Ensure actual stage names are rendered in the ChoiceChips
    expect(find.textContaining('Flowering & Anthesis (35'), findsOneWidget);
    expect(find.textContaining('Germination / Emergence (38'), findsOneWidget);
  });

  testWidgets('Crop stage chips fall back safely without showing null even if data is corrupted', (WidgetTester tester) async {
    final corrupted = CropHeatAssessment.fromJson({
      'crop_code': 'soybean',
      'growth_stage_code': 'stage_flowering',
      'supported_stages': [
        {'stage_code': 'stage_flowering', 'stage_name_en': null, 'stage_name': null, 'crit_tmax': 35.0},
        {'stage_code': 'stage_maturity', 'stage_name_en': 'null', 'crit_tmax': 42.0},
        {'stage_code': null, 'crit_tmax': 36.0},
      ]
    });
    expect(corrupted.supportedStages[0]['stage_name'], 'FLOWERING');
    expect(corrupted.supportedStages[1]['stage_name'], 'MATURITY');
    expect(corrupted.supportedStages[2]['stage_name'], 'Growth Stage');
    expect(corrupted.supportedStages.any((s) => s['stage_name'].toString().contains('null')), isFalse);
  });
}
