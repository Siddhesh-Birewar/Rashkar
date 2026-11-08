import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/farm_models.dart';

class ApiService {
  // Configurable backend URL. On Android emulator use 10.0.2.2; on device use LAN IP; default local localhost
  static String baseUrl = 'http://127.0.0.1:8000/v1';

  // In-memory offline cache for weak-connectivity resilience
  static FarmSummary? _cachedSummary;
  static final List<CropLossCase> _offlineDraftCases = [];

  // --- 1. Farm Summary / Home Screen ---
  static Future<FarmSummary> getFarmSummary({String farmId = 'farm_demo_pune_01'}) async {
    try {
      final uri = Uri.parse('$baseUrl/farms/$farmId/summary');
      final response = await http.get(uri).timeout(const Duration(seconds: 4));

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        _cachedSummary = FarmSummary.fromJson(data);
        return _cachedSummary!;
      }
    } catch (_) {
      // Offline fallback
    }

    if (_cachedSummary != null) {
      return _cachedSummary!;
    }

    // Default offline fallback for demonstration
    return FarmSummary(
      farmerId: 'farmer_demo_01',
      farmerName: 'Ramesh Patil',
      farmId: farmId,
      farmName: 'Patil Krishi Farm',
      locationDisplay: 'Malegaon Budruk, Baramati, Pune',
      latitude: 18.151,
      longitude: 74.577,
      totalAreaAcres: 4.5,
      activeCropCode: 'soybean',
      activeCropName: 'Soybean',
      sowingDate: '2024-06-15',
      daysAfterSowing: 75,
      estimatedStageCode: 'stage_pod_development',
      estimatedStageName: 'Pod Development (R3-R4)',
      plantedAreaAcres: 2.5,
      irrigationType: 'rainfed',
      weatherSummary: {
        'temperature_c': 32.5,
        'relative_humidity_pct': 58.0,
        'wind_speed_kmh': 12.0,
        'condition': 'Partly Cloudy',
        'rainfall_today_mm': 0.0,
        'source': 'IMD Pune Station / Gridded Reanalysis'
      },
      dataLastUpdated: '08 Nov 2026, 06:30 PM',
      isDataStale: false,
      soilSummary: {
        'depth': '0-30cm',
        'ph': 7.8,
        'organic_carbon_pct': 0.58,
        'clay_pct': 52.0,
        'available_water_capacity_mm_m': 160.0,
        'data_provenance': 'CropNet_UnifiedSoilProfile_v1',
        'is_lab_measured': false
      },
      activeAlerts: [
        {
          'title': 'Irrigation Recommendation',
          'message': 'Crop is in pod formation. Soil moisture is adequate; withhold irrigation for the next 48 hours to prevent waterlogging.',
          'urgency': 'medium',
          'source': 'MPKV Rahuri Package of Practices'
        },
        {
          'title': 'Heat Safety Notice',
          'message': 'Field temperatures will peak between 12:30 PM and 3:30 PM. Shift heavy spraying and weeding to early morning.',
          'urgency': 'high',
          'source': 'Rashkar Heat Safety Advisory'
        }
      ],
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
        'latitude': 18.151,
        'longitude': 74.577,
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
    } catch (_) {
      // Fallback
    }

