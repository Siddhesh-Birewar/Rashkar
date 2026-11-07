import 'package:flutter/foundation.dart';

/// Lifecycle status of an uploaded physical soil test report.
enum SoilReportStatus {
  uploaded('UPLOADED'),
  processing('PROCESSING'),
  extractionCompleted('EXTRACTION_COMPLETED'),
  needsReview('NEEDS_REVIEW'),
  confirmed('CONFIRMED'),
  failed('FAILED');

  final String value;
  const SoilReportStatus(this.value);

  static SoilReportStatus fromString(String? val) {
    if (val == null) return SoilReportStatus.uploaded;
    final upper = val.toUpperCase().trim();
    for (final s in SoilReportStatus.values) {
      if (s.value == upper) return s;
    }
    return SoilReportStatus.uploaded;
  }

  String get displayName {
    switch (this) {
      case SoilReportStatus.uploaded:
        return 'Uploaded';
      case SoilReportStatus.processing:
        return 'Processing OCR';
      case SoilReportStatus.extractionCompleted:
        return 'Extraction Completed';
      case SoilReportStatus.needsReview:
        return 'Needs Review';
      case SoilReportStatus.confirmed:
        return 'Confirmed';
      case SoilReportStatus.failed:
        return 'Extraction Failed';
    }
  }

  bool get isPendingReview =>
      this == SoilReportStatus.needsReview || this == SoilReportStatus.extractionCompleted;

  bool get isConfirmed => this == SoilReportStatus.confirmed;

  bool get isProcessing => this == SoilReportStatus.processing;

  bool get isFailed => this == SoilReportStatus.failed;
}

/// Verification status of an individual soil measurement record.
enum MeasurementVerificationStatus {
  extractedUnverified('EXTRACTED_UNVERIFIED'),
  farmerCorrected('FARMER_CORRECTED'),
  farmerConfirmed('FARMER_CONFIRMED'),
  rejected('REJECTED'),
  flagged('FLAGGED');

  final String value;
  const MeasurementVerificationStatus(this.value);

  static MeasurementVerificationStatus fromString(String? val) {
    if (val == null) return MeasurementVerificationStatus.extractedUnverified;
    final upper = val.toUpperCase().trim();
    if (upper == 'EXTRACTED' || upper == 'EXTRACTED_UNVERIFIED') {
      return MeasurementVerificationStatus.extractedUnverified;
    }
    if (upper == 'CORRECTED' || upper == 'FARMER_CORRECTED') {
      return MeasurementVerificationStatus.farmerCorrected;
    }
    if (upper == 'CONFIRMED' || upper == 'FARMER_CONFIRMED') {
      return MeasurementVerificationStatus.farmerConfirmed;
    }
    if (upper == 'REJECTED') return MeasurementVerificationStatus.rejected;
    if (upper == 'FLAGGED') return MeasurementVerificationStatus.flagged;
    return MeasurementVerificationStatus.extractedUnverified;
  }

  String get displayName {
    switch (this) {
      case MeasurementVerificationStatus.extractedUnverified:
        return 'Extracted (Unverified)';
      case MeasurementVerificationStatus.farmerCorrected:
        return 'Farmer Corrected';
      case MeasurementVerificationStatus.farmerConfirmed:
        return 'Farmer Confirmed';
      case MeasurementVerificationStatus.rejected:
        return 'Rejected';
      case MeasurementVerificationStatus.flagged:
        return 'Flagged';
    }
  }
}

/// Standardized parameter metadata lookup for canonical naming and units.
class CanonicalSoilParameters {
  CanonicalSoilParameters._();

