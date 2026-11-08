import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

import 'package:cropnet_mobile/core/network/api_client.dart';
import 'package:cropnet_mobile/features/farm_health/data/farm_health_repository.dart';
import 'package:cropnet_mobile/features/farm_health/presentation/screens/farm_health_dashboard_screen.dart';
import 'package:cropnet_mobile/features/farm_health/presentation/widgets/ai_entry_points_card.dart';
import 'package:cropnet_mobile/features/farm_health/presentation/widgets/farm_overview_card.dart';
import 'package:cropnet_mobile/features/farm_health/presentation/widgets/farm_timeline_card.dart';
import 'package:cropnet_mobile/features/farm_health/presentation/widgets/overall_evidence_card.dart';
import 'package:cropnet_mobile/features/farm_health/presentation/widgets/satellite_vegetation_card.dart';
import 'package:cropnet_mobile/features/farm_health/presentation/widgets/soil_intelligence_card.dart';
import 'package:cropnet_mobile/features/farm_health/presentation/widgets/water_intelligence_card.dart';
import 'package:cropnet_mobile/features/farm_health/presentation/widgets/weather_summary_card.dart';

void main() {
  final fullEvidencePayload = {
    'contract_version': '1.0',
    'farm_id': 'farm-baramati-001',
    'farm_name': 'Baramati Model Farm',
    'owner_id': '00000000-0000-0000-0000-000000000001',
    'taluka': 'Baramati',
    'district': 'Pune',
    'state': 'Maharashtra',
    'calculated_area_hectares': 2.5,
    'calculated_area_acres': 6.18,
    'snapshot_timestamp': '2026-11-08T11:45:00Z',
    'overall_evidence_overview': {
      'domains_available': 5,
      'domains_partially_available': 0,
      'domains_stale': 0,
      'domains_not_available': 0,
      'domains_insufficient_evidence': 0,
      'total_domains': 5,
      'actionable_summary': 'Complete actionable evidence available across all 5 domains.',
    },
    'soil': {
      'availability_state': 'AVAILABLE',
      'last_updated': '2026-10-15T09:30:00Z',
      'data_age_days': 24,
      'provenance': 'MIXED_DUAL_SOURCE',
      'laboratory_name': 'KVK Baramati Soil Testing Laboratory',
      'sample_depth': '0-15 cm',
      'key_indicators': {
        'soil_ph': 7.6,
        'organic_carbon_pct': 0.58,
        'electrical_conductivity_ds_m': 0.45,
        'available_nitrogen_kg_ha': 210.0,
        'available_phosphorus_kg_ha': 18.5,
        'available_potassium_kg_ha': 340.0,
        'soil_texture': 'Clay Loam',
        'cation_exchange_capacity': 38.2,
      },
      'missing_critical_parameters': [],
      'agronomic_notes': ['Farmer-confirmed physical laboratory test.'],
    },
    'water': {
      'availability_state': 'AVAILABLE',
      'last_updated': '2026-09-20T14:15:00Z',
      'data_age_days': 49,
      'registered_sources_count': 1,
      'sources': [
        {
          'source_id': 'wsrc-001',
          'source_type': 'borewell',
          'name': 'North Field Borewell',
          'seasonal_availability': 'perennial',
          'reliability': 'reliable',
          'irrigation_method': 'drip',
          'measured_capacity_lph': 12000.0,
          'capacity_provenance': 'MEASURED',
        }
      ],
      'laboratory_name': 'Agricultural Water Testing Laboratory, Pune',
      'key_indicators': {
        'ph': 7.6,
        'electrical_conductivity_ds_m': 1.85,
        'tds_mg_l': 1184.0,
        'sar': 3.01,
        'sar_status': 'AVAILABLE',
        'rsc_meq_l': -1.9,
        'rsc_status': 'AVAILABLE',
        'chloride_meq_l': 4.8,
        'boron_mg_l': 0.65,
      },
      'institutional_evaluations': [
        {
          'parameter_key': 'electrical_conductivity',
          'parameter_name': 'Electrical Conductivity (EC)',
          'hazard_level': 'MEDIUM',
          'hazard_title': 'Medium Salinity (Class 2 - Moderate Restriction)',
          'standard_applied': 'BIS IS 11624:2019',
          'management_guidance': 'Water can be used on soils with moderate drainage.',
        }
      ],
      'missing_critical_parameters': [],
    },
    'satellite': {
      'availability_state': 'AVAILABLE',
      'observation_date': '2026-11-04T05:43:53Z',
      'observation_age_days': 4,
      'sensor': 'Sentinel-2 L2A',
      'product_id': 'S2B_MSIL2A_20261104',
      'canopy_ndvi': 0.68,
      'canopy_ndmi': 0.22,
      'composite_mean_ndvi': 0.52,
      'bare_soil_mean_ndvi': 0.28,
      'vegetation_coverage_percent': 68.4,
      'bare_soil_coverage_percent': 31.6,
      'cloud_masked_percent': 0.0,
      'valid_pixel_count': 250,
      'quality_status': 'VALID_OBSERVATION',
      'is_small_farm_warning': false,
      'agronomic_interpretation': 'Active photosynthetic canopy covering 68.4% of parcel.',
      'scientific_disclaimer': 'Sentinel-2 NDVI and NDMI reflect surface optical reflectance (10m GSD). They are indirect canopy vigor indicators, NOT direct disease pathogen or yield diagnoses.',
    },
    'weather': {
      'availability_state': 'AVAILABLE',
      'last_updated': '2026-11-08T11:30:00Z',
      'current_weather': {
        'observation_time': '2026-11-08T11:20:00Z',
        'temperature_c': 28.4,
        'humidity_percent': 48.0,
        'precipitation_mm': 0.0,
        'wind_speed_ms': 3.1,
        'weather_condition': 'Clear',
        'weather_description': 'clear sky',
      },
      'forecast': {
        'forecast_days_count': 5,
        'next_48h_rain_expected_mm': 0.0,
        'temp_min_c': 17.5,
        'temp_max_c': 31.0,
        'weather_alerts': [],
      },
      'climate_normals': {
        'annual_rainfall_mm': 560.0,
        'monsoon_rainfall_mm': 440.0,
        'mean_temperature_c': 24.5,
        'potential_water_stress_indicator': 'Moderate seasonal winter dry spell',
      },
    },
    'crop_context': {
      'availability_state': 'AVAILABLE',
      'evaluated_at': '2026-11-08T10:00:00Z',
      'target_season': 'Rabi 2026-27',
      'taluka_resolved': 'Baramati',
      'evaluated_crops_count': 10,
      'suitable_crops': [
        {
          'crop_id': 'wheat',
          'common_name': 'Wheat',
          'marathi_name': 'गहू',
          'decision_state': 'VERIFIED_SUITABLE',
          'limiting_factors': [],
          'irrigation_guidance': 'Crown root initiation irrigation critical at 21 DAS.',
        }
      ],
      'conditionally_suitable_crops': [],
      'disqualified_crops': [],
      'abstain_crops': [],
      'top_limiting_factors': [],
      'pending_followup_questions_count': 0,
    },
    'governance_notice': 'CropNet AI provides independent, evidence-gated agricultural domain summaries. In accordance with institutional agricultural guidelines, no universal health score is computed.',
  };

  final missingEvidencePayload = {
    'contract_version': '1.0',
    'farm_id': 'farm-new-002',
    'farm_name': 'New Registered Parcel',
    'owner_id': '00000000-0000-0000-0000-000000000001',
    'taluka': 'Indapur',
    'district': 'Pune',
    'state': 'Maharashtra',
    'calculated_area_hectares': 1.2,
    'calculated_area_acres': 2.97,
    'snapshot_timestamp': '2026-11-08T11:45:00Z',
    'overall_evidence_overview': {
      'domains_available': 0,
      'domains_partially_available': 0,
      'domains_stale': 0,
      'domains_not_available': 5,
      'domains_insufficient_evidence': 0,
      'total_domains': 5,
      'actionable_summary': 'Zero evidence recorded for this farm. Actions required: upload soil card, register water source, sync satellite.',
    },
    'soil': {
      'availability_state': 'NOT_AVAILABLE',
      'last_updated': null,
      'data_age_days': null,
      'key_indicators': {},
      'missing_critical_parameters': ['soil_ph', 'organic_carbon'],
      'agronomic_notes': ['No soil profile has been generated or uploaded.'],
    },
    'water': {
      'availability_state': 'NOT_AVAILABLE',
      'last_updated': null,
      'data_age_days': null,
      'registered_sources_count': 0,
      'sources': [],
      'key_indicators': {'sar_status': 'UNAVAILABLE', 'rsc_status': 'UNAVAILABLE'},
      'institutional_evaluations': [],
      'missing_critical_parameters': ['water_source'],
    },
    'satellite': {
      'availability_state': 'NOT_AVAILABLE',
      'observation_date': null,
      'valid_pixel_count': 0,
      'scientific_disclaimer': 'Sentinel-2 NDVI and NDMI reflect surface optical reflectance.',
    },
    'weather': {
      'availability_state': 'NOT_AVAILABLE',
      'last_updated': null,
      'current_weather': {},
      'forecast': {},
      'climate_normals': {},
    },
    'crop_context': {
      'availability_state': 'NOT_AVAILABLE',
      'evaluated_crops_count': 0,
      'suitable_crops': [],
    },
    'governance_notice': 'No universal health score is computed.',
  };

  final staleEvidencePayload = {
    'contract_version': '1.0',
    'farm_id': 'farm-stale-003',
    'farm_name': 'Sangamner Pomegranate Orchard',
    'owner_id': '00000000-0000-0000-0000-000000000001',
    'taluka': 'Sangamner',
    'district': 'Ahmednagar',
    'state': 'Maharashtra',
    'calculated_area_hectares': 3.1,
    'calculated_area_acres': 7.66,
    'snapshot_timestamp': '2026-11-08T11:45:00Z',
    'overall_evidence_overview': {
      'domains_available': 0,
      'domains_partially_available': 0,
      'domains_stale': 5,
      'domains_not_available': 0,
      'domains_insufficient_evidence': 0,
      'total_domains': 5,
      'actionable_summary': 'All recorded farm evidence is stale.',
    },
    'soil': {
      'availability_state': 'STALE',
      'last_updated': '2022-08-10T10:00:00Z',
      'data_age_days': 1551,
      'key_indicators': {'soil_ph': 8.1},
    },
    'water': {
      'availability_state': 'STALE',
      'last_updated': '2025-06-15T11:30:00Z',
      'data_age_days': 511,
      'registered_sources_count': 1,
      'key_indicators': {'electrical_conductivity_ds_m': 2.2},
    },
    'satellite': {
      'availability_state': 'STALE',
      'observation_date': '2026-09-12T05:40:02Z',
      'observation_age_days': 57,
      'canopy_ndvi': 0.44,
      'scientific_disclaimer': 'Sentinel-2 NDVI and NDMI reflect surface optical reflectance.',
    },
    'weather': {
      'availability_state': 'STALE',
      'last_updated': '2026-11-08T06:00:00Z',
      'current_weather': {'temperature_c': 21.0},
    },
    'crop_context': {
      'availability_state': 'STALE',
      'evaluated_at': '2025-07-01T08:00:00Z',
      'suitable_crops': [],
    },
    'governance_notice': 'No universal health score is computed.',
  };

  FarmHealthRepository createMockRepo(Map<String, dynamic> payload) {
    final mockClient = MockClient((request) async {
      return http.Response(jsonEncode(payload), 200, headers: {'content-type': 'application/json'});
    });
    return FarmHealthRepository(client: ApiClient(httpClient: mockClient));
  }

  Widget createTestWidget({
    required FarmHealthRepository repository,
    required String farmId,
    double width = 400.0,
    double height = 900.0,
  }) {
    return MaterialApp(
      home: MediaQuery(
        data: MediaQueryData(size: Size(width, height)),
        child: FarmHealthDashboardScreen(
          farmId: farmId,
          repository: repository,
        ),
      ),
    );
  }

  group('Farm Health Dashboard Screen Widget Tests', () {
    testWidgets('Renders all 8 required sections with live full evidence data', (tester) async {
      final repo = createMockRepo(fullEvidencePayload);

      await tester.pumpWidget(createTestWidget(repository: repo, farmId: 'farm-baramati-001'));
      await tester.pumpAndSettle();

      // Section 1: Overview
      expect(find.byType(FarmOverviewCard), findsOneWidget);
      expect(find.widgetWithText(FarmOverviewCard, 'Baramati Model Farm'), findsOneWidget);
      expect(find.textContaining('2.50 ha'), findsOneWidget);

      // Section 2: Overall Evidence Overview
      expect(find.byType(OverallEvidenceCard), findsOneWidget);
      expect(find.text('Overall Evidence Status Board'), findsOneWidget);
      expect(find.descendant(of: find.byType(OverallEvidenceCard), matching: find.text('Complete actionable evidence available across all 5 domains.')), findsOneWidget);

      // Section 3: Soil Intelligence
      expect(find.byType(SoilIntelligenceCard), findsOneWidget);
      expect(find.text('Soil Intelligence Summary'), findsOneWidget);
      expect(find.text('KVK Baramati Soil Testing Laboratory'), findsOneWidget);
      expect(find.text('7.6'), findsWidgets); // pH value

      // Section 4: Water Intelligence
      expect(find.byType(WaterIntelligenceCard), findsOneWidget);
      expect(find.text('Water Intelligence Summary'), findsOneWidget);
      expect(find.text('North Field Borewell'), findsOneWidget);
      expect(find.text('Medium Salinity (Class 2 - Moderate Restriction)'), findsOneWidget);

      // Section 5: Satellite Vegetation
      expect(find.byType(SatelliteVegetationCard), findsOneWidget);
      expect(find.text('Satellite Vegetation Summary'), findsOneWidget);
      expect(find.text('0.68'), findsOneWidget); // Canopy NDVI
      expect(find.textContaining('indirect canopy vigor indicators'), findsOneWidget); // Disclaimer

      // Section 6: Weather Summary
      expect(find.byType(WeatherSummaryCard), findsOneWidget);
      expect(find.text('Weather & Climate Summary'), findsOneWidget);
      expect(find.text('28.4°C'), findsOneWidget);

      // Section 7: Observations Timeline
      expect(find.byType(FarmTimelineCard), findsOneWidget);
      expect(find.text('Farm Changes & Observations Timeline'), findsOneWidget);

      // Section 8: AI Assistant Entry Points
      expect(find.byType(AiEntryPointsCard), findsOneWidget);
      expect(find.text('AI Assistant Entry Points'), findsOneWidget);
      expect(find.text('Consult CropNet AI Advisor'), findsOneWidget);

      // Strict Governance Verification: NO Universal Health Score displayed
      expect(find.textContaining('/100'), findsNothing);
      expect(find.textContaining('Health Score'), findsNothing);
      expect(find.textContaining('Overall Grade'), findsNothing);
    });

    testWidgets('Missing evidence parcel renders clean NOT_AVAILABLE empty states without fake numbers', (tester) async {
      final repo = createMockRepo(missingEvidencePayload);

      await tester.pumpWidget(createTestWidget(repository: repo, farmId: 'farm-new-002'));
      await tester.pumpAndSettle();

      expect(find.widgetWithText(FarmOverviewCard, 'New Registered Parcel'), findsOneWidget);

      // Soil Empty State
      expect(find.text('No Soil Intelligence Available'), findsOneWidget);

      // Water Empty State
      expect(find.text('No Water Intelligence Available'), findsOneWidget);

      // Satellite Empty State
      expect(find.text('No Satellite Synchronization Recorded'), findsOneWidget);

      // Weather Empty State
      expect(find.text('Weather Observations Unavailable'), findsOneWidget);

      // Check that missing domains show Not Available chips
      expect(find.text('Not Available'), findsWidgets);
    });

    testWidgets('Stale evidence parcel displays warning banners', (tester) async {
      final repo = createMockRepo(staleEvidencePayload);

      await tester.pumpWidget(createTestWidget(repository: repo, farmId: 'farm-stale-003'));
      await tester.pumpAndSettle();

      expect(find.widgetWithText(FarmOverviewCard, 'Sangamner Pomegranate Orchard'), findsOneWidget);

      // Stale warning in soil
      expect(find.textContaining('Soil test report is 1551 days old (>3 years)'), findsOneWidget);

      // Stale warning in water
      expect(find.textContaining('Water test is 511 days old (>1 year)'), findsOneWidget);

      // Stale warning in satellite
      expect(find.textContaining('Satellite observation is 57 days old (>30 days)'), findsOneWidget);

      // Stale warning in weather
      expect(find.textContaining('Weather cache is over 2 hours old'), findsOneWidget);
    });

    testWidgets('Responsive layouts adapt across Mobile, Tablet, and Desktop', (tester) async {
      final repo = createMockRepo(fullEvidencePayload);

      tester.view.devicePixelRatio = 1.0;
      addTearDown(() {
        tester.view.resetPhysicalSize();
        tester.view.resetDevicePixelRatio();
      });

      // 1. Mobile viewport (<600px)
      tester.view.physicalSize = const Size(390, 844);
      await tester.pumpWidget(createTestWidget(repository: repo, farmId: 'farm-baramati-001', width: 390, height: 844));
      await tester.pumpAndSettle();
      expect(find.byType(FarmOverviewCard), findsOneWidget);
      expect(find.byType(OverallEvidenceCard), findsOneWidget);

      // 2. Tablet viewport (800px)
      tester.view.physicalSize = const Size(800, 1024);
      await tester.pumpWidget(createTestWidget(repository: repo, farmId: 'farm-baramati-001', width: 800, height: 1024));
      await tester.pumpAndSettle();
      expect(find.byType(FarmOverviewCard), findsOneWidget);
      expect(find.byType(OverallEvidenceCard), findsOneWidget);

      // 3. Desktop viewport (1280px)
      tester.view.physicalSize = const Size(1280, 900);
      await tester.pumpWidget(createTestWidget(repository: repo, farmId: 'farm-baramati-001', width: 1280, height: 900));
      await tester.pumpAndSettle();
      expect(find.byType(FarmOverviewCard), findsOneWidget);
      expect(find.byType(OverallEvidenceCard), findsOneWidget);
      expect(find.byType(AiEntryPointsCard), findsOneWidget);
    });
  });
}
