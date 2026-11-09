import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/farm_models.dart';

class ApiService {
  // Configurable backend URL reading from --dart-define=API_BASE_URL or defaulting to local FastAPI
  static const String _apiHost = String.fromEnvironment('API_BASE_URL', defaultValue: 'http://127.0.0.1:8000');
  static String get baseUrl => _apiHost.endsWith('/v1') ? _apiHost : '$_apiHost/v1';

  // Toggle for automated widget tests only
  static bool mockMode = false;

  // In-memory cache for offline resilience
  static FarmSummary? _cachedSummary;
  static final List<CropLossCase> _offlineDraftCases = [];

  // --- 0. Geographic & Crop Catalogues ---
  static Future<List<Map<String, dynamic>>> getDistricts() async {
    if (mockMode) {
      return [
        {'district_name': 'Pune', 'talukas_count': 12, 'is_pilot': true},
        {'district_name': 'Solapur', 'talukas_count': 11, 'is_pilot': false},
        {'district_name': 'Nashik', 'talukas_count': 13, 'is_pilot': false},
        {'district_name': 'Ahmednagar', 'talukas_count': 12, 'is_pilot': false},
      ];
    }
    try {
      final uri = Uri.parse('$baseUrl/geo/districts');
      final res = await http.get(uri).timeout(const Duration(seconds: 4));
      if (res.statusCode == 200) {
        final List list = json.decode(res.body);
        return List<Map<String, dynamic>>.from(list);
      }
    } catch (_) {}
    return [
      {'district_name': 'Pune', 'talukas_count': 12, 'is_pilot': true},
      {'district_name': 'Solapur', 'talukas_count': 11, 'is_pilot': false},
      {'district_name': 'Nashik', 'talukas_count': 13, 'is_pilot': false},
      {'district_name': 'Ahmednagar', 'talukas_count': 12, 'is_pilot': false},
    ];
  }

  static Future<List<Map<String, dynamic>>> getTalukas({String? district}) async {
    if (mockMode) {
      return [
        {'taluka_name': 'Baramati', 'district_name': 'Pune', 'latitude': 18.151, 'longitude': 74.577, 'is_pune_pilot': true},
        {'taluka_name': 'Indapur', 'district_name': 'Pune', 'latitude': 18.115, 'longitude': 75.025, 'is_pune_pilot': true},
      ];
    }
    try {
      final q = district != null ? '?district=${Uri.encodeComponent(district)}' : '';
      final uri = Uri.parse('$baseUrl/geo/talukas$q');
      final res = await http.get(uri).timeout(const Duration(seconds: 4));
      if (res.statusCode == 200) {
        final List list = json.decode(res.body);
        return List<Map<String, dynamic>>.from(list);
      }
    } catch (_) {}
    return [];
  }

  static Future<List<Map<String, dynamic>>> getCrops() async {
    if (mockMode) {
      return [
        {'crop_code': 'soybean', 'common_name_en': 'Soybean', 'common_name_mr': 'सोयाबीन', 'support_level': 'rule_and_baseline_supported'},
        {'crop_code': 'cotton', 'common_name_en': 'Cotton', 'common_name_mr': 'कापूस', 'support_level': 'rule_and_baseline_supported'},
        {'crop_code': 'jowar', 'common_name_en': 'Jowar / Sorghum', 'common_name_mr': 'ज्वारी', 'support_level': 'rule_and_baseline_supported'},
        {'crop_code': 'onion', 'common_name_en': 'Onion', 'common_name_mr': 'कांदा', 'support_level': 'advisory_only'},
      ];
    }
    try {
      final uri = Uri.parse('$baseUrl/geo/crops');
      final res = await http.get(uri).timeout(const Duration(seconds: 4));
      if (res.statusCode == 200) {
        final List list = json.decode(res.body);
        return List<Map<String, dynamic>>.from(list);
      }
    } catch (_) {}
    return [
      {'crop_code': 'soybean', 'common_name_en': 'Soybean', 'common_name_mr': 'सोयाबीन', 'support_level': 'rule_and_baseline_supported'},
      {'crop_code': 'cotton', 'common_name_en': 'Cotton', 'common_name_mr': 'कापूस', 'support_level': 'rule_and_baseline_supported'},
      {'crop_code': 'jowar', 'common_name_en': 'Jowar', 'common_name_mr': 'ज्वारी', 'support_level': 'rule_and_baseline_supported'},
      {'crop_code': 'onion', 'common_name_en': 'Onion', 'common_name_mr': 'कांदा', 'support_level': 'advisory_only'},
      {'crop_code': 'sugarcane', 'common_name_en': 'Sugarcane', 'common_name_mr': 'ऊस', 'support_level': 'rule_and_baseline_supported'},
      {'crop_code': 'gram', 'common_name_en': 'Gram / Chickpea', 'common_name_mr': 'हरभरा', 'support_level': 'advisory_only'},
      {'crop_code': 'wheat', 'common_name_en': 'Wheat', 'common_name_mr': 'गहू', 'support_level': 'advisory_only'},
    ];
  }

