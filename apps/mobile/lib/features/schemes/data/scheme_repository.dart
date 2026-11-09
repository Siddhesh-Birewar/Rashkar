import '../../../core/network/api_client.dart';
import '../../../core/network/api_constants.dart';
import '../models/scheme_models.dart';

/// Repository for the Government Schemes module.
///
/// Communicates with FastAPI `/api/v1/schemes` endpoints. Public read methods
/// (list / search / filter / detail) mirror the crops knowledge base; admin
/// mutation methods require the authenticated user to have admin rights.
class SchemeRepository {
  final ApiClient _client;

  static SchemeRepository? _instance;
  static SchemeRepository get instance => _instance ??= SchemeRepository();

  SchemeRepository({ApiClient? client}) : _client = client ?? ApiClient();

  List<GovernmentScheme> _parseList(dynamic json) {
    final list = json as List<dynamic>;
    return list
        .map((item) => GovernmentScheme.fromJson(item as Map<String, dynamic>))
        .toList();
  }

  Future<List<GovernmentScheme>> listSchemes({
    String? search,
    String? category,
    String? governmentLevel,
    String? state,
    String? status,
    String? verificationStatus,
  }) async {
    final queryParams = <String, dynamic>{};
    if (search != null && search.trim().isNotEmpty) queryParams['search'] = search.trim();
    if (category != null && category.isNotEmpty) queryParams['category'] = category;
    if (governmentLevel != null && governmentLevel.isNotEmpty) {
      queryParams['government_level'] = governmentLevel;
    }
    if (state != null && state.isNotEmpty) queryParams['state'] = state;
    if (status != null && status.isNotEmpty) queryParams['status'] = status;
    if (verificationStatus != null && verificationStatus.isNotEmpty) {
      queryParams['verification_status'] = verificationStatus;
    }

    return _client.get<List<GovernmentScheme>>(
      ApiConstants.schemes,
      queryParameters: queryParams.isEmpty ? null : queryParams,
      fromJson: _parseList,
    );
  }

  Future<GovernmentScheme> getScheme(String schemeId) {
    return _client.get<GovernmentScheme>(
      ApiConstants.schemeById(schemeId),
      fromJson: (json) => GovernmentScheme.fromJson(json as Map<String, dynamic>),
    );
  }

  Future<SchemeFilterOptions> getFilterOptions() {
    return _client.get<SchemeFilterOptions>(
      ApiConstants.schemesFilters,
      fromJson: (json) => SchemeFilterOptions.fromJson(json as Map<String, dynamic>),
    );
  }

  Future<bool> isAdmin() async {
    final res = await _client.get<Map<String, dynamic>>(
      ApiConstants.schemesAdminStatus,
      fromJson: (json) => json as Map<String, dynamic>,
    );
    return res['is_admin'] == true;
  }

  // --- Admin operations ---

  Future<GovernmentScheme> createScheme(Map<String, dynamic> payload) {
    return _client.post<GovernmentScheme>(
      ApiConstants.schemes,
      body: payload,
      fromJson: (json) => GovernmentScheme.fromJson(json as Map<String, dynamic>),
    );
  }

  Future<GovernmentScheme> updateScheme(String schemeId, Map<String, dynamic> payload) {
    return _client.put<GovernmentScheme>(
      ApiConstants.schemeById(schemeId),
      body: payload,
      fromJson: (json) => GovernmentScheme.fromJson(json as Map<String, dynamic>),
    );
  }

  Future<GovernmentScheme> setSchemeStatus(
    String schemeId, {
    String? status,
    String? verificationStatus,
  }) {
    final queryParams = <String, dynamic>{};
    if (status != null) queryParams['status'] = status;
    if (verificationStatus != null) queryParams['verification_status'] = verificationStatus;
    return _client.patch<GovernmentScheme>(
      ApiConstants.schemeStatus(schemeId),
      queryParameters: queryParams,
      fromJson: (json) => GovernmentScheme.fromJson(json as Map<String, dynamic>),
    );
  }

  Future<void> deleteScheme(String schemeId) async {
    await _client.delete<dynamic>(ApiConstants.schemeById(schemeId));
  }

  Future<Map<String, dynamic>> seedSchemes() {
    return _client.post<Map<String, dynamic>>(
      ApiConstants.schemesSeed,
      fromJson: (json) => json as Map<String, dynamic>,
    );
  }
}
