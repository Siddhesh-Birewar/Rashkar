/// CropNet AI — Farm Models
///
/// Matches FastAPI schemas in `services/api/app/schemas/farm.py`.
class GeoJsonPolygon {
  final String type;
  final List<List<List<double>>> coordinates;

  const GeoJsonPolygon({
    this.type = 'Polygon',
    required this.coordinates,
  });

  factory GeoJsonPolygon.fromJson(Map<String, dynamic> json) {
    final rawCoords = json['coordinates'] as List<dynamic>;
    final parsedCoords = rawCoords.map<List<List<double>>>((ring) {
      return (ring as List<dynamic>).map<List<double>>((pt) {
        return (pt as List<dynamic>).map<double>((c) => (c as num).toDouble()).toList();
      }).toList();
    }).toList();

    return GeoJsonPolygon(
      type: json['type'] as String? ?? 'Polygon',
      coordinates: parsedCoords,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'type': type,
      'coordinates': coordinates,
    };
  }
}

class FarmCreate {
  final String name;
  final String? village;
  final String taluka;
  final String district;
  final String state;
  final String? irrigationType;
  final String? waterSource;
  final GeoJsonPolygon geometry;

  const FarmCreate({
    required this.name,
    this.village,
    required this.taluka,
    this.district = 'Pune',
    this.state = 'Maharashtra',
    this.irrigationType = 'unknown',
    this.waterSource = 'unknown',
    required this.geometry,
  });

  Map<String, dynamic> toJson() {
    return {
      'name': name,
      if (village != null) 'village': village,
      'taluka': taluka,
      'district': district,
      'state': state,
      'irrigation_type': irrigationType,
      'water_source': waterSource,
      'geometry': geometry.toJson(),
    };
  }
}

class FarmUpdate {
  final String? name;
  final String? village;
  final String? taluka;
  final String? district;
  final String? state;
  final String? irrigationType;
  final String? waterSource;
  final GeoJsonPolygon? geometry;

  const FarmUpdate({
    this.name,
    this.village,
    this.taluka,
    this.district,
    this.state,
    this.irrigationType,
    this.waterSource,
    this.geometry,
  });

  Map<String, dynamic> toJson() {
    final map = <String, dynamic>{};
    if (name != null) map['name'] = name;
    if (village != null) map['village'] = village;
    if (taluka != null) map['taluka'] = taluka;
    if (district != null) map['district'] = district;
    if (state != null) map['state'] = state;
    if (irrigationType != null) map['irrigation_type'] = irrigationType;
    if (waterSource != null) map['water_source'] = waterSource;
    if (geometry != null) map['geometry'] = geometry!.toJson();
    return map;
  }
}

class Farm {
  final String id;
  final String ownerId;
  final String name;
  final String? village;
  final String taluka;
  final String district;
  final String state;
  final String? irrigationType;
  final String? waterSource;
  final GeoJsonPolygon geometry;
  final double calculatedAreaHectares;
  final double calculatedAreaAcres;
  final double centroidLatitude;
  final double centroidLongitude;
  final double latitude;
  final double longitude;
  final DateTime createdAt;
  final DateTime updatedAt;

  const Farm({
    required this.id,
    required this.ownerId,
    required this.name,
    this.village,
    required this.taluka,
    required this.district,
    required this.state,
    this.irrigationType,
    this.waterSource,
    required this.geometry,
    required this.calculatedAreaHectares,
    required this.calculatedAreaAcres,
    required this.centroidLatitude,
    required this.centroidLongitude,
    required this.latitude,
    required this.longitude,
    required this.createdAt,
    required this.updatedAt,
  });

  factory Farm.fromJson(Map<String, dynamic> json) {
    return Farm(
      id: json['id'] as String,
      ownerId: json['owner_id'] as String,
      name: json['name'] as String,
      village: json['village'] as String?,
      taluka: json['taluka'] as String,
      district: json['district'] as String? ?? 'Pune',
      state: json['state'] as String? ?? 'Maharashtra',
      irrigationType: json['irrigation_type'] as String?,
      waterSource: json['water_source'] as String?,
      geometry: GeoJsonPolygon.fromJson(json['geometry'] as Map<String, dynamic>),
      calculatedAreaHectares: (json['calculated_area_hectares'] as num).toDouble(),
      calculatedAreaAcres: (json['calculated_area_acres'] as num).toDouble(),
      centroidLatitude: (json['centroid_latitude'] as num).toDouble(),
      centroidLongitude: (json['centroid_longitude'] as num).toDouble(),
      latitude: (json['latitude'] as num?)?.toDouble() ?? (json['centroid_latitude'] as num).toDouble(),
      longitude: (json['longitude'] as num?)?.toDouble() ?? (json['centroid_longitude'] as num).toDouble(),
      createdAt: DateTime.parse(json['created_at'] as String),
      updatedAt: DateTime.parse(json['updated_at'] as String),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'owner_id': ownerId,
      'name': name,
      if (village != null) 'village': village,
      'taluka': taluka,
      'district': district,
      'state': state,
      if (irrigationType != null) 'irrigation_type': irrigationType,
      if (waterSource != null) 'water_source': waterSource,
      'geometry': geometry.toJson(),
      'calculated_area_hectares': calculatedAreaHectares,
      'calculated_area_acres': calculatedAreaAcres,
      'centroid_latitude': centroidLatitude,
      'centroid_longitude': centroidLongitude,
      'latitude': latitude,
      'longitude': longitude,
      'created_at': createdAt.toIso8601String(),
      'updated_at': updatedAt.toIso8601String(),
    };
  }
}
