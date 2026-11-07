import 'dart:collection';
import 'package:flutter/foundation.dart';

import '../../data/soil_lab_repository.dart';
import '../../models/soil_lab_models.dart';

/// State management for the Soil Laboratory Workspace.
/// Handles report listing, active report detail, upload progress,
/// buffered parameter edits, and explicit farmer confirmation.
class SoilLabNotifier extends ChangeNotifier {
  final String farmId;
  final SoilLabRepository _repo;

  SoilLabNotifier({
    required this.farmId,
    SoilLabRepository? repo,
  }) : _repo = repo ?? SoilLabRepository();

  List<SoilReportSummary> _reports = [];
  SoilReportDetail? _activeReport;
  final Map<String, SoilMeasurementUpdate> _editBuffer = {};

  bool _isLoading = false;
  bool _isUploading = false;
  bool _isProcessing = false;
  bool _isConfirming = false;
  double _uploadProgress = 0.0;
  String? _errorMessage;
  String? _successMessage;
  bool _confirmationAccepted = false;

  // Getters
  List<SoilReportSummary> get reports => UnmodifiableListView(_reports);
  SoilReportDetail? get activeReport => _activeReport;
  Map<String, SoilMeasurementUpdate> get editBuffer => UnmodifiableMapView(_editBuffer);

  bool get isLoading => _isLoading;
  bool get isUploading => _isUploading;
  bool get isProcessing => _isProcessing;
  bool get isConfirming => _isConfirming;
  double get uploadProgress => _uploadProgress;
  String? get errorMessage => _errorMessage;
  String? get successMessage => _successMessage;
  bool get confirmationAccepted => _confirmationAccepted;

  bool get hasBufferedEdits => _editBuffer.isNotEmpty;