  static const Map<String, String> displayNames = {
    'soil_ph': 'Soil pH (H2O)',
    'ph': 'Soil pH (H2O)',
    'electrical_conductivity': 'Electrical Conductivity (EC)',
    'ec': 'Electrical Conductivity (EC)',
    'organic_carbon': 'Soil Organic Carbon (SOC)',
    'oc': 'Soil Organic Carbon (SOC)',
    'organic_matter': 'Soil Organic Matter (SOM)',
    'som': 'Soil Organic Matter (SOM)',
    'available_nitrogen': 'Available Nitrogen (N)',
    'available_n': 'Available Nitrogen (N)',
    'total_nitrogen': 'Total Nitrogen (N)',
    'total_n': 'Total Nitrogen (N)',
    'available_phosphorus': 'Available Phosphorus (P2O5)',
    'available_p': 'Available Phosphorus (P2O5)',
    'available_potassium': 'Available Potassium (K2O)',
    'available_k': 'Available Potassium (K2O)',
    'sulphur': 'Available Sulphur (S)',
    's': 'Available Sulphur (S)',
    'zinc': 'Available Zinc (Zn)',
    'zn': 'Available Zinc (Zn)',
    'iron': 'Available Iron (Fe)',
    'fe': 'Available Iron (Fe)',
    'manganese': 'Available Manganese (Mn)',
    'mn': 'Available Manganese (Mn)',
    'copper': 'Available Copper (Cu)',
    'cu': 'Available Copper (Cu)',
    'boron': 'Available Boron (B)',
    'b': 'Available Boron (B)',
    'cec': 'Cation Exchange Capacity (CEC)',
  };

  static const Map<String, String> defaultUnits = {
    'soil_ph': 'pH',
    'ph': 'pH',
    'electrical_conductivity': 'dS/m',
    'ec': 'dS/m',
    'organic_carbon': '%',
    'oc': '%',
    'organic_matter': '%',
    'som': '%',
    'available_nitrogen': 'kg/ha',
    'available_n': 'kg/ha',
    'total_nitrogen': 'g/kg',
    'total_n': 'g/kg',
    'available_phosphorus': 'kg/ha',
    'available_p': 'kg/ha',
    'available_potassium': 'kg/ha',
    'available_k': 'kg/ha',
    'sulphur': 'mg/kg',
    's': 'mg/kg',
    'zinc': 'mg/kg',
    'zn': 'mg/kg',
    'iron': 'mg/kg',
    'fe': 'mg/kg',
    'manganese': 'mg/kg',
    'mn': 'mg/kg',
    'copper': 'mg/kg',
    'cu': 'mg/kg',
    'boron': 'mg/kg',
    'b': 'mg/kg',
    'cec': 'cmol(+)/kg',
  };

  static const Map<String, String> categories = {
    'soil_ph': 'chemical',
    'ph': 'chemical',
    'electrical_conductivity': 'chemical',
    'ec': 'chemical',
    'organic_carbon': 'biological',
    'oc': 'biological',
    'organic_matter': 'biological',
    'som': 'biological',
    'available_nitrogen': 'macronutrient',
    'available_n': 'macronutrient',
    'total_nitrogen': 'macronutrient',
    'total_n': 'macronutrient',
    'available_phosphorus': 'macronutrient',
    'available_p': 'macronutrient',
    'available_potassium': 'macronutrient',
    'available_k': 'macronutrient',
    'sulphur': 'secondary',
    's': 'secondary',
    'zinc': 'micronutrient',
    'zn': 'micronutrient',
    'iron': 'micronutrient',
    'fe': 'micronutrient',
    'manganese': 'micronutrient',
    'mn': 'micronutrient',
    'copper': 'micronutrient',
    'cu': 'micronutrient',
    'boron': 'micronutrient',
    'b': 'micronutrient',
    'cec': 'chemical',
  };

  static String resolveDisplayName(String key, [String? fallback]) {
    final clean = key.toLowerCase().trim();
    return displayNames[clean] ?? fallback ?? key;
  }

  static String resolveDefaultUnit(String key, [String? fallback]) {
    final clean = key.toLowerCase().trim();
    return defaultUnits[clean] ?? fallback ?? '';
  }

  static String resolveCategory(String key) {
    final clean = key.toLowerCase().trim();
    return categories[clean] ?? 'other';
  }
}

/// An individual soil measurement item extracted from a laboratory document.
@immutable
class SoilMeasurementItem {
  final String id;
  final String reportId;
  final String? farmId;
  final String parameterKey;
  final String parameterCategory;
  final String originalParameterName;
  final String displayName;
  final double? originalValue;
  final String? originalValueText;
  final String originalUnit;
  final double? normalizedValue;
  final String? normalizedUnit;
  final String? analyticalMethod;
  final Map<String, dynamic>? labReferenceRange;
  final String? labRating;
  final double? detectionLimit;
  final int? pageNumber;
  final List<double>? boundingBox;
  final double extractionConfidence;
  final MeasurementVerificationStatus verificationStatus;
  final double? farmerCorrectedValue;
  final String? farmerCorrectedUnit;
  final String? farmerNotes;
  final bool isAmbiguous;
  final String? sampleDepth;
  final DateTime? testDate;

