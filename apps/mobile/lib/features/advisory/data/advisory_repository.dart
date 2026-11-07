import '../../../core/network/api_client.dart';
import '../../../core/network/api_constants.dart';
import '../models/advisory_models.dart';

/// Repository for Deterministic Agricultural Intelligence, Decision Inspection, and Advisory Dialogue.
///
/// Communicates with FastAPI `/api/v1/agriculture` endpoints.
class AdvisoryRepository {
  final ApiClient _client;

  AdvisoryRepository({ApiClient? client}) : _client = client ?? ApiClient();

  /// Execute deterministic agricultural evaluation of candidate crops for a farm context.
  Future<FarmEvaluationResponse> evaluateFarm(FarmContextInput context) async {
    return _client.post<FarmEvaluationResponse>(
      ApiConstants.agricultureEvaluateFarm,
      body: context.toJson(),
      fromJson: (json) => FarmEvaluationResponse.fromJson(json as Map<String, dynamic>),
    );
  }

  /// Retrieve a previously computed farm evaluation decision by its decision ID.
  Future<FarmEvaluationResponse> getEvaluationDecision(String decisionId) async {
    return _client.get<FarmEvaluationResponse>(
      ApiConstants.agricultureDecision(decisionId),
      fromJson: (json) => FarmEvaluationResponse.fromJson(json as Map<String, dynamic>),
    );
  }

  /// Submit diagnostic follow-up answers to re-evaluate farm context with updated parameters.
  Future<FarmEvaluationResponse> processFollowUp(
    String decisionId,
    Map<String, dynamic> answers,
  ) async {
    final payload = {
      'decision_id': decisionId,
      'answers': answers,
    };
    return _client.post<FarmEvaluationResponse>(
      ApiConstants.agricultureFollowUp,
      body: payload,
      fromJson: (json) => FarmEvaluationResponse.fromJson(json as Map<String, dynamic>),
    );
  }

  /// Generate a natural, farmer-friendly explanation of a validated decision.
  Future<AgriculturalExplanationResponse> explainDecision(
    String decisionId, {
    String language = 'en',
    String? focusCrop,
  }) async {
    final request = ExplainDecisionRequest(
      decisionId: decisionId,
      language: language,
      focusCrop: focusCrop,
    );
    return _client.post<AgriculturalExplanationResponse>(
      ApiConstants.agricultureExplainDecision,
      body: request.toJson(),
      fromJson: (json) =>
          AgriculturalExplanationResponse.fromJson(json as Map<String, dynamic>),
    );
  }

  /// Interactive dialogue and follow-up consultation grounded in a validated decision.
  Future<AgriculturalExplanationResponse> processConversation(
    String decisionId,
    String message, {
    String language = 'en',
    List<ConversationMessage> history = const [],
    Map<String, dynamic>? submittedAnswers,
  }) async {
    final request = ConversationRequest(
      decisionId: decisionId,
      message: message,
      language: language,
      history: history,
      submittedAnswers: submittedAnswers,
    );
    return _client.post<AgriculturalExplanationResponse>(
      ApiConstants.agricultureConversation,
      body: request.toJson(),
      fromJson: (json) =>
          AgriculturalExplanationResponse.fromJson(json as Map<String, dynamic>),
    );
  }
}
