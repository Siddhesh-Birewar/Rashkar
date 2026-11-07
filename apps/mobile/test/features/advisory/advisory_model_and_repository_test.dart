import 'dart:convert';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

import 'package:cropnet_mobile/core/network/api_client.dart';
import 'package:cropnet_mobile/core/network/api_exception.dart';
import 'package:cropnet_mobile/features/advisory/data/advisory_repository.dart';
import 'package:cropnet_mobile/features/advisory/models/advisory_models.dart';

void main() {
  group('Advisory Models & Repository Tests', () {
    final sampleDecisionJson = {
      'decision_id': 'dec-2026-0301-baramati-01',
      'evaluated_at': '2026-03-01T15:00:00Z',
      'input_validation_status': 'VALID',
      'contradictions_detected': [],
      'missing_parameters_flagged': ['available_nitrogen_kg_ha'],
      'taluka_resolved': 'Baramati',
      'target_season': 'rabi',
      'language': 'en',
      'crop_outcomes': [
        {
          'crop_id': 'crop-chickpea',
          'common_name': 'Chickpea (Gram)',
          'scientific_name': 'Cicer arietinum',
          'marathi_name': 'हरभरा',
          'decision_state': 'VERIFIED_SUITABLE',
          'is_disqualified': false,
          'limiting_factors': [],
          'reproductive_risk_warnings': [],
          'missing_information': ['available_nitrogen_kg_ha'],
          'uncertainty_notes': ['Soil available N unverified; assuming conservative baseline.'],
          'applied_rules': [
            {
              'rule_id': 'RULE-SOIL-PH-CHICKPEA',
              'domain': 'soil',
              'parameter_checked': 'soil_ph',
              'rule_statement': 'Chickpea requires pH between 6.0 and 8.0 in deep clay loam',
              'condition_met': true,
              'evidence_tier': 'VERIFIED',
              'claim_verification_status': 'VERIFIED',
              'enforcement_level': 'VERIFIED_HARD_CONSTRAINT',
              'can_trigger_disqualification': true,
            }
          ],
          'citations': [
            {
              'source_id': 'src-mpkv-2022',
              'organization': 'MPKV Rahuri',
              'publication_title': 'Rabi Pulse Production Package',
              'publication_year': 2022,
              'evidence_tier': 'VERIFIED',
            }
          ],
          'explanation': 'Soil pH (7.29) and texture (Clay Loam) are ideal for Chickpea in Baramati.',
        },
        {
          'crop_id': 'crop-sugarcane',
          'common_name': 'Sugarcane',
          'scientific_name': 'Saccharum officinarum',
          'marathi_name': 'ऊस',
          'decision_state': 'UNSUITABLE_VERIFIED_CONSTRAINT',
          'is_disqualified': true,
          'limiting_factors': ['Severe water deficit; canal water unavailable in summer.'],
          'reproductive_risk_warnings': [],
          'missing_information': [],
          'uncertainty_notes': [],
          'applied_rules': [],
          'citations': [],
          'explanation': 'Sugarcane disqualified due to perennial water requirement exceeding rainfed capacity.',
        }
      ],
      'follow_up_questions': [
        {
          'question_id': 'Q-IRR-01',
          'target_parameter': 'irrigation_capacity',
          'priority': 1,
          'question_text_en': 'What is your seasonal irrigation water availability?',
          'question_text_mr': 'तुमच्याकडे सिंचनासाठी पाण्याची उपलब्धता किती काळ असते?',
          'question_type': 'choice',
          'options': ['perennial', 'seasonal_dry_by_february', 'critical_only'],
          'agronomic_rationale': 'Distinguishes perennial orchard feasibility from seasonal rainfed pulses.',
        }
      ],
      'governance_notice':
          'CropNet AI evaluates biological and environmental feasibility.',
    };

    final sampleExplanationJson = {
      'decision_id': 'dec-2026-0301-baramati-01',
      'language': 'en',
      'explanation_text':
          'Based on verified agricultural guidelines from MPKV Rahuri, Chickpea is verified suitable for your Baramati plot. Soil pH (7.29) falls comfortably within the optimum 6.0–8.0 range for deep Vertisols.',
      'generation_source': 'deterministic_fallback',
      'validation_passed': true,
      'validation_warnings': [],
      'decision_state_summary': {
        'crop-chickpea': 'VERIFIED_SUITABLE',
        'crop-sugarcane': 'UNSUITABLE_VERIFIED_CONSTRAINT',
      },
      'authoritative_citations': [
        {
          'source_id': 'src-mpkv-2022',
          'organization': 'MPKV Rahuri',
          'publication_title': 'Rabi Pulse Production Package',
          'publication_year': 2022,
          'evidence_tier': 'VERIFIED',
        }
      ],
      'follow_up_questions': [
        {
          'question_id': 'Q-IRR-01',
          'target_parameter': 'irrigation_capacity',
          'priority': 1,
          'question_text_en': 'What is your seasonal irrigation water availability?',
          'question_text_mr': 'तुमच्याकडे सिंचनासाठी पाण्याची उपलब्धता किती काळ असते?',
          'question_type': 'choice',
          'options': ['perennial', 'seasonal_dry_by_february', 'critical_only'],
          'agronomic_rationale': 'Distinguishes perennial orchard feasibility from seasonal rainfed pulses.',
        }
      ],
      'governance_notice':
          'CropNet AI explanations are strictly derived from validated deterministic agronomic decisions.',
    };

    test('FarmContextInput serializes valid structured evaluation payload', () {
      const input = FarmContextInput(
        farmId: 'farm-001',
        taluka: 'Baramati',
        soilPh: 7.29,
        soilTexture: 'Clay Loam',
        drainage: 'Well-drained',
        irrigationAvailable: true,
        targetSeason: 'rabi',
      );

      final json = input.toJson();
      expect(json['taluka'], 'Baramati');
      expect(json['soil_ph'], 7.29);
      expect(json['soil_texture'], 'Clay Loam');
      expect(json['irrigation_available'], true);
      expect(json['target_season'], 'rabi');
    });

    test('FarmEvaluationResponse parses decision states and applied rules correctly', () {
      final response = FarmEvaluationResponse.fromJson(sampleDecisionJson);

      expect(response.decisionId, 'dec-2026-0301-baramati-01');
      expect(response.talukaResolved, 'Baramati');
      expect(response.cropOutcomes.length, 2);

      final chickpea = response.cropOutcomes[0];
      expect(chickpea.cropId, 'crop-chickpea');
      expect(chickpea.decisionState, DecisionState.verifiedSuitable);
      expect(chickpea.isDisqualified, false);
      expect(chickpea.appliedRules.first.enforcementLevel, EnforcementLevel.verifiedHardConstraint);
      expect(chickpea.appliedRules.first.canTriggerDisqualification, true);

      final sugarcane = response.cropOutcomes[1];
      expect(sugarcane.cropId, 'crop-sugarcane');
      expect(sugarcane.decisionState, DecisionState.unsuitableVerifiedConstraint);
      expect(sugarcane.isDisqualified, true);

      expect(response.followUpQuestions.length, 1);
      expect(response.followUpQuestions.first.targetParameter, 'irrigation_capacity');
    });

    test('AgriculturalExplanationResponse parses explanation text and citations', () {
      final explanation = AgriculturalExplanationResponse.fromJson(sampleExplanationJson);

      expect(explanation.decisionId, 'dec-2026-0301-baramati-01');
      expect(explanation.generationSource, 'deterministic_fallback');
      expect(explanation.validationPassed, true);
      expect(explanation.decisionStateSummary['crop-chickpea'], 'VERIFIED_SUITABLE');
      expect(explanation.authoritativeCitations.length, 1);
      expect(explanation.authoritativeCitations.first.organization, 'MPKV Rahuri');
    });

    test('AdvisoryRepository.evaluateFarm executes evaluation request', () async {
      final mockClient = MockClient((request) async {
        expect(request.method, 'POST');
        expect(request.url.path, '/api/v1/agriculture/evaluate-farm');
        return http.Response(
          jsonEncode(sampleDecisionJson),
          200,
          headers: {'content-type': 'application/json; charset=utf-8'},
        );
      });

      final repo = AdvisoryRepository(client: ApiClient(httpClient: mockClient));
      final response = await repo.evaluateFarm(const FarmContextInput(
        taluka: 'Baramati',
        soilPh: 7.29,
      ));

      expect(response.decisionId, 'dec-2026-0301-baramati-01');
      expect(response.cropOutcomes.first.decisionState, DecisionState.verifiedSuitable);
    });

    test('AdvisoryRepository.explainDecision calls explain-decision endpoint', () async {
      final mockClient = MockClient((request) async {
        expect(request.method, 'POST');
        expect(request.url.path, '/api/v1/agriculture/explain-decision');
        return http.Response(
          jsonEncode(sampleExplanationJson),
          200,
          headers: {'content-type': 'application/json; charset=utf-8'},
        );
      });

      final repo = AdvisoryRepository(client: ApiClient(httpClient: mockClient));
      final explanation = await repo.explainDecision('dec-2026-0301-baramati-01', language: 'en');

      expect(explanation.validationPassed, true);
      expect(explanation.explanationText, contains('MPKV Rahuri'));
    });

    test('AdvisoryRepository.processConversation handles dialogue turns', () async {
      final mockClient = MockClient((request) async {
        expect(request.method, 'POST');
        expect(request.url.path, '/api/v1/agriculture/conversation');
        return http.Response(
          jsonEncode(sampleExplanationJson),
          200,
          headers: {'content-type': 'application/json; charset=utf-8'},
        );
      });

      final repo = AdvisoryRepository(client: ApiClient(httpClient: mockClient));
      final conversation = await repo.processConversation(
        'dec-2026-0301-baramati-01',
        'Can I cultivate chickpea without irrigation?',
      );

      expect(conversation.decisionId, 'dec-2026-0301-baramati-01');
    });

    test('AdvisoryRepository maps network timeout to RequestTimeoutException', () async {
      final mockClient = MockClient((request) async {
        await Future.delayed(const Duration(milliseconds: 50));
        return http.Response('{}', 200);
      });

      final client = ApiClient(httpClient: mockClient);
      final repo = AdvisoryRepository(client: client);

      expect(
        () => repo.evaluateFarm(
          const FarmContextInput(taluka: 'Baramati'),
          timeout: const Duration(milliseconds: 10),
        ),
        throwsA(isA<RequestTimeoutException>()),
      );
    });
  });
}