  const SoilMeasurementItem({
    required this.id,
    required this.reportId,
    this.farmId,
    required this.parameterKey,
    String? parameterCategory,
    String? originalParameterName,
    String? displayName,
    this.originalValue,
    this.originalValueText,
    required this.originalUnit,
    this.normalizedValue,
    this.normalizedUnit,
    this.analyticalMethod,
    this.labReferenceRange,
    this.labRating,
    this.detectionLimit,
    this.pageNumber,
    this.boundingBox,
    this.extractionConfidence = 1.0,
    this.verificationStatus = MeasurementVerificationStatus.extractedUnverified,
    this.farmerCorrectedValue,
    this.farmerCorrectedUnit,
    this.farmerNotes,
    this.isAmbiguous = false,
    this.sampleDepth,
    this.testDate,
  })  : parameterCategory = parameterCategory ?? 'macronutrient',
        originalParameterName = originalParameterName ?? parameterKey,
        displayName = displayName ?? parameterKey;

  /// Effective value considering farmer corrections first, then normalized, then original.
  double? get effectiveValue => farmerCorrectedValue ?? normalizedValue ?? originalValue;

  /// Effective unit considering farmer corrections first, then normalized, then original.
  String get effectiveUnit =>
      farmerCorrectedUnit ?? normalizedUnit ?? (originalUnit.isNotEmpty ? originalUnit : '');

  bool get isFarmerCorrected =>
      verificationStatus == MeasurementVerificationStatus.farmerCorrected ||
      farmerCorrectedValue != null;

  bool get isConfirmed =>
      verificationStatus == MeasurementVerificationStatus.farmerConfirmed;

  SoilMeasurementItem copyWith({
    String? id,
    String? reportId,
    String? farmId,
    String? parameterKey,
    String? parameterCategory,
    String? originalParameterName,
    String? displayName,
    double? originalValue,
    String? originalValueText,
    String? originalUnit,
    double? normalizedValue,
    String? normalizedUnit,
    String? analyticalMethod,
    Map<String, dynamic>? labReferenceRange,
    String? labRating,
    double? detectionLimit,
    int? pageNumber,
    List<double>? boundingBox,
    double? extractionConfidence,
    MeasurementVerificationStatus? verificationStatus,
    double? farmerCorrectedValue,
    String? farmerCorrectedUnit,
    String? farmerNotes,
    bool? isAmbiguous,
    String? sampleDepth,
    DateTime? testDate,
  }) {
    return SoilMeasurementItem(
      id: id ?? this.id,
      reportId: reportId ?? this.reportId,
      farmId: farmId ?? this.farmId,
      parameterKey: parameterKey ?? this.parameterKey,
      parameterCategory: parameterCategory ?? this.parameterCategory,
      originalParameterName: originalParameterName ?? this.originalParameterName,
      displayName: displayName ?? this.displayName,
      originalValue: originalValue ?? this.originalValue,
      originalValueText: originalValueText ?? this.originalValueText,
      originalUnit: originalUnit ?? this.originalUnit,
      normalizedValue: normalizedValue ?? this.normalizedValue,
      normalizedUnit: normalizedUnit ?? this.normalizedUnit,
      analyticalMethod: analyticalMethod ?? this.analyticalMethod,
      labReferenceRange: labReferenceRange ?? this.labReferenceRange,
      labRating: labRating ?? this.labRating,
      detectionLimit: detectionLimit ?? this.detectionLimit,
      pageNumber: pageNumber ?? this.pageNumber,
      boundingBox: boundingBox ?? this.boundingBox,
      extractionConfidence: extractionConfidence ?? this.extractionConfidence,
      verificationStatus: verificationStatus ?? this.verificationStatus,
      farmerCorrectedValue: farmerCorrectedValue ?? this.farmerCorrectedValue,
      farmerCorrectedUnit: farmerCorrectedUnit ?? this.farmerCorrectedUnit,
      farmerNotes: farmerNotes ?? this.farmerNotes,
      isAmbiguous: isAmbiguous ?? this.isAmbiguous,
      sampleDepth: sampleDepth ?? this.sampleDepth,
      testDate: testDate ?? this.testDate,
    );
  }

