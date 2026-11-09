import 'package:flutter/material.dart';
import '../models/farm_models.dart';
import '../services/api_service.dart';

class InsurerDashboardScreen extends StatefulWidget {
  const InsurerDashboardScreen({Key? key}) : super(key: key);

  @override
  State<InsurerDashboardScreen> createState() => _InsurerDashboardScreenState();
}

class _InsurerDashboardScreenState extends State<InsurerDashboardScreen> {
  List<CropLossCase> _queue = [];
  bool _isLoading = true;
  String? _selectedCaseId;
  
  // Reviewer Form Inputs
  String _reviewerId = 'rev_officer_pune_01';
  String _decision = 'verified_loss';
  final TextEditingController _rationaleController = TextEditingController(
    text: 'Multimodal convergence verified: Sentinel-2 NDVI drop correlates with field photos and IMD rainfall anomaly.',
  );
  bool _isSubmittingReview = false;

  final List<Map<String, String>> _decisionOptions = [
    {'value': 'verified_loss', 'label': 'Approve Verified Loss (Fast-Track)'},
    {'value': 'partially_verified', 'label': 'Partially Verified (Adjust Loss %)'},
    {'value': 'information_required', 'label': 'Request Additional Field Re-visit'},
    {'value': 'rejected', 'label': 'Reject Claim (Unsubstantiated / Inconsistent)'},
  ];

  @override
  void initState() {
    super.initState();
    _loadQueue();
  }

  Future<void> _loadQueue() async {
    setState(() => _isLoading = true);
    final queue = await ApiService.getReviewerQueue();
    setState(() {
      _queue = queue;
      _isLoading = false;
      if (_queue.isNotEmpty && _selectedCaseId == null) {
        _selectedCaseId = _queue.first.caseId;
      }
    });
  }

