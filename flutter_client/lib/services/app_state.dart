import 'package:flutter/foundation.dart';
import '../models/farm_models.dart';
import 'api_service.dart';

class AppState extends ChangeNotifier {
  static final AppState instance = AppState._internal();
  AppState._internal();

  FarmSummary? _activeFarm;
  List<FarmSummary> _allFarms = [];
  bool _isLoading = false;
  bool _isInitialized = false;

  FarmSummary? get activeFarm => _activeFarm;
  List<FarmSummary> get allFarms => _allFarms;
  bool get isLoading => _isLoading;
  bool get isInitialized => _isInitialized;
  bool get hasActiveFarm => _activeFarm != null;

  String? get activeFarmId => _activeFarm?.farmId;
  String? get activeFarmerId => _activeFarm?.farmerId;
  String get activeCropCode => _activeFarm?.activeCropCode ?? 'soybean';
  String get activeCropName => _activeFarm?.activeCropName ?? 'Crop';
  String get activeTaluka {
    if (_activeFarm == null) return 'Baramati';
    final parts = _activeFarm!.locationDisplay.split(',');
    return parts.length > 1 ? parts[parts.length - 2].trim() : parts.first.trim();
  }
  String get activeDistrict {
    if (_activeFarm == null) return 'Pune';
    final parts = _activeFarm!.locationDisplay.split(',');
    return parts.isNotEmpty ? parts.last.trim() : 'Pune';
  }
  double get activeLatitude => _activeFarm?.latitude ?? 18.151;
  double get activeLongitude => _activeFarm?.longitude ?? 74.577;

  /// Default to clean starting state as requested by the user
  Future<void> initialize({bool forceClean = true}) async {
    _isLoading = true;
    notifyListeners();

    try {
      final farms = await ApiService.getAllFarms();
      _allFarms = farms;
      if (!forceClean && farms.isNotEmpty) {
        _activeFarm = farms.first;
      } else {
        _activeFarm = null;
      }
    } catch (_) {
      _allFarms = [];
      _activeFarm = null;
    } finally {
      _isLoading = false;
      _isInitialized = true;
      notifyListeners();
    }
  }

  Future<void> refreshFarms() async {
    try {
      final farms = await ApiService.getAllFarms();
      _allFarms = farms;
      if (_activeFarm != null) {
        final match = farms.where((f) => f.farmId == _activeFarm!.farmId);
        if (match.isNotEmpty) {
          _activeFarm = match.first;
        }
      }
      notifyListeners();
    } catch (_) {}
  }

  void setActiveFarm(FarmSummary farm) {
    _activeFarm = farm;
    if (!_allFarms.any((f) => f.farmId == farm.farmId)) {
      _allFarms.insert(0, farm);
    } else {
      final idx = _allFarms.indexWhere((f) => f.farmId == farm.farmId);
      if (idx != -1) _allFarms[idx] = farm;
    }
    notifyListeners();
  }

  Future<void> selectFarmById(String farmId) async {
    _isLoading = true;
    notifyListeners();
    try {
      final summary = await ApiService.getFarmSummary(farmId: farmId);
      if (summary != null) {
        setActiveFarm(summary);
      }
    } catch (_) {}
    _isLoading = false;
    notifyListeners();
  }

  Future<void> loadDemoFarm() async {
    _isLoading = true;
    notifyListeners();
    try {
      final summary = await ApiService.getFarmSummary(farmId: 'farm_demo_pune_01');
      if (summary != null) {
        setActiveFarm(summary);
      }
    } catch (_) {}
    _isLoading = false;
    notifyListeners();
  }

  void clearSession() {
    _activeFarm = null;
    notifyListeners();
  }
}
