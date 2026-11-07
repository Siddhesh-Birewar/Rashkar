import 'dart:async';
import '../../../core/network/api_client.dart';
import '../../../core/network/api_constants.dart';
import '../models/satellite_models.dart';

/// Repository for Sentinel-2 Satellite Vegetation Intelligence.
class SatelliteRepository {
  final ApiClient _client;

  SatelliteRepository({ApiClient? client}) : _client = client ?? ApiClient();

  String _satelliteBasePath(String farmId) => '${ApiConstants.farms}/$farmId/satellite';

  Future<SatelliteObservation> syncObservations(String farmId) async {
    final res = await _client.post('${_satelliteBasePath(farmId)}/sync');
    final map = res as Map<String, dynamic>;
    final latest = map['latest_observation'] as Map<String, dynamic>;
    return SatelliteObservation.fromJson(latest);
  }

  Future<SatelliteObservation?> getLatestObservation(String farmId) async {
    try {
      final res = await _client.get('${_satelliteBasePath(farmId)}/latest');
      return SatelliteObservation.fromJson(res as Map<String, dynamic>);
    } catch (_) {
      return null;
    }
  }

  Future<List<SatelliteObservation>> getObservations(String farmId) async {
    try {
      final res = await _client.get('${_satelliteBasePath(farmId)}/observations');
      final list = res as List<dynamic>;
      return list.map((e) => SatelliteObservation.fromJson(e as Map<String, dynamic>)).toList();
    } catch (_) {
      return [];
    }
  }

  Future<VegetationTimeSeriesData> getTimeSeries(String farmId, {int months = 6}) async {
    final res = await _client.get(
      '${_satelliteBasePath(farmId)}/timeseries',
      queryParameters: {'months': months},
    );
    return VegetationTimeSeriesData.fromJson(res as Map<String, dynamic>);
  }
}