  factory SoilMeasurementItem.fromJson(Map<String, dynamic> json) {
    final key = json['parameter_key'] as String? ?? json['parameterKey'] as String? ?? '';
    final origName = json['original_parameter_name'] as String? ??
        json['originalParameterName'] as String? ??
        key;
    final dispName = json['display_name'] as String? ??
        json['displayName'] as String? ??
        CanonicalSoilParameters.resolveDisplayName(key, origName);
    final category = json['parameter_category'] as String? ??
        json['parameterCategory'] as String? ??
        CanonicalSoilParameters.resolveCategory(key);

    List<double>? bbox;
    if (json['bounding_box'] is List) {
      bbox = (json['bounding_box'] as List).map((e) => (e as num).toDouble()).toList();
    } else if (json['boundingBox'] is List) {
      bbox = (json['boundingBox'] as List).map((e) => (e as num).toDouble()).toList();
    }

    Map<String, dynamic>? refRange;
    if (json['lab_reference_range'] is Map) {
      refRange = Map<String, dynamic>.from(json['lab_reference_range'] as Map);
    } else if (json['labReferenceRange'] is Map) {
      refRange = Map<String, dynamic>.from(json['labReferenceRange'] as Map);
    }

    return SoilMeasurementItem(
      id: json['id'] as String? ?? '',
      reportId: json['report_id'] as String? ?? json['reportId'] as String? ?? '',
      farmId: json['farm_id'] as String? ?? json['farmId'] as String?,
      parameterKey: key,
      parameterCategory: category,
      originalParameterName: origName,
      displayName: dispName,
      originalValue: (json['original_value'] ?? json['originalValue']) != null
          ? (json['original_value'] ?? json['originalValue'] as num).toDouble()
          : null,
      originalValueText: json['original_value_text'] as String? ??
          json['originalValueText'] as String?,
      originalUnit: json['original_unit'] as String? ??
          json['originalUnit'] as String? ??
          CanonicalSoilParameters.resolveDefaultUnit(key),
      normalizedValue: (json['normalized_value'] ?? json['normalizedValue']) != null
          ? (json['normalized_value'] ?? json['normalizedValue'] as num).toDouble()
          : null,
      normalizedUnit: json['normalized_unit'] as String? ??
          json['normalizedUnit'] as String?,
      analyticalMethod: json['analytical_method'] as String? ??
          json['analyticalMethod'] as String?,
      labReferenceRange: refRange,
      labRating: json['lab_rating'] as String? ?? json['labRating'] as String?,
      detectionLimit: (json['detection_limit'] ?? json['detectionLimit']) != null
          ? (json['detection_limit'] ?? json['detectionLimit'] as num).toDouble()
          : null,
      pageNumber: json['page_number'] as int? ?? json['pageNumber'] as int?,
      boundingBox: bbox,
      extractionConfidence: (json['extraction_confidence'] ??
              json['extractionConfidence'] ??
              1.0 as num)
          .toDouble(),
      verificationStatus: MeasurementVerificationStatus.fromString(
        json['verification_status'] as String? ?? json['verificationStatus'] as String?,
      ),
      farmerCorrectedValue: (json['farmer_corrected_value'] ??
              json['farmerCorrectedValue']) !=
          null
          ? (json['farmer_corrected_value'] ?? json['farmerCorrectedValue'] as num)
              .toDouble()
          : null,
      farmerCorrectedUnit: json['farmer_corrected_unit'] as String? ??
          json['farmerCorrectedUnit'] as String?,
      farmerNotes: json['farmer_notes'] as String? ?? json['farmerNotes'] as String?,
      isAmbiguous: json['is_ambiguous'] as bool? ?? json['isAmbiguous'] as bool? ?? false,
      sampleDepth: json['sample_depth'] as String? ?? json['sampleDepth'] as String?,
      testDate: json['test_date'] != null
          ? DateTime.tryParse(json['test_date'].toString())
          : (json['testDate'] != null
              ? DateTime.tryParse(json['testDate'].toString())
              : null),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'report_id': reportId,
      'farm_id': farmId,
      'parameter_key': parameterKey,
      'parameter_category': parameterCategory,
      'original_parameter_name': originalParameterName,
      'display_name': displayName,
      'original_value': originalValue,
      'original_value_text': originalValueText,
      'original_unit': originalUnit,
      'normalized_value': normalizedValue,
      'normalized_unit': normalizedUnit,
      'analytical_method': analyticalMethod,
      'lab_reference_range': labReferenceRange,
      'lab_rating': labRating,
      'detection_limit': detectionLimit,
      'page_number': pageNumber,
      'bounding_box': boundingBox,
      'extraction_confidence': extractionConfidence,
      'verification_status': verificationStatus.value,
      'farmer_corrected_value': farmerCorrectedValue,
      'farmer_corrected_unit': farmerCorrectedUnit,
      'farmer_notes': farmerNotes,
      'is_ambiguous': isAmbiguous,
      'sample_depth': sampleDepth,
      'test_date': testDate?.toIso8601String(),
    };
  }
}

