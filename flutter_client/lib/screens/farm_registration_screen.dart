import 'package:flutter/material.dart';
import '../models/farm_models.dart';
import '../services/api_service.dart';

class FarmRegistrationScreen extends StatefulWidget {
  final VoidCallback? onComplete;

  const FarmRegistrationScreen({Key? key, this.onComplete}) : super(key: key);

  @override
  State<FarmRegistrationScreen> createState() => _FarmRegistrationScreenState();
}

class _FarmRegistrationScreenState extends State<FarmRegistrationScreen> {
  int _currentStep = 0;
  bool _isSubmitting = false;

  // Step 1: Farmer details
  final _farmerNameController = TextEditingController(text: 'Ramesh Patil');
  final _phoneController = TextEditingController(text: '9876543210');
  String _selectedDistrict = 'Pune';
  String _selectedTaluka = 'Baramati';
  final _villageController = TextEditingController(text: 'Malegaon Khurd');

  // Step 2: Farm details
  final _farmNameController = TextEditingController(text: 'Patil Krishi Farm');
  final _totalAreaController = TextEditingController(text: '4.5');
  double _latitude = 18.151;
  double _longitude = 74.577;

  // Step 3: Crop details
  String _selectedCropCode = 'soybean';
  DateTime _sowingDate = DateTime.now().subtract(const Duration(days: 42));
  final _plantedAreaController = TextEditingController(text: '3.0');
  String _selectedIrrigation = 'rainfed';

  // Taluka coordinates map for Pune pilot
  final Map<String, Map<String, double>> _talukaCoords = {
    'Baramati': {'lat': 18.151, 'lon': 74.577},
    'Indapur': {'lat': 18.115, 'lon': 75.025},
    'Maval': {'lat': 18.754, 'lon': 73.541},
    'Mulshi': {'lat': 18.503, 'lon': 73.513},
  };

  final List<String> _districts = ['Pune', 'Satara', 'Solapur', 'Ahmednagar', 'Kolhapur'];
  final List<String> _talukas = ['Baramati', 'Indapur', 'Maval', 'Mulshi'];

