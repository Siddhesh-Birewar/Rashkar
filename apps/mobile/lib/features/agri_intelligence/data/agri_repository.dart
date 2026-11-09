import 'dart:async';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:http_parser/http_parser.dart';

import '../../../core/network/api_client.dart';
import '../../../core/network/api_constants.dart';
import '../models/agri_models.dart';

/// Repository for the consolidated Agri Intelligence hub (Crop Doctor + Heat Risk).
class AgriIntelligenceRepository {
  final ApiClient _client;
  final http.Client _httpClient;

  static AgriIntelligenceRepository? _instance;
  static AgriIntelligenceRepository get instance =>
      _instance ??= AgriIntelligenceRepository();

  AgriIntelligenceRepository({ApiClient? client, http.Client? httpClient})
      : _client = client ?? ApiClient(),
        _httpClient = httpClient ?? http.Client();

  Future<CropDoctorResult> analyzeCropImage({
    required List<int> bytes,
    required String fileName,
    required String mimeType,
  }) async {
    final uri = Uri.parse('${_client.baseUrl}${ApiConstants.cropDoctorPredict}');
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
      final devId = _client.devUserId ?? ApiClient.defaultDevUserId;
      if (devId != null && devId.isNotEmpty) {
        request.headers[ApiConstants.devUserIdHeader] = devId;
      }
    }
    request.headers['Accept'] = 'application/json';
    MediaType? mediaType;
    try {
      mediaType = MediaType.parse(mimeType);
    } catch (_) {
      mediaType = MediaType('image', 'jpeg');
    }
    request.files.add(http.MultipartFile.fromBytes('file', bytes,
        filename: fileName, contentType: mediaType));

    final streamed = await _httpClient.send(request).timeout(const Duration(seconds: 60));
    final response = await http.Response.fromStream(streamed);
    final decoded = _decode(response.bodyBytes);
    if (response.statusCode >= 200 && response.statusCode < 300) {
      return CropDoctorResult.fromJson(decoded as Map<String, dynamic>);
    }
    throw Exception(_errorMessage(decoded, response.statusCode));
  }

  Future<CropHeatResult> assessCropHeat({
    required String cropCode,
    required double tmaxC,
    required double tminC,
    String? growthStage,
    int? daysAfterSowing,
  }) async {
    final body = {
      'crop_code': cropCode,
      'forecast_tmax_c': tmaxC,
      'forecast_tmin_c': tminC,
      if (growthStage != null) 'growth_stage': growthStage,
      if (daysAfterSowing != null) 'days_after_sowing': daysAfterSowing,
    };
    final json = await _client.post<Map<String, dynamic>>(
      ApiConstants.heatRiskCrop,
      body: body,
      fromJson: (j) => j as Map<String, dynamic>,
    );
    return CropHeatResult.fromJson(json);
  }

  Future<WorkerHeatResult> assessWorkerHeat({
    required double airTempC,
    required double relativeHumidityPct,
    double windSpeedMs = 1.5,
    double solarIrradianceWm2 = 600.0,
    String workloadCategory = 'moderate',
    bool isAcclimatised = true,
    String sunExposure = 'direct_sun',
  }) async {
    final json = await _client.post<Map<String, dynamic>>(
      ApiConstants.heatRiskWorker,
      body: {
        'air_temp_c': airTempC,
        'relative_humidity_pct': relativeHumidityPct,
        'wind_speed_ms': windSpeedMs,
        'solar_irradiance_wm2': solarIrradianceWm2,
        'workload_category': workloadCategory,
        'is_acclimatised': isAcclimatised,
        'sun_exposure': sunExposure,
      },
      fromJson: (j) => j as Map<String, dynamic>,
    );
    return WorkerHeatResult.fromJson(json);
  }

  dynamic _decode(List<int> bytes) {
    try {
      return jsonDecode(utf8.decode(bytes));
    } catch (_) {
      return null;
    }
  }

  String _errorMessage(dynamic decoded, int status) {
    if (decoded is Map && decoded['detail'] != null) return decoded['detail'].toString();
    return 'Request failed with HTTP $status';
  }
}
