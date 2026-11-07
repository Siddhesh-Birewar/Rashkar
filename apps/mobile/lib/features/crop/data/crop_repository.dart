import '../../../core/network/api_client.dart';
import '../../../core/network/api_constants.dart';
import '../models/crop_models.dart';

/// Repository for the Agricultural Knowledge Base and Crop Specifications.
///
/// Communicates with FastAPI `/api/v1/crops` and `/api/v1/agriculture/seasons` endpoints.
class CropRepository {
  final ApiClient _client;

  CropRepository({ApiClient? client}) : _client = client ?? ApiClient();

  /// List all crops in the Knowledge Base, optionally filtered by category or season.
  Future<List<CropCatalogSummary>> listCrops({
    String? category,
    String? season,
  }) async {
    final queryParams = <String, dynamic>{};
    if (category != null) queryParams['category'] = category;
    if (season != null) queryParams['season'] = season;

    return _client.get<List<CropCatalogSummary>>(
      ApiConstants.crops,
      queryParameters: queryParams.isEmpty ? null : queryParams,
      fromJson: (json) {
        final list = json as List<dynamic>;
        return list
            .map((item) => CropCatalogSummary.fromJson(item as Map<String, dynamic>))
            .toList();
      },
    );
  }

  /// Retrieve full agronomic profile and requirements for a single crop.
  Future<CropFullProfile> getCropProfile(String cropId) async {
    return _client.get<CropFullProfile>(
      ApiConstants.cropById(cropId),
      fromJson: (json) => CropFullProfile.fromJson(json as Map<String, dynamic>),
    );
  }

  /// Retrieve modular requirement packages (soil, climate, seasons, water) for a crop.
  Future<Map<String, dynamic>> getCropRequirements(String cropId) async {
    return _client.get<Map<String, dynamic>>(
      ApiConstants.cropRequirements(cropId),
      fromJson: (json) => json as Map<String, dynamic>,
    );
  }

  /// Retrieve cited authoritative research publications and sources for a crop.
  Future<List<AgriculturalKnowledgeSource>> getCropSources(String cropId) async {
    return _client.get<List<AgriculturalKnowledgeSource>>(
      ApiConstants.cropSources(cropId),
      fromJson: (json) {
        final list = json as List<dynamic>;
        return list
            .map((item) => AgriculturalKnowledgeSource.fromJson(item as Map<String, dynamic>))
            .toList();
      },
    );
  }

  /// Retrieve standard agricultural cropping seasons in Maharashtra.
  Future<List<MaharashtraSeasonCalendar>> listMaharashtraSeasons() async {
    return _client.get<List<MaharashtraSeasonCalendar>>(
      ApiConstants.agricultureSeasons,
      fromJson: (json) {
        final list = json as List<dynamic>;
        return list
            .map((item) =>
                MaharashtraSeasonCalendar.fromJson(item as Map<String, dynamic>))
            .toList();
      },
    );
  }
}