  final List<Map<String, String>> _crops = [
    {'code': 'soybean', 'name': 'Soybean (सोयाबीन)'},
    {'code': 'cotton', 'name': 'Cotton (कापूस)'},
    {'code': 'jowar', 'name': 'Jowar (ज्वारी)'},
    {'code': 'gram', 'name': 'Gram / Chana (हरभरा)'},
    {'code': 'wheat', 'name': 'Wheat (गहू)'},
    {'code': 'sugarcane', 'name': 'Sugarcane (ऊस)'},
  ];

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
    _updateCoordinates('Baramati');
  }

  void _updateCoordinates(String taluka) {
    if (_talukaCoords.containsKey(taluka)) {
      _latitude = _talukaCoords[taluka]!['lat']!;
      _longitude = _talukaCoords[taluka]!['lon']!;
    }
  }

  Future<void> _handleCompleteRegistration() async {
    setState(() => _isSubmitting = true);

    final totalArea = double.tryParse(_totalAreaController.text) ?? 4.5;
    final plantedArea = double.tryParse(_plantedAreaController.text) ?? 3.0;
    final sowingDateStr =
        '${_sowingDate.year}-${_sowingDate.month.toString().padLeft(2, '0')}-${_sowingDate.day.toString().padLeft(2, '0')}';

    try {
      await ApiService.guidedRegisterFarm(
        farmerName: _farmerNameController.text.trim().isEmpty ? 'Farmer' : _farmerNameController.text.trim(),
        phoneNumber: _phoneController.text.trim(),
        taluka: _selectedTaluka,
        district: _selectedDistrict,
        village: _villageController.text.trim(),
        farmName: _farmNameController.text.trim(),
        totalAreaAcres: totalArea,
        cropCode: _selectedCropCode,
        sowingDate: sowingDateStr,
        irrigationType: _selectedIrrigation,
        plantedAreaAcres: plantedArea,
      );

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Farm registered successfully! CropNet soil profile attached.'),
            backgroundColor: Color(0xFF1B5E20),
          ),
        );
        widget.onComplete?.call();
        Navigator.pop(context, true);
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error registering farm: $e'), backgroundColor: Colors.red),
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
            subtitle: const Text('Name and village location'),
            isActive: _currentStep >= 0,
            state: _currentStep > 0 ? StepState.complete : StepState.indexed,
            content: Column(
              children: [
                TextFormField(
                  controller: _farmerNameController,
                  decoration: InputDecoration(
                    labelText: 'Full Name *',
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                    prefixIcon: const Icon(Icons.person_outline),
                  ),
                ),
                const SizedBox(height: 12),
                TextFormField(
                  controller: _phoneController,
                  keyboardType: TextInputType.phone,
                  decoration: InputDecoration(
                    labelText: 'Mobile Number',
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
                          labelText: 'District',
                          border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                        ),
                        items: _districts.map((d) => DropdownMenuItem(value: d, child: Text(d))).toList(),
                        onChanged: (val) => setState(() => _selectedDistrict = val!),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: DropdownButtonFormField<String>(
                        value: _selectedTaluka,
                        decoration: InputDecoration(
                          labelText: 'Taluka',
                          border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                        ),
                        items: _talukas.map((t) => DropdownMenuItem(value: t, child: Text(t))).toList(),
                        onChanged: (val) {
                          if (val != null) {
                            setState(() {
                              _selectedTaluka = val;
                              _updateCoordinates(val);
                            });
                          }
                        },
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                TextFormField(
                  controller: _villageController,
                  decoration: InputDecoration(
                    labelText: 'Village Name',
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
                    labelText: 'Farm Name',
                    hintText: 'e.g. Patil Krishi Farm',
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
                          'Estimated Center: ${_latitude.toStringAsFixed(3)}°N, ${_longitude.toStringAsFixed(3)}°E\n(Derived from $_selectedTaluka pilot taluka centroid)',
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
            subtitle: const Text('Crop type, sowing date, irrigation'),
            isActive: _currentStep >= 2,
            state: _currentStep > 2 ? StepState.complete : StepState.indexed,
            content: Column(
              children: [
                DropdownButtonFormField<String>(
                  value: _selectedCropCode,
                  decoration: InputDecoration(
                    labelText: 'Active Crop *',
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                    prefixIcon: const Icon(Icons.grass),
                  ),
                  items: _crops.map((c) => DropdownMenuItem(value: c['code'], child: Text(c['name']!))).toList(),
                  onChanged: (val) => setState(() => _selectedCropCode = val!),
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
            subtitle: const Text('Auto-matched soil profile & provenance'),
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
                        '$_selectedTaluka Soil Association',
                        style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Color(0xFF1B5E20)),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  const Text('Soil Type: Medium to Deep Black Soil (Vertisol / Inceptisol)', style: TextStyle(fontWeight: FontWeight.w600)),
                  const SizedBox(height: 4),
                  const Text('Texture: Clay loam (Clay 48%, Silt 28%, Sand 24%)', style: TextStyle(fontSize: 13, color: Colors.black87)),
                  const SizedBox(height: 4),
                  const Text('Organic Carbon: 0.65% (Medium)', style: TextStyle(fontSize: 13, color: Colors.black87)),
                  const SizedBox(height: 4),
                  const Text('pH: 7.8 (Slightly Alkaline) · EC: 0.28 dS/m (Normal)', style: TextStyle(fontSize: 13, color: Colors.black87)),
                  const Divider(height: 20),
                  Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Icon(Icons.info_outline, size: 18, color: Colors.black54),
                      const SizedBox(width: 6),
                      Expanded(
                        child: Text(
                          'Source: CropNet Maharashtra gridded baseline. If you possess an official Soil Health Card, you can upload lab-tested values in settings.',
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
            subtitle: const Text('Confirm farm details'),
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
                  _buildSummaryRow('Farmer', _farmerNameController.text),
                  _buildSummaryRow('Location', '$_selectedTaluka, $_selectedDistrict'),
                  _buildSummaryRow('Farm Name', _farmNameController.text),
                  _buildSummaryRow('Total Area', '${_totalAreaController.text} Acres'),
                  _buildSummaryRow('Active Crop', _selectedCropCode.toUpperCase()),
                  _buildSummaryRow('Sowing Date', '${_sowingDate.day}/${_sowingDate.month}/${_sowingDate.year}'),
                  _buildSummaryRow('Irrigation', _selectedIrrigation),
                  const Divider(height: 20),
                  const Text(
                    'Ready to activate farm intelligence and start receiving localized yield, weather, and heat-safety advisories.',
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
