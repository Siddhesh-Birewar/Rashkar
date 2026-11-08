import 'package:flutter/material.dart';
import '../models/farm_models.dart';
import '../services/api_service.dart';
import '../services/app_state.dart';

class EditProfileScreen extends StatefulWidget {
  final FarmSummary? farm;

  const EditProfileScreen({Key? key, this.farm}) : super(key: key);

  @override
  State<EditProfileScreen> createState() => _EditProfileScreenState();
}

class _EditProfileScreenState extends State<EditProfileScreen> {
  final _formKey = GlobalKey<FormState>();

  // Text Controllers
  late TextEditingController _farmerNameController;
  late TextEditingController _phoneController;
  late TextEditingController _farmNameController;
  late TextEditingController _villageController;
  late TextEditingController _totalAcresController;
  late TextEditingController _plantedAcresController;
  late TextEditingController _varietyController;

  // Selections
  String? _selectedDistrict;
  String? _selectedTaluka;
  String? _selectedCropCode;
  String _selectedIrrigation = 'rainfed';
  DateTime _sowingDate = DateTime.now().subtract(const Duration(days: 45));
  double _latitude = 18.151;
  double _longitude = 74.577;

  // Catalogs
  List<Map<String, dynamic>> _districts = [];
  List<Map<String, dynamic>> _talukas = [];
  List<Map<String, dynamic>> _crops = [];

  bool _isLoadingCatalogs = true;
  bool _isSaving = false;

  @override
  void initState() {
    super.initState();
    final f = widget.farm ?? AppState.instance.activeFarm;

    _farmerNameController = TextEditingController(text: f?.farmerName ?? '');
    _phoneController = TextEditingController(text: '9822012345');
    _farmNameController = TextEditingController(text: f?.farmName ?? '');
    _villageController = TextEditingController();
    _totalAcresController = TextEditingController(text: (f?.totalAreaAcres ?? 3.0).toString());
    _plantedAcresController = TextEditingController(text: (f?.plantedAreaAcres ?? 2.5).toString());
    _varietyController = TextEditingController();

    if (f != null) {
      _latitude = f.latitude;
      _longitude = f.longitude;
      _selectedCropCode = f.activeCropCode;
      _selectedIrrigation = f.irrigationType ?? 'rainfed';
      if (f.sowingDate != null) {
        _sowingDate = DateTime.tryParse(f.sowingDate!) ?? _sowingDate;
      }
      final parts = f.locationDisplay.split(',');
      if (parts.isNotEmpty) {
        _selectedDistrict = parts.last.trim();
      }
      if (parts.length > 1) {
        _selectedTaluka = parts[parts.length - 2].trim();
      }
      if (parts.length > 2) {
        _villageController.text = parts.first.trim();
      }
    }

    _loadCatalogs();
  }

  @override
  void dispose() {
    _farmerNameController.dispose();
    _phoneController.dispose();
    _farmNameController.dispose();
    _villageController.dispose();
    _totalAcresController.dispose();
    _plantedAcresController.dispose();
    _varietyController.dispose();
    super.dispose();
  }

  Future<void> _loadCatalogs() async {
    setState(() => _isLoadingCatalogs = true);
    final districts = await ApiService.getDistricts();
    final crops = await ApiService.getCrops();

    if (mounted) {
      setState(() {
        _districts = districts;
        _crops = crops;
        if (_selectedDistrict == null && districts.isNotEmpty) {
          _selectedDistrict = districts.first['district_name'];
        }
        if (_selectedCropCode == null && crops.isNotEmpty) {
          _selectedCropCode = crops.first['crop_code'];
        }
      });
      if (_selectedDistrict != null) {
        await _loadTalukasForDistrict(_selectedDistrict!);
      } else {
        setState(() => _isLoadingCatalogs = false);
      }
    }
  }

