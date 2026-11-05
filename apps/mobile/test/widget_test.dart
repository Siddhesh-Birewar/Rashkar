import 'package:flutter_test/flutter_test.dart';
import 'package:cropnet_mobile/main.dart';

void main() {
  testWidgets('CropNet AI app shell renders successfully with soil intelligence', (WidgetTester tester) async {
    await tester.pumpWidget(const CropNetApp());

    // Verify title and main elements
    expect(find.text('CropNet AI — Soil Intelligence'), findsOneWidget);
    expect(find.text('Select Maharashtra Pilot Region:'), findsOneWidget);
    expect(find.text('Baramati Farm Profile'), findsOneWidget);
    expect(find.text('Soil pH (0-5cm)'), findsOneWidget);
    expect(find.text('Soil Organic Carbon'), findsOneWidget);
    expect(find.text('Total Nitrogen'), findsOneWidget);

    // Verify disclaimer and NPK safeguards
    expect(find.textContaining('Map-Derived Estimate'), findsOneWidget);
    expect(find.textContaining('Available Nitrogen (N):'), findsOneWidget);
  });
}
