/// CropNet AI — Government Schemes models.
///
/// Matches FastAPI schemas in `services/api/app/schemas/government_scheme.py`.
library;

class GovernmentScheme {
  final String id;
  final String schemeName;
  final String category;
  final String governmentLevel;
  final String? state;
  final String? description;
  final List<String> benefits;
  final List<String> eligibility;
  final List<String> requiredDocuments;
  final List<String> applicationSteps;
  final String? department;
  final String? applicationUrl;
  final String? sourceUrl;
  final String status;
  final String verificationStatus;
  final DateTime? lastVerifiedDate;
  final DateTime? createdAt;
  final DateTime? updatedAt;

  const GovernmentScheme({
    required this.id,
    required this.schemeName,
    required this.category,
    required this.governmentLevel,
    this.state,
    this.description,
    this.benefits = const [],
    this.eligibility = const [],
    this.requiredDocuments = const [],
    this.applicationSteps = const [],
    this.department,
    this.applicationUrl,
    this.sourceUrl,
    this.status = 'ACTIVE',
    this.verificationStatus = 'VERIFIED',
    this.lastVerifiedDate,
    this.createdAt,
    this.updatedAt,
  });

  bool get isActive => status == 'ACTIVE';
  bool get isVerified => verificationStatus == 'VERIFIED';

  factory GovernmentScheme.fromJson(Map<String, dynamic> json) {
    return GovernmentScheme(
      id: json['id'] as String,
      schemeName: json['scheme_name'] as String,
      category: json['category'] as String? ?? 'Other',
      governmentLevel: json['government_level'] as String? ?? 'Central',
      state: json['state'] as String?,
      description: json['description'] as String?,
      benefits: _stringList(json['benefits']),
      eligibility: _stringList(json['eligibility']),
      requiredDocuments: _stringList(json['required_documents']),
      applicationSteps: _stringList(json['application_steps']),
      department: json['department'] as String?,
      applicationUrl: json['application_url'] as String?,
      sourceUrl: json['source_url'] as String?,
      status: json['status'] as String? ?? 'ACTIVE',
      verificationStatus: json['verification_status'] as String? ?? 'VERIFIED',
      lastVerifiedDate: _parseDate(json['last_verified_date']),
      createdAt: _parseDate(json['created_at']),
      updatedAt: _parseDate(json['updated_at']),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'scheme_name': schemeName,
      'category': category,
      'government_level': governmentLevel,
      'state': state,
      'description': description,
      'benefits': benefits,
      'eligibility': eligibility,
      'required_documents': requiredDocuments,
      'application_steps': applicationSteps,
      'department': department,
      'application_url': applicationUrl,
      'source_url': sourceUrl,
      'status': status,
      'verification_status': verificationStatus,
      if (lastVerifiedDate != null)
        'last_verified_date': lastVerifiedDate!.toIso8601String(),
    };
  }

  static List<String> _stringList(dynamic value) {
    if (value is List) {
      return value.map((e) => e.toString()).where((s) => s.trim().isNotEmpty).toList();
    }
    return const [];
  }

  static DateTime? _parseDate(dynamic value) {
    if (value is String && value.isNotEmpty) {
      return DateTime.tryParse(value);
    }
    return null;
  }
}

class SchemeFilterOptions {
  final List<String> categories;
  final List<String> governmentLevels;
  final List<String> states;
  final List<String> statuses;
  final List<String> verificationStatuses;

  const SchemeFilterOptions({
    this.categories = const [],
    this.governmentLevels = const [],
    this.states = const [],
    this.statuses = const [],
    this.verificationStatuses = const [],
  });

  factory SchemeFilterOptions.fromJson(Map<String, dynamic> json) {
    return SchemeFilterOptions(
      categories: _stringList(json['categories']),
      governmentLevels: _stringList(json['government_levels']),
      states: _stringList(json['states']),
      statuses: _stringList(json['statuses']),
      verificationStatuses: _stringList(json['verification_statuses']),
    );
  }

  static List<String> _stringList(dynamic value) {
    if (value is List) return value.map((e) => e.toString()).toList();
    return const [];
  }
}

/// Canonical categories (fallback when the filters endpoint is unavailable).
const List<String> kSchemeCategories = [
  'Crop Insurance',
  'Financial Assistance',
  'Loans',
  'Irrigation',
  'Soil Health',
  'Machinery',
  'Seeds & Fertilizers',
  'Infrastructure',
  'State Schemes',
];
