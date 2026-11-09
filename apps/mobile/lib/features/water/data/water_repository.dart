import 'dart:async';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:http_parser/http_parser.dart';

import '../../../core/network/api_client.dart';
import '../../../core/network/api_constants.dart';
import '../../../core/network/api_exception.dart';
import '../models/water_models.dart';

/// Repository managing irrigation water sources, laboratory test reports,
/// SAR/RSC calculations, and institutional water quality evaluations.
class WaterRepository {
  final ApiClient _client;
  final http.Client _httpClient;

  WaterRepository({ApiClient? client, http.Client? httpClient})
      : _client = client ?? ApiClient(),
        _httpClient = httpClient ?? http.Client();

  static const int maxFileSizeBytes = 15 * 1024 * 1024; // 15 MB

  String _waterBasePath(String farmId) => '${ApiConstants.farms}/$farmId/water';

  // ---------------------------------------------------------------------------
  // WATER SOURCES
  // ---------------------------------------------------------------------------

  Future<List<WaterSource>> getWaterSources(String farmId) async {
    try {
      final res = await _client.get('${_waterBasePath(farmId)}/sources');
      final list = res as List<dynamic>;
      return list.map((e) => WaterSource.fromJson(e as Map<String, dynamic>)).toList();
    } catch (_) {
      return [];
    }
  }

  Future<WaterSource> createWaterSource(
    String farmId, {
    required WaterSourceType sourceType,
    required String name,
    String? locationDescription,
    double? latitude,
    double? longitude,
    String seasonalAvailability = 'perennial',
    String reliability = 'reliable',
    double? dailyAvailableHours,
    String irrigationMethod = 'drip',
    double? measuredCapacityLph,
    String capacityProvenance = 'FARMER_REPORTED',
  }) async {
    final payload = {
      'source_type': sourceType.toApiString(),
      'name': name,
      'location_description': locationDescription,
      'latitude': latitude,
      'longitude': longitude,
      'seasonal_availability': seasonalAvailability,
      'reliability': reliability,
      'daily_available_hours': dailyAvailableHours,
      'irrigation_method': irrigationMethod,
      'measured_capacity_lph': measuredCapacityLph,
      'capacity_provenance': capacityProvenance,
    };
    final res = await _client.post('${_waterBasePath(farmId)}/sources', body: payload);
    return WaterSource.fromJson(res as Map<String, dynamic>);
  }

  Future<void> deleteWaterSource(String farmId, String sourceId) async {
    await _client.delete('${_waterBasePath(farmId)}/sources/$sourceId');
  }

  // ---------------------------------------------------------------------------
  // WATER LAB REPORTS
  // ---------------------------------------------------------------------------

  Future<List<WaterReportSummary>> getWaterReports(String farmId) async {
    try {
      final res = await _client.get('${_waterBasePath(farmId)}/reports');
      final list = res as List<dynamic>;
      return list.map((e) => WaterReportSummary.fromJson(e as Map<String, dynamic>)).toList();
    } catch (_) {
      return [];
    }
  }

  Future<WaterQualityEvaluation> getWaterEvaluation(String farmId, {String? waterSourceId}) async {
    final query = <String, dynamic>{};
    if (waterSourceId != null) query['water_source_id'] = waterSourceId;
    final res = await _client.get('${_waterBasePath(farmId)}/evaluation', queryParameters: query);
    return WaterQualityEvaluation.fromJson(res as Map<String, dynamic>);
  }

  Future<WaterReportSummary> uploadWaterReport(
    String farmId, {
    required List<int> fileBytes,
    required String fileName,
    required String mimeType,
    String? waterSourceId,
    String? laboratoryName,
    DateTime? reportDate,
    String? samplingLocation,
  }) async {
    if (fileBytes.length > maxFileSizeBytes) {
      throw ValidationException(
        message: 'File size (${(fileBytes.length / (1024 * 1024)).toStringAsFixed(2)} MB) '
            'exceeds the 15 MB limit.',
      );
    }

    final uri = Uri.parse('${_client.baseUrl}${_waterBasePath(farmId)}/reports/upload');
    final request = http.MultipartRequest('POST', uri);

    String? token = _client.bearerToken;
    final provider = _client.authTokenProvider ?? ApiClient.defaultAuthTokenProvider;
    if (provider != null) {
      try {
        token = await provider();
      } catch (_) {}
    }

    if (token != null && token.isNotEmpty) {
      request.headers['Authorization'] = 'Bearer $token';
    } else {
      // Dev-only fallback (compile-time DEV_AUTH flag) for local prototype uploads.
      final effectiveDevUserId = _client.devUserId ?? ApiClient.defaultDevUserId;
      if (effectiveDevUserId != null && effectiveDevUserId.isNotEmpty) {
        request.headers[ApiConstants.devUserIdHeader] = effectiveDevUserId;
      }
    }

    request.headers['Accept'] = 'application/json';

    if (waterSourceId != null) request.fields['water_source_id'] = waterSourceId;
    if (laboratoryName != null) request.fields['laboratory_name'] = laboratoryName;
    if (reportDate != null) request.fields['report_date'] = reportDate.toIso8601String();
    if (samplingLocation != null) request.fields['sampling_location'] = samplingLocation;

    MediaType? parsedContentType;
    try {
      parsedContentType = MediaType.parse(mimeType);
    } catch (_) {
      parsedContentType = MediaType('application', 'octet-stream');
    }

    final multipartFile = http.MultipartFile.fromBytes(
      'file',
      fileBytes,
      filename: fileName,
      contentType: parsedContentType,
    );
    request.files.add(multipartFile);

    final streamed = await _httpClient.send(request);
    final response = await http.Response.fromStream(streamed);

    if (response.statusCode >= 200 && response.statusCode < 300) {
      final dynamic decoded = jsonDecode(utf8.decode(response.bodyBytes));
      return WaterReportSummary.fromJson(Map<String, dynamic>.from(decoded as Map));
    }

    throw NetworkException(
      message: 'Failed to upload water report with status ${response.statusCode}: ${response.body}',
    );
  }
}
