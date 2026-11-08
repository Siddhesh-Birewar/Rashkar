import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:rashkar_farmer/main.dart';
import 'package:rashkar_farmer/services/api_service.dart';
import 'package:rashkar_farmer/screens/home_screen.dart';
import 'package:rashkar_farmer/screens/farm_registration_screen.dart';
import 'package:rashkar_farmer/screens/extra_income_screen.dart';
import 'package:rashkar_farmer/screens/crop_loss_screen.dart';
import 'package:rashkar_farmer/screens/ask_rashkar_screen.dart';

void main() {
  setUp(() {
    ApiService.mockMode = true;
  });

  testWidgets('Rashkar main app boots and renders navigation shell', (WidgetTester tester) async {
    await tester.pumpWidget(const RashkarFarmerApp());
    await tester.pumpAndSettle();

    expect(find.text('RASHKAR'), findsWidgets);
    expect(find.text('Home'), findsOneWidget);
    expect(find.text('My Crop'), findsWidgets);
    expect(find.text('Heat Safety'), findsWidgets);
    expect(find.text('Income'), findsOneWidget);
    expect(find.text('Ask Rashkar'), findsOneWidget);
  });

  testWidgets('Home screen displays 4 primary action buttons and Ask Rashkar banner', (WidgetTester tester) async {
    await tester.pumpWidget(const MaterialApp(home: HomeScreen()));
    await tester.pumpAndSettle();

    expect(find.text('WHAT WOULD YOU LIKE TO DO?'), findsOneWidget);
    expect(find.text('My Crop'), findsOneWidget);
    expect(find.text('Heat Safety'), findsOneWidget);
    expect(find.text('Extra Income'), findsOneWidget);
    expect(find.text('Crop Loss'), findsOneWidget);
    expect(find.text('ASK RASHKAR ASSISTANT'), findsOneWidget);
  });

  testWidgets('Farm registration screen displays 5-step guided flow', (WidgetTester tester) async {
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

    expect(find.text('Extra Income & Diversification'), findsOneWidget);
    expect(find.text('CURATED AGRO-ENTERPRISES'), findsOneWidget);
  });

  testWidgets('Ask Rashkar chat screen renders prompt chips and input field', (WidgetTester tester) async {
    await tester.pumpWidget(const MaterialApp(home: AskRashkarScreen()));
    await tester.pumpAndSettle();

    expect(find.text('Ask Rashkar Assistant'), findsOneWidget);
    expect(find.text('Ask a question about your farm...'), findsOneWidget);
    expect(find.text('Why is my crop at risk today?'), findsOneWidget);
  });

  testWidgets('Crop loss screen renders tabs and form controls', (WidgetTester tester) async {
    await tester.pumpWidget(const MaterialApp(home: CropLossScreen()));
    await tester.pumpAndSettle();

    expect(find.text('PMFBY Crop Loss Evidence'), findsOneWidget);
    expect(find.text('New Evidence'), findsOneWidget);
    expect(find.text('Dossier Cases'), findsOneWidget);
    expect(find.text('SAVE AS OFFLINE DRAFT'), findsOneWidget);
    expect(find.text('SUBMIT EVIDENCE DOSSIER FOR REVIEW'), findsOneWidget);
  });
}
