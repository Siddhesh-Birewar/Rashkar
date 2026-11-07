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
  Future<FarmEvaluationResponse> evaluateFarm(
    FarmContextInput context, {
    Duration timeout = const Duration(seconds: 30),
  }) async {
    return _client.post<FarmEvaluationResponse>(
      ApiConstants.agricultureEvaluateFarm,
      body: context.toJson(),
      timeout: timeout,
      fromJson: (json) => FarmEvaluationResponse.fromJson(json as Map<String, dynamic>),
    );
  }

  /// Retrieve a previously computed farm evaluation decision by its decision ID.
  Future<FarmEvaluationResponse> getEvaluationDecision(
    String decisionId, {
    Duration timeout = const Duration(seconds: 30),
  }) async {
    return _client.get<FarmEvaluationResponse>(
      ApiConstants.agricultureDecision(decisionId),
      timeout: timeout,
      fromJson: (json) => FarmEvaluationResponse.fromJson(json as Map<String, dynamic>),
    );
  }

  /// Submit diagnostic follow-up answers to re-evaluate farm context with updated parameters.
  Future<FarmEvaluationResponse> processFollowUp(
    String decisionId,
    Map<String, dynamic> answers, {
    Duration timeout = const Duration(seconds: 30),
  }) async {
    final payload = {
      'decision_id': decisionId,
      'answers': answers,
    };
    return _client.post<FarmEvaluationResponse>(
      ApiConstants.agricultureFollowUp,
      body: payload,
      timeout: timeout,
      fromJson: (json) => FarmEvaluationResponse.fromJson(json as Map<String, dynamic>),
    );
  }

  /// Generate a natural, farmer-friendly explanation of a validated decision.
  /// Uses a dedicated 45-second timeout to allow local LLM inference while failing safely.
  Future<AgriculturalExplanationResponse> explainDecision(
    String decisionId, {
    String language = 'en',
    String? focusCrop,
    Duration timeout = const Duration(seconds: 45),
  }) async {
    final request = ExplainDecisionRequest(
      decisionId: decisionId,
      language: language,
      focusCrop: focusCrop,
    );
    return _client.post<AgriculturalExplanationResponse>(
      ApiConstants.agricultureExplainDecision,
      body: request.toJson(),
      timeout: timeout,
      fromJson: (json) =>
          AgriculturalExplanationResponse.fromJson(json as Map<String, dynamic>),
    );
  }

  /// Interactive dialogue and follow-up consultation grounded in a validated decision.
  /// Uses a dedicated 45-second timeout to accommodate multi-turn LLM reasoning.
  Future<AgriculturalExplanationResponse> processConversation(
    String decisionId,
    String message, {
    String language = 'en',
    List<ConversationMessage> history = const [],
    Map<String, dynamic>? submittedAnswers,
    Duration timeout = const Duration(seconds: 45),
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
      timeout: timeout,
      fromJson: (json) =>
          AgriculturalExplanationResponse.fromJson(json as Map<String, dynamic>),
    );
  }
}