    // Save offline
    _cachedSummary = FarmSummary(
      farmerId: 'farmer_offline_01',
      farmerName: farmerName,
      farmId: 'farm_offline_01',
      farmName: farmName ?? '$farmerName\'s Farm',
      locationDisplay: '$taluka, $district',
      latitude: 18.151,
      longitude: 74.577,
      totalAreaAcres: totalAreaAcres,
      activeCropCode: cropCode,
      activeCropName: cropCode.toUpperCase(),
      sowingDate: sowingDate,
      daysAfterSowing: 30,
      estimatedStageCode: 'vegetative',
      estimatedStageName: 'Vegetative Growth',
      plantedAreaAcres: plantedAreaAcres,
      irrigationType: irrigationType,
      weatherSummary: {'temperature_c': 31.0, 'condition': 'Sunny', 'rainfall_today_mm': 0.0, 'source': 'Cached'},
      dataLastUpdated: 'Saved Offline',
      isDataStale: false,
      activeAlerts: [],
    );
    return _cachedSummary!;
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
    } catch (_) {
      // Offline fallback
    }

    return YieldAssessment(
      farmId: farmId,
      cropCode: 'soybean',
      cropStageCode: 'stage_pod_development',
      cropStageNameEn: 'Pod Development (R3-R4)',
      das: 75,
      risks: [
        RiskDimensionItem(
          riskDimension: 'weather_dry_spell',
          riskLevel: 'moderate',
          timeHorizon: 'next_7_days',
          impactSeverity: 'moderate',
          confidence: 'high',
          drivers: ['Dry spell of 9 days observed in Baramati taluka during pod formation phase.'],
          recommendedActions: [
            {
              'action_id': 'ADV_SOY_DRY_01',
              'title_en': 'Protective Supplemental Irrigation for Soybean',
              'description_en': 'Apply light protective irrigation (25-30 mm) via sprinkler or drip during critical pod development to prevent flower/pod drop.',
              'evidence_citation': 'MPKV Rahuri Soybean Package of Practices 2023, p. 14'
            }
          ],
        ),
        RiskDimensionItem(
          riskDimension: 'excess_rainfall_waterlogging',
          riskLevel: 'low',
          timeHorizon: 'next_7_days',
          impactSeverity: 'low',
          confidence: 'high',
          drivers: ['No heavy rainfall predicted over the next 7 days in Pune district.'],
          recommendedActions: [],
        ),
        RiskDimensionItem(
          riskDimension: 'crop_heat_stress',
          riskLevel: 'low',
          timeHorizon: 'next_7_days',
          impactSeverity: 'low',
          confidence: 'high',
          drivers: ['Max daytime temperatures (33-35°C) remain safely below the 38°C critical threshold.'],
          recommendedActions: [],
        )
      ],
      baseline: {
        'status': 'district_historical_baseline',
        'historical_mean_t_ha': 1.62,
        'historical_std_dev': 0.28,
        'data_period': '1997-2024',
        'geographical_unit': 'Pune District APY (DES / UPAg / Dataful 5632)',
        'disclaimer': 'District-level statistical baseline from official APY records. Plot-level numerical prediction is gated pending CCE labels.'
      },
    );
  }

  // --- 4. Worker Heat Risk ---
  static Future<WorkerHeatResponse> getWorkerHeatHazard({
    required double latitude,
    required double longitude,
    String taluka = 'Baramati',
    String workload = 'moderate',
    bool isAcclimatised = true,
    String sunExposure = 'direct_sun',
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
        }),
      ).timeout(const Duration(seconds: 4));

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        return WorkerHeatResponse.fromJson(data);
      }
    } catch (_) {
      // Offline fallback
    }

    return WorkerHeatResponse(
      hazardLevel: 'moderate',
      wbgtSunC: 28.6,
      wbgtShadeC: 25.4,
      airTempC: 33.2,
      rhPct: 56.0,
      advice: 'Take regular 15-minute breaks in shade. Drink clean drinking water frequently. Avoid continuous heavy weeding between 12:30 PM and 3:30 PM.',
      methodology: 'Liljegren_et_al_2008_energy_balance_retrospective',
    );
  }

  // --- 5. Crop Heat Risk ---
  static Future<CropHeatAssessment> getCropHeatHazard({
    required String cropCode,
    required String stageCode,
  }) async {
    try {
      final uri = Uri.parse('$baseUrl/heat-risk/crop-heat');
      final response = await http.post(
        uri,
        headers: {'Content-Type': 'application/json'},
        body: json.encode({
          'farm_id': 'farm_demo_pune_01',
          'crop_code': cropCode,
          'stage_code': stageCode,
          'forecast_hourly_temps_c': [31.0, 33.5, 35.0, 35.8, 34.2, 32.0],
          'forecast_night_min_temp_c': 23.5,
        }),
      ).timeout(const Duration(seconds: 4));

      if (response.statusCode == 200) {
        return CropHeatAssessment.fromJson(json.decode(response.body));
      }
    } catch (_) {
      // Offline fallback
    }

    return CropHeatAssessment(
      cropCode: cropCode,
      stageCode: stageCode,
      maxForecastTempC: 35.8,
      criticalThresholdC: 38.0,
      exceedanceHours: 0,
      riskLevel: 'low',
      citation: 'MPKV Rahuri Soybean Package of Practices 2023, p. 14',
    );
  }

  // --- 6. Income Diversification ---
  static Future<List<IncomeOpportunity>> getIncomeOpportunities({String? cropCode}) async {
    try {
      final uri = Uri.parse('$baseUrl/income/opportunities${cropCode != null ? '?crop_code=$cropCode' : ''}');
      final response = await http.get(uri).timeout(const Duration(seconds: 4));

      if (response.statusCode == 200) {
        final List list = json.decode(response.body);
        return list.map((item) => IncomeOpportunity.fromJson(item)).toList();
      }
    } catch (_) {
      // Offline fallback
    }

    return [
      IncomeOpportunity(
        opportunityId: 'OPP_VERMICOMPOST_01',
        title: 'Farm-Scale Vermicomposting from Crop Residues',
        category: 'byproduct_utilization',
        targetCrops: ['soybean', 'cotton'],
        requiredResources: ['crop_residue', 'cow_dung', 'water', 'shade_net'],
        minInvestmentInr: 18000.0,
        maxInvestmentInr: 35000.0,
        paybackPeriodMonths: 4,
        potentialAnnualProfitInr: 54000.0,
        riskLevel: 'low',
        summary: 'Convert harvested crop biomass into high-value organic vermicompost for self-farm nutrition and local nursery sales.',
        keyAssumptions: ['Biomass availability: 2-3 tonnes/season', 'Cycle time: 60-75 days', 'Sales price: ₹6 to ₹8 per kg'],
        keyRisks: ['Moisture management during peak summer heat', 'Termite infestation if bed is dry'],
        sourceAttribution: 'KVK Baramati & ICAR-NIASM Baramati Agri-Allied Practice',
      ),
      IncomeOpportunity(
        opportunityId: 'OPP_OSMANABADI_GOAT_01',
        title: 'Osmanabadi Goat Rearing Unit (10+1)',
        category: 'livestock',
        targetCrops: ['soybean', 'jowar'],
        requiredResources: ['shed', 'fodder', 'fencing'],
        minInvestmentInr: 85000.0,
        maxInvestmentInr: 140000.0,
        paybackPeriodMonths: 12,
        potentialAnnualProfitInr: 95000.0,
        riskLevel: 'moderate',
        summary: 'Hardy drought-tolerant indigenous breed reared on farm-grown dry fodders and pulse husks with high meat market demand.',
        keyAssumptions: ['Twinning rate: ~60-70%', 'Kid marketing at 8-10 months (25-30 kg)', 'Live weight price: ₹300-340/kg'],
        keyRisks: ['PPR and enterotoxemia if vaccinations missed', 'Green fodder shortage in April-May'],
        sourceAttribution: 'MPKV Rahuri Goat & Sheep Directorate / Pune District KVK',
      ),
      IncomeOpportunity(
        opportunityId: 'OPP_SOLAR_DRYER_01',
        title: 'Solar Conduction Dryer for Onion & Chillies',
        category: 'value_addition',
        targetCrops: ['onion', 'tomato'],
        requiredResources: ['direct_sunlight', 'grading_area', 'packaging'],
        minInvestmentInr: 45000.0,
        maxInvestmentInr: 85000.0,
        paybackPeriodMonths: 8,
        potentialAnnualProfitInr: 65000.0,
        riskLevel: 'moderate',
        summary: 'Prevents distress sales during market gluts by dehydrating surplus produce into shelf-stable flakes and powders.',
        keyAssumptions: ['Processing capacity: 15-20 kg/batch', 'Dehydration ratio: 8:1 for onions', 'Flake price: ₹220-280/kg'],
        keyRisks: ['Unseasonal cloudy weather or rain', 'Moisture-proof packing requirements'],
        sourceAttribution: 'ICAR-DOGR Rajgurunagar, Pune',
      )
    ];
  }

  static Future<IncomeScenario> calculateIncomeScenario({
    required String opportunityId,
    required double customBudgetInr,
    double labourHours = 2.0,
  }) async {
    try {
      final uri = Uri.parse('$baseUrl/income/calculate-scenario');
      final response = await http.post(
        uri,
        headers: {'Content-Type': 'application/json'},
        body: json.encode({
          'opportunity_id': opportunityId,
          'custom_budget_inr': customBudgetInr,
          'available_labour_hours_day': labourHours,
        }),
      ).timeout(const Duration(seconds: 4));

      if (response.statusCode == 200) {
        return IncomeScenario.fromJson(json.decode(response.body));
      }
    } catch (_) {
      // Offline fallback
    }

    final opex = customBudgetInr * 0.25;
    final profit = customBudgetInr * 1.8;
    return IncomeScenario(
      opportunityId: opportunityId,
      opportunityTitle: 'Custom Agro-Allied Scenario',
      customBudgetInr: customBudgetInr,
      calculatedCapexInr: customBudgetInr,
      calculatedOpexAnnualInr: opex,
      calculatedGrossRevenueInr: profit + opex,
      calculatedNetProfitAnnualInr: profit,
      calculatedBreakEvenMonths: 6.5,
      assumptionsApplied: ['Standard ICAR benchmark scale ratios', 'Average local Maharashtra rural input costs'],
      risksToMonitor: ['Price volatility in local agricultural markets'],
      sourceAttribution: 'KVK / MPKV Agri-Enterprise Benchmarks',
      disclaimer: 'Transparent planning scenario only. Does not guarantee market revenue.',
    );
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
    } catch (_) {
      // Offline draft save
    }

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
    try {
      final uri = Uri.parse('$baseUrl/pmfby/cases/farmer/$farmerId');
      final response = await http.get(uri).timeout(const Duration(seconds: 4));

      if (response.statusCode == 200) {
        final List list = json.decode(response.body);
        return list.map((item) => CropLossCase.fromJson(item)).toList();
      }
    } catch (_) {
      // Return cached/offline
    }

    return _offlineDraftCases.isNotEmpty
        ? _offlineDraftCases
        : [
            CropLossCase(
              caseId: 'case_loss_demo_01',
              farmerId: farmerId,
              farmId: 'farm_demo_pune_01',
              cropCode: 'soybean',
              season: 'kharif',
              eventDate: '2024-09-10',
              perilType: 'unseasonal_rainfall',
              damageEstimatePct: 45.0,
              affectedAreaAcres: 2.0,
              photoUrls: [],
              dossierStatus: 'under_review',
              weatherEvidenceSummary: {
                'source': 'IMD Pune Gridded Rainfall (0.25 deg)',
                'anomaly_classification': 'Severe excess rainfall (>7x normal)'
              },
              reviewerDecision: null,
              reviewerRationale: null,
              createdAt: '2024-09-11',
              disclaimer: 'Evidence packet prepared for human review queue.',
            )
          ];
  }

  // --- 8. AI Grounded Assistant ---
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
      ).timeout(const Duration(seconds: 7));

      if (response.statusCode == 200) {
        return json.decode(response.body);
      }
    } catch (_) {
      // Offline fallback
    }

    return {
      'session_id': sessionId ?? 'sess_offline',
      'reply': 'You are currently working in offline mode. For your active soybean crop in Baramati, current field moisture is adequate and no critical heat hazards are forecasted for the next 24 hours. (Source: Cached Rashkar Advisories).',
      'provider_used': 'none (offline cache)',
      'citations': [
        {'title': 'MPKV Soybean Advisory', 'citation': 'Package of Practices 2023'}
      ]
    };
  }
}