/// Payload sent by the farmer to correct an extracted measurement.
@immutable
class SoilMeasurementUpdate {
  final String measurementId;
  final double? correctedValue;
  final String? correctedUnit;
  final String? sampleDepth;
  final DateTime? testDate;
  final String? farmerNotes;
  final MeasurementVerificationStatus verificationStatus;

  const SoilMeasurementUpdate({
    required this.measurementId,
    this.correctedValue,
    this.correctedUnit,
    this.sampleDepth,
    this.testDate,
    this.farmerNotes,
    this.verificationStatus = MeasurementVerificationStatus.farmerCorrected,
  });

  Map<String, dynamic> toJson() {
    return {
      'measurement_id': measurementId,
      'corrected_value': correctedValue,
      'corrected_unit': correctedUnit,
      'sample_depth': sampleDepth,
      'test_date': testDate?.toIso8601String(),
      'farmer_notes': farmerNotes,
      'verification_status': verificationStatus.value,
    };
  }

  factory SoilMeasurementUpdate.fromJson(Map<String, dynamic> json) {
    return SoilMeasurementUpdate(
      measurementId: json['measurement_id'] as String? ??
          json['measurementId'] as String? ??
          '',
      correctedValue: (json['corrected_value'] ?? json['correctedValue']) != null
          ? (json['corrected_value'] ?? json['correctedValue'] as num).toDouble()
          : null,
      correctedUnit: json['corrected_unit'] as String? ??
          json['correctedUnit'] as String?,
      sampleDepth: json['sample_depth'] as String? ?? json['sampleDepth'] as String?,
      testDate: json['test_date'] != null
          ? DateTime.tryParse(json['test_date'].toString())
          : (json['testDate'] != null
              ? DateTime.tryParse(json['testDate'].toString())
              : null),
      farmerNotes: json['farmer_notes'] as String? ?? json['farmerNotes'] as String?,
      verificationStatus: MeasurementVerificationStatus.fromString(
        json['verification_status'] as String? ?? json['verificationStatus'] as String?,
      ),
    );
  }
}

/// Summary card representation of a soil report for list views and history.
@immutable
class SoilReportSummary {
  final String id;
  final String farmId;
  final String filename;
  final SoilReportStatus status;
  final DateTime uploadTimestamp;
  final String? laboratoryName;
  final DateTime? reportDate;
  final DateTime? sampleDate;
  final String? sampleDepth;
  final int measurementCount;
  final Map<String, dynamic> keyMetrics;

  const SoilReportSummary({
    required this.id,
    required this.farmId,
    required this.filename,
    required this.status,
    required this.uploadTimestamp,
    this.laboratoryName,
    this.reportDate,
    this.sampleDate,
    this.sampleDepth,
    this.measurementCount = 0,
    this.keyMetrics = const {},
  });