  Future<void> _loadTalukasForDistrict(String district) async {
    final talukas = await ApiService.getTalukas(district: district);
    if (mounted) {
      setState(() {
        _talukas = talukas;
        _isLoadingCatalogs = false;
        final match = talukas.where((t) => t['taluka_name'].toString().toLowerCase() == _selectedTaluka?.toLowerCase());
        if (match.isNotEmpty) {
          _selectedTaluka = match.first['taluka_name'];
          _latitude = (match.first['latitude'] as num).toDouble();
          _longitude = (match.first['longitude'] as num).toDouble();
        } else if (talukas.isNotEmpty) {
          _selectedTaluka = talukas.first['taluka_name'];
          _latitude = (talukas.first['latitude'] as num).toDouble();
          _longitude = (talukas.first['longitude'] as num).toDouble();
        }
      });
    }
  }

  Future<void> _saveChanges() async {
    if (!_formKey.currentState!.validate()) return;
    final farmId = widget.farm?.farmId ?? AppState.instance.activeFarmId;
    if (farmId == null) return;

    setState(() => _isSaving = true);

    final sowingStr = '${_sowingDate.year}-${_sowingDate.month.toString().padLeft(2, '0')}-${_sowingDate.day.toString().padLeft(2, '0')}';
    final totalAcres = double.tryParse(_totalAcresController.text.trim()) ?? 3.0;
    final plantedAcres = double.tryParse(_plantedAcresController.text.trim()) ?? 2.5;

    final updated = await ApiService.updateFarmProfile(
      farmId: farmId,
      farmerName: _farmerNameController.text.trim(),
      phoneNumber: _phoneController.text.trim(),
      farmName: _farmNameController.text.trim(),
      district: _selectedDistrict,
      taluka: _selectedTaluka,
      village: _villageController.text.trim().isNotEmpty ? _villageController.text.trim() : null,
      latitude: _latitude,
      longitude: _longitude,
      totalAreaAcres: totalAcres,
      plantedAreaAcres: plantedAcres,
      cropCode: _selectedCropCode,
      varietyName: _varietyController.text.trim().isNotEmpty ? _varietyController.text.trim() : null,
      sowingDate: sowingStr,
      irrigationType: _selectedIrrigation,
    );

    if (mounted) {
      setState(() => _isSaving = false);
      if (updated != null) {
        AppState.instance.setActiveFarm(updated);
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Farm profile updated successfully! All models re-aligned.'),
            backgroundColor: Color(0xFF1B5E20),
          ),
        );
        Navigator.pop(context, true);
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Failed to update farm profile. Please check inputs.'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF6F8F6),
      appBar: AppBar(
        title: const Text('Edit Farm & Crop Profile', style: TextStyle(fontWeight: FontWeight.bold)),
        backgroundColor: const Color(0xFF1B5E20),
        foregroundColor: Colors.white,
      ),
      body: _isLoadingCatalogs
          ? const Center(child: CircularProgressIndicator(color: Color(0xFF1B5E20)))
          : SingleChildScrollView(
              padding: const EdgeInsets.all(20.0),
              child: Form(
                key: _formKey,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    // Section 1: Farmer Identity
                    _buildSectionHeader('1. FARMER IDENTITY', Icons.person_outline),
                    Card(
                      elevation: 1,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                      child: Padding(
                        padding: const EdgeInsets.all(16.0),
                        child: Column(
                          children: [
                            TextFormField(
                              controller: _farmerNameController,
                              decoration: const InputDecoration(
                                labelText: 'Farmer Full Name',
                                border: OutlineInputBorder(),
                                prefixIcon: Icon(Icons.person),
                              ),
                              validator: (v) => v == null || v.trim().isEmpty ? 'Enter farmer name' : null,
                            ),
                            const SizedBox(height: 14),
                            TextFormField(
                              controller: _phoneController,
                              decoration: const InputDecoration(
                                labelText: 'Phone Number (Optional)',
                                border: OutlineInputBorder(),
                                prefixIcon: Icon(Icons.phone),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                    const SizedBox(height: 20),

                    // Section 2: Farm & Location
                    _buildSectionHeader('2. FARM & GEOGRAPHIC LOCATION', Icons.location_on_outlined),
                    Card(
                      elevation: 1,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                      child: Padding(
                        padding: const EdgeInsets.all(16.0),
                        child: Column(
                          children: [
                            TextFormField(
                              controller: _farmNameController,
                              decoration: const InputDecoration(
                                labelText: 'Farm Name',
                                border: OutlineInputBorder(),
                                prefixIcon: Icon(Icons.business_outlined),
                              ),
                              validator: (v) => v == null || v.trim().isEmpty ? 'Enter farm name' : null,
                            ),
                            const SizedBox(height: 14),
                            // District dropdown
                            DropdownButtonFormField<String>(
                              value: _selectedDistrict,
                              decoration: const InputDecoration(
                                labelText: 'District (Maharashtra)',
                                border: OutlineInputBorder(),
                                prefixIcon: Icon(Icons.map_outlined),
                              ),
                              items: _districts.map((d) {
                                final name = d['district_name'].toString();
                                return DropdownMenuItem(value: name, child: Text(name));
                              }).toList(),
                              onChanged: (val) {
                                if (val != null && val != _selectedDistrict) {
                                  setState(() => _selectedDistrict = val);
                                  _loadTalukasForDistrict(val);
                                }
                              },
                            ),
                            const SizedBox(height: 14),
                            // Taluka dropdown
                            DropdownButtonFormField<String>(
                              value: _selectedTaluka,
                              decoration: const InputDecoration(
                                labelText: 'Taluka',
                                border: OutlineInputBorder(),
                                prefixIcon: Icon(Icons.pin_drop_outlined),
                              ),
                              items: _talukas.map((t) {
                                final name = t['taluka_name'].toString();
                                return DropdownMenuItem(value: name, child: Text(name));
                              }).toList(),
                              onChanged: (val) {
                                if (val != null) {
                                  final match = _talukas.where((t) => t['taluka_name'] == val);
                                  setState(() {
                                    _selectedTaluka = val;
                                    if (match.isNotEmpty) {
                                      _latitude = (match.first['latitude'] as num).toDouble();
                                      _longitude = (match.first['longitude'] as num).toDouble();
                                    }
                                  });
                                }
                              },
                            ),
                            const SizedBox(height: 14),
                            TextFormField(
                              controller: _villageController,
                              decoration: const InputDecoration(
                                labelText: 'Village (Optional)',
                                border: OutlineInputBorder(),
                                prefixIcon: Icon(Icons.home_work_outlined),
                              ),
                            ),
                            const SizedBox(height: 10),
                            Container(
                              padding: const EdgeInsets.all(10),
                              decoration: BoxDecoration(
                                color: const Color(0xFFF1F8E9),
                                borderRadius: BorderRadius.circular(8),
                              ),
                              child: Text(
                                'Official Coordinates: ${_latitude.toStringAsFixed(4)}°N, ${_longitude.toStringAsFixed(4)}°E (Auto-aligned for IMD gridded weather & CropNet soil profile)',
                                style: const TextStyle(fontSize: 12, color: Color(0xFF2E7D32)),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                    const SizedBox(height: 20),

                    // Section 3: Crop & Sowing Specifications
                    _buildSectionHeader('3. ACTIVE CROP & MANAGEMENT', Icons.eco_outlined),
                    Card(
                      elevation: 1,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                      child: Padding(
                        padding: const EdgeInsets.all(16.0),
                        child: Column(
                          children: [
                            // Canonical crop selector
                            DropdownButtonFormField<String>(
                              value: _selectedCropCode,
                              decoration: const InputDecoration(
                                labelText: 'Crop (from 38 Canonical Crops)',
                                border: OutlineInputBorder(),
                                prefixIcon: Icon(Icons.grass),
                              ),
                              items: _crops.map((c) {
                                final code = c['crop_code'].toString();
                                final name = c['common_name_en'].toString();
                                final mr = c['common_name_mr'] ?? '';
                                return DropdownMenuItem(
                                  value: code,
                                  child: Text('$name ($mr)'),
                                );
                              }).toList(),
                              onChanged: (val) {
                                if (val != null) setState(() => _selectedCropCode = val);
                              },
                            ),
                            const SizedBox(height: 14),
                            TextFormField(
                              controller: _varietyController,
                              decoration: const InputDecoration(
                                labelText: 'Variety / Cultivar (e.g. JS-335, Phule Samruddhi)',
                                border: OutlineInputBorder(),
                                prefixIcon: Icon(Icons.label_outline),
                              ),
                            ),
                            const SizedBox(height: 14),
                            // Sowing Date Picker
                            ListTile(
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(8),
                                side: BorderSide(color: Colors.grey.shade400),
                              ),
                              leading: const Icon(Icons.calendar_today, color: Color(0xFF1B5E20)),
                              title: const Text('Sowing Date', style: TextStyle(fontSize: 13, color: Colors.black54)),
                              subtitle: Text(
                                '${_sowingDate.day}/${_sowingDate.month}/${_sowingDate.year}',
                                style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                              ),
                              trailing: const Icon(Icons.edit, size: 18),
                              onTap: () async {
                                final d = await showDatePicker(
                                  context: context,
                                  initialDate: _sowingDate,
                                  firstDate: DateTime(2023, 1, 1),
                                  lastDate: DateTime.now(),
                                );
                                if (d != null) setState(() => _sowingDate = d);
                              },
                            ),
                            const SizedBox(height: 14),
                            Row(
                              children: [
                                Expanded(
                                  child: TextFormField(
                                    controller: _totalAcresController,
                                    keyboardType: TextInputType.number,
                                    decoration: const InputDecoration(
                                      labelText: 'Total Farm Acres',
                                      border: OutlineInputBorder(),
                                    ),
                                  ),
                                ),
                                const SizedBox(width: 12),
                                Expanded(
                                  child: TextFormField(
                                    controller: _plantedAcresController,
                                    keyboardType: TextInputType.number,
                                    decoration: const InputDecoration(
                                      labelText: 'Planted Crop Acres',
                                      border: OutlineInputBorder(),
                                    ),
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 14),
                            // Irrigation type
                            DropdownButtonFormField<String>(
                              value: _selectedIrrigation,
                              decoration: const InputDecoration(
                                labelText: 'Irrigation Source / Method',
                                border: OutlineInputBorder(),
                                prefixIcon: Icon(Icons.water_drop_outlined),
                              ),
                              items: const [
                                DropdownMenuItem(value: 'rainfed', child: Text('Rainfed / Non-irrigated')),
                                DropdownMenuItem(value: 'drip', child: Text('Drip Micro-irrigation')),
                                DropdownMenuItem(value: 'sprinkler', child: Text('Sprinkler Irrigation')),
                                DropdownMenuItem(value: 'flood', child: Text('Canal / Surface Flood')),
                                DropdownMenuItem(value: 'well', child: Text('Open Well / Borewell')),
                              ],
                              onChanged: (val) {
                                if (val != null) setState(() => _selectedIrrigation = val);
                              },
                            ),
                          ],
                        ),
                      ),
                    ),
                    const SizedBox(height: 24),

                    // Save Button
                    SizedBox(
                      height: 52,
                      child: ElevatedButton.icon(
                        onPressed: _isSaving ? null : _saveChanges,
                        icon: _isSaving
                            ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                            : const Icon(Icons.check_circle_outline),
                        label: Text(
                          _isSaving ? 'Saving Changes...' : 'Save Profile Changes',
                          style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                        ),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: const Color(0xFF1B5E20),
                          foregroundColor: Colors.white,
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                        ),
                      ),
                    ),
                    const SizedBox(height: 20),
                  ],
                ),
              ),
            ),
    );
  }

  Widget _buildSectionHeader(String title, IconData icon) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8.0, left: 4.0),
      child: Row(
        children: [
          Icon(icon, size: 18, color: const Color(0xFF1B5E20)),
          const SizedBox(width: 6),
          Text(
            title,
            style: const TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: Color(0xFF333333), letterSpacing: 0.8),
          ),
        ],
      ),
    );
  }
}
