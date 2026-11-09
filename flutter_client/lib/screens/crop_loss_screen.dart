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

  // Form State
  String _cropCode = 'soybean';
  String _perilType = 'unseasonal_rainfall';
  double _damagePct = 40.0;
  double _affectedAcres = 2.0;
  DateTime _eventDate = DateTime.now().subtract(const Duration(days: 2));
  bool _isSubmitting = false;

  final List<String> _perils = [
    'unseasonal_rainfall',
    'hailstorm',
    'dry_spell_drought',
    'post_harvest_cyclone',
    'inundation_waterlogging'
  ];

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    AppState.instance.addListener(_onStateChange);
    _cropCode = AppState.instance.activeCropCode;
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
        _tabController.animateTo(1); // switch to history tab
      });

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(isDraft ? 'Draft saved offline.' : 'Evidence dossier submitted for human review.'),
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
            const Text('PMFBY Crop Loss Evidence', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
            Text(
              '${appState.activeFarm?.farmName ?? "Farm"} · ${appState.activeTaluka}, ${appState.activeDistrict}',
              style: const TextStyle(fontSize: 12, color: Colors.white70),
            ),
          ],
        ),
        backgroundColor: const Color(0xFF4527A0),
        foregroundColor: Colors.white,
        actions: [
          IconButton(
            icon: const Icon(Icons.admin_panel_settings),
            tooltip: 'Open Insurer & Reviewer Queue',
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => const InsurerDashboardScreen()),
              );
            },
          ),
          IconButton(icon: const Icon(Icons.refresh), onPressed: _loadCases),
        ],
        bottom: TabBar(
          controller: _tabController,
          indicatorColor: Colors.white,
          labelColor: Colors.white,
          unselectedLabelColor: Colors.white70,
          tabs: const [
            Tab(icon: Icon(Icons.add_photo_alternate_outlined), text: 'New Evidence'),
            Tab(icon: Icon(Icons.folder_shared_outlined), text: 'Dossier Cases'),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          _buildFormTab(),
          _buildHistoryTab(),
        ],
      ),
    );
  }

  Widget _buildFormTab() {
    final appState = AppState.instance;

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Active Farm Indicator
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
            decoration: BoxDecoration(
              color: const Color(0xFFEDE7F6),
              borderRadius: BorderRadius.circular(10),
              border: Border.all(color: const Color(0xFFB39DDB)),
            ),
            child: Row(
              children: [
                const Icon(Icons.shield_outlined, size: 16, color: Color(0xFF4527A0)),
                const SizedBox(width: 6),
                Expanded(
                  child: Text(
                    'Filing for: ${appState.activeFarm?.farmName ?? "Active Farm"} (${appState.activeCropName}) in ${appState.activeDistrict}',
                    style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Color(0xFF4527A0)),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 14),

          const Text(
            'RECORD CROP LOSS INCIDENT',
            style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: Color(0xFF333333), letterSpacing: 0.8),
          ),
          const SizedBox(height: 12),

          // Peril Type Selector
          Card(
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Select Peril / Hazard Type', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                  const SizedBox(height: 8),
                  DropdownButtonFormField<String>(
                    value: _perilType,
                    decoration: const InputDecoration(border: OutlineInputBorder()),
                    items: _perils.map((p) {
                      return DropdownMenuItem(
                        value: p,
                        child: Text(p.replaceAll('_', ' ').toUpperCase(), style: const TextStyle(fontSize: 13)),
                      );
                    }).toList(),
                    onChanged: (val) {
                      if (val != null) setState(() => _perilType = val);
                    },
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 12),

          // Incident Date
          Card(
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
            child: ListTile(
              title: const Text('Date of Weather Event', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
              subtitle: Text('${_eventDate.day}/${_eventDate.month}/${_eventDate.year}'),
              trailing: const Icon(Icons.calendar_today, color: Color(0xFF4527A0)),
              onTap: () async {
                final d = await showDatePicker(
                  context: context,
                  initialDate: _eventDate,
                  firstDate: DateTime(2024, 1, 1),
                  lastDate: DateTime.now(),
                );
                if (d != null) setState(() => _eventDate = d);
              },
            ),
          ),
          const SizedBox(height: 12),

          // Damage Estimate Slider
          Card(
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text('Estimated Crop Damage:', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                      Text('${_damagePct.toInt()}%', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18, color: Color(0xFF4527A0))),
                    ],
                  ),
                  Slider(
                    value: _damagePct,
                    min: 5,
                    max: 100,
                    divisions: 19,
                    activeColor: const Color(0xFF4527A0),
                    onChanged: (val) => setState(() => _damagePct = val),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 12),

          // Photo Upload Mock Card
          Card(
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Field Photos (with GPS & Timestamp)', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                  const SizedBox(height: 8),
                  Container(
                    height: 100,
                    width: double.infinity,
                    decoration: BoxDecoration(
                      color: Colors.grey.shade100,
                      borderRadius: BorderRadius.circular(10),
                      border: Border.all(color: Colors.grey.shade300, style: BorderStyle.solid),
                    ),
                    child: Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: const [
                          Icon(Icons.camera_alt_outlined, color: Colors.black45, size: 32),
                          SizedBox(height: 6),
                          Text('1 geotagged photo attached (simulated)', style: TextStyle(fontSize: 12, color: Colors.black54)),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),

          // Action Buttons
          if (_isSubmitting)
            const Center(child: CircularProgressIndicator(color: Color(0xFF4527A0)))
          else ...[
            SizedBox(
              height: 50,
              child: ElevatedButton.icon(
                onPressed: () => _submitCase(isDraft: false),
                icon: const Icon(Icons.send_rounded),
                label: const Text('Submit Evidence Dossier for Review', style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold)),
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF4527A0),
                  foregroundColor: Colors.white,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                ),
              ),
            ),
            const SizedBox(height: 10),
            OutlinedButton(
              onPressed: () => _submitCase(isDraft: true),
              style: OutlinedButton.styleFrom(
                foregroundColor: Colors.black87,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              ),
              child: const Text('Save Offline Draft'),
            ),
          ],
          const SizedBox(height: 16),

          // Mandatory PMFBY Disclaimers
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: Colors.amber.withOpacity(0.12),
              borderRadius: BorderRadius.circular(10),
              border: Border.all(color: Colors.amber.shade400),
            ),
            child: const Text(
              'Statutory PMFBY Notice: Rashkar is a decision-support and evidence gathering platform. Submission here compiles an evidentiary dossier under PMFBY Clause 11/12 guidelines. It does NOT constitute final official claim settlement, which is governed exclusively by designated insurance companies and government authorities.',
              style: TextStyle(fontSize: 11, color: Color(0xFF5D4037)),
            ),
          ),
          const SizedBox(height: 20),
        ],
      ),
    );
  }

  Widget _buildHistoryTab() {
    if (_isLoading) {
      return const Center(child: CircularProgressIndicator(color: Color(0xFF4527A0)));
    }
    if (_cases.isEmpty) {
      return const Center(
        child: Text('No loss cases recorded yet. Use the New Evidence tab to start.'),
      );
    }

    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: _cases.length,
      itemBuilder: (context, idx) {
        final c = _cases[idx];
        final isDraft = c.dossierStatus == 'draft';
        final eventDt = DateTime.tryParse(c.eventDate) ?? DateTime.now();
        final hoursSince = DateTime.now().difference(eventDt).inHours;
        final within72 = hoursSince <= 72;

        final fusion = c.multimodalFusionSummary;
        final sat = c.satelliteEvidenceSummary;
        final vis = c.visionEvidenceSummary;
        final verifiedLoss = (fusion['verified_damage_pct'] as num?)?.toDouble() ?? c.damageEstimatePct;
        final confidence = (fusion['confidence_score'] as num?)?.toDouble() ?? 85.0;

        return Card(
          elevation: 2,
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
                      style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: Color(0xFF4527A0)),
                    ),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                      decoration: BoxDecoration(
                        color: isDraft ? Colors.grey.shade200 : const Color(0xFFEDE7F6),
                        borderRadius: BorderRadius.circular(6),
                      ),
                      child: Text(
                        isDraft ? 'OFFLINE DRAFT' : c.dossierStatus.toUpperCase(),
                        style: TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.bold,
                          color: isDraft ? Colors.black54 : const Color(0xFF4527A0),
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                Text(
                  'Peril: ${c.perilType.replaceAll('_', ' ').toUpperCase()} · ${c.cropCode.toUpperCase()}',
                  style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13),
                ),
                Text(
                  'Reported Event Date: ${c.eventDate} · Claimed Damage: ${c.damageEstimatePct.toInt()}%',
                  style: const TextStyle(fontSize: 13, color: Colors.black87),
                ),
                const SizedBox(height: 8),

                // AI Multimodal Verification Box
                Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: Colors.blue.shade50,
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: Colors.blue.shade200),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text(
                            'AI Verified Loss: ${verifiedLoss.toStringAsFixed(1)}%',
                            style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: Colors.blue.shade900),
                          ),
                          Text(
                            'Confidence: ${confidence.toStringAsFixed(1)}%',
                            style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12, color: Colors.green.shade900),
                          ),
                        ],
                      ),
                      const SizedBox(height: 4),
                      Text(
                        'Sentinel-2 NDVI Drop: ${sat['vegetation_loss_pct'] ?? 45.4}% · Vision AI: ${vis['primary_damage_type'] ?? "Canopy damage"}',
                        style: const TextStyle(fontSize: 11, color: Colors.black87),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        'Target Turnaround: 24-48 Hours (SLA: ${c.slaRemainingHours.toStringAsFixed(1)}h remaining)',
                        style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: Colors.indigo.shade800),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 8),

                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      '72h Window Status: ${hoursSince}h elapsed (${within72 ? "Compliant" : "Exceeds 72h"})',
                      style: TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.bold,
                        color: within72 ? Colors.green.shade800 : Colors.red.shade800,
                      ),
                    ),
                    TextButton.icon(
                      onPressed: () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(builder: (_) => const InsurerDashboardScreen()),
                        );
                      },
                      icon: const Icon(Icons.arrow_forward, size: 14),
                      label: const Text('View Insurer Queue', style: TextStyle(fontSize: 11)),
                    ),
                  ],
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}
