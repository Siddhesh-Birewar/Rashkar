import 'dart:async';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:http_parser/http_parser.dart';

import '../../../core/network/api_client.dart';
import '../../../core/network/api_constants.dart';
import '../../../core/network/api_exception.dart';
import '../models/soil_lab_models.dart';

/// Repository managing physical soil laboratory reports, OCR extraction review,
/// per-parameter corrections, and farmer transcription confirmation.
class SoilLabRepository {
  final ApiClient _client;
  final http.Client _httpClient;

  SoilLabRepository({ApiClient? client, http.Client? httpClient})
      : _client = client ?? ApiClient(),
        _httpClient = httpClient ?? http.Client();

  static const int maxFileSizeBytes = 15 * 1024 * 1024; // 15 MB

  /// Path builder for farm soil reports base endpoint.
  String _reportsBasePath(String farmId) => '${ApiConstants.farms}/$farmId/soil-reports';

  /// Upload a physical soil laboratory report document (PDF, JPEG, PNG, max 15MB).
  Future<SoilReportUploadResponse> uploadReport(
    String farmId, {
    required List<int> fileBytes,
    required String fileName,
    required String mimeType,
    String? laboratoryName,
    String? sampleDepth,
    DateTime? sampleCollectionDate,
    String? samplingPointName,
    void Function(double progress)? onProgress,
  }) async {
    // 1. Client-side size validation
    if (fileBytes.length > maxFileSizeBytes) {
      throw ValidationException(
        message: 'File size (${(fileBytes.length / (1024 * 1024)).toStringAsFixed(2)} MB) '
            'exceeds the maximum allowed limit of 15 MB.',
      );
    }

    // 2. Client-side format validation
    final lowerName = fileName.toLowerCase();
    final lowerMime = mimeType.toLowerCase();
    final isValidExtension = lowerName.endsWith('.pdf') ||
        lowerName.endsWith('.png') ||
        lowerName.endsWith('.jpg') ||
        lowerName.endsWith('.jpeg');
    final isValidMime = lowerMime.contains('pdf') ||
        lowerMime.contains('image/png') ||
        lowerMime.contains('image/jpeg') ||
        lowerMime.contains('image/jpg');

    if (!isValidExtension && !isValidMime) {
      throw const ValidationException(
        message: 'Unsupported document format. Please upload a PDF, PNG, or JPEG file.',
      );
    }

    onProgress?.call(0.1);

    // 3. Prepare multipart request
    final uri = Uri.parse('${_client.baseUrl}${_reportsBasePath(farmId)}/upload');
    final request = http.MultipartRequest('POST', uri);

    // Inject authentication headers
    String? token = _client.bearerToken;
    final provider = _client.authTokenProvider ?? ApiClient.defaultAuthTokenProvider;
    if (provider != null) {
      try {
        token = await provider();
      } catch (_) {}
    }

    if (token != null && token.isNotEmpty) {
      request.headers['Authorization'] = 'Bearer $token';
    } else if (_client.devUserId != null && _client.devUserId!.isNotEmpty) {
      request.headers[ApiConstants.devUserIdHeader] = _client.devUserId!;
    }

    request.headers['Accept'] = 'application/json';

    // Add metadata form fields (supporting both laboratory_name and lab_name)
    if (laboratoryName != null && laboratoryName.isNotEmpty) {
      request.fields['laboratory_name'] = laboratoryName;
      request.fields['lab_name'] = laboratoryName;
    }
    if (sampleDepth != null && sampleDepth.isNotEmpty) {
      request.fields['sample_depth_interval'] = sampleDepth;
    }
    if (sampleCollectionDate != null) {
      request.fields['sample_collection_date'] = sampleCollectionDate.toIso8601String();
    }
    if (samplingPointName != null && samplingPointName.isNotEmpty) {
      request.fields['sampling_point_name'] = samplingPointName;
    }

    // Attach file with explicit MediaType
    final effectiveMime = mimeType.isNotEmpty
        ? mimeType
        : (lowerName.endsWith('.pdf')
            ? 'application/pdf'
            : (lowerName.endsWith('.png') ? 'image/png' : 'image/jpeg'));
    MediaType? mediaType;
    try {
      mediaType = MediaType.parse(effectiveMime);
    } catch (_) {
      mediaType = MediaType('application', 'octet-stream');
    }

    final multipartFile = http.MultipartFile.fromBytes(
      'file',
      fileBytes,
      filename: fileName,
      contentType: mediaType,
    );
    request.files.add(multipartFile);

    onProgress?.call(0.5);

    // 4. Send request
    http.StreamedResponse streamedResponse;
    try {
      streamedResponse = await _httpClient.send(request).timeout(const Duration(seconds: 60));
    } on TimeoutException catch (e) {
      throw RequestTimeoutException(timeout: const Duration(seconds: 60), details: e);
    } on http.ClientException catch (e) {
      throw NetworkException(message: 'Connection failed: ${e.message}', details: e);
    } catch (e) {
      throw NetworkException(message: 'Unexpected network error during upload: $e', details: e);
    }

    final response = await http.Response.fromStream(streamedResponse);
    onProgress?.call(0.9);

    if (response.statusCode >= 200 && response.statusCode < 300) {
      onProgress?.call(1.0);
      final dynamic decoded = jsonDecode(utf8.decode(response.bodyBytes));
      return SoilReportUploadResponse.fromJson(Map<String, dynamic>.from(decoded as Map));
    }

    // Handle error
    dynamic errorBody;
    try {
      errorBody = jsonDecode(utf8.decode(response.bodyBytes));
    } catch (_) {
      errorBody = response.body;
    }

    final errorMsg = errorBody is Map && errorBody['detail'] != null
        ? errorBody['detail'].toString()
        : 'Upload failed with HTTP ${response.statusCode}';

    if (response.statusCode == 400) {
      throw BadRequestException(message: errorMsg, details: errorBody);
    } else if (response.statusCode == 401) {
      throw UnauthorizedException(message: errorMsg, details: errorBody);
    } else if (response.statusCode == 403) {
      throw ForbiddenException(message: errorMsg, details: errorBody);
    } else if (response.statusCode == 422) {
      throw ValidationException(message: errorMsg, details: errorBody);
    } else {
      throw ServerException(
        message: errorMsg,
        statusCode: response.statusCode,
        details: errorBody,
      );
    }
  }