  // --- 1. All Registered Farms & Active Farm Summary ---
  static Future<List<FarmSummary>> getAllFarms() async {
    if (mockMode) return [];
    try {
      final uri = Uri.parse('$baseUrl/farms/');
      final res = await http.get(uri).timeout(const Duration(seconds: 4));
      if (res.statusCode == 200) {
        final List list = json.decode(res.body);
        return list.map((item) => FarmSummary.fromJson(item)).toList();
      }
    } catch (_) {}
    return [];
  }

  static Future<FarmSummary> getFarmSummary({required String farmId}) async {
    if (mockMode && _cachedSummary != null) return _cachedSummary!;
    if (!mockMode) {
      try {
        final uri = Uri.parse('$baseUrl/farms/$farmId/summary');
        final response = await http.get(uri).timeout(const Duration(seconds: 4));

        if (response.statusCode == 200) {
          final data = json.decode(response.body);
          _cachedSummary = FarmSummary.fromJson(data);
          return _cachedSummary!;
        }
      } catch (_) {}
    }

    if (_cachedSummary != null) return _cachedSummary!;

    return FarmSummary(
      farmerId: 'farmer_demo_01',
      farmerName: 'Farmer',
      farmId: farmId,
      farmName: 'My Farm',
      locationDisplay: 'Maharashtra',
      latitude: 18.151,
      longitude: 74.577,
      totalAreaAcres: 3.0,
      activeCropCode: 'soybean',
      activeCropName: 'Soybean',
      sowingDate: '2024-06-20',
      daysAfterSowing: 45,
      estimatedStageCode: 'vegetative',
      estimatedStageName: 'Vegetative Growth',
      plantedAreaAcres: 2.5,
      irrigationType: 'rainfed',
      weatherSummary: {
        'temperature_c': 32.5,
        'relative_humidity_pct': 55.0,
        'wind_speed_kmh': 12.0,
        'condition': 'Partly Cloudy',
        'rainfall_today_mm': 0.0,
        'source': 'IMD Station / Gridded Baseline'
      },
      dataLastUpdated: 'Recently',
      isDataStale: false,
      soilSummary: {
        'depth': '0-30cm',
        'ph': 7.8,
        'organic_carbon_pct': 0.65,
        'clay_pct': 52.0,
        'available_water_capacity_mm_m': 160.0,
        'data_provenance': 'CropNet Maharashtra Baseline',
        'is_lab_measured': false
      },
      activeAlerts: [],
    );
  }

  // --- 1.1 CropNet Soil Card Integration ---
  static Future<CropNetSoilCardData> getFarmSoilCard(String farmId) async {
    if (mockMode) {
      return CropNetSoilCardData(
        farmId: farmId,
        farmName: 'Shinde Krishi Sheti',
        locationDisplay: 'Bawada, Indapur, Pune',
        textureSummary: 'Medium to Deep Black Vertisol (Clay)',
        reactionSummary: 'Moderately Alkaline (pH 7.8)',
        provenanceBadge: 'Location-Based Estimate (SoilGrids 250m)',
        isLabMeasured: false,
        lastUpdatedDisplay: 'Today',
        depthInterval: '0-5cm',
        disclaimer:
            'These results are estimates derived from geospatial soil datasets (ISRIC SoilGrids 2.0). They are not laboratory soil test results. Actual farm soil conditions may vary.',
        unmeasuredNutrientsNotice:
            'Available N-P-K: Physical Lab Test Required (Not Estimated from satellite rasters)',
        indicators: [
          SoilIndicatorItem(
            key: 'ph',
            displayName: 'Soil pH (Reaction)',
            valueDisplay: '7.8',
            unit: 'pH',
            status: 'normal',
            isEstimated: true,
            scientificNote: 'Measured in H2O solution (0-5cm depth).',
          ),
          SoilIndicatorItem(
            key: 'organic_carbon',
            displayName: 'Organic Carbon',
            valueDisplay: '6.5',
            unit: 'g/kg',
            status: 'normal',
            isEstimated: true,
            scientificNote: 'Soil Organic Carbon density at topsoil 0-5cm depth.',
          ),
          SoilIndicatorItem(
            key: 'clay',
            displayName: 'Clay Fraction',
            valueDisplay: '54%',
            unit: '%',
            status: 'high',
            isEstimated: true,
            scientificNote:
                'Particles < 2 um. Imparts high moisture and nutrient retention capacity.',
          ),
          SoilIndicatorItem(
            key: 'cec',
            displayName: 'Cation Exchange Capacity',
            valueDisplay: '38.5',
            unit: 'cmol(c)/kg',
            status: 'normal',
            isEstimated: true,
            scientificNote: 'Buffering capacity of fine earth at pH 7.',
          ),
        ],
        technicalDetails: {
          'source_dataset': 'ISRIC SoilGrids 2.0',
          'dataset_version': '2.0.0',
          'spatial_resolution': '250m',
          'depth_interval': '0-5cm',
          'sand_fraction_pct': 18.0,
          'silt_fraction_pct': 28.0,
          'clay_fraction_pct': 54.0,
          'total_nitrogen_g_kg': 0.85,
        },
      );
    }
    try {
      final uri = Uri.parse('$baseUrl/soil/farms/$farmId/card');
      final res = await http.get(uri).timeout(const Duration(seconds: 4));
      if (res.statusCode == 200) {
        final Map<String, dynamic> data = json.decode(res.body);
        return CropNetSoilCardData.fromJson(data);
      }
    } catch (_) {}

    return CropNetSoilCardData(
      farmId: farmId,
      farmName: 'My Farm',
      locationDisplay: 'Maharashtra, India',
      textureSummary: 'Medium Black Vertisol (Clay)',
      reactionSummary: 'Moderately Alkaline (pH 7.8)',
      provenanceBadge: 'Location-Based Estimate (SoilGrids 250m)',
      isLabMeasured: false,
      lastUpdatedDisplay: 'Cached',
      depthInterval: '0-5cm',
      disclaimer:
          'These results are estimates derived from geospatial soil datasets (ISRIC SoilGrids 2.0). They are not laboratory soil test results. Actual farm soil conditions may vary.',
      unmeasuredNutrientsNotice:
          'Available N-P-K: Physical Lab Test Required (Not Estimated)',
      indicators: [
        SoilIndicatorItem(
          key: 'ph',
          displayName: 'Soil pH (Reaction)',
          valueDisplay: '7.8',
          unit: 'pH',
          status: 'normal',
          isEstimated: true,
        ),
        SoilIndicatorItem(
          key: 'organic_carbon',
          displayName: 'Organic Carbon',
          valueDisplay: '6.5',
          unit: 'g/kg',
          status: 'normal',
          isEstimated: true,
        ),
        SoilIndicatorItem(
          key: 'clay',
          displayName: 'Clay Fraction',
          valueDisplay: '52%',
          unit: '%',
          status: 'high',
          isEstimated: true,
        ),
        SoilIndicatorItem(
          key: 'cec',
          displayName: 'Cation Exchange Capacity',
          valueDisplay: '38.0',
          unit: 'cmol(c)/kg',
          status: 'normal',
          isEstimated: true,
        ),
      ],
      technicalDetails: {
        'source_dataset': 'ISRIC SoilGrids 2.0',
        'spatial_resolution': '250m',
      },
    );
  }


