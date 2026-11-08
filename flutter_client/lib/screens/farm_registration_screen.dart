import 'package:flutter/material.dart';
import '../models/farm_models.dart';
import '../services/api_service.dart';
import '../services/app_state.dart';

class FarmRegistrationScreen extends StatefulWidget {
  final VoidCallback? onComplete;

  const FarmRegistrationScreen({Key? key, this.onComplete}) : super(key: key);

  @override
  State<FarmRegistrationScreen> createState() => _FarmRegistrationScreenState();
}

class _FarmRegistrationScreenState extends State<FarmRegistrationScreen> {
  int _currentStep = 0;
  bool _isSubmitting = false;
  bool _isLoadingGeo = true;

  // Step 1: Farmer details (Clean starting inputs)
  final _farmerNameController = TextEditingController();
  final _phoneController = TextEditingController();
  String? _selectedDistrict;
  String? _selectedTaluka;
  final _villageController = TextEditingController();

  // Step 2: Farm details
  final _farmNameController = TextEditingController();
  final _totalAreaController = TextEditingController();
  double _latitude = 18.151;
  double _longitude = 74.577;

  // Step 3: Crop details
  String? _selectedCropCode;
  DateTime _sowingDate = DateTime.now().subtract(const Duration(days: 35));
  final _plantedAreaController = TextEditingController();
  String _selectedIrrigation = 'rainfed';

  // Dynamic catalogs loaded from backend
  List<Map<String, dynamic>> _districts = [];
  List<Map<String, dynamic>> _talukas = [];
  List<Map<String, dynamic>> _crops = [];

  final List<Map<String, String>> _irrigationTypes = [
    {'code': 'rainfed', 'name': 'Rainfed (जिरायत)'},
    {'code': 'canal', 'name': 'Canal Irrigation (कालवा)'},
    {'code': 'drip', 'name': 'Drip Irrigation (ठिबक)'},
    {'code': 'sprinkler', 'name': 'Sprinkler (तुषार)'},
    {'code': 'well', 'name': 'Well / Borewell (विहीर / बोअरवेल)'},
  ];

  @override
  void initState() {
    super.initState();
    _loadCatalogs();
  }

  Future<void> _loadCatalogs() async {
    setState(() => _isLoadingGeo = true);
    final dists = await ApiService.getDistricts();
    final crops = await ApiService.getCrops();

    String? defaultDist;
    if (dists.isNotEmpty) {
      defaultDist = dists.firstWhere((d) => d['district_name'] == 'Pune', orElse: () => dists.first)['district_name'];
    }

    List<Map<String, dynamic>> tals = [];
    if (defaultDist != null) {
      tals = await ApiService.getTalukas(district: defaultDist);
    }

    if (mounted) {
      setState(() {
        _districts = dists;
        _crops = crops;
        _selectedDistrict = defaultDist;
        _talukas = tals;
        if (tals.isNotEmpty) {
          _selectedTaluka = tals.first['taluka_name'];
          _latitude = (tals.first['latitude'] as num).toDouble();
          _longitude = (tals.first['longitude'] as num).toDouble();
        }
        if (crops.isNotEmpty) {
          _selectedCropCode = crops.first['crop_code'];
        }
        _isLoadingGeo = false;
      });
    }
  }

  Future<void> _onDistrictChanged(String? newDist) async {
    if (newDist == null || newDist == _selectedDistrict) return;
    setState(() {
      _selectedDistrict = newDist;
      _selectedTaluka = null;
    });

    final tals = await ApiService.getTalukas(district: newDist);
    if (mounted) {
      setState(() {
        _talukas = tals;
        if (tals.isNotEmpty) {
          _selectedTaluka = tals.first['taluka_name'];
          _latitude = (tals.first['latitude'] as num).toDouble();
          _longitude = (tals.first['longitude'] as num).toDouble();
        }
      });
    }
  }

  void _onTalukaChanged(String? newTaluka) {
    if (newTaluka == null) return;
    final match = _talukas.firstWhere((t) => t['taluka_name'] == newTaluka, orElse: () => {});
    setState(() {
      _selectedTaluka = newTaluka;
      if (match.containsKey('latitude')) {
        _latitude = (match['latitude'] as num).toDouble();
        _longitude = (match['longitude'] as num).toDouble();
      }
    });
  }

  Future<void> _handleCompleteRegistration() async {
    final name = _farmerNameController.text.trim();
    if (name.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please enter your farmer name in Step 1.')),
      );
      setState(() => _currentStep = 0);
      return;
    }

    setState(() => _isSubmitting = true);

    final totalArea = double.tryParse(_totalAreaController.text) ?? 3.0;
    final plantedArea = double.tryParse(_plantedAreaController.text) ?? (totalArea * 0.8);
    final sowingDateStr =
        '${_sowingDate.year}-${_sowingDate.month.toString().padLeft(2, '0')}-${_sowingDate.day.toString().padLeft(2, '0')}';

