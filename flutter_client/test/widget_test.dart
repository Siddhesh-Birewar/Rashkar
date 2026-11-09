import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:rashkar_farmer/main.dart';
import 'package:rashkar_farmer/services/api_service.dart';
import 'package:rashkar_farmer/services/app_state.dart';
import 'package:rashkar_farmer/screens/home_screen.dart';
import 'package:rashkar_farmer/screens/farm_registration_screen.dart';
import 'package:rashkar_farmer/screens/extra_income_screen.dart';
import 'package:rashkar_farmer/screens/crop_loss_screen.dart';
import 'package:rashkar_farmer/screens/ask_rashkar_screen.dart';

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
}