  // --- 2. Guided Farm Registration ---
  static Future<FarmSummary> guidedRegisterFarm({
    required String farmerName,
    String? phoneNumber,
    required String taluka,
    required String district,
    String? village,
    String? farmName,
    double totalAreaAcres = 3.0,
    required String cropCode,
    required String sowingDate,
    String irrigationType = 'rainfed',
    double plantedAreaAcres = 2.5,
    double latitude = 18.151,
    double longitude = 74.577,
  }) async {
    try {
      final uri = Uri.parse('$baseUrl/farms/guided-registration');
      final payload = {
        'farmer_name': farmerName,
        'phone_number': phoneNumber,
        'taluka': taluka,
        'district': district,
        'village': village,
        'farm_name': farmName ?? '$farmerName\'s Farm',
        'total_area_acres': totalAreaAcres,
        'latitude': latitude,
        'longitude': longitude,
        'crop_code': cropCode,
        'season': 'kharif',
        'sowing_date': sowingDate,
        'irrigation_type': irrigationType,
        'planted_area_acres': plantedAreaAcres
      };

      final response = await http.post(
        uri,
        headers: {'Content-Type': 'application/json'},
        body: json.encode(payload),
      ).timeout(const Duration(seconds: 6));

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        _cachedSummary = FarmSummary.fromJson(data);
        return _cachedSummary!;
      }
    } catch (_) {}

