import 'package:flutter/material.dart';
import '../models/farm_models.dart';
import '../services/api_service.dart';

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
    _loadCases();
  }

  Future<void> _loadCases() async {
    setState(() => _isLoading = true);
    final c = await ApiService.getFarmerLossCases('farmer_demo_01');
    if (mounted) {
      setState(() {
        _cases = c;
        _isLoading = false;
      });
    }
  }

  Future<void> _submitCase({required bool isDraft}) async {
    setState(() => _isSubmitting = true);
    final newCase = await ApiService.submitCropLossCase(
      farmerId: 'farmer_demo_01',
      farmId: 'farm_demo_pune_01',
      cropCode: _cropCode,
      eventDate: '${_eventDate.year}-${_eventDate.month.toString().padLeft(2, '0')}-${_eventDate.day.toString().padLeft(2, '0')}',
      perilType: _perilType,
      damageEstimatePct: _damagePct,
      affectedAreaAcres: _affectedAcres,
      photoUrls: ['/storage/photos/demo_damage_01.jpg'],
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
    return Scaffold(
      backgroundColor: const Color(0xFFF6F8F6),
      appBar: AppBar(
        title: const Text('PMFBY Crop Loss Evidence', style: TextStyle(fontWeight: FontWeight.bold)),
        backgroundColor: const Color(0xFF4527A0),
        foregroundColor: Colors.white,
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
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
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
                  const Text('Geotagged Field Photos', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                  const SizedBox(height: 8),
                  Container(
                    height: 90,
                    decoration: BoxDecoration(
                      color: const Color(0xFFEDE7F6),
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: const Color(0xFFB39DDB), style: BorderStyle.solid),
                    ),
                    child: const Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(Icons.camera_alt, color: Color(0xFF4527A0), size: 28),
                          SizedBox(height: 4),
                          Text('2 field photos attached (GPS Verified)', style: TextStyle(fontSize: 12, color: Color(0xFF4527A0), fontWeight: FontWeight.w600)),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 20),

          // Action Buttons
          if (_isSubmitting)
            const Center(child: CircularProgressIndicator(color: Color(0xFF4527A0)))
          else ...[
            ElevatedButton.icon(
              onPressed: () => _submitCase(isDraft: false),
              icon: const Icon(Icons.send),
              label: const Text('SUBMIT EVIDENCE DOSSIER FOR REVIEW', style: TextStyle(fontWeight: FontWeight.bold)),
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFF4527A0),
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(vertical: 14),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              ),
            ),
            const SizedBox(height: 8),
            OutlinedButton.icon(
              onPressed: () => _submitCase(isDraft: true),
              icon: const Icon(Icons.save_alt),
              label: const Text('SAVE AS OFFLINE DRAFT'),
              style: OutlinedButton.styleFrom(
                foregroundColor: Colors.black87,
                padding: const EdgeInsets.symmetric(vertical: 12),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              ),
            ),
          ],
          const SizedBox(height: 16),

          // Legal Disclaimer
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: Colors.grey.withOpacity(0.1),
              borderRadius: BorderRadius.circular(12),
            ),
            child: const Text(
              'Notice: This prototype prepares a verified evidence packet for formal human review. Strictly NOT an official automatic PMFBY claim approval or insurer submission without authorized integration.',
              style: TextStyle(fontSize: 12, color: Colors.black54, fontStyle: FontStyle.italic),
            ),
          ),
          const SizedBox(height: 24),
        ],
      ),
    );
  }

  Widget _buildHistoryTab() {
    if (_isLoading) {
      return const Center(child: CircularProgressIndicator(color: Color(0xFF4527A0)));
    }
    if (_cases.isEmpty) {
      return const Center(child: Text('No crop loss cases submitted yet.'));
    }

    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: _cases.length,
      itemBuilder: (context, idx) {
        final c = _cases[idx];
        Color statusColor = Colors.orange;
        String statusText = 'Under Review';
        if (c.dossierStatus == 'draft_saved') {
          statusColor = Colors.blueGrey;
          statusText = 'Draft Saved';
        } else if (c.dossierStatus == 'evidence_submitted') {
          statusColor = Colors.indigo;
          statusText = 'Evidence Submitted';
        } else if (c.dossierStatus == 'review_completed') {
          statusColor = Colors.green;
          statusText = 'Review Completed';
        }

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
                      'Case: ${c.caseId}',
                      style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                    ),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                      decoration: BoxDecoration(
                        color: statusColor.withOpacity(0.15),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Text(
                        statusText,
                        style: TextStyle(color: statusColor, fontWeight: FontWeight.bold, fontSize: 11),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                Text('Crop: ${c.cropCode.toUpperCase()} · Loss Event: ${c.perilType.replaceAll("_", " ").toUpperCase()}', style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13)),
                Text('Damage: ${c.damageEstimatePct.toInt()}% on ${c.affectedAreaAcres} acres (Date: ${c.eventDate})', style: const TextStyle(fontSize: 13, color: Colors.black87)),
                const Divider(height: 18),
                Text(
                  'Weather Anomaly: ${c.weatherEvidenceSummary['anomaly_classification'] ?? "Recorded locally"}',
                  style: const TextStyle(fontSize: 12, color: Color(0xFF1B5E20), fontWeight: FontWeight.w500),
                ),
                if (c.reviewerDecision != null) ...[
                  const SizedBox(height: 6),
                  Text('Reviewer Decision: ${c.reviewerDecision} (${c.reviewerRationale})', style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Colors.deepPurple)),
                ]
              ],
            ),
          ),
        );
      },
    );
  }
}