  Future<void> _submitDecision(CropLossCase c) async {
    setState(() => _isSubmittingReview = true);
    final res = await ApiService.submitReviewDecision(
      caseId: c.caseId,
      reviewerId: _reviewerId,
      decision: _decision,
      rationale: _rationaleController.text,
      compensationBasis: 'PMFBY Mid-Season Adversity / Localized Calamity (Clause 21.2)',
    );
    setState(() => _isSubmittingReview = false);

    if (!mounted) return;
    if (res != null) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Claim ${c.caseId} review recorded successfully: $_decision'),
          backgroundColor: Colors.green,
        ),
      );
      _loadQueue();
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Failed to submit reviewer decision. Please check backend connection.'),
          backgroundColor: Colors.red,
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final selectedCase = _queue.cast<CropLossCase?>().firstWhere(
      (c) => c?.caseId == _selectedCaseId,
      orElse: () => _queue.isNotEmpty ? _queue.first : null,
    );

    return Scaffold(
      appBar: AppBar(
        title: const Text('PMFBY Insurer & Reviewer Dashboard'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            tooltip: 'Refresh Queue',
            onPressed: _loadQueue,
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _queue.isEmpty
              ? _buildEmptyState()
              : LayoutBuilder(
                  builder: (context, constraints) {
                    final isWide = constraints.maxWidth > 900;
                    if (isWide) {
                      return Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          SizedBox(
                            width: 380,
                            child: _buildQueueList(),
                          ),
                          const VerticalDivider(width: 1),
                          Expanded(
                            child: selectedCase == null
                                ? const Center(child: Text('Select a claim to review'))
                                : _buildCaseDetail(selectedCase),
                          ),
                        ],
                      );
                    } else {
                      return ListView(
                        padding: const EdgeInsets.all(12),
                        children: [
                          _buildQueueList(),
                          const SizedBox(height: 16),
                          if (selectedCase != null) _buildCaseDetail(selectedCase),
                        ],
                      );
                    }
                  },
                ),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.check_circle_outline, size: 64, color: Colors.green),
            const SizedBox(height: 16),
            const Text(
              'Review Queue Clear',
              style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            const Text(
              'All submitted PMFBY crop loss evidence packets have been reviewed within the 48-hour SLA.',
              textAlign: TextAlign.center,
              style: TextStyle(color: Colors.grey),
            ),
            const SizedBox(height: 20),
            ElevatedButton.icon(
              onPressed: _loadQueue,
              icon: const Icon(Icons.refresh),
              label: const Text('Check for New Claims'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildQueueList() {
    return Card(
      margin: const EdgeInsets.all(8),
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(color: Colors.grey.shade300),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: Colors.blueGrey.shade50,
              borderRadius: const BorderRadius.vertical(top: Radius.circular(12)),
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text(
                  'Pending Claims Queue',
                  style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                  decoration: BoxDecoration(
                    color: Colors.blue.shade100,
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text(
                    '${_queue.length} Active',
                    style: TextStyle(
                      color: Colors.blue.shade900,
                      fontWeight: FontWeight.bold,
                      fontSize: 12,
                    ),
                  ),
                ),
              ],
            ),
          ),
          const Divider(height: 1),
          Expanded(
            child: ListView.separated(
              itemCount: _queue.length,
              separatorBuilder: (_, __) => const Divider(height: 1),
              itemBuilder: (context, index) {
                final c = _queue[index];
                final isSelected = c.caseId == _selectedCaseId;
                final fusion = c.multimodalFusionSummary;
                final verifiedLoss = (fusion['verified_damage_pct'] as num?)?.toDouble() ?? c.damageEstimatePct;
                final confidence = (fusion['confidence_score'] as num?)?.toDouble() ?? 85.0;

                return ListTile(
                  selected: isSelected,
                  selectedTileColor: Colors.blue.shade50,
                  title: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        c.caseId.toUpperCase(),
                        style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
                      ),
                      _buildSlaBadge(c.slaRemainingHours, c.slaStatus),
                    ],
                  ),
                  subtitle: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const SizedBox(height: 4),
                      Text('${c.cropCode.toUpperCase()} • ${c.perilType.replaceAll('_', ' ')}'),
                      const SizedBox(height: 2),
                      Row(
                        children: [
                          Text('Claimed: ${c.damageEstimatePct.toStringAsFixed(0)}%'),
                          const Text(' → '),
                          Text(
                            'AI Verified: ${verifiedLoss.toStringAsFixed(0)}%',
                            style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.blue),
                          ),
                        ],
                      ),
                      const SizedBox(height: 2),
                      Text(
                        'Confidence: ${confidence.toStringAsFixed(1)}%',
                        style: TextStyle(fontSize: 11, color: Colors.green.shade800),
                      ),
                    ],
                  ),
                  onTap: () {
                    setState(() {
                      _selectedCaseId = c.caseId;
                    });
                  },
                );
              },
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSlaBadge(double remainingHours, String status) {
    Color bg = Colors.green.shade100;
    Color fg = Colors.green.shade900;
    String label = '${remainingHours.toStringAsFixed(1)}h SLA';

    if (status == 'sla_breached' || remainingHours <= 0) {
      bg = Colors.red.shade100;
      fg = Colors.red.shade900;
      label = 'SLA Breached';
    } else if (status == 'sla_critical' || remainingHours < 12) {
      bg = Colors.orange.shade100;
      fg = Colors.orange.shade900;
      label = '${remainingHours.toStringAsFixed(1)}h Urgent';
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(6),
      ),
      child: Text(
        label,
        style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: fg),
      ),
    );
  }

  Widget _buildCaseDetail(CropLossCase c) {
    final sat = c.satelliteEvidenceSummary;
    final vis = c.visionEvidenceSummary;
    final fusion = c.multimodalFusionSummary;
    final wx = c.weatherEvidenceSummary;

    final verifiedLoss = (fusion['verified_damage_pct'] as num?)?.toDouble() ?? c.damageEstimatePct;
    final confidence = (fusion['confidence_score'] as num?)?.toDouble() ?? 85.0;
    final routing = fusion['routing_channel'] ?? 'Human Reviewer Queue (Target 48h SLA)';
    final fusionRationale = fusion['fusion_rationale'] ?? '';

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Banner
          Card(
            color: Colors.blue.shade50,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Row(
                children: [
                  const Icon(Icons.verified_user, color: Colors.blue, size: 36),
                  const SizedBox(width: 16),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Text(
                              'Claim ${c.caseId}',
                              style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                            ),
                            const SizedBox(width: 8),
                            _buildSlaBadge(c.slaRemainingHours, c.slaStatus),
                          ],
                        ),
                        const SizedBox(height: 4),
                        Text(
                          'Farmer: ${c.farmerId} • Farm: ${c.farmId} • Event Date: ${c.eventDate}',
                          style: TextStyle(color: Colors.grey.shade800, fontSize: 13),
                        ),
                        const SizedBox(height: 2),
                        Text(
                          'Target SLA: 48 Hours (Eliminating 45-day manual CCE bottleneck)',
                          style: TextStyle(color: Colors.blue.shade900, fontWeight: FontWeight.bold, fontSize: 12),
                        ),
                        if (fusionRationale.isNotEmpty) ...[
                          const SizedBox(height: 4),
                          Text(
                            fusionRationale,
                            style: TextStyle(color: Colors.blue.shade900, fontSize: 11, fontStyle: FontStyle.italic),
                          ),
                        ],
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),

          // Key Multimodal Metrics Grid
          Row(
            children: [
              Expanded(
                child: _buildMetricTile(
                  'Claimed Loss',
                  '${c.damageEstimatePct.toStringAsFixed(0)}%',
                  '${c.affectedAreaAcres} Acres',
                  Colors.amber.shade800,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: _buildMetricTile(
                  'AI Verified Loss',
                  '${verifiedLoss.toStringAsFixed(1)}%',
                  'Multimodal Weighted',
                  Colors.blue.shade800,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: _buildMetricTile(
                  'Confidence Score',
                  '${confidence.toStringAsFixed(1)}%',
                  routing,
                  Colors.green.shade800,
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),

          // Section 1: Satellite Evidence
          _buildEvidenceSection(
            title: '1. Sentinel-2 Satellite Multi-Spectral Evidence',
            icon: Icons.satellite_alt,
            color: Colors.indigo,
            children: [
              Text(
                'Platform: ${sat['satellite_platform'] ?? 'Sentinel-2 MSI Level-2A (ESA Copernicus)'} (10m Resolution)',
                style: const TextStyle(fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 8),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceAround,
                children: [
                  _buildIndexCard('Pre-Event NDVI', '${sat['pre_event_indices']?['ndvi'] ?? 0.73}'),
                  _buildIndexCard('Post-Event NDVI', '${sat['post_event_indices']?['ndvi'] ?? 0.40}'),
                  _buildIndexCard('Delta NDVI', '${sat['delta_ndvi'] ?? -0.33}', isNegative: true),
                  _buildIndexCard('NDVI Loss', '${sat['vegetation_loss_pct'] ?? 45.4}%'),
                ],
              ),
              const SizedBox(height: 8),
              Text(
                'Signature: ${sat['damage_signature'] ?? 'Canopy waterlogging and subversion'} • Cloud Cover: ${sat['cloud_cover_pct'] ?? 4.2}%',
                style: const TextStyle(fontSize: 12, color: Colors.black87),
              ),
            ],
          ),
          const SizedBox(height: 16),

          // Section 2: Computer Vision (YOLOv8 + U-Net + ViT)
          _buildEvidenceSection(
            title: '2. Vision AI Field Photo Analysis (YOLOv8 + U-Net + ViT)',
            icon: Icons.camera_alt,
            color: Colors.purple,
            children: [
              Text(
                'Primary Detected Pattern: ${vis['primary_damage_type'] ?? 'Crop Lodging & Shatter'}',
                style: const TextStyle(fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 6),
              Text(
                'U-Net Segmentation: Damaged Area ${vis['unet_segmentation']?['damaged_polygon_area_pct'] ?? verifiedLoss}% • Intact Area ${vis['unet_segmentation']?['intact_canopy_area_pct'] ?? (100 - verifiedLoss)}%',
                style: const TextStyle(fontSize: 12),
              ),
              const SizedBox(height: 4),
              Text(
                'ViT Fine-tuned Feature Embeddings: Structural Similarity Drop vs Baseline: ${vis['vit_feature_extraction']?['structural_similarity_index'] ?? 0.41}',
                style: const TextStyle(fontSize: 12, color: Colors.black87),
              ),
              const SizedBox(height: 8),
              if (c.photoUrls.isNotEmpty)
                Wrap(
                  spacing: 8,
                  children: c.photoUrls.map((p) => Chip(
                    avatar: const Icon(Icons.image, size: 16),
                    label: Text(p.split('/').last, style: const TextStyle(fontSize: 11)),
                  )).toList(),
                ),
            ],
          ),
          const SizedBox(height: 16),

          // Section 3: Weather Anomaly
          _buildEvidenceSection(
            title: '3. IMD & AgERA5 Gridded Weather Hazard Verification',
            icon: Icons.thunderstorm,
            color: Colors.teal,
            children: [
              Text(
                'Source: ${wx['source'] ?? 'IMD Pune Gridded Rainfall (0.25 deg) & AgERA5'}',
                style: const TextStyle(fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 4),
              Text(
                'Recorded Rainfall: ${wx['recorded_rainfall_event_mm'] ?? 68.4} mm (Historical Mean: ${wx['historical_mean_daily_rainfall_mm'] ?? 8.2} mm)',
                style: const TextStyle(fontSize: 13),
              ),
              Text(
                'Classification: ${wx['anomaly_classification'] ?? 'Severe excess cloudburst event'}',
                style: TextStyle(fontSize: 12, color: Colors.teal.shade900, fontWeight: FontWeight.bold),
              ),
            ],
          ),
          const SizedBox(height: 16),

          // Section 4: Assessor Review Action Card
          Card(
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(12),
              side: BorderSide(color: Colors.blue.shade300, width: 1.5),
            ),
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      const Icon(Icons.rate_review, color: Colors.blue),
                      const SizedBox(width: 8),
                      const Text(
                        'Assessor / Insurer Review Action',
                        style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                      ),
                    ],
                  ),
                  const Divider(height: 20),
                  DropdownButtonFormField<String>(
                    value: _decision,
                    decoration: const InputDecoration(
                      labelText: 'Reviewer Decision',
                      border: OutlineInputBorder(),
                    ),
                    items: _decisionOptions.map((opt) {
                      return DropdownMenuItem(
                        value: opt['value'],
                        child: Text(opt['label']!),
                      );
                    }).toList(),
                    onChanged: (val) {
                      if (val != null) setState(() => _decision = val);
                    },
                  ),
                  const SizedBox(height: 12),
                  TextField(
                    controller: _rationaleController,
                    maxLines: 3,
                    decoration: const InputDecoration(
                      labelText: 'Formal Review Rationale & Findings',
                      border: OutlineInputBorder(),
                    ),
                  ),
                  const SizedBox(height: 16),
                  SizedBox(
                    width: double.infinity,
                    height: 44,
                    child: ElevatedButton.icon(
                      onPressed: _isSubmittingReview ? null : () => _submitDecision(c),
                      icon: _isSubmittingReview
                          ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2))
                          : const Icon(Icons.check),
                      label: Text(_isSubmittingReview ? 'Submitting Review...' : 'Record Binding Review Decision'),
                      style: ElevatedButton.styleFrom(backgroundColor: Colors.blue.shade800, foregroundColor: Colors.white),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMetricTile(String label, String value, String sub, Color color) {
    return Card(
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(10),
        side: BorderSide(color: Colors.grey.shade300),
      ),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(label, style: const TextStyle(fontSize: 12, color: Colors.grey)),
            const SizedBox(height: 4),
            Text(
              value,
              style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: color),
            ),
            const SizedBox(height: 2),
            Text(sub, style: const TextStyle(fontSize: 11, color: Colors.black54)),
          ],
        ),
      ),
    );
  }

  Widget _buildEvidenceSection({
    required String title,
    required IconData icon,
    required Color color,
    required List<Widget> children,
  }) {
    return Card(
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(color: Colors.grey.shade300),
      ),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(icon, color: color, size: 20),
                const SizedBox(width: 8),
                Text(
                  title,
                  style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: color),
                ),
              ],
            ),
            const Divider(height: 16),
            ...children,
          ],
        ),
      ),
    );
  }

  Widget _buildIndexCard(String label, String value, {bool isNegative = false}) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
      decoration: BoxDecoration(
        color: Colors.grey.shade100,
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        children: [
          Text(label, style: const TextStyle(fontSize: 10, color: Colors.black54)),
          const SizedBox(height: 2),
          Text(
            value,
            style: TextStyle(
              fontSize: 14,
              fontWeight: FontWeight.bold,
              color: isNegative ? Colors.red.shade700 : Colors.indigo.shade900,
            ),
          ),
        ],
      ),
    );
  }
}