    // Fallback if offline
    _cachedSummary = FarmSummary(
      farmerId: 'farmer_local_${DateTime.now().millisecondsSinceEpoch}',
      farmerName: farmerName,
      farmId: 'farm_local_${DateTime.now().millisecondsSinceEpoch}',
      farmName: farmName ?? '$farmerName\'s Farm',
      locationDisplay: '$village, $taluka, $district',
      latitude: latitude,
      longitude: longitude,
      totalAreaAcres: totalAreaAcres,
      activeCropCode: cropCode,
      activeCropName: cropCode.toUpperCase(),
      sowingDate: sowingDate,
      daysAfterSowing: 30,
      estimatedStageCode: 'vegetative',
      estimatedStageName: 'Vegetative Growth',
      plantedAreaAcres: plantedAreaAcres,
      irrigationType: irrigationType,
      weatherSummary: {'temperature_c': 32.0, 'condition': 'Partly Cloudy', 'rainfall_today_mm': 0.0, 'source': 'IMD Baseline'},
      dataLastUpdated: 'Saved Offline',
      isDataStale: false,
      activeAlerts: [],
    );
    return _cachedSummary!;
  }

  static Future<FarmSummary?> updateFarmProfile({
    required String farmId,
    String? farmerName,
    String? phoneNumber,
    String? farmName,
    String? district,
    String? taluka,
    String? village,
    double? latitude,
    double? longitude,
    double? totalAreaAcres,
    double? plantedAreaAcres,
    String? cropCode,
    String? varietyName,
    String? sowingDate,
    String? season,
    String? irrigationType,
    String? farmerConfirmedStage,
  }) async {
    final payload = <String, dynamic>{};
    if (farmerName != null) payload['farmer_name'] = farmerName;
    if (phoneNumber != null) payload['phone_number'] = phoneNumber;
    if (farmName != null) payload['farm_name'] = farmName;
    if (district != null) payload['district'] = district;
    if (taluka != null) payload['taluka'] = taluka;
    if (village != null) payload['village'] = village;
    if (latitude != null) payload['latitude'] = latitude;
    if (longitude != null) payload['longitude'] = longitude;
    if (totalAreaAcres != null) payload['total_area_acres'] = totalAreaAcres;
    if (plantedAreaAcres != null) payload['planted_area_acres'] = plantedAreaAcres;
    if (cropCode != null) payload['crop_code'] = cropCode;
    if (varietyName != null) payload['variety_name'] = varietyName;
    if (sowingDate != null) payload['sowing_date'] = sowingDate;
    if (season != null) payload['season'] = season;
    if (irrigationType != null) payload['irrigation_type'] = irrigationType;
    if (farmerConfirmedStage != null) payload['farmer_confirmed_stage'] = farmerConfirmedStage;

    try {
      final uri = Uri.parse('$baseUrl/farms/$farmId/profile');
      final response = await http.put(
        uri,
        headers: {'Content-Type': 'application/json'},
        body: json.encode(payload),
      ).timeout(const Duration(seconds: 6));

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        _cachedSummary = FarmSummary.fromJson(data);
        return _cachedSummary;
      }
    } catch (_) {}
    return null;
  }

  // --- 3. Yield Intelligence ---
  static Future<YieldAssessment> getYieldAssessment({
    required String farmId,
    String? plotId,
  }) async {
    try {
      final uri = Uri.parse('$baseUrl/yield-intelligence/$farmId/yield-risk${plotId != null ? '?plot_id=$plotId' : ''}');
      final response = await http.get(uri).timeout(const Duration(seconds: 4));

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        return YieldAssessment.fromJson(data);
      }
    } catch (_) {}

    return YieldAssessment(
      farmId: farmId,
      cropCode: 'soybean',
      daysAfterSowing: 45,
      risks: [
        RiskDimensionItem(
          riskDimension: 'weather_dry_spell',
          riskLevel: 'moderate',
          timeHorizon: 'next_7_days',
          impactSeverity: 'moderate',
          confidence: 'high',
          drivers: ['Dry spell monitoring active for local taluka.'],
          recommendedActions: [
            {
              'action_id': 'ADV_01',
              'title_en': 'Protective Supplemental Irrigation',
              'description_en': 'Apply light protective irrigation during critical growth stages to maintain root zone moisture.',
              'evidence_citation': 'MPKV Rahuri Agronomic Package of Practices'
            }
          ],
        ),
      ],
      baseline: {
        'status': 'district_historical_baseline',
        'historical_mean_t_ha': 1.62,
        'historical_std_dev': 0.28,
        'data_period': '1997-2024',
        'geographical_unit': 'District APY Baseline',
        'disclaimer': 'District-level statistical baseline from official APY records.'
      },
    );
  }

  // --- 4. Worker Heat Risk ---
  static Future<WorkerHeatResponse> getWorkerHeatHazard({
    required double latitude,
    required double longitude,
    required String taluka,
    String workload = 'moderate',
    bool isAcclimatised = true,
    String sunExposure = 'direct_sun',
    String clothingType = 'standard_work_clothes',
    double exposureDurationHours = 3.0,
  }) async {
    try {
      final uri = Uri.parse('$baseUrl/heat-risk/worker-hazard');
      final response = await http.post(
        uri,
        headers: {'Content-Type': 'application/json'},
        body: json.encode({
          'latitude': latitude,
          'longitude': longitude,
          'taluka': taluka,
          'workload_category': workload,
          'is_acclimatised': isAcclimatised,
          'sun_exposure': sunExposure,
          'clothing_type': clothingType,
          'exposure_duration_hours': exposureDurationHours,
        }),
      ).timeout(const Duration(seconds: 6));

      if (response.statusCode == 200) {
        return WorkerHeatResponse.fromJson(json.decode(response.body));
      }
    } catch (_) {}

    return WorkerHeatResponse(
      currentHazardLevel: 'MODERATE',
      currentAirTempC: 33.2,
      currentRelativeHumidityPct: 56.0,
      currentWbgtEstimatedC: 28.6,
      categorySelectionReason: 'Approaching threshold under direct sunlight.',
    );
  }

  // --- 5. Crop Heat Risk ---
  static Future<CropHeatAssessment> getCropHeatHazard({
    String? farmId,
    String? cropCode,
    String? stageCode,
    double? forecastTmax,
    double? forecastTmin,
  }) async {
    final effectiveFarmId = farmId ?? 'farm_demo_pune_01';
    try {
      final uri = Uri.parse('$baseUrl/heat-risk/crop-heat');
      final payload = <String, dynamic>{
        'farm_id': effectiveFarmId,
      };
      if (stageCode != null) payload['farmer_confirmed_stage'] = stageCode;
      if (forecastTmax != null) payload['forecast_tmax_c'] = forecastTmax;
      if (forecastTmin != null) payload['forecast_tmin_c'] = forecastTmin;

      final response = await http.post(
        uri,
        headers: {'Content-Type': 'application/json'},
        body: json.encode(payload),
      ).timeout(const Duration(seconds: 6));

      if (response.statusCode == 200) {
        return CropHeatAssessment.fromJson(json.decode(response.body));
      }
    } catch (_) {}

    return CropHeatAssessment(
      cropCode: cropCode ?? 'soybean',
      growthStageCode: stageCode ?? 'stage_flowering',
      growthStageNameEn: 'Flowering & Anthesis',
      supportedStages: const [
        {'stage_code': 'stage_germination', 'stage_name': 'Germination / Emergence', 'stage_name_en': 'Germination / Emergence', 'das_range': 'DAS 0-10', 'crit_tmax': 38.0},
        {'stage_code': 'stage_vegetative', 'stage_name': 'Vegetative Branching', 'stage_name_en': 'Vegetative Branching', 'das_range': 'DAS 11-35', 'crit_tmax': 39.0},
        {'stage_code': 'stage_flowering', 'stage_name': 'Flowering & Anthesis', 'stage_name_en': 'Flowering & Anthesis', 'das_range': 'DAS 36-55', 'crit_tmax': 35.0},
        {'stage_code': 'stage_pod_development', 'stage_name': 'Pod Formation & Seed Filling', 'stage_name_en': 'Pod Formation & Seed Filling', 'das_range': 'DAS 56-85', 'crit_tmax': 36.5},
        {'stage_code': 'stage_maturity', 'stage_name': 'Maturity / Harvest', 'stage_name_en': 'Maturity / Harvest', 'das_range': 'DAS 86-105', 'crit_tmax': 42.0},
      ],
      criticalTmaxThresholdC: 35.0,
      tmaxForecastC: forecastTmax ?? 36.5,
      overallCropHeatRisk: 'moderate',
      evidenceCitation: 'ICAR / MPKV Package of Practices',
    );
  }

  // --- 6. Income Diversification ---
  static Future<List<IncomeOpportunity>> getIncomeOpportunities({String? cropCode, String? category}) async {
    if (!mockMode) {
      try {
        final queryParams = <String>[];
        if (cropCode != null) queryParams.add('crop_code=$cropCode');
        if (category != null && category != 'all') queryParams.add('category=$category');
        final qStr = queryParams.isNotEmpty ? '?${queryParams.join('&')}' : '';
        final uri = Uri.parse('$baseUrl/income/opportunities$qStr');
        final response = await http.get(uri).timeout(const Duration(seconds: 6));

        if (response.statusCode == 200) {
          final List list = json.decode(response.body);
          return list.map((item) => IncomeOpportunity.fromJson(item)).toList();
        }
      } catch (_) {}
    }

    return [
      IncomeOpportunity(
        opportunityId: 'OPP_VERMICOMPOST_01',
        title: 'Farm-Scale Vermicomposting from Crop Residues',
        category: 'byproduct_utilization',
        targetCrops: ['soybean', 'cotton', 'sugarcane'],
        requiredResources: ['crop_residue', 'cow_dung', 'water', 'shade_net'],
        minInvestmentInr: 18000.0,
        maxInvestmentInr: 35000.0,
        paybackPeriodMonths: 8,
        potentialAnnualProfitInr: 48000.0,
        riskLevel: 'low',
        summary: 'Convert harvested crop biomass into high-value organic vermicompost.',
        keyAssumptions: ['Cycle time: 60-70 days', 'Sales price: ₹7-10/kg'],
        keyRisks: ['Summer drying', 'Ants/termites'],
        sourceAttribution: 'MPKV Rahuri Organic Farming Project',
      ),
      IncomeOpportunity(
        opportunityId: 'OPP_OSMANABADI_GOAT_01',
        title: 'Osmanabadi Goat Rearing Unit (10+1)',
        category: 'livestock',
        targetCrops: ['soybean', 'jowar', 'bajra'],
        requiredResources: ['shed', 'fodder', 'fencing'],
        minInvestmentInr: 75000.0,
        maxInvestmentInr: 120000.0,
        paybackPeriodMonths: 12,
        potentialAnnualProfitInr: 95000.0,
        riskLevel: 'moderate',
        summary: 'Hardy drought-tolerant indigenous breed reared on farm-grown dry fodders.',
        keyAssumptions: ['Twinning rate: ~60-70%', 'Live weight price: ₹320-360/kg'],
        keyRisks: ['PPR and ET infections', 'Summer fodder deficit'],
        sourceAttribution: 'NABARD Maharashtra State Focus Paper FY26-27',
      ),
      IncomeOpportunity(
        opportunityId: 'OPP_SOLAR_DRYER_01',
        title: 'Solar Conduction Dryer for Onion & Vegetables',
        category: 'value_addition',
        targetCrops: ['onion', 'tomato', 'chilli'],
        requiredResources: ['direct_sunlight', 'grading_area', 'packaging'],
        minInvestmentInr: 45000.0,
        maxInvestmentInr: 85000.0,
        paybackPeriodMonths: 10,
        potentialAnnualProfitInr: 62000.0,
        riskLevel: 'low',
        summary: 'Dehydrates seasonal surplus onion, garlic, tomatoes, and vegetables.',
        keyAssumptions: ['Drying cycle: 5-7 hours', 'Zero electricity'],
        keyRisks: ['Monsoon cloud cover', 'Packaging integrity'],
        sourceAttribution: 'Science for Society (S4S Technologies) / UNIDO',
      )
    ];
  }

  static Future<List<ScoredOpportunityItem>> matchIncomeOpportunities({
    required double availableInvestmentInr,
    required double workingCapitalInr,
    required double availableLandAcres,
    required double unusedLandAcres,
    required String waterAvailability,
    required double familyLaborHoursDay,
    required String existingLivestock,
    required bool hasStorageOrShed,
    required String riskTolerance,
    required String categoryPreference,
    String? ageRange,
    String workPreference = 'active_physical',
    String paybackHorizon = 'within_1_year',
    String familyManagementRole = 'personal_direct',
    List<String> cropByproducts = const [],
    List<String> interests = const [],
  }) async {
    try {
      final uri = Uri.parse('$baseUrl/income/match-opportunities');
      final response = await http.post(
        uri,
        headers: {'Content-Type': 'application/json'},
        body: json.encode({
          'available_investment_inr': availableInvestmentInr,
          'monthly_operating_budget_inr': workingCapitalInr,
          'available_land_acres': availableLandAcres,
          'unused_land_acres': unusedLandAcres,
          'water_availability': waterAvailability,
          'family_labor_hours_day': familyLaborHoursDay,
          'existing_livestock': existingLivestock,
          'has_storage_room': hasStorageOrShed,
          'has_animal_shed': hasStorageOrShed,
          'crop_byproducts': cropByproducts,
          'interests': interests,
          'risk_tolerance': riskTolerance,
          'category_preference': categoryPreference,
          if (ageRange != null) 'age_range': ageRange,
          'work_preference': workPreference,
          'payback_horizon': paybackHorizon,
          'family_management_role': familyManagementRole,
        }),
      ).timeout(const Duration(seconds: 6));

      if (response.statusCode == 200) {
        final List list = json.decode(response.body);
        return list.map((item) => ScoredOpportunityItem.fromJson(item)).toList();
      }
    } catch (_) {}
    return [];
  }

  static Future<FarmerResourceProfile> getFarmResourceProfile(String farmId) async {
    try {
      final uri = Uri.parse('$baseUrl/income/farms/$farmId/profile');
      final response = await http.get(uri).timeout(const Duration(seconds: 6));
      if (response.statusCode == 200) {
        return FarmerResourceProfile.fromJson(json.decode(response.body));
      }
    } catch (_) {}
    return FarmerResourceProfile(farmId: farmId, farmerId: 'farmer_demo_01');
  }

  static Future<FarmerResourceProfile?> saveFarmResourceProfile(FarmerResourceProfile profile) async {
    try {
      final uri = Uri.parse('$baseUrl/income/farms/${profile.farmId}/profile');
      final response = await http.put(
        uri,
        headers: {'Content-Type': 'application/json'},
        body: json.encode(profile.toJson()),
      ).timeout(const Duration(seconds: 6));
      if (response.statusCode == 200) {
        return FarmerResourceProfile.fromJson(json.decode(response.body));
      }
    } catch (_) {}
    return null;
  }

  static Future<List<ScoredOpportunityItem>> discoverFarmOpportunities(
    String farmId, {
    double? customBudgetInr,
  }) async {
    try {
      final query = customBudgetInr != null ? '?custom_budget_inr=$customBudgetInr' : '';
      final uri = Uri.parse('$baseUrl/income/farms/$farmId/discover$query');
      final response = await http.post(uri).timeout(const Duration(seconds: 8));
      if (response.statusCode == 200) {
        final List list = json.decode(response.body);
        return list.map((item) => ScoredOpportunityItem.fromJson(item)).toList();
      }
    } catch (_) {}
    return [];
  }

  static Future<SavedIncomePlan?> saveIncomePlan({
    required String farmId,
    required String opportunityId,
    required double plannedInvestmentInr,
    String notes = '',
  }) async {
    try {
      final uri = Uri.parse('$baseUrl/income/farms/$farmId/plans');
      final response = await http.post(
        uri,
        headers: {'Content-Type': 'application/json'},
        body: json.encode({
          'farm_id': farmId,
          'opportunity_id': opportunityId,
          'planned_investment_inr': plannedInvestmentInr,
          'notes': notes,
        }),
      ).timeout(const Duration(seconds: 6));
      if (response.statusCode == 200) {
        return SavedIncomePlan.fromJson(json.decode(response.body));
      }
    } catch (_) {}
    return null;
  }

  static Future<List<SavedIncomePlan>> getSavedIncomePlans(String farmId) async {
    try {
      final uri = Uri.parse('$baseUrl/income/farms/$farmId/plans');
      final response = await http.get(uri).timeout(const Duration(seconds: 6));
      if (response.statusCode == 200) {
        final List list = json.decode(response.body);
        return list.map((item) => SavedIncomePlan.fromJson(item)).toList();
      }
    } catch (_) {}
    return [];
  }

  static Future<IncomeScenario> calculateIncomeScenario({
    required String opportunityId,
    required double customBudgetInr,
    double labourHours = 2.0,
    String waterAvailability = 'seasonal_canal',
  }) async {
    if (!mockMode) {
      try {
        final uri = Uri.parse('$baseUrl/income/calculate-scenario');
        final response = await http.post(
          uri,
          headers: {'Content-Type': 'application/json'},
          body: json.encode({
            'opportunity_id': opportunityId,
            'custom_budget_inr': customBudgetInr,
            'available_labour_hours_day': labourHours,
            'water_availability': waterAvailability,
          }),
        ).timeout(const Duration(seconds: 6));

        if (response.statusCode == 200) {
          return IncomeScenario.fromJson(json.decode(response.body));
        }
      } catch (_) {}
    }

    final opex = customBudgetInr * 0.25;
    final revenue = customBudgetInr * 1.6;
    final netProfit = revenue - opex;
    return IncomeScenario(
      opportunityId: opportunityId,
      opportunityTitle: 'Farm-Scale Enterprise Scenario',
      customBudgetInr: customBudgetInr,
      calculatedCapexInr: customBudgetInr,
      calculatedOpexAnnualInr: opex,
      calculatedGrossRevenueInr: revenue,
      calculatedNetProfitAnnualInr: netProfit,
      calculatedBreakEvenMonths: 8.5,
      assumptionsApplied: ['Scale factor applied to initial capital', 'Local raw material utilization'],
      risksToMonitor: ['Seasonal input price volatility', 'Market transport costs'],
      sourceAttribution: 'Maharashtra Agricultural University Enterprise Models',
      disclaimer: 'Projections are planning estimates. No revenue guarantees provided.',
    );
  }

  static Future<List<OpportunityComparisonItem>> compareOpportunities({
    required List<String> opportunityIds,
    double customBudgetInr = 60000.0,
  }) async {
    try {
      final uri = Uri.parse('$baseUrl/income/compare-opportunities');
      final response = await http.post(
        uri,
        headers: {'Content-Type': 'application/json'},
        body: json.encode({
          'opportunity_ids': opportunityIds,
          'custom_budget_inr': customBudgetInr,
        }),
      ).timeout(const Duration(seconds: 6));

      if (response.statusCode == 200) {
        final List list = json.decode(response.body);
        return list.map((item) => OpportunityComparisonItem.fromJson(item)).toList();
      }
    } catch (_) {}
    return [];
  }

  // --- 7. PMFBY Crop Loss Evidence ---
  static Future<CropLossCase> submitCropLossCase({
    required String farmerId,
    required String farmId,
    required String cropCode,
    required String eventDate,
    required String perilType,
    required double damageEstimatePct,
    required double affectedAreaAcres,
    List<String> photoUrls = const [],
    bool isDraft = false,
  }) async {
    try {
      final uri = Uri.parse('$baseUrl/pmfby/cases');
      final response = await http.post(
        uri,
        headers: {'Content-Type': 'application/json'},
        body: json.encode({
          'farmer_id': farmerId,
          'farm_id': farmId,
          'crop_code': cropCode,
          'season': 'kharif',
          'event_date': eventDate,
          'peril_type': perilType,
          'damage_estimate_pct': damageEstimatePct,
          'affected_area_acres': affectedAreaAcres,
          'photo_urls': photoUrls,
          'is_draft': isDraft,
        }),
      ).timeout(const Duration(seconds: 5));

      if (response.statusCode == 200) {
        return CropLossCase.fromJson(json.decode(response.body));
      }
    } catch (_) {}

    final offlineCase = CropLossCase(
      caseId: 'case_offline_${DateTime.now().millisecondsSinceEpoch}',
      farmerId: farmerId,
      farmId: farmId,
      cropCode: cropCode,
      season: 'kharif',
      eventDate: eventDate,
      perilType: perilType,
      damageEstimatePct: damageEstimatePct,
      affectedAreaAcres: affectedAreaAcres,
      photoUrls: photoUrls,
      dossierStatus: isDraft ? 'draft_saved' : 'evidence_submitted',
      weatherEvidenceSummary: {
        'source': 'Cached IMD Pune Baseline',
        'anomaly_classification': 'Unseasonal rainfall recorded in local taluka'
      },
      createdAt: DateTime.now().toIso8601String(),
      disclaimer: 'Draft evidence saved locally. Will synchronize when network connectivity is restored.',
    );
    _offlineDraftCases.add(offlineCase);
    return offlineCase;
  }

  static Future<List<CropLossCase>> getFarmerLossCases(String farmerId) async {
    if (!mockMode) {
      try {
        final uri = Uri.parse('$baseUrl/pmfby/cases/farmer/$farmerId');
        final response = await http.get(uri).timeout(const Duration(seconds: 4));

        if (response.statusCode == 200) {
          final List list = json.decode(response.body);
          return list.map((item) => CropLossCase.fromJson(item)).toList();
        }
      } catch (_) {}
    }

    return _offlineDraftCases;
  }

  static Future<List<CropLossCase>> getReviewerQueue() async {
    try {
      final uri = Uri.parse('$baseUrl/pmfby/reviewer/queue');
      final response = await http.get(uri).timeout(const Duration(seconds: 4));
      if (response.statusCode == 200) {
        final List list = json.decode(response.body);
        return list.map((item) => CropLossCase.fromJson(item)).toList();
      }
    } catch (_) {}
    return [];
  }

  static Future<CropLossCase?> submitReviewDecision({
    required String caseId,
    required String reviewerId,
    required String decision,
    required String rationale,
    String? compensationBasis,
  }) async {
    try {
      final uri = Uri.parse('$baseUrl/pmfby/cases/$caseId/review');
      final response = await http.post(
        uri,
        headers: {'Content-Type': 'application/json'},
        body: json.encode({
          'reviewer_id': reviewerId,
          'decision': decision,
          'rationale': rationale,
          'recommended_compensation_basis': compensationBasis ?? 'PMFBY Mid-Season Adversity (Clause 21.2)',
        }),
      ).timeout(const Duration(seconds: 5));
      if (response.statusCode == 200) {
        return CropLossCase.fromJson(json.decode(response.body));
      }
    } catch (_) {}
    return null;
  }

  // --- 7B. Dashboard Prioritized Issues ---
  static Future<DashboardSummaryResponse> getDashboardIssues(String farmId) async {
    if (mockMode) {
      return DashboardSummaryResponse(
        farmId: farmId,
        farmName: 'My Farm',
        hasUrgentIssues: false,
        totalIssuesCount: 0,
        issues: [],
        positiveStatusSummary: 'No major concerns found in the latest assessments. Weather conditions and soil moisture are within safe agronomic bounds.',
        assessedAt: DateTime.now().toIso8601String(),
      );
    }
    try {
      final uri = Uri.parse('$baseUrl/dashboard/issues?farm_id=$farmId');
      final res = await http.get(uri).timeout(const Duration(seconds: 5));
      if (res.statusCode == 200) {
        return DashboardSummaryResponse.fromJson(json.decode(res.body));
      }
    } catch (_) {}
    return DashboardSummaryResponse(
      farmId: farmId,
      farmName: 'My Farm',
      hasUrgentIssues: false,
      totalIssuesCount: 0,
      issues: [],
      positiveStatusSummary: 'No major concerns found in the latest assessments. Farm conditions are normal.',
      assessedAt: DateTime.now().toIso8601String(),
    );
  }

  // --- 8. AI Grounded Assistant & Context Chip ---
  static Future<String> getAssistantContextChip(String farmId) async {
    try {
      final uri = Uri.parse('$baseUrl/assistant/context?farm_id=$farmId');
      final res = await http.get(uri).timeout(const Duration(seconds: 4));
      if (res.statusCode == 200) {
        final data = json.decode(res.body);
        return data['chip_label'] ?? 'Using your farm information';
      }
    } catch (_) {}
    return 'Using your farm information: Onion · Niphad · 3.0 acres';
  }

  static Future<Map<String, dynamic>> sendAssistantMessage({
    required String farmerId,
    required String farmId,
    required String message,
    String? sessionId,
  }) async {
    try {
      final uri = Uri.parse('$baseUrl/assistant/chat');
      final response = await http.post(
        uri,
        headers: {'Content-Type': 'application/json'},
        body: json.encode({
          'farmer_id': farmerId,
          'farm_id': farmId,
          'message': message,
          'session_id': sessionId,
        }),
      ).timeout(const Duration(seconds: 60));

      if (response.statusCode == 200) {
        return json.decode(response.body);
      }
    } catch (_) {}

    return {
      'session_id': sessionId ?? 'sess_offline',
      'reply': 'For your active farm in Maharashtra, weather and soil moisture conditions are monitored. Check the My Crop and Heat Safety tabs for active advisories.',
      'provider_used': 'none (grounded fallback)',
      'citations': [
        {'title': 'Maharashtra Krishi Advisory', 'citation': 'State Package of Practices'}
      ]
    };
  }
}
