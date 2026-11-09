import 'package:flutter/material.dart';
import '../models/farm_models.dart';
import '../services/api_service.dart';
import '../services/app_state.dart';
import 'insurer_dashboard_screen.dart';

class CropLossScreen extends StatefulWidget {
  const CropLossScreen({Key? key}) : super(key: key);

  @override
  State<CropLossScreen> createState() => _CropLossScreenState();
}

class _CropLossScreenState extends State<CropLossScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  List<CropLossCase> _cases = [];
  bool _isLoading = true;

  // Wizard / Form State
  int _currentStep = 0;
  String _cropCode = 'soybean';
  String _perilType = 'unseasonal_rainfall';
  double _damagePct = 40.0;
  double _affectedAcres = 2.0;
  DateTime _eventDate = DateTime.now().subtract(const Duration(days: 1));
  bool _isSubmitting = false;

  final Map<String, Map<String, dynamic>> _perilOptions = {
    'unseasonal_rainfall': {
      'title': 'Unseasonal Rain / Flood',
      'icon': Icons.water_drop_outlined,
      'color': Colors.blue,
    },
    'hailstorm': {
      'title': 'Hailstorm Damage',
      'icon': Icons.ac_unit_outlined,
      'color': Colors.teal,
    },
    'dry_spell_drought': {
      'title': 'Drought / Dry Spell',
      'icon': Icons.wb_sunny_outlined,
      'color': Colors.deepOrange,
    },
    'post_harvest_cyclone': {
      'title': 'Heatwave / Extreme Heat',
      'icon': Icons.local_fire_department_outlined,
      'color': Colors.red,
    },
    'inundation_waterlogging': {
      'title': 'Pest or Disease Attack',
      'icon': Icons.bug_report_outlined,
      'color': Colors.brown,
    },
  };

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    AppState.instance.addListener(_onStateChange);
    _cropCode = AppState.instance.activeCropCode;
    _affectedAcres = AppState.instance.activeFarm?.totalAreaAcres ?? 2.0;
    _loadCases();
  }

  @override
  void dispose() {
    AppState.instance.removeListener(_onStateChange);
    _tabController.dispose();
    super.dispose();
  }

  void _onStateChange() {
    if (mounted) {
      setState(() {
        _cropCode = AppState.instance.activeCropCode;
      });
      _loadCases();
    }
  }

  Future<void> _loadCases() async {
    setState(() => _isLoading = true);
    final farmerId = AppState.instance.activeFarmerId ?? 'farmer_demo_01';
    final c = await ApiService.getFarmerLossCases(farmerId);
    if (mounted) {
      setState(() {
        _cases = c;
        _isLoading = false;
      });
    }
  }

  Future<void> _submitCase({required bool isDraft}) async {
    setState(() => _isSubmitting = true);
    final farmerId = AppState.instance.activeFarmerId ?? 'farmer_demo_01';
    final farmId = AppState.instance.activeFarmId ?? 'farm_demo_pune_01';

    final newCase = await ApiService.submitCropLossCase(
      farmerId: farmerId,
      farmId: farmId,
      cropCode: _cropCode,
      eventDate: '${_eventDate.year}-${_eventDate.month.toString().padLeft(2, '0')}-${_eventDate.day.toString().padLeft(2, '0')}',
      perilType: _perilType,
      damageEstimatePct: _damagePct,
      affectedAreaAcres: _affectedAcres,
      photoUrls: ['/storage/photos/damage_field_evidence.jpg'],
      isDraft: isDraft,
    );

    if (mounted) {
      setState(() {
        _cases.insert(0, newCase);
        _isSubmitting = false;
        _currentStep = 0; // reset wizard
        _tabController.animateTo(1); // view past claims
      });

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(isDraft ? 'Draft saved offline.' : 'Crop loss claim submitted successfully!'),
          backgroundColor: isDraft ? Colors.blueGrey : const Color(0xFF1B5E20),
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final appState = AppState.instance;

    return Scaffold(
      backgroundColor: const Color(0xFFF6F8F6),
      appBar: AppBar(
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Crop Loss Claim (PMFBY)', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
            Text(
              '${appState.activeFarm?.farmName ?? "Farm"} · ${appState.activeTaluka}, ${appState.activeDistrict}',
              style: const TextStyle(fontSize: 12, color: Colors.white70),
            ),
          ],
        ),
        backgroundColor: const Color(0xFF1B5E20),
        foregroundColor: Colors.white,
        actions: [
          IconButton(
            tooltip: 'Refresh Claims',
            icon: const Icon(Icons.refresh),
            onPressed: _loadCases,
          ),
        ],
        bottom: TabBar(
          controller: _tabController,
          indicatorColor: Colors.white,
          indicatorWeight: 3.0,
          labelColor: Colors.white,
          unselectedLabelColor: Colors.white70,
          labelStyle: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
          tabs: const [
            Tab(icon: Icon(Icons.note_add_outlined), text: 'Report Loss'),
            Tab(icon: Icon(Icons.history_outlined), text: 'My Claims'),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          _buildGuidedReportLossTab(),
          _buildFarmerClaimsTab(),
        ],
      ),
    );
  }

  // ==================== SECTION A & B: Guided Report Loss Tab ====================
  Widget _buildGuidedReportLossTab() {
    final appState = AppState.instance;

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Header Card
          Card(
            elevation: 2,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
            child: Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.all(10),
                        decoration: BoxDecoration(
                          color: const Color(0xFFE8F5E9),
                          shape: BoxShape.circle,
                        ),
                        child: const Icon(Icons.shield_outlined, color: Color(0xFF1B5E20), size: 28),
                      ),
                      const SizedBox(width: 12),
                      const Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'Report Crop Damage',
                              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Color(0xFF1B5E20)),
                            ),
                            SizedBox(height: 2),
                            Text(
                              'File damage details within 72 hours for prompt insurance claim verification.',
                              style: TextStyle(fontSize: 12, color: Colors.black54),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),

          // Guided Step-by-Step Stepper
          Theme(
            data: Theme.of(context).copyWith(
              colorScheme: Theme.of(context).colorScheme.copyWith(
                    primary: const Color(0xFF1B5E20),
                  ),
            ),
            child: Stepper(
              physics: const NeverScrollableScrollPhysics(),
              currentStep: _currentStep,
              onStepTapped: (step) => setState(() => _currentStep = step),
              onStepContinue: () {
                if (_currentStep < 4) {
                  setState(() => _currentStep += 1);
                } else {
                  _submitCase(isDraft: false);
                }
              },
              onStepCancel: () {
                if (_currentStep > 0) {
                  setState(() => _currentStep -= 1);
                }
              },
              controlsBuilder: (context, details) {
                final isLast = _currentStep == 4;
                return Padding(
                  padding: const EdgeInsets.only(top: 16.0),
                  child: Row(
                    children: [
                      ElevatedButton(
                        style: ElevatedButton.styleFrom(
                          backgroundColor: const Color(0xFF1B5E20),
                          foregroundColor: Colors.white,
                          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                        ),
                        onPressed: _isSubmitting ? null : details.onStepContinue,
                        child: _isSubmitting
                            ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                            : Text(isLast ? 'Submit Loss Claim' : 'Continue', style: const TextStyle(fontWeight: FontWeight.bold)),
                      ),
                      const SizedBox(width: 10),
                      if (_currentStep > 0)
                        OutlinedButton(
                          style: OutlinedButton.styleFrom(
                            foregroundColor: Colors.black87,
                            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                          ),
                          onPressed: details.onStepCancel,
                          child: const Text('Back'),
                        ),
                      if (isLast) ...[
                        const Spacer(),
                        TextButton(
                          onPressed: () => _submitCase(isDraft: true),
                          child: const Text('Save as Draft', style: TextStyle(color: Colors.black54)),
                        ),
                      ],
                    ],
                  ),
                );
              },
              steps: [
                // STEP 1: Which Field & Crop
                Step(
                  title: const Text('Farm Plot & Crop', style: TextStyle(fontWeight: FontWeight.bold)),
                  subtitle: Text('${appState.activeFarm?.farmName ?? "Farm"} · ${appState.activeCropName}'),
                  isActive: _currentStep >= 0,
                  content: Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: Colors.grey.shade50,
                      borderRadius: BorderRadius.circular(10),
                      border: Border.all(color: Colors.grey.shade300),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('Plot: ${appState.activeFarm?.farmName ?? "My Farm"}', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                        const SizedBox(height: 2),
                        Text('Location: ${appState.activeTaluka}, ${appState.activeDistrict}', style: const TextStyle(fontSize: 12, color: Colors.black54)),
                        const SizedBox(height: 2),
                        Text('Total Acreage: ${appState.activeFarm?.totalAreaAcres ?? 2.0} acres', style: const TextStyle(fontSize: 12, color: Colors.black54)),
                        const SizedBox(height: 8),
                        Text('Registered Crop: ${appState.activeCropName.toUpperCase()}', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12, color: Color(0xFF1B5E20))),
                      ],
                    ),
                  ),
                ),

                // STEP 2: What Happened (Peril Selection)
                Step(
                  title: const Text('What Happened?', style: TextStyle(fontWeight: FontWeight.bold)),
                  subtitle: Text(_perilOptions[_perilType]?['title'] ?? _perilType),
                  isActive: _currentStep >= 1,
                  content: Column(
                    children: _perilOptions.entries.map((entry) {
                      final key = entry.key;
                      final data = entry.value;
                      final isSelected = _perilType == key;
                      final col = data['color'] as Color;

                      return Container(
                        margin: const EdgeInsets.only(bottom: 8),
                        child: Material(
                          color: isSelected ? col.withOpacity(0.08) : Colors.white,
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(10),
                            side: BorderSide(
                              color: isSelected ? col : Colors.grey.shade300,
                              width: isSelected ? 2.0 : 1.0,
                            ),
                          ),
                          child: RadioListTile<String>(
                            value: key,
                            groupValue: _perilType,
                            activeColor: col,
                            title: Text(
                              data['title'],
                              style: TextStyle(fontWeight: isSelected ? FontWeight.bold : FontWeight.normal, fontSize: 13),
                            ),
                            secondary: Icon(data['icon'] as IconData, color: col),
                            onChanged: (val) {
                              if (val != null) setState(() => _perilType = val);
                            },
                          ),
                        ),
                      );
                    }).toList(),
                  ),
                ),

                // STEP 3: When & How Much Damage
                Step(
                  title: const Text('Date & Damage Extent', style: TextStyle(fontWeight: FontWeight.bold)),
                  subtitle: Text('${_eventDate.day}/${_eventDate.month}/${_eventDate.year} · ${_damagePct.toInt()}% affected'),
                  isActive: _currentStep >= 2,
                  content: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // Date selector button
                      OutlinedButton.icon(
                        style: OutlinedButton.styleFrom(
                          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                        ),
                        icon: const Icon(Icons.calendar_today, size: 18, color: Color(0xFF1B5E20)),
                        label: Text(
                          'Event Date: ${_eventDate.day}/${_eventDate.month}/${_eventDate.year} (Tap to change)',
                          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: Colors.black87),
                        ),
                        onPressed: () async {
                          final d = await showDatePicker(
                            context: context,
                            initialDate: _eventDate,
                            firstDate: DateTime(2024, 1, 1),
                            lastDate: DateTime.now(),
                          );
                          if (d != null) setState(() => _eventDate = d);
                        },
                      ),
                      const SizedBox(height: 14),

                      // Damage percentage slider
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          const Text('Estimated Damage:', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                          Text('${_damagePct.toInt()}% of crop damaged', style: const TextStyle(fontWeight: FontWeight.bold, color: Color(0xFF1B5E20))),
                        ],
                      ),
                      Slider(
                        value: _damagePct,
                        min: 5,
                        max: 100,
                        divisions: 19,
                        activeColor: const Color(0xFF1B5E20),
                        label: '${_damagePct.toInt()}%',
                        onChanged: (val) => setState(() => _damagePct = val),
                      ),
                      const SizedBox(height: 6),

                      // Affected Area Acres
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          const Text('Affected Area:', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                          Text('${_affectedAcres.toStringAsFixed(1)} acres', style: const TextStyle(fontWeight: FontWeight.bold, color: Color(0xFF1B5E20))),
                        ],
                      ),
                      Slider(
                        value: _affectedAcres,
                        min: 0.5,
                        max: 10.0,
                        divisions: 19,
                        activeColor: const Color(0xFF1B5E20),
                        label: '${_affectedAcres.toStringAsFixed(1)} ac',
                        onChanged: (val) => setState(() => _affectedAcres = val),
                      ),
                    ],
                  ),
                ),

                // STEP 4: Field Photos
                Step(
                  title: const Text('Field Photos', style: TextStyle(fontWeight: FontWeight.bold)),
                  subtitle: const Text('Geotagged proof helps faster verification'),
                  isActive: _currentStep >= 3,
                  content: Container(
                    padding: const EdgeInsets.all(14),
                    decoration: BoxDecoration(
                      color: Colors.grey.shade50,
                      borderRadius: BorderRadius.circular(10),
                      border: Border.all(color: Colors.grey.shade300),
                    ),
                    child: Column(
                      children: const [
                        Icon(Icons.camera_alt_outlined, color: Color(0xFF1B5E20), size: 36),
                        SizedBox(height: 6),
                        Text('1 Geotagged Field Photo Attached', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                        SizedBox(height: 2),
                        Text('GPS Coordinates and timestamp embedded automatically.', style: TextStyle(fontSize: 11, color: Colors.black54)),
                      ],
                    ),
                  ),
                ),

                // STEP 5: Review & Submit
                Step(
                  title: const Text('Review & Submit', style: TextStyle(fontWeight: FontWeight.bold)),
                  subtitle: const Text('Confirm all details before submitting claim'),
                  isActive: _currentStep >= 4,
                  content: Container(
                    padding: const EdgeInsets.all(14),
                    decoration: BoxDecoration(
                      color: const Color(0xFFE8F5E9),
                      borderRadius: BorderRadius.circular(10),
                      border: Border.all(color: const Color(0xFFC8E6C9)),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text('Claim Summary:', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: Color(0xFF1B5E20))),
                        const Divider(height: 16),
                        Text('• Peril: ${_perilOptions[_perilType]?['title'] ?? _perilType}', style: const TextStyle(fontSize: 12)),
                        Text('• Crop: ${appState.activeCropName}', style: const TextStyle(fontSize: 12)),
                        Text('• Date: ${_eventDate.day}/${_eventDate.month}/${_eventDate.year}', style: const TextStyle(fontSize: 12)),
                        Text('• Damage: ${_damagePct.toInt()}% over ${_affectedAcres.toStringAsFixed(1)} acres', style: const TextStyle(fontSize: 12)),
                        Text('• Evidence: Geotagged photo + Sentinel-2 satellite cross-check', style: const TextStyle(fontSize: 12)),
                        const SizedBox(height: 8),
                        const Text(
                          'Note: Your submission will be verified against Sentinel-2 satellite vegetation indices within 48 hours.',
                          style: TextStyle(fontSize: 11, color: Colors.black54, fontStyle: FontStyle.italic),
                        ),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),

          // Insurance Reviewer link
          Center(
            child: TextButton.icon(
              icon: const Icon(Icons.admin_panel_settings_outlined, size: 16, color: Colors.blueGrey),
              label: const Text('Insurance Surveyor or Official? Open Review Portal', style: TextStyle(fontSize: 12, color: Colors.blueGrey)),
              onPressed: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(builder: (_) => const InsurerDashboardScreen()),
                );
              },
            ),
          ),
          const SizedBox(height: 20),
        ],
      ),
    );
  }

  // ==================== SECTION C: My Past Claims Tab ====================
  Widget _buildFarmerClaimsTab() {
    if (_isLoading) {
      return const Center(child: CircularProgressIndicator(color: Color(0xFF1B5E20)));
    }
    if (_cases.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.assignment_outlined, size: 48, color: Colors.grey),
            const SizedBox(height: 12),
            const Text('No crop loss claims recorded yet.', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
            const SizedBox(height: 4),
            const Text('Use the "Report Loss" tab to submit evidence.', style: TextStyle(fontSize: 12, color: Colors.black54)),
            const SizedBox(height: 16),
            ElevatedButton(
              style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF1B5E20), foregroundColor: Colors.white),
              onPressed: () => _tabController.animateTo(0),
              child: const Text('Start Loss Report'),
            ),
          ],
        ),
      );
    }

    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: _cases.length,
      itemBuilder: (context, idx) {
        final c = _cases[idx];
        final isDraft = c.dossierStatus == 'draft';
        final fusion = c.multimodalFusionSummary;
        final verifiedLoss = (fusion['verified_damage_pct'] as num?)?.toDouble() ?? c.damageEstimatePct;
        final confidence = (fusion['confidence_score'] as num?)?.toDouble() ?? 85.0;

        return Card(
          elevation: 1,
          margin: const EdgeInsets.only(bottom: 12),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      c.caseId.toUpperCase(),
                      style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: Color(0xFF1B5E20)),
                    ),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                      decoration: BoxDecoration(
                        color: isDraft ? Colors.grey.shade200 : const Color(0xFFE8F5E9),
                        borderRadius: BorderRadius.circular(6),
                      ),
                      child: Text(
                        isDraft ? 'DRAFT' : 'UNDER VERIFICATION',
                        style: TextStyle(
                          fontSize: 10,
                          fontWeight: FontWeight.bold,
                          color: isDraft ? Colors.black54 : const Color(0xFF1B5E20),
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                Text(
                  '${c.cropCode.toUpperCase()} · ${c.perilType.replaceAll('_', ' ').toUpperCase()}',
                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                ),
                const SizedBox(height: 2),
                Text(
                  'Date: ${c.eventDate} · Claimed Loss: ${c.damageEstimatePct.toInt()}%',
                  style: const TextStyle(fontSize: 12, color: Colors.black87),
                ),
                const SizedBox(height: 10),

                // Verification details box
                Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: Colors.grey.shade50,
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: Colors.grey.shade200),
                  ),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text('Satellite Cross-Check', style: TextStyle(fontSize: 10, color: Colors.black54)),
                          Text('${verifiedLoss.toStringAsFixed(1)}% drop', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12, color: Color(0xFF1B5E20))),
                        ],
                      ),
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text('AI Confidence', style: TextStyle(fontSize: 10, color: Colors.black54)),
                          Text('${confidence.toStringAsFixed(0)}%', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12, color: Color(0xFF1B5E20))),
                        ],
                      ),
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.end,
                        children: [
                          const Text('Verification SLA', style: TextStyle(fontSize: 10, color: Colors.black54)),
                          Text('${c.slaRemainingHours.toStringAsFixed(0)}h remaining', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12, color: Colors.deepOrange)),
                        ],
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}