  factory SoilReportSummary.fromJson(Map<String, dynamic> json) {
    return SoilReportSummary(
      id: json['id'] as String? ?? '',
      farmId: json['farm_id'] as String? ?? json['farmId'] as String? ?? '',
      filename: json['filename'] as String? ??
          json['original_filename'] as String? ??
          json['originalFilename'] as String? ??
          'Soil Report',
      status: SoilReportStatus.fromString(
        json['extraction_status'] as String? ?? json['status'] as String?,
      ),
      uploadTimestamp: json['upload_timestamp'] != null
          ? DateTime.tryParse(json['upload_timestamp'].toString()) ?? DateTime.now()
          : (json['created_at'] != null
              ? DateTime.tryParse(json['created_at'].toString()) ?? DateTime.now()
              : DateTime.now()),
      laboratoryName: json['lab_name'] as String? ?? json['laboratoryName'] as String?,
      reportDate: json['report_date'] != null
          ? DateTime.tryParse(json['report_date'].toString())
          : (json['reportDate'] != null
              ? DateTime.tryParse(json['reportDate'].toString())
              : null),
      sampleDate: json['sample_collection_date'] != null
          ? DateTime.tryParse(json['sample_collection_date'].toString())
          : (json['sampleDate'] != null
              ? DateTime.tryParse(json['sampleDate'].toString())
              : null),
      sampleDepth: json['sample_depth_interval'] as String? ??
          json['sample_depth'] as String? ??
          json['sampleDepth'] as String?,
      measurementCount: json['measurement_count'] as int? ??
          json['measurementCount'] as int? ??
          (json['measurements'] is List ? (json['measurements'] as List).length : 0),
      keyMetrics: json['key_metrics'] is Map
          ? Map<String, dynamic>.from(json['key_metrics'] as Map)
          : (json['keyMetrics'] is Map
              ? Map<String, dynamic>.from(json['keyMetrics'] as Map)
              : const {}),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'farm_id': farmId,
      'filename': filename,
      'status': status.value,
      'upload_timestamp': uploadTimestamp.toIso8601String(),
      'lab_name': laboratoryName,
      'report_date': reportDate?.toIso8601String(),
      'sample_date': sampleDate?.toIso8601String(),
      'sample_depth': sampleDepth,
      'measurement_count': measurementCount,
      'key_metrics': keyMetrics,
    };
  }
}

/// Comprehensive soil report detail including file provenance and all extracted measurements.
@immutable
class SoilReportDetail {
  final String id;
  final String farmId;
  final String? userId;
  final String filename;
  final String storagePath;
  final String? documentUrl;
  final String mimeType;
  final int fileSizeBytes;
  final DateTime uploadTimestamp;
  final SoilReportStatus status;
  final String reviewStatus;
  final String? laboratoryName;
  final String? labAddress;
  final String? labAccreditation;
  final String? sampleIdCode;
  final DateTime? reportDate;
  final DateTime? sampleDate;
  final String? sampleDepth;
  final double? sampleDepthMinCm;
  final double? sampleDepthMaxCm;
  final String? samplingPointName;
  final bool isConfirmed;
  final DateTime? confirmedAt;
  final String? extractionError;
  final List<SoilMeasurementItem> measurements;

  const SoilReportDetail({
    required this.id,
    required this.farmId,
    this.userId,
    required this.filename,
    required this.storagePath,
    this.documentUrl,
    required this.mimeType,
    required this.fileSizeBytes,
    required this.uploadTimestamp,
    required this.status,
    this.reviewStatus = 'PENDING_REVIEW',
    this.laboratoryName,
    this.labAddress,
    this.labAccreditation,
    this.sampleIdCode,
    this.reportDate,
    this.sampleDate,
    this.sampleDepth,
    this.sampleDepthMinCm,
    this.sampleDepthMaxCm,
    this.samplingPointName,
    this.isConfirmed = false,
    this.confirmedAt,
    this.extractionError,
    this.measurements = const [],
  });

  /// Retrieve measurement item by canonical parameter key (e.g. 'soil_ph', 'available_nitrogen').
  SoilMeasurementItem? getMeasurement(String key) {
    final clean = key.toLowerCase().trim();
    for (final m in measurements) {
      if (m.parameterKey.toLowerCase().trim() == clean) return m;
    }
    // Also try canonical alias matching (e.g., ph -> soil_ph or vice versa)
    for (final m in measurements) {
      if (clean == 'ph' && m.parameterKey == 'soil_ph') return m;
      if (clean == 'soil_ph' && m.parameterKey == 'ph') return m;
      if (clean == 'ec' && m.parameterKey == 'electrical_conductivity') return m;
      if (clean == 'electrical_conductivity' && m.parameterKey == 'ec') return m;
      if (clean == 'oc' && m.parameterKey == 'organic_carbon') return m;
      if (clean == 'organic_carbon' && m.parameterKey == 'oc') return m;
      if (clean == 'available_n' && m.parameterKey == 'available_nitrogen') return m;
      if (clean == 'available_nitrogen' && m.parameterKey == 'available_n') return m;
      if (clean == 'available_p' && m.parameterKey == 'available_phosphorus') return m;
      if (clean == 'available_phosphorus' && m.parameterKey == 'available_p') return m;
      if (clean == 'available_k' && m.parameterKey == 'available_potassium') return m;
      if (clean == 'available_potassium' && m.parameterKey == 'available_k') return m;
    }
    return null;
  }

