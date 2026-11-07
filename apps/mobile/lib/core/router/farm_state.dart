import 'package:flutter/foundation.dart';
import 'package:latlong2/latlong.dart';
import 'package:cropnet_mobile/main.dart';

/// Central Farm Repository providing reactive state management and lookup
/// for all routing branches, deep linking, and URL synchronization.
class FarmRepository extends ChangeNotifier {
  static final FarmRepository _instance = FarmRepository._internal();
  static FarmRepository get instance => _instance;

  factory FarmRepository() => _instance;

  FarmRepository._internal() {
    _initializeDefaultFarms();
  }

  final List<FarmItem> _farms = [];

  List<FarmItem> get farms => List.unmodifiable(_farms);

  void _initializeDefaultFarms() {
    _farms.clear();
    _farms.add(
      FarmItem(
        id: "demo-baramati-1",
        name: "Baramati Pilot Plot",
        village: "Malegaon",
        taluka: "Baramati",
        district: "Pune",
        irrigationType: "irrigated",
        waterSource: "canal",
        polygonPoints: [
          const LatLng(18.175, 74.525),
          const LatLng(18.175, 74.535),
          const LatLng(18.185, 74.535),
          const LatLng(18.185, 74.525),
        ],
        areaHectares: 11.82,
        areaAcres: 29.21,
        centroid: const LatLng(18.180, 74.530),
        createdAt: DateTime.now().subtract(const Duration(days: 2)),
      ),
    );
  }

  FarmItem? getFarmById(String id) {
    try {
      return _farms.firstWhere((f) => f.id == id);
    } catch (_) {
      return null;
    }
  }

  void addFarm(FarmItem farm) {
    _farms.insert(0, farm);
    notifyListeners();
  }

  void updateFarm(FarmItem farm) {
    final index = _farms.indexWhere((f) => f.id == farm.id);
    if (index != -1) {
      _farms[index] = farm;
      notifyListeners();
    }
  }

  void deleteFarm(String farmId) {
    _farms.removeWhere((f) => f.id == farmId);
    notifyListeners();
  }

  /// Resets repository back to baseline (used for testing and teardown)
  void resetToDefault() {
    _initializeDefaultFarms();
    notifyListeners();
  }
}