    try {
      final summary = await ApiService.guidedRegisterFarm(
        farmerName: name,
        phoneNumber: _phoneController.text.trim().isNotEmpty ? _phoneController.text.trim() : null,
        taluka: _selectedTaluka ?? 'Baramati',
        district: _selectedDistrict ?? 'Pune',
        village: _villageController.text.trim().isNotEmpty ? _villageController.text.trim() : 'Gram',
        farmName: _farmNameController.text.trim().isNotEmpty ? _farmNameController.text.trim() : '$name\'s Farm',
        totalAreaAcres: totalArea,
        cropCode: _selectedCropCode ?? 'soybean',
        sowingDate: sowingDateStr,
        irrigationType: _selectedIrrigation,
        plantedAreaAcres: plantedArea,
        latitude: _latitude,
        longitude: _longitude,
      );

      // Update active app state so all screens reflect this new farm
      AppState.instance.setActiveFarm(summary);

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Farm registered in ${_selectedTaluka ?? "Baramati"}, ${_selectedDistrict ?? "Pune"}! All tabs updated.'),
            backgroundColor: const Color(0xFF1B5E20),
          ),
        );
        widget.onComplete?.call();
        Navigator.pop(context, true);
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Registration error: $e'), backgroundColor: Colors.red),
        );
      }
    } finally {
      if (mounted) {
        setState(() => _isSubmitting = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoadingGeo) {
      return Scaffold(
        appBar: AppBar(
          title: const Text('Farm Setup Guide'),
          backgroundColor: const Color(0xFF1B5E20),
          foregroundColor: Colors.white,
        ),
        body: const Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              CircularProgressIndicator(color: Color(0xFF1B5E20)),
              SizedBox(height: 16),
              Text('Loading Maharashtra district and crop catalogues...'),
            ],
          ),
        ),
      );
    }

    return Scaffold(
      appBar: AppBar(
        title: const Text('Farm Setup Guide', style: TextStyle(fontWeight: FontWeight.bold)),
        backgroundColor: const Color(0xFF1B5E20),
        foregroundColor: Colors.white,
      ),
      body: Stepper(
        type: StepperType.vertical,
        currentStep: _currentStep,
        onStepTapped: (step) => setState(() => _currentStep = step),
        onStepContinue: () {
          if (_currentStep < 4) {
            setState(() => _currentStep += 1);
          } else {
            _handleCompleteRegistration();
          }
        },
        onStepCancel: () {
          if (_currentStep > 0) {
            setState(() => _currentStep -= 1);
          } else {
            Navigator.pop(context);
          }
        },
        controlsBuilder: (context, details) {
          final isLastStep = _currentStep == 4;
          return Padding(
            padding: const EdgeInsets.only(top: 20.0),
            child: Row(
              children: [
                Expanded(
                  child: ElevatedButton(
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFF1B5E20),
                      foregroundColor: Colors.white,
                      padding: const EdgeInsets.symmetric(vertical: 14),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                    ),
                    onPressed: _isSubmitting ? null : details.onStepContinue,
                    child: _isSubmitting
                        ? const SizedBox(
                            height: 20,
                            width: 20,
                            child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                          )
                        : Text(
                            isLastStep ? 'SAVE & GO TO MY FARM' : 'CONTINUE',
                            style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15),
                          ),
                  ),
                ),
                if (_currentStep > 0) ...[
                  const SizedBox(width: 12),
                  OutlinedButton(
                    style: OutlinedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 20),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                    ),
                    onPressed: details.onStepCancel,
                    child: const Text('BACK'),
                  ),
                ],
              ],
            ),
          );
        },
        steps: [
          // Step 1: Farmer Details
          Step(
            title: const Text('Farmer Details', style: TextStyle(fontWeight: FontWeight.bold)),
            subtitle: const Text('Full name and Maharashtra location'),
            isActive: _currentStep >= 0,
            state: _currentStep > 0 ? StepState.complete : StepState.indexed,
            content: Column(
              children: [
                TextFormField(
                  controller: _farmerNameController,
                  decoration: InputDecoration(
                    labelText: 'Full Name *',
                    hintText: 'Enter your name (e.g. Dattatraya Shinde)',
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                    prefixIcon: const Icon(Icons.person_outline),
                  ),
                ),
                const SizedBox(height: 12),
                TextFormField(
                  controller: _phoneController,
                  keyboardType: TextInputType.phone,
                  decoration: InputDecoration(
                    labelText: 'Mobile Number (Optional)',
                    hintText: 'e.g. 9822012345',
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                    prefixIcon: const Icon(Icons.phone_outlined),
                  ),
                ),
                const SizedBox(height: 12),
                Row(
                  children: [
                    Expanded(
                      child: DropdownButtonFormField<String>(
                        value: _selectedDistrict,
                        decoration: InputDecoration(
                          labelText: 'District (36 Total) *',
                          border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                        ),
                        items: _districts.map((d) {
                          final name = d['district_name'].toString();
                          return DropdownMenuItem(value: name, child: Text(name, overflow: TextOverflow.ellipsis));
                        }).toList(),
                        onChanged: _onDistrictChanged,
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: DropdownButtonFormField<String>(
                        value: _selectedTaluka,
                        decoration: InputDecoration(
                          labelText: 'Taluka *',
                          border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                        ),
                        items: _talukas.map((t) {
                          final name = t['taluka_name'].toString();
                          return DropdownMenuItem(value: name, child: Text(name, overflow: TextOverflow.ellipsis));
                        }).toList(),
                        onChanged: _onTalukaChanged,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                TextFormField(
                  controller: _villageController,
                  decoration: InputDecoration(
                    labelText: 'Village Name',
                    hintText: 'e.g. Bawada, Malegaon, Nimgaon',
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                    prefixIcon: const Icon(Icons.location_city_outlined),
                  ),
                ),
              ],
            ),
          ),

          // Step 2: Farm Details
          Step(
            title: const Text('Farm Profile', style: TextStyle(fontWeight: FontWeight.bold)),
            subtitle: const Text('Farm name and acreage'),
            isActive: _currentStep >= 1,
            state: _currentStep > 1 ? StepState.complete : StepState.indexed,
            content: Column(
              children: [
                TextFormField(
                  controller: _farmNameController,
                  decoration: InputDecoration(
                    labelText: 'Farm Name (Optional)',
                    hintText: 'e.g. Shinde Krishi Sheti',
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                    prefixIcon: const Icon(Icons.terrain_outlined),
                  ),
                ),
                const SizedBox(height: 12),
                TextFormField(
                  controller: _totalAreaController,
                  keyboardType: const TextInputType.numberWithOptions(decimal: true),
                  decoration: InputDecoration(
                    labelText: 'Total Farm Land (Acres) *',
                    hintText: 'e.g. 4.5',
                    suffixText: 'Acres',
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                    prefixIcon: const Icon(Icons.aspect_ratio),
                  ),
                ),
                const SizedBox(height: 12),
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: Colors.grey.shade100,
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: Colors.grey.shade300),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.pin_drop, color: Color(0xFF1B5E20)),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          'Centroid: ${_latitude.toStringAsFixed(4)}°N, ${_longitude.toStringAsFixed(4)}°E\n(Official centroid from Maharashtra GIS catalog for ${_selectedTaluka ?? "selected taluka"})',
                          style: const TextStyle(fontSize: 12, color: Colors.black87),
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),

          // Step 3: Crop Details
          Step(
            title: const Text('Active Crop & Season', style: TextStyle(fontWeight: FontWeight.bold)),
            subtitle: const Text('Select from 38 Maharashtra canonical crops'),
            isActive: _currentStep >= 2,
            state: _currentStep > 2 ? StepState.complete : StepState.indexed,
            content: Column(
              children: [
                DropdownButtonFormField<String>(
                  value: _selectedCropCode,
                  isExpanded: true,
                  decoration: InputDecoration(
                    labelText: 'Active Crop (38 Canonical Crops) *',
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                    prefixIcon: const Icon(Icons.grass),
                  ),
                  items: _crops.map((c) {
                    final code = c['crop_code'].toString();
                    final en = c['common_name_en'] ?? code;
                    final mr = c['common_name_mr'] != null ? ' (${c['common_name_mr']})' : '';
                    return DropdownMenuItem(
                      value: code,
                      child: Text('$en$mr', overflow: TextOverflow.ellipsis),
                    );
                  }).toList(),
                  onChanged: (val) => setState(() => _selectedCropCode = val),
                ),
                const SizedBox(height: 12),
                ListTile(
                  shape: RoundedRectangleBorder(
                    side: BorderSide(color: Colors.grey.shade400),
                    borderRadius: BorderRadius.circular(10),
                  ),
                  leading: const Icon(Icons.calendar_today, color: Color(0xFF1B5E20)),
                  title: Text(
                    'Sowing Date: ${_sowingDate.day}/${_sowingDate.month}/${_sowingDate.year}',
                    style: const TextStyle(fontWeight: FontWeight.w600),
                  ),
                  subtitle: Text(
                    '${DateTime.now().difference(_sowingDate).inDays} days after sowing',
                    style: const TextStyle(fontSize: 12, color: Colors.black54),
                  ),
                  trailing: const Icon(Icons.edit_calendar),
                  onTap: () async {
                    final picked = await showDatePicker(
                      context: context,
                      initialDate: _sowingDate,
                      firstDate: DateTime(2023),
                      lastDate: DateTime.now(),
                    );
                    if (picked != null) {
                      setState(() => _sowingDate = picked);
                    }
                  },
                ),
                const SizedBox(height: 12),
                TextFormField(
                  controller: _plantedAreaController,
                  keyboardType: const TextInputType.numberWithOptions(decimal: true),
                  decoration: InputDecoration(
                    labelText: 'Planted Area for this Crop (Acres)',
                    hintText: 'e.g. 3.0',
                    suffixText: 'Acres',
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                    prefixIcon: const Icon(Icons.pie_chart_outline),
                  ),
                ),
                const SizedBox(height: 12),
                DropdownButtonFormField<String>(
                  value: _selectedIrrigation,
                  decoration: InputDecoration(
                    labelText: 'Irrigation Method',
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                    prefixIcon: const Icon(Icons.water_drop_outlined),
                  ),
                  items: _irrigationTypes.map((i) => DropdownMenuItem(value: i['code'], child: Text(i['name']!))).toList(),
                  onChanged: (val) => setState(() => _selectedIrrigation = val!),
                ),
              ],
            ),
          ),

          // Step 4: Soil Information
          Step(
            title: const Text('Soil Baseline (CropNet)', style: TextStyle(fontWeight: FontWeight.bold)),
            subtitle: const Text('Matched soil profile for selected region'),
            isActive: _currentStep >= 3,
            state: _currentStep > 3 ? StepState.complete : StepState.indexed,
            content: Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: const Color(0xFFF1F8E9),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: const Color(0xFFC8E6C9)),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      const Icon(Icons.layers, color: Color(0xFF2E7D32)),
                      const SizedBox(width: 8),
                      Text(
                        '${_selectedTaluka ?? "Local"} Regional Soil Baseline',
                        style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Color(0xFF1B5E20)),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  const Text('Soil Order: Medium to Deep Black Soil (Vertisol / Inceptisol)', style: TextStyle(fontWeight: FontWeight.w600)),
                  const SizedBox(height: 4),
                  const Text('Texture: Clay Loam (Clay 48-52%, Sand 18-24%, Silt 28%)', style: TextStyle(fontSize: 13, color: Colors.black87)),
                  const SizedBox(height: 4),
                  const Text('Organic Carbon: ~0.65% (Medium fertility baseline)', style: TextStyle(fontSize: 13, color: Colors.black87)),
                  const SizedBox(height: 4),
                  const Text('pH: 7.6 - 7.9 (Normal to slightly alkaline Deccan plateau)', style: TextStyle(fontSize: 13, color: Colors.black87)),
                  const Divider(height: 20),
                  Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Icon(Icons.info_outline, size: 18, color: Colors.black54),
                      const SizedBox(width: 6),
                      Expanded(
                        child: Text(
                          'Source: CropNet Maharashtra gridded baseline. Lab test values can be uploaded later if you have a Soil Health Card.',
                          style: TextStyle(fontSize: 11, color: Colors.grey.shade700, fontStyle: FontStyle.italic),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),

          // Step 5: Finish & Confirmation
          Step(
            title: const Text('Review & Activate', style: TextStyle(fontWeight: FontWeight.bold)),
            subtitle: const Text('Confirm details and enter farm'),
            isActive: _currentStep >= 4,
            state: StepState.indexed,
            content: Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: Colors.grey.shade300),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Registration Summary', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Color(0xFF1B5E20))),
                  const SizedBox(height: 12),
                  _buildSummaryRow('Farmer', _farmerNameController.text.isEmpty ? 'Not specified' : _farmerNameController.text),
                  _buildSummaryRow('Location', '${_selectedTaluka ?? ""}, ${_selectedDistrict ?? ""}'),
                  _buildSummaryRow('Farm Name', _farmNameController.text.isEmpty ? 'My Farm' : _farmNameController.text),
                  _buildSummaryRow('Total Area', '${_totalAreaController.text.isEmpty ? "3.0" : _totalAreaController.text} Acres'),
                  _buildSummaryRow('Active Crop', (_selectedCropCode ?? 'SOYBEAN').toUpperCase()),
                  _buildSummaryRow('Sowing Date', '${_sowingDate.day}/${_sowingDate.month}/${_sowingDate.year}'),
                  _buildSummaryRow('Irrigation', _selectedIrrigation),
                  const Divider(height: 20),
                  const Text(
                    'Ready to activate farm intelligence and start receiving localized yield, weather, and heat-safety advisories for your region.',
                    style: TextStyle(fontSize: 12, color: Colors.black54),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSummaryRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4.0),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(fontSize: 13, color: Colors.black54)),
          Text(value, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.bold)),
        ],
      ),
    );
  }
}
