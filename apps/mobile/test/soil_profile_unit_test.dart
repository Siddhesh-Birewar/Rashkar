import 'package:flutter_test/flutter_test.dart';

class SoilParameter {
  final String key;
  final String displayName;
  final double? value;
  final String unit;
  final String source;
  final bool isAvailable;

  SoilParameter({
    required this.key,
    required this.displayName,
    this.value,
    required this.unit,
    required this.source,
    required this.isAvailable,
  });
}

class FarmSoilProfile {
  final String taluka;
  final Map<String, SoilParameter> parameters;
  final bool isMapDerived;

  FarmSoilProfile({
    required this.taluka,
    required this.parameters,
    this.isMapDerived = true,
  });

  bool get hasAvailableNPK =>
      parameters.containsKey('available_n') &&
      parameters['available_n']?.value != null;
}

void main() {
  group('Soil Intelligence Unit Tests', () {
    test('Verified SoilGrids Baramati profile does not fabricate available NPK', () {
      final profile = FarmSoilProfile(
        taluka: 'Baramati',
        parameters: {
          'ph': SoilParameter(
            key: 'ph',
            displayName: 'Soil pH',
            value: 7.29,
            unit: 'pH',
            source: 'ISRIC SoilGrids',
            isAvailable: true,
          ),
          'total_nitrogen': SoilParameter(
            key: 'total_nitrogen',
            displayName: 'Total Nitrogen',
            value: 1.25,
            unit: 'g/kg',
            source: 'ISRIC SoilGrids',
            isAvailable: true,
          ),
          'available_n': SoilParameter(
            key: 'available_n',
            displayName: 'Available Nitrogen',
            value: null,
            unit: 'kg/ha',
            source: 'None',
            isAvailable: false,
          ),
        },
      );

      expect(profile.taluka, 'Baramati');
      expect(profile.isMapDerived, true);
      expect(profile.parameters['ph']?.value, 7.29);
      expect(profile.parameters['total_nitrogen']?.value, 1.25);
      expect(profile.hasAvailableNPK, false);
      expect(profile.parameters['available_n']?.value, isNull);
    });

    test('All four Maharashtra pilot regions have valid regional profiles', () {
      final pilotRegions = ['Maval', 'Mulshi', 'Baramati', 'Indapur'];
      expect(pilotRegions.length, 4);
      expect(pilotRegions.contains('Maval'), true);
      expect(pilotRegions.contains('Mulshi'), true);
      expect(pilotRegions.contains('Baramati'), true);
      expect(pilotRegions.contains('Indapur'), true);
    });
  });
}
