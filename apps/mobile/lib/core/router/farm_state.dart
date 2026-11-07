import 'package:flutter/foundation.dart';
import 'package:cropnet_mobile/main.dart';
import 'package:cropnet_mobile/features/farm/data/farm_repository.dart' as data;
import 'package:cropnet_mobile/features/farm/models/farm_models.dart';

/// Central Farm Repository providing reactive state management and lookup
/// for all routing branches, deep linking, and URL synchronization.
///
/// Wraps the typed HTTP data repository [data.FarmRepository] and manages
/// authentic multi-tenant user farm state with zero hardcoded demo data.
class FarmRepository extends ChangeNotifier {
  static final FarmRepository _instance = FarmRepository._internal();
  static FarmRepository get instance => _instance;

  factory FarmRepository() => _instance;

  final data.FarmRepository _dataRepo;

  FarmRepository._internal({data.FarmRepository? dataRepo})
      : _dataRepo = dataRepo ?? data.FarmRepository();

  final List<FarmItem> _farms = [];
  bool _isLoading = false;
  String? _error;
  String? _selectedFarmId;

  List<FarmItem> get farms => List.unmodifiable(_farms);
  bool get isLoading => _isLoading;
  String? get error => _error;
  String? get selectedFarmId => _selectedFarmId;

  set selectedFarmId(String? id) {
    if (_selectedFarmId != id) {
      _selectedFarmId = id;
      notifyListeners();
    }
  }

  void selectFarm(String? id) {
    if (_selectedFarmId != id) {
      _selectedFarmId = id;
      notifyListeners();
    }
  }

  FarmItem? getFarmById(String id) {
    try {
      return _farms.firstWhere((f) => f.id == id);
    } catch (_) {
      return null;
    }
  }

  /// Load authenticated user's farms from FastAPI backend.
  Future<void> loadFarms() async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final realFarms = await _dataRepo.listFarms();
      _farms.clear();
      for (final f in realFarms) {
        _farms.add(FarmItem.fromFarm(f));
      }
    } catch (e) {
      _error = e.toString();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  /// Create a new farm via FastAPI and prepend to active state.
  Future<FarmItem> createFarm(FarmCreate payload) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final created = await _dataRepo.createFarm(payload);
      final item = FarmItem.fromFarm(created);
      _farms.insert(0, item);
      return item;
    } catch (e) {
      _error = e.toString();
      rethrow;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  /// Update an existing farm via FastAPI.
  Future<FarmItem> updateFarmRemote(String farmId, FarmUpdate payload) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final updated = await _dataRepo.updateFarm(farmId, payload);
      final item = FarmItem.fromFarm(updated);
      final idx = _farms.indexWhere((f) => f.id == farmId);
      if (idx != -1) {
        _farms[idx] = item;
      }
      return item;
    } catch (e) {
      _error = e.toString();
      rethrow;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  /// Delete an existing farm via FastAPI.
  Future<void> deleteFarmRemote(String farmId) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      await _dataRepo.deleteFarm(farmId);
      _farms.removeWhere((f) => f.id == farmId);
      if (_selectedFarmId == farmId) {
        _selectedFarmId = _farms.isNotEmpty ? _farms.first.id : null;
      }
    } catch (e) {
      _error = e.toString();
      rethrow;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  void addFarm(FarmItem farm) {
    final index = _farms.indexWhere((f) => f.id == farm.id);
    if (index != -1) {
      _farms[index] = farm;
    } else {
      _farms.insert(0, farm);
    }
    notifyListeners();
  }

  void updateFarm(FarmItem farm) {
    final index = _farms.indexWhere((f) => f.id == farm.id);
    if (index != -1) {
      _farms[index] = farm;
    } else {
      _farms.insert(0, farm);
    }
    notifyListeners();
  }

  void deleteFarm(String farmId) {
    _farms.removeWhere((f) => f.id == farmId);
    if (_selectedFarmId == farmId) {
      _selectedFarmId = _farms.isNotEmpty ? _farms.first.id : null;
    }
    notifyListeners();
  }

  /// Clears repository state (e.g. on user logout).
  void clear() {
    _farms.clear();
    _error = null;
    _isLoading = false;
    _selectedFarmId = null;
    notifyListeners();
  }

  /// Resets repository back to empty baseline.
  void resetToDefault() {
    clear();
  }
}
