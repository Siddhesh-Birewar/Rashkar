import 'package:flutter/material.dart';
import '../models/farm_models.dart';
import '../services/api_service.dart';
import '../services/app_state.dart';
import 'farm_registration_screen.dart';
import 'edit_profile_screen.dart';

class MyCropScreen extends StatefulWidget {
  const MyCropScreen({Key? key}) : super(key: key);

  @override
  State<MyCropScreen> createState() => _MyCropScreenState();
}

class _MyCropScreenState extends State<MyCropScreen> {
  YieldAssessment? _assessment;
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    AppState.instance.addListener(_onStateChange);
    _loadAssessment();
  }

  @override
  void dispose() {
    AppState.instance.removeListener(_onStateChange);
    super.dispose();
  }

  void _onStateChange() {
    _loadAssessment();
  }

  Future<void> _loadAssessment() async {
    final farmId = AppState.instance.activeFarmId;
    if (farmId == null) {
      if (mounted) {
        setState(() {
          _assessment = null;
          _isLoading = false;
        });
      }
      return;
    }

    setState(() => _isLoading = true);
    final a = await ApiService.getYieldAssessment(farmId: farmId);
    if (mounted) {
      setState(() {
        _assessment = a;
        _isLoading = false;
      });
    }
  }

  String _determineOverallCondition() {
    if (_assessment == null) return 'Not enough information';
    final risks = _assessment!.risks;
    if (risks.isEmpty) return 'Looking good';

    final hasCritical = risks.any((r) => r.riskLevel.toLowerCase() == 'critical');
    final hasHigh = risks.any((r) => r.riskLevel.toLowerCase() == 'high');
    final hasModerate = risks.any((r) => r.riskLevel.toLowerCase() == 'moderate');

    if (hasCritical || hasHigh) return 'High concern';
    if (hasModerate) return 'Needs attention';
    return 'Looking good';
  }

  Color _getConditionColor(String condition) {
    switch (condition) {
      case 'Looking good':
        return const Color(0xFF2E7D32);
      case 'Needs attention':
        return const Color(0xFFE65100);
      case 'High concern':
        return const Color(0xFFC62828);
      default:
        return Colors.grey.shade700;
    }
  }

  IconData _getConditionIcon(String condition) {
    switch (condition) {
      case 'Looking good':
        return Icons.check_circle_outline;
      case 'Needs attention':
        return Icons.info_outline;
      case 'High concern':
        return Icons.warning_amber_rounded;
      default:
        return Icons.help_outline;
    }
  }

  @override
  Widget build(BuildContext context) {
    final appState = AppState.instance;
    final hasFarm = appState.hasActiveFarm;

    return Scaffold(
      backgroundColor: const Color(0xFFF6F8F6),
      appBar: AppBar(
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('My Crop', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 20)),
            Text(
              hasFarm ? '${appState.activeCropName} · ${appState.activeTaluka}, ${appState.activeDistrict}' : 'Maharashtra',
              style: const TextStyle(fontSize: 12, color: Colors.white70),
            ),
          ],
        ),
        backgroundColor: const Color(0xFF1B5E20),
        foregroundColor: Colors.white,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            tooltip: 'Refresh Assessment',
            onPressed: _loadAssessment,
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator(color: Color(0xFF1B5E20)))
          : !hasFarm
              ? _buildEmptyState()
              : _assessment == null
                  ? const Center(child: Text('Unable to load crop assessment.'))
                  : SingleChildScrollView(
                      padding: const EdgeInsets.all(16.0),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          // A. My Crop Card
                          _buildCropSummaryCard(),
                          const SizedBox(height: 16),

                          // B. Crop Condition Card
                          _buildConditionCard(),
                          const SizedBox(height: 16),

                          // C. Main Concerns
                          _buildMainConcernsCard(),
                          const SizedBox(height: 16),

                          // D. What Should I Do? (Actionable Steps)
                          _buildRecommendationsCard(),
                          const SizedBox(height: 16),

                          // E. Past District Crop Performance
                          _buildPastPerformanceCard(),
                          const SizedBox(height: 16),

                          // F. Progressive Disclosure: Technical & Scientific Details
                          _buildTechnicalDetailsExpansion(),
                          const SizedBox(height: 24),
                        ],
                      ),
                    ),
    );
  }

  // ==================== SECTION A: Crop Summary ====================
  Widget _buildCropSummaryCard() {
    final a = _assessment!;
    final appState = AppState.instance;

    return Card(
      elevation: 1,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Padding(
        padding: const EdgeInsets.all(18.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.eco, color: Color(0xFF2E7D32), size: 28),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        a.cropName,
                        style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: Color(0xFF1B5E20)),
                      ),
                      Text(
                        '${a.totalAreaAcres} acres · ${a.irrigationType.toUpperCase()} irrigation',
                        style: const TextStyle(fontSize: 14, color: Colors.black54),
                      ),
                    ],
                  ),
                ),
                OutlinedButton.icon(
                  onPressed: () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(builder: (_) => EditProfileScreen(farm: appState.activeFarm)),
                    ).then((_) => _loadAssessment());
                  },
                  icon: const Icon(Icons.edit, size: 14),
                  label: const Text('Change'),
                  style: OutlinedButton.styleFrom(
                    foregroundColor: const Color(0xFF1B5E20),
                    side: const BorderSide(color: Color(0xFF1B5E20)),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                  ),
                ),
              ],
            ),
            const Divider(height: 24),
            Row(
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text('Sowing Date', style: TextStyle(fontSize: 12, color: Colors.black54)),
                      const SizedBox(height: 3),
                      Text(
                        a.sowingDate.isNotEmpty ? a.sowingDate : 'Kharif',
                        style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w600),
                      ),
                    ],
                  ),
                ),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text('Growth Stage', style: TextStyle(fontSize: 12, color: Colors.black54)),
                      const SizedBox(height: 3),
                      Row(
                        children: [
                          Flexible(
                            child: Text(
                              'Day ${a.daysAfterSowing}',
                              style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w600),
                              overflow: TextOverflow.ellipsis,
                            ),
                          ),
                          const SizedBox(width: 6),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                            decoration: BoxDecoration(
                              color: const Color(0xFFE8F5E9),
                              borderRadius: BorderRadius.circular(6),
                            ),
                            child: const Text(
                              'Tracked',
                              style: TextStyle(fontSize: 10, color: Color(0xFF1B5E20), fontWeight: FontWeight.bold),
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  // ==================== SECTION B: Crop Condition ====================
  Widget _buildConditionCard() {
    final condition = _determineOverallCondition();
    final col = _getConditionColor(condition);
    final icon = _getConditionIcon(condition);

    String message = 'Your crop is progressing normally under current conditions.';
    if (condition == 'Needs attention') {
      message = 'Your crop has mild weather or soil stresses. Review the recommendations below.';
    } else if (condition == 'High concern') {
      message = 'Significant heat or moisture stress detected for this crop growth stage.';
    }

    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Container(
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: col.withValues(alpha: 0.3), width: 1.5),
        ),
        padding: const EdgeInsets.all(18),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            CircleAvatar(
              radius: 24,
              backgroundColor: col.withValues(alpha: 0.12),
              child: Icon(icon, color: col, size: 28),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Crop Condition', style: TextStyle(fontSize: 13, color: Colors.black54)),
                  const SizedBox(height: 2),
                  Text(
                    condition,
                    style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: col),
                  ),
                  const SizedBox(height: 6),
                  Text(
                    message,
                    style: const TextStyle(fontSize: 14, color: Colors.black87, height: 1.3),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  // ==================== SECTION C: Main Concerns ====================
  Widget _buildMainConcernsCard() {
    final risks = _assessment!.risks;
    final notableRisks = risks.where((r) => r.riskLevel.toLowerCase() != 'low').toList();

    return Card(
      elevation: 1,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Padding(
        padding: const EdgeInsets.all(18.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'MAIN CONCERNS',
              style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: Color(0xFF1B5E20), letterSpacing: 0.8),
            ),
            const SizedBox(height: 12),
            if (notableRisks.isEmpty)
              Row(
                children: const [
                  Icon(Icons.check_circle, color: Color(0xFF2E7D32), size: 20),
                  SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      'No severe weather, water, or soil constraints detected for today.',
                      style: TextStyle(fontSize: 14, color: Colors.black87),
                    ),
                  ),
                ],
              )
            else
              ...notableRisks.take(3).map((r) {
                final isUrgent = r.riskLevel.toLowerCase() == 'high' || r.riskLevel.toLowerCase() == 'critical';
                final col = isUrgent ? const Color(0xFFC62828) : const Color(0xFFE65100);

                String friendlyTitle = r.riskDimension.replaceAll('_', ' ');
                if (friendlyTitle.contains('dry spell')) friendlyTitle = 'Rainfall Deficit / Dry Spell';
                if (friendlyTitle.contains('excess')) friendlyTitle = 'Excess Rainfall / Standing Water';
                if (friendlyTitle.contains('soil')) friendlyTitle = 'Soil Moisture Constraint';
                if (friendlyTitle.contains('heat')) friendlyTitle = 'Canopy Heat Stress';
                if (friendlyTitle.contains('pest')) friendlyTitle = 'Pest & Disease Advisory';

                return Padding(
                  padding: const EdgeInsets.only(bottom: 10.0),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Icon(isUrgent ? Icons.error_outline : Icons.info_outline, color: col, size: 20),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              friendlyTitle,
                              style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold, color: col),
                            ),
                            const SizedBox(height: 2),
                            Text(
                              r.drivers.isNotEmpty ? r.drivers.first : 'Risk factor identified for current crop stage.',
                              style: const TextStyle(fontSize: 13, color: Colors.black87),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                );
              }).toList(),
          ],
        ),
      ),
    );
  }

  // ==================== SECTION D: What Should I Do? ====================
  Widget _buildRecommendationsCard() {
    final recs = _assessment!.recommendations;

    return Card(
      elevation: 1,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Padding(
        padding: const EdgeInsets.all(18.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'WHAT SHOULD I DO?',
              style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: Color(0xFF1B5E20), letterSpacing: 0.8),
            ),
            const SizedBox(height: 12),
            if (recs.isEmpty)
              const Text('No immediate interventions required. Continue routine crop monitoring.')
            else
              ...recs.take(3).map((rec) {
                return Container(
                  margin: const EdgeInsets.only(bottom: 12),
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(
                    color: const Color(0xFFF1F8E9),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: const Color(0xFFC8E6C9)),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Icon(Icons.arrow_circle_right_outlined, color: Color(0xFF1B5E20), size: 22),
                          const SizedBox(width: 10),
                          Expanded(
                            child: Text(
                              rec.title,
                              style: const TextStyle(fontSize: 15, fontWeight: FontWeight.bold, color: Color(0xFF1B5E20)),
                            ),
                          ),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                            decoration: BoxDecoration(
                              color: rec.urgency.toLowerCase() == 'urgent' ? Colors.red.shade100 : Colors.green.shade100,
                              borderRadius: BorderRadius.circular(8),
                            ),
                            child: Text(
                              rec.urgency.toUpperCase(),
                              style: TextStyle(
                                fontSize: 10,
                                fontWeight: FontWeight.bold,
                                color: rec.urgency.toLowerCase() == 'urgent' ? Colors.red.shade800 : Colors.green.shade900,
                              ),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 6),
                      Text(
                        rec.description,
                        style: const TextStyle(fontSize: 13, color: Colors.black87, height: 1.3),
                      ),
                      if (rec.whyRecommended.isNotEmpty) ...[
                        const SizedBox(height: 6),
                        ExpansionTile(
                          tilePadding: EdgeInsets.zero,
                          childrenPadding: EdgeInsets.zero,
                          title: const Text('Why this action?', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Color(0xFF2E7D32))),
                          children: [
                            Padding(
                              padding: const EdgeInsets.only(top: 4.0, bottom: 6.0),
                              child: Text(
                                rec.whyRecommended,
                                style: const TextStyle(fontSize: 12, color: Colors.black87, fontStyle: FontStyle.italic),
                              ),
                            ),
                          ],
                        ),
                      ],
                    ],
                  ),
                );
              }).toList(),
          ],
        ),
      ),
    );
  }

  // ==================== SECTION E: Past Crop Performance ====================
  Widget _buildPastPerformanceCard() {
    final b = _assessment!.baseline;
    final appState = AppState.instance;

    final mean = b['historical_mean_t_ha'] != null ? '${b['historical_mean_t_ha']} t/ha' : '1.48 t/ha';
    final district = appState.activeDistrict.isNotEmpty ? appState.activeDistrict : 'Pune';

    return Card(
      elevation: 1,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Padding(
        padding: const EdgeInsets.all(18.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'PAST CROP PERFORMANCE IN YOUR DISTRICT',
              style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: Color(0xFF1B5E20), letterSpacing: 0.8),
            ),
            const SizedBox(height: 10),
            Row(
              children: [
                const Icon(Icons.bar_chart, color: Color(0xFF2E7D32), size: 36),
                const SizedBox(width: 14),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Past Average Yield: $mean',
                        style: const TextStyle(fontSize: 17, fontWeight: FontWeight.bold, color: Color(0xFF1B5E20)),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        'Based on historical harvest records across $district district.',
                        style: const TextStyle(fontSize: 13, color: Colors.black87),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            const Text(
              'Note: This is a regional historical benchmark, not a harvest guarantee for your individual plot.',
              style: TextStyle(fontSize: 11, color: Colors.black54, fontStyle: FontStyle.italic),
            ),
          ],
        ),
      ),
    );
  }

  // ==================== SECTION F: Progressive Disclosure ====================
  Widget _buildTechnicalDetailsExpansion() {
    final b = _assessment!.baseline;
    final soil = _assessment!.suitabilityAnalysis;

    final count = b['sample_seasons_count'] ?? 22;
    final period = b['data_period'] ?? '1997-2021';
    final p10 = b['historical_p10_t_ha'] != null ? '${b['historical_p10_t_ha']} t/ha' : '1.06 t/ha';
    final p90 = b['historical_p90_t_ha'] != null ? '${b['historical_p90_t_ha']} t/ha' : '1.98 t/ha';

    return Card(
      elevation: 0,
      color: Colors.white,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: BorderSide(color: Colors.grey.shade300),
      ),
      child: ExpansionTile(
        title: const Text(
          'Scientific and Data Source Details',
          style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: Color(0xFF333333)),
        ),
        subtitle: const Text(
          'Expand to inspect APY records, CropNet soil parameters, and research models',
          style: TextStyle(fontSize: 11, color: Colors.black54),
        ),
        childrenPadding: const EdgeInsets.all(16.0),
        children: [
          const Text(
            'Official APY Yield Records (1997–2021)',
            style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: Color(0xFF1B5E20)),
          ),
          const SizedBox(height: 6),
          Text(
            'Sample count: $count seasons · Period: $period\n10th Percentile (Stress year): $p10\n90th Percentile (Favorable year): $p90',
            style: const TextStyle(fontSize: 12, height: 1.4, color: Colors.black87),
          ),
          const Divider(height: 20),
          if (soil != null) ...[
            const Text(
              'CropNet Soil & Edaphic Properties',
              style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: Color(0xFF1B5E20)),
            ),
            const SizedBox(height: 6),
            Text(
              'Texture: ${soil.soilTexture} · pH: ${soil.soilPh.toStringAsFixed(1)} (${soil.phStatus})\nOrganic Carbon: ${soil.organicCarbonPct}% · Available Water: ${soil.availableWaterCapacityMmM} mm/m\nRooting Depth: ${soil.effectiveRootingDepthCm} cm · Normal Rain: ${soil.climateNormalRainfallMm} mm',
              style: const TextStyle(fontSize: 12, height: 1.4, color: Colors.black87),
            ),
            const SizedBox(height: 4),
            Text(
              'Provenance: ${soil.dataProvenance}',
              style: const TextStyle(fontSize: 10, color: Colors.black54, fontStyle: FontStyle.italic),
            ),
            const Divider(height: 20),
          ],
          const Text(
            'Safeguards & Methodology',
            style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: Color(0xFF1B5E20)),
          ),
          const SizedBox(height: 4),
          Text(
            b['disclaimer'] ?? 'Plot-level numerical prediction is gated pending verified harvest ground truth.',
            style: const TextStyle(fontSize: 11, color: Colors.black54, height: 1.3),
          ),
        ],
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
            const Icon(Icons.grass, size: 64, color: Color(0xFF1B5E20)),
            const SizedBox(height: 16),
            const Text(
              'No Farm Selected',
              style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: Color(0xFF1B5E20)),
            ),
            const SizedBox(height: 8),
            const Text(
              'Please register or select a farm to view crop health and yield analysis.',
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 14, color: Colors.black54),
            ),
            const SizedBox(height: 20),
            ElevatedButton.icon(
              onPressed: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(builder: (_) => const FarmRegistrationScreen()),
                );
              },
              icon: const Icon(Icons.add_location_alt),
              label: const Text('Register Farm'),
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFF1B5E20),
                foregroundColor: Colors.white,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