  /// Retrieve effective value for parameter key, or null if missing.
  double? getEffectiveValue(String key) => getMeasurement(key)?.effectiveValue;

  SoilReportDetail copyWith({
    String? id,
    String? farmId,
    String? userId,
    String? filename,
    String? storagePath,
    String? documentUrl,
    String? mimeType,
    int? fileSizeBytes,
    DateTime? uploadTimestamp,
    SoilReportStatus? status,
    String? reviewStatus,
    String? laboratoryName,
    String? labAddress,
    String? labAccreditation,
    String? sampleIdCode,
    DateTime? reportDate,
    DateTime? sampleDate,
    String? sampleDepth,
    double? sampleDepthMinCm,
    double? sampleDepthMaxCm,
    String? samplingPointName,
    bool? isConfirmed,
    DateTime? confirmedAt,
    String? extractionError,
    List<SoilMeasurementItem>? measurements,
  }) {
    return SoilReportDetail(
      id: id ?? this.id,
      farmId: farmId ?? this.farmId,
      userId: userId ?? this.userId,
      filename: filename ?? this.filename,
      storagePath: storagePath ?? this.storagePath,
      documentUrl: documentUrl ?? this.documentUrl,
      mimeType: mimeType ?? this.mimeType,
      fileSizeBytes: fileSizeBytes ?? this.fileSizeBytes,
      uploadTimestamp: uploadTimestamp ?? this.uploadTimestamp,
      status: status ?? this.status,
      reviewStatus: reviewStatus ?? this.reviewStatus,
      laboratoryName: laboratoryName ?? this.laboratoryName,
      labAddress: labAddress ?? this.labAddress,
      labAccreditation: labAccreditation ?? this.labAccreditation,
      sampleIdCode: sampleIdCode ?? this.sampleIdCode,
      reportDate: reportDate ?? this.reportDate,
      sampleDate: sampleDate ?? this.sampleDate,
      sampleDepth: sampleDepth ?? this.sampleDepth,
      sampleDepthMinCm: sampleDepthMinCm ?? this.sampleDepthMinCm,
      sampleDepthMaxCm: sampleDepthMaxCm ?? this.sampleDepthMaxCm,
      samplingPointName: samplingPointName ?? this.samplingPointName,
      isConfirmed: isConfirmed ?? this.isConfirmed,
      confirmedAt: confirmedAt ?? this.confirmedAt,
      extractionError: extractionError ?? this.extractionError,
      measurements: measurements ?? this.measurements,
    );
  }

