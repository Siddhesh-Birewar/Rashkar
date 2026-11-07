import 'dart:convert';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

import 'package:cropnet_mobile/core/network/api_client.dart';
import 'package:cropnet_mobile/features/crop/data/crop_repository.dart';
import 'package:cropnet_mobile/features/crop/models/crop_models.dart';

void main() {
  group('Crop Models & Repository Tests', () {
    final sampleCropSummaryJson = {
      'id': 'crop-chickpea',
      'common_name': 'Chickpea (Gram)',
      'scientific_name': 'Cicer arietinum',
      'marathi_name': 'हरभरा',
      'category': 'Pulse',
      'crop_type': 'Field Crop',
      'typical_duration_days_min': 90,
      'typical_duration_days_max': 110,
      'recommended_varieties': ['Digvijay', 'Vijay', 'Vishal'],
      'primary_source_org': 'MPKV Rahuri',
      'degraded_mode': false,
      'data_source_mode': 'database',
    };

    final sampleFullProfileJson = {
      'id': 'crop-chickpea',
      'common_name': 'Chickpea (Gram)',
      'scientific_name': 'Cicer arietinum',
      'marathi_name': 'हरभरा',
      'category': 'Pulse',
      'crop_type': 'Field Crop',
      'typical_duration_days_min': 90,
      'typical_duration_days_max': 110,
      'recommended_varieties': ['Digvijay', 'Vijay', 'Vishal'],
      'soil': {
        'preferred_textures': ['Clay Loam', 'Loam', 'Silt Loam'],
        'acceptable_textures': ['Clay', 'Sandy Clay Loam'],
        'ph_best_suited_min': 6.0,
        'ph_best_suited_max': 8.0,
        'ph_tolerable_min': 5.5,
        'ph_tolerable_max': 8.6,
        'ph_context_notes': 'Optimal in neutral to moderately alkaline deep black soils',
        'best_suited_soil_textures': ['Clay Loam', 'Loam'],
        'drainage_requirement': 'well-drained',
        'salinity_sensitivity': 'moderately sensitive',
        'min_soil_depth_cm': 30.0,
      },
      'climate': {
        'temp_optimum_min_c': 15.0,
        'temp_optimum_max_c': 25.0,
        'temp_reproductive_max_c': 35.0,
        'temp_reproductive_min_mean_c': 15.0,
        'annual_rainfall_min_mm': 400.0,
        'annual_rainfall_max_mm': 700.0,
        'frost_sensitivity': 'highly sensitive',
        'heat_sensitivity': 'sensitive during flowering',
      },
      'seasons': [
        {
          'season_name': 'Rabi',
          'is_primary_season': true,
          'planting_window_maharashtra': 'October 15 – November 15',
          'harvesting_window_maharashtra': 'February – March',
          'duration_days_min': 90,
          'duration_days_max': 110,
        }
      ],
      'water': {
        'annual_water_requirement_mm_min': 250.0,
        'annual_water_requirement_mm_max': 400.0,
        'rainfed_suitable': true,
        'irrigation_dependency': 'low to moderate',
        'critical_growth_stages': ['Pre-flowering', 'Pod development'],
        'waterlogging_sensitivity': 'extremely sensitive',
        'drought_sensitivity': 'tolerant',
      },
      'regional_suitability': [
        {
          'taluka': 'Baramati',
          'district': 'Pune',
          'suitability_status': 'highly_suitable',
          'agronomic_rationale': 'Excellent performance in rabi season under residual moisture.',
        }
      ],
      'sources': [
        {
          'id': 'src-mpkv-2022',
          'organization': 'Mahatma Phule Krishi Vidyapeeth (MPKV)',
          'publication_title': 'Rabi Crop Production Technology Package',
          'publication_year': 2022,
          'evidence_quality': 'peer_reviewed_university',
          'last_verified_date': '2026-01-15T00:00:00Z',
        }
      ],
      'degraded_mode': false,
      'data_source_mode': 'database',
    };

    test('CropCatalogSummary deserializes accurately', () {
      final summary = CropCatalogSummary.fromJson(sampleCropSummaryJson);

      expect(summary.id, 'crop-chickpea');
      expect(summary.commonName, 'Chickpea (Gram)');
      expect(summary.marathiName, 'हरभरा');
      expect(summary.category, 'Pulse');
      expect(summary.recommendedVarieties?.length, 3);
      expect(summary.degradedMode, false);
    });

    test('CropFullProfile deserializes and preserves texture-conditioned pH and heat limits', () {
      final profile = CropFullProfile.fromJson(sampleFullProfileJson);

      expect(profile.id, 'crop-chickpea');
      expect(profile.soil?.phBestSuitedMin, 6.0);
      expect(profile.soil?.phBestSuitedMax, 8.0);
      expect(profile.climate?.tempReproductiveMaxC, 35.0);
      expect(profile.seasons.first.seasonName, 'Rabi');
      expect(profile.water?.rainfedSuitable, true);
      expect(profile.sources.first.organization, contains('MPKV'));
    });

    test('CropRepository.listCrops filters by category and season', () async {
      final mockClient = MockClient((request) async {
        expect(request.url.queryParameters['category'], 'Pulse');
        expect(request.url.queryParameters['season'], 'Rabi');
        return http.Response(
          jsonEncode([sampleCropSummaryJson]),
          200,
          headers: {'content-type': 'application/json; charset=utf-8'},
        );
      });

      final repo = CropRepository(client: ApiClient(httpClient: mockClient));
      final crops = await repo.listCrops(category: 'Pulse', season: 'Rabi');

      expect(crops.length, 1);
      expect(crops.first.id, 'crop-chickpea');
    });

    test('CropRepository.getCropProfile returns full profile with sources', () async {
      final mockClient = MockClient((request) async {
        expect(request.url.path, '/api/v1/crops/crop-chickpea');
        return http.Response(
          jsonEncode(sampleFullProfileJson),
          200,
          headers: {'content-type': 'application/json; charset=utf-8'},
        );
      });

      final repo = CropRepository(client: ApiClient(httpClient: mockClient));
      final profile = await repo.getCropProfile('crop-chickpea');

      expect(profile.id, 'crop-chickpea');
      expect(profile.sources.length, 1);
    });

    test('CropRepository.listMaharashtraSeasons retrieves agro-climatic season calendar', () async {
      final mockClient = MockClient((request) async {
        expect(request.url.path, '/api/v1/agriculture/seasons');
        return http.Response(
          jsonEncode([
            {
              'season_name': 'Kharif',
              'marathi_name': 'खरीप',
              'period_months': 'June – October',
              'primary_crops': ['Soybean', 'Cotton', 'Bajra'],
              'rainfall_dependency': 'South-West Monsoon',
              'description': 'Monsoon cropping season',
            }
          ]),
          200,
          headers: {'content-type': 'application/json; charset=utf-8'},
        );
      });

      final repo = CropRepository(client: ApiClient(httpClient: mockClient));
      final seasons = await repo.listMaharashtraSeasons();

      expect(seasons.length, 1);
      expect(seasons.first.seasonName, 'Kharif');
      expect(seasons.first.marathiName, 'खरीप');
    });
  });
}