  /// Load all soil laboratory reports for the active farm.
  Future<void> loadReports() async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      _reports = await _repo.listReports(farmId);
    } catch (e) {
      _errorMessage = 'Failed to load soil reports: $e';
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  /// Load full report detail including all extracted measurements.
  Future<void> loadReportDetail(String reportId) async {
    _isLoading = true;
    _errorMessage = null;
    _editBuffer.clear();
    _confirmationAccepted = false;
    notifyListeners();

    try {
      _activeReport = await _repo.getReportDetail(farmId, reportId);
      _confirmationAccepted = _activeReport?.isConfirmed ?? false;
    } catch (e) {
      _errorMessage = 'Failed to load report detail: $e';
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  /// Upload a physical soil test report document.
  Future<SoilReportUploadResponse?> uploadReport({
    required List<int> fileBytes,
    required String fileName,
    required String mimeType,
    String? laboratoryName,
    String? sampleDepth,
    DateTime? sampleCollectionDate,
    String? samplingPointName,
  }) async {
    _isUploading = true;
    _uploadProgress = 0.05;
    _errorMessage = null;
    _successMessage = null;
    notifyListeners();

    try {
      final response = await _repo.uploadReport(
        farmId,
        fileBytes: fileBytes,
        fileName: fileName,
        mimeType: mimeType,
        laboratoryName: laboratoryName,
        sampleDepth: sampleDepth,
        sampleCollectionDate: sampleCollectionDate,
        samplingPointName: samplingPointName,
        onProgress: (progress) {
          _uploadProgress = progress;
          notifyListeners();
        },
      );

      _uploadProgress = 1.0;
      _successMessage = 'Document uploaded successfully. Processing extraction.';

      // If report detail returned in response, set as active
      if (response.report != null) {
        _activeReport = response.report;
      }

      // Reload reports in background
      await loadReports();
      return response;
    } catch (e) {
      _errorMessage = 'Upload failed: $e';
      return null;
    } finally {
      _isUploading = false;
      notifyListeners();
    }
  }

  /// Buffer an edit to a parameter measurement without immediately saving to server.
  void bufferMeasurementEdit(String measurementId, SoilMeasurementUpdate update) {
    _editBuffer[measurementId] = update;

    // Speculatively update activeReport locally for immediate visual feedback
    if (_activeReport != null) {
      final updatedMeasurements = _activeReport!.measurements.map((m) {
        if (m.id == measurementId) {
          return m.copyWith(
            farmerCorrectedValue: update.correctedValue,
            farmerCorrectedUnit: update.correctedUnit,
            farmerNotes: update.farmerNotes,
            sampleDepth: update.sampleDepth,
            testDate: update.testDate,
            verificationStatus: MeasurementVerificationStatus.farmerCorrected,
          );
        }
        return m;
      }).toList();

      _activeReport = _activeReport!.copyWith(measurements: updatedMeasurements);
    }

    notifyListeners();
  }

  /// Remove an edit from the local edit buffer and revert the measurement.
  void removeBufferedEdit(String measurementId) {
    _editBuffer.remove(measurementId);
    notifyListeners();
  }

  /// Clear all pending buffered edits.
  void clearEditBuffer() {
    _editBuffer.clear();
    notifyListeners();
  }

  /// Commit a single buffered measurement edit to the server.
  Future<bool> saveMeasurement(String reportId, String measurementId) async {
    final update = _editBuffer[measurementId];
    if (update == null) return true;

    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      final updated = await _repo.updateMeasurement(farmId, reportId, measurementId, update);
      _editBuffer.remove(measurementId);

      // Update active report in memory
      if (_activeReport != null) {
        final updatedList = _activeReport!.measurements.map((m) {
          return m.id == measurementId ? updated : m;
        }).toList();
        _activeReport = _activeReport!.copyWith(measurements: updatedList);
      }

      _successMessage = 'Measurement updated successfully.';
      return true;
    } catch (e) {
      _errorMessage = 'Failed to update measurement: $e';
      return false;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  /// Commit all buffered measurement edits to the backend.
  Future<bool> saveAllBufferedMeasurements(String reportId) async {
    if (_editBuffer.isEmpty) return true;

    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      final entries = Map<String, SoilMeasurementUpdate>.from(_editBuffer).entries;
      for (final entry in entries) {
        final updated = await _repo.updateMeasurement(
          farmId,
          reportId,
          entry.key,
          entry.value,
        );
        _editBuffer.remove(entry.key);

        if (_activeReport != null) {
          final updatedList = _activeReport!.measurements.map((m) {
            return m.id == entry.key ? updated : m;
          }).toList();
          _activeReport = _activeReport!.copyWith(measurements: updatedList);
        }
      }

      _successMessage = 'All parameter corrections saved.';
      return true;
    } catch (e) {
      _errorMessage = 'Failed saving some parameter corrections: $e';
      return false;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  /// Toggle farmer confirmation agreement checkbox.
  void toggleConfirmationCheck(bool? value) {
    _confirmationAccepted = value ?? false;
    notifyListeners();
  }

  /// Farmer triggers explicit confirmation of the document transcription.
  Future<bool> confirmTranscription(String reportId) async {
    if (!_confirmationAccepted) {
      _errorMessage = 'You must confirm that the extracted parameters match your report.';
      notifyListeners();
      return false;
    }

    _isConfirming = true;
    _errorMessage = null;
    notifyListeners();

    try {
      // 1. Commit any remaining unsaved edits first
      if (_editBuffer.isNotEmpty) {
        final saved = await saveAllBufferedMeasurements(reportId);
        if (!saved) {
          _errorMessage = 'Failed saving pending edits before confirmation.';
          return false;
        }
      }

      // 2. Send explicit confirmation action
      final confirmedReport = await _repo.confirmReport(farmId, reportId);
      _activeReport = confirmedReport;
      _confirmationAccepted = true;
      _successMessage = 'Soil report transcription confirmed! Lab results are now active in Soil Intelligence.';

      // 3. Refresh reports list
      await loadReports();
      return true;
    } catch (e) {
      _errorMessage = 'Failed to confirm transcription: $e';
      return false;
    } finally {
      _isConfirming = false;
      notifyListeners();
    }
  }

  /// Re-run extraction pipeline for an ambiguous or failed document.
  Future<void> reprocess(String reportId) async {
    _isProcessing = true;
    _errorMessage = null;
    notifyListeners();

    try {
      _activeReport = await _repo.reprocessReport(farmId, reportId);
      _successMessage = 'Document re-extraction initiated.';
      await loadReports();
    } catch (e) {
      _errorMessage = 'Reprocess request failed: $e';
    } finally {
      _isProcessing = false;
      notifyListeners();
    }
  }

  void clearErrors() {
    _errorMessage = null;
    notifyListeners();
  }

  void clearSuccess() {
    _successMessage = null;
    notifyListeners();
  }
}