  /// List all past uploaded soil laboratory reports for a given farm.
  Future<List<SoilReportSummary>> listReports(String farmId) async {
    return _client.get<List<SoilReportSummary>>(
      _reportsBasePath(farmId),
      fromJson: (json) {
        if (json is List) {
          return json
              .map((item) => SoilReportSummary.fromJson(Map<String, dynamic>.from(item as Map)))
              .toList();
        }
        return [];
      },
    );
  }

  /// Retrieve full report details including storage path, status, and all measurements.
  Future<SoilReportDetail> getReportDetail(String farmId, String reportId) async {
    return _client.get<SoilReportDetail>(
      '${_reportsBasePath(farmId)}/$reportId',
      fromJson: (json) => SoilReportDetail.fromJson(Map<String, dynamic>.from(json as Map)),
    );
  }

  /// Retrieve all extracted individual measurements for a specific report.
  Future<List<SoilMeasurementItem>> getMeasurements(String farmId, String reportId) async {
    return _client.get<List<SoilMeasurementItem>>(
      '${_reportsBasePath(farmId)}/$reportId/measurements',
      fromJson: (json) {
        if (json is List) {
          return json
              .map((item) => SoilMeasurementItem.fromJson(Map<String, dynamic>.from(item as Map)))
              .toList();
        }
        return [];
      },
    );
  }

  /// Submit a farmer correction for an individual measurement item.
  Future<SoilMeasurementItem> updateMeasurement(
    String farmId,
    String reportId,
    String measurementId,
    SoilMeasurementUpdate update,
  ) async {
    final path = '${_reportsBasePath(farmId)}/$reportId/measurements/$measurementId';
    return _client.put<SoilMeasurementItem>(
      path,
      body: update.toJson(),
      fromJson: (json) => SoilMeasurementItem.fromJson(Map<String, dynamic>.from(json as Map)),
    );
  }

  /// Explicit farmer confirmation action.
  /// Transitions report to CONFIRMED and activates reviewed measurements for agronomic use.
  Future<SoilReportDetail> confirmReport(
    String farmId,
    String reportId, {
    List<String>? confirmedMeasurementIds,
  }) async {
    final path = '${_reportsBasePath(farmId)}/$reportId/confirm';
    final body = confirmedMeasurementIds != null
        ? {'measurement_ids': confirmedMeasurementIds}
        : <String, dynamic>{};

    return _client.post<SoilReportDetail>(
      path,
      body: body,
      fromJson: (json) => SoilReportDetail.fromJson(Map<String, dynamic>.from(json as Map)),
    );
  }

  /// Re-trigger OCR extraction pipeline (e.g. after transient extraction failure).
  Future<SoilReportDetail> reprocessReport(String farmId, String reportId) async {
    final path = '${_reportsBasePath(farmId)}/$reportId/reprocess';
    return _client.post<SoilReportDetail>(
      path,
      fromJson: (json) => SoilReportDetail.fromJson(Map<String, dynamic>.from(json as Map)),
    );
  }

  /// Generate a fresh short-lived private signed URL for document viewing.
  Future<String> getDocumentUrl(
    String farmId,
    String reportId, {
    int expiresInSeconds = 3600,
  }) async {
    final path = '${_reportsBasePath(farmId)}/$reportId/document-url';
    return _client.get<String>(
      path,
      queryParameters: {'expires_in_seconds': expiresInSeconds},
      fromJson: (json) {
        if (json is Map) {
          return json['signed_url'] as String? ??
              json['signedUrl'] as String? ??
              json['url'] as String? ??
              '';
        }
        if (json is String) return json;
        return '';
      },
    );
  }

  /// Retrieve the latest confirmed laboratory report for a farm, if one exists.
  /// Used by dual-source soil intelligence to prioritize verified lab measurements.
  Future<SoilReportDetail?> getLatestConfirmedReport(String farmId) async {
    try {
      final summaries = await listReports(farmId);
      final confirmed = summaries.where((s) => s.status == SoilReportStatus.confirmed).toList();
      if (confirmed.isEmpty) return null;

      // Sort by sampleDate or uploadTimestamp descending
      confirmed.sort((a, b) {
        final dateA = a.sampleDate ?? a.uploadTimestamp;
        final dateB = b.sampleDate ?? b.uploadTimestamp;
        return dateB.compareTo(dateA);
      });

      return await getReportDetail(farmId, confirmed.first.id);
    } catch (_) {
      return null;
    }
  }

  void close() {
    _client.close();
    _httpClient.close();
  }
}
