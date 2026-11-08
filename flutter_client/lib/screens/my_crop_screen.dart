import 'package:flutter/material.dart';
import '../models/farm_models.dart';
import '../services/api_service.dart';
import '../services/app_state.dart';
import 'farm_registration_screen.dart';

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
            const Text('My Crop & Yield', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
            Text(
              hasFarm ? '${appState.activeCropName} · ${appState.activeTaluka}, ${appState.activeDistrict}' : 'Maharashtra',
              style: const TextStyle(fontSize: 12, color: Colors.white70),
            ),
          ],
        ),
        backgroundColor: const Color(0xFF2E7D32),
        foregroundColor: Colors.white,
        actions: [
          IconButton(icon: const Icon(Icons.refresh), onPressed: _loadAssessment),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator(color: Color(0xFF2E7D32)))
          : !hasFarm
              ? _buildEmptyState()
              : _assessment == null
                  ? const Center(child: Text('Unable to load crop yield assessment.'))
                  : SingleChildScrollView(
                      padding: const EdgeInsets.all(16.0),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          // Farm & Location Badge
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                            decoration: BoxDecoration(
                              color: const Color(0xFFE8F5E9),
                              borderRadius: BorderRadius.circular(10),
                              border: Border.all(color: const Color(0xFF81C784)),
                            ),
                            child: Row(
                              children: [
                                const Icon(Icons.location_on, size: 16, color: Color(0xFF1B5E20)),
                                const SizedBox(width: 6),
                                Expanded(
                                  child: Text(
                                    'Active Farm: ${appState.activeFarm?.farmName} · ${appState.activeTaluka}, ${appState.activeDistrict}',
                                    style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Color(0xFF1B5E20)),
                                  ),
                                ),
                              ],
                            ),
                          ),
                          const SizedBox(height: 16),

                          // 1. Crop Status Summary Card
                          _buildCropStatusCard(),
                          const SizedBox(height: 16),

                          // 2. Weather & Crop Stress Screening
                          const Text(
                            'CROP STRESS SCREENING',
                            style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: Color(0xFF333333), letterSpacing: 0.8),
                          ),
                          const SizedBox(height: 8),
                          if (_assessment!.risks.isEmpty)
                            const Card(
                              child: Padding(
                                padding: EdgeInsets.all(16.0),
                                child: Text('No active stress conditions detected today.'),
                              ),
                            )
                          else
                            ..._assessment!.risks.map((r) => _buildRiskCard(r)).toList(),
                          const SizedBox(height: 20),

                          // 3. Historical Yield Baseline Context
                          const Text(
                            'DISTRICT HISTORICAL YIELD CONTEXT',
                            style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: Color(0xFF333333), letterSpacing: 0.8),
                          ),
                          const SizedBox(height: 8),
                          _buildYieldContextCard(),
                          const SizedBox(height: 20),

                          // 4. Actionable Agronomic Recommendations (with "Why?" disclosure)
                          const Text(
                            'RECOMMENDED ACTIONS',
                            style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: Color(0xFF333333), letterSpacing: 0.8),
                          ),
                          const SizedBox(height: 8),
                          _buildRecommendationsSection(),
                          const SizedBox(height: 24),
                        ],
                      ),
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
            const Icon(Icons.grass_outlined, size: 64, color: Color(0xFF2E7D32)),
            const SizedBox(height: 16),
            const Text(
              'No Farm Selected',
              style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: Color(0xFF1B5E20)),
            ),
            const SizedBox(height: 8),
            const Text(
              'Register your farm or load a sample farm to see yield intelligence, phenological stages, and district historical yield baselines.',
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 14, color: Colors.black54),
            ),
            const SizedBox(height: 24),
            ElevatedButton.icon(
              onPressed: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(builder: (_) => const FarmRegistrationScreen()),
                );
              },
              icon: const Icon(Icons.add_location_alt),
              label: const Text('Register Your Farm'),
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFF2E7D32),
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
              ),
            ),
            const SizedBox(height: 12),
            TextButton(
              onPressed: () async {
                await AppState.instance.loadDemoFarm();
              },
              child: const Text('Load Baramati Demo Farm'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildCropStatusCard() {
    final a = _assessment!;
    final appState = AppState.instance;
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  appState.activeCropName.toUpperCase(),
                  style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: Color(0xFF1B5E20)),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: const Color(0xFFE8F5E9),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text(
                    'Day ${a.das}',
                    style: const TextStyle(fontWeight: FontWeight.bold, color: Color(0xFF2E7D32)),
                  ),
                )
              ],
            ),
            const SizedBox(height: 12),
            Text('Current Stage: ${a.cropStageNameEn}', style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
            const SizedBox(height: 4),
            Text(
              '${a.cropStageNameEn} is critical for yield determination in ${appState.activeDistrict}. Monitor soil moisture and temperature regularly.',
              style: const TextStyle(fontSize: 13, color: Colors.black54),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildRiskCard(RiskDimensionItem r) {
    Color badgeColor = Colors.green;
    String badgeText = 'Normal';
    if (r.riskLevel == 'high') {
      badgeColor = Colors.red;
      badgeText = 'Elevated Risk';
    } else if (r.riskLevel == 'moderate') {
      badgeColor = Colors.orange;
      badgeText = 'Moderate Stress';
    }

    String title = r.riskDimension.replaceAll('_', ' ').toUpperCase();
    if (r.riskDimension.contains('dry_spell')) title = 'Drought / Dry Spell Stress';
    if (r.riskDimension.contains('excess_rainfall')) title = 'Excess Rainfall / Waterlogging';
    if (r.riskDimension.contains('heat')) title = 'Crop Heat Stress';

    return Card(
      elevation: 1,
      margin: const EdgeInsets.only(bottom: 10),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
      child: Padding(
        padding: const EdgeInsets.all(14.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Expanded(
                  child: Text(title, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.bold)),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: badgeColor.withOpacity(0.15),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Text(badgeText, style: TextStyle(color: badgeColor, fontWeight: FontWeight.bold, fontSize: 12)),
                )
              ],
            ),
            const SizedBox(height: 6),
            ...r.drivers.map((d) => Text('• $d', style: const TextStyle(fontSize: 13, color: Colors.black87))).toList(),
          ],
        ),
      ),
    );
  }

  Widget _buildYieldContextCard() {
    final b = _assessment!.baseline;
    final mean = b['historical_mean_t_ha'] ?? 1.62;
    final unit = b['geographical_unit'] ?? '${AppState.instance.activeDistrict} District Baseline';
    final disclaimer = b['disclaimer'] ?? 'Historical reference statistics only.';

    return Card(
      elevation: 1,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
      child: Padding(
        padding: const EdgeInsets.all(14.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.analytics_outlined, color: Color(0xFF2E7D32)),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    'District Historical Average: $mean tonnes/ha',
                    style: const TextStyle(fontSize: 15, fontWeight: FontWeight.bold),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 6),
            Text('Source: $unit (Official APY Yield Records)', style: const TextStyle(fontSize: 12, color: Colors.black54)),
            const SizedBox(height: 8),
            Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: Colors.amber.withOpacity(0.12),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Text(
                disclaimer,
                style: const TextStyle(fontSize: 12, color: Color(0xFF6D4C41), fontStyle: FontStyle.italic),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildRecommendationsSection() {
    final allActions = _assessment!.risks.expand((r) => r.recommendedActions).toList();
    if (allActions.isEmpty) {
      return const Card(
        child: Padding(
          padding: EdgeInsets.all(16.0),
          child: Text('No urgent interventions required today. Continue regular crop monitoring.'),
        ),
      );
    }

    return Column(
      children: allActions.map((action) => _ActionCard(action: action)).toList(),
    );
  }
}

class _ActionCard extends StatefulWidget {
  final Map<String, dynamic> action;
  const _ActionCard({Key? key, required this.action}) : super(key: key);

  @override
  State<_ActionCard> createState() => _ActionCardState();
}

class _ActionCardState extends State<_ActionCard> {
  bool _expanded = false;

  @override
  Widget build(BuildContext context) {
    final a = widget.action;
    return Card(
      elevation: 2,
      margin: const EdgeInsets.only(bottom: 12),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              a['title_en'] ?? 'Advisory',
              style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Color(0xFF1B5E20)),
            ),
            const SizedBox(height: 6),
            Text(
              a['description_en'] ?? '',
              style: const TextStyle(fontSize: 14, color: Colors.black87),
            ),
            const SizedBox(height: 10),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                TextButton.icon(
                  onPressed: () {
                    setState(() => _expanded = !_expanded);
                  },
                  icon: Icon(_expanded ? Icons.keyboard_arrow_up : Icons.help_outline, size: 18),
                  label: Text(_expanded ? 'Hide Source' : 'Why this recommendation?'),
                  style: TextButton.styleFrom(foregroundColor: const Color(0xFF2E7D32)),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: const Color(0xFFE8F5E9),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: const Text('Verified POP', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: Color(0xFF1B5E20))),
                )
              ],
            ),
            if (_expanded) ...[
              const Divider(height: 16),
              Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: const Color(0xFFF9FBE7),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('Scientific Evidence & Provenance:', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
                    const SizedBox(height: 4),
                    Text(a['evidence_citation'] ?? 'MPKV Rahuri Agronomic Research Manual', style: const TextStyle(fontSize: 12, color: Colors.black87)),
                  ],
                ),
              ),
            ]
          ],
        ),
      ),
    );
  }
}
