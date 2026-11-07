import 'package:flutter/foundation.dart';
import 'package:cropnet_mobile/main.dart';

/// Assessment record model for historical soil and crop analyses.
class AssessmentHistoryRecord {
  final String id;
  final String farmId;
  final String farmName;
  final String taluka;
  final String assessmentType;
  final DateTime date;
  final String summary;
  final String provenance;
  final Map<String, String> keyMetrics;
  final String? cropId;
  final String? cropName;

  const AssessmentHistoryRecord({
    required this.id,
    required this.farmId,
    required this.farmName,
    required this.taluka,
    required this.assessmentType,
    required this.date,
    required this.summary,
    required this.provenance,
    required this.keyMetrics,
    this.cropId,
    this.cropName,
  });
}

/// Central Assessment History Repository providing reactive state management
/// and persistence for soil intelligence extractions and crop feasibility runs.
class AssessmentHistoryRepository extends ChangeNotifier {
  static final AssessmentHistoryRepository _instance =
      AssessmentHistoryRepository._internal();
  static AssessmentHistoryRepository get instance => _instance;

  factory AssessmentHistoryRepository() => _instance;

  AssessmentHistoryRepository._internal();

  final List<AssessmentHistoryRecord> _records = [];

  List<AssessmentHistoryRecord> get records => List.unmodifiable(_records);

  /// Add an assessment record to history, avoiding duplicate runs within a 10s window.
  void addRecord(AssessmentHistoryRecord record) {
    final isDuplicate = _records.any((r) =>
        r.farmId == record.farmId &&
        r.assessmentType == record.assessmentType &&
        r.cropId == record.cropId &&
        record.date.difference(r.date).inSeconds.abs() < 10);

    if (!isDuplicate) {
      _records.insert(0, record);
      notifyListeners();
    }
  }

  /// Record an ISRIC SoilGrids extraction into history.
  void recordSoilAssessment({
    required FarmItem farm,
    required double ph,
    required String texture,
    required double soc,
    required double cec,
    required String depth,
    String? provenance,
  }) {
    final record = AssessmentHistoryRecord(
      id: 'soil-${farm.id}-${DateTime.now().millisecondsSinceEpoch}',
      farmId: farm.id,
      farmName: farm.name,
      taluka: farm.taluka,
      assessmentType: 'Soil Intelligence Profile',
      date: DateTime.now(),
      summary:
          'ISRIC SoilGrids 2.0 digital soil profiling for depth $depth. USDA texture: $texture, pH: ${ph.toStringAsFixed(1)}. Lab soil test required for bioavailable NPK.',
      provenance: provenance ?? 'ISRIC SoilGrids 2.0 | 250m Resolution | 2020',
      keyMetrics: {
        'Depth': depth,
        'pH': ph.toStringAsFixed(1),
        'Texture': texture,
        'SOC': '${soc.toStringAsFixed(1)} g/kg',
        'CEC': '${cec.toStringAsFixed(1)} cmol/kg',
        'NPK': 'Lab Test Req.',
      },
    );
    addRecord(record);
  }

  /// Record a crop suitability evaluation into history.
  void recordCropEvaluation({
    required FarmItem farm,
    required String cropId,
    required String cropName,
    required String decisionState,
    required String summary,
    required Map<String, String> keyMetrics,
    String? provenance,
  }) {
    final record = AssessmentHistoryRecord(
      id: 'crop-${farm.id}-$cropId-${DateTime.now().millisecondsSinceEpoch}',
      farmId: farm.id,
      farmName: farm.name,
      taluka: farm.taluka,
      assessmentType: 'Crop Feasibility Evaluation',
      date: DateTime.now(),
      summary: summary,
      provenance: provenance ?? 'MPKV Rahuri / ICAR Agronomic Framework',
      keyMetrics: keyMetrics,
      cropId: cropId,
      cropName: cropName,
    );
    addRecord(record);
  }

  List<AssessmentHistoryRecord> getRecordsByFarm(String farmId) {
    return _records.where((r) => r.farmId == farmId).toList();
  }

  void clear() {
    _records.clear();
    notifyListeners();
  }
}