  factory SoilReportDetail.fromJson(Map<String, dynamic> json) {
    final statusStr = json['extraction_status'] as String? ?? json['status'] as String?;
    final status = SoilReportStatus.fromString(statusStr);
    final confirmed = json['is_confirmed'] as bool? ??
        (status == SoilReportStatus.confirmed) ||
        (json['confirmed_at'] != null);

    List<SoilMeasurementItem> mList = [];
    if (json['measurements'] is List) {
      mList = (json['measurements'] as List)
          .map((m) => SoilMeasurementItem.fromJson(Map<String, dynamic>.from(m as Map)))
          .toList();
    }

    return SoilReportDetail(
      id: json['id'] as String? ?? '',
      farmId: json['farm_id'] as String? ?? json['farmId'] as String? ?? '',
      userId: json['user_id'] as String? ?? json['userId'] as String?,
      filename: json['filename'] as String? ??
          json['original_filename'] as String? ??
          json['originalFilename'] as String? ??
          'Soil Report',
      storagePath: json['storage_path'] as String? ??
          json['documentStoragePath'] as String? ??
          '',
      documentUrl: json['document_url'] as String? ??
          json['documentSignedUrl'] as String? ??
          json['signed_url'] as String?,
      mimeType: json['mime_type'] as String? ??
          json['mimeType'] as String? ??
          'application/pdf',
      fileSizeBytes: json['file_size_bytes'] as int? ??
          json['fileSizeBytes'] as int? ??
          0,
      uploadTimestamp: json['upload_timestamp'] != null
          ? DateTime.tryParse(json['upload_timestamp'].toString()) ?? DateTime.now()
          : (json['created_at'] != null
              ? DateTime.tryParse(json['created_at'].toString()) ?? DateTime.now()
              : DateTime.now()),
      status: status,
      reviewStatus: json['review_status'] as String? ??
          json['reviewStatus'] as String? ??
          'PENDING_REVIEW',
      laboratoryName: json['lab_name'] as String? ?? json['laboratoryName'] as String?,
      labAddress: json['lab_address'] as String? ?? json['labAddress'] as String?,
      labAccreditation: json['lab_accreditation'] as String? ??
          json['labAccreditation'] as String?,
      sampleIdCode: json['sample_id_code'] as String? ?? json['sampleIdCode'] as String?,
      reportDate: json['report_date'] != null
          ? DateTime.tryParse(json['report_date'].toString())
          : (json['reportDate'] != null
              ? DateTime.tryParse(json['reportDate'].toString())
              : null),
      sampleDate: json['sample_collection_date'] != null
          ? DateTime.tryParse(json['sample_collection_date'].toString())
          : (json['sampleDate'] != null
              ? DateTime.tryParse(json['sampleDate'].toString())
              : null),
      sampleDepth: json['sample_depth_interval'] as String? ??
          json['sample_depth'] as String? ??
          json['sampleDepth'] as String?,
      sampleDepthMinCm: (json['sample_depth_min_cm'] ?? json['sampleDepthMinCm']) != null
          ? (json['sample_depth_min_cm'] ?? json['sampleDepthMinCm'] as num).toDouble()
          : null,
      sampleDepthMaxCm: (json['sample_depth_max_cm'] ?? json['sampleDepthMaxCm']) != null
          ? (json['sample_depth_max_cm'] ?? json['sampleDepthMaxCm'] as num).toDouble()
          : null,
      samplingPointName: json['sampling_point_name'] as String? ??
          json['samplingPointName'] as String?,
      isConfirmed: confirmed,
      confirmedAt: json['confirmed_at'] != null
          ? DateTime.tryParse(json['confirmed_at'].toString())
          : null,
      extractionError: json['extraction_error'] as String? ??
          json['extractionError'] as String?,
      measurements: mList,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'farm_id': farmId,
      'user_id': userId,
      'filename': filename,
      'storage_path': storagePath,
      'document_url': documentUrl,
      'mime_type': mimeType,
      'file_size_bytes': fileSizeBytes,
      'upload_timestamp': uploadTimestamp.toIso8601String(),
      'status': status.value,
      'review_status': reviewStatus,
      'lab_name': laboratoryName,
      'lab_address': labAddress,
      'lab_accreditation': labAccreditation,
      'sample_id_code': sampleIdCode,
      'report_date': reportDate?.toIso8601String(),
      'sample_date': sampleDate?.toIso8601String(),
      'sample_depth': sampleDepth,
      'sample_depth_min_cm': sampleDepthMinCm,
      'sample_depth_max_cm': sampleDepthMaxCm,
      'sampling_point_name': samplingPointName,
      'is_confirmed': isConfirmed,
      'confirmed_at': confirmedAt?.toIso8601String(),
      'extraction_error': extractionError,
      'measurements': measurements.map((m) => m.toJson()).toList(),
    };
  }
}

/// Response returned when a new report document is uploaded.
@immutable
class SoilReportUploadResponse {
  final String reportId;
  final SoilReportStatus status;
  final String filename;
  final String? message;
  final SoilReportDetail? report;

  const SoilReportUploadResponse({
    required this.reportId,
    required this.status,
    required this.filename,
    this.message,
    this.report,
  });

  factory SoilReportUploadResponse.fromJson(Map<String, dynamic> json) {
    SoilReportDetail? rep;
    if (json['report'] is Map) {
      rep = SoilReportDetail.fromJson(Map<String, dynamic>.from(json['report'] as Map));
    } else if (json['id'] != null && json['farm_id'] != null) {
      rep = SoilReportDetail.fromJson(json);
    }

    final id = json['report_id'] as String? ??
        json['reportId'] as String? ??
        json['id'] as String? ??
        rep?.id ??
        '';

    final statusStr = json['status'] as String? ??
        json['extraction_status'] as String? ??
        rep?.status.value;

    return SoilReportUploadResponse(
      reportId: id,
      status: SoilReportStatus.fromString(statusStr),
      filename: json['filename'] as String? ??
          json['original_filename'] as String? ??
          rep?.filename ??
          '',
      message: json['message'] as String? ?? json['detail'] as String?,
      report: rep,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'report_id': reportId,
      'status': status.value,
      'filename': filename,
      'message': message,
      'report': report?.toJson(),
    };
  }
}
