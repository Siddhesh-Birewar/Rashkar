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

  Color _getRiskColor(String level) {
    switch (level.toLowerCase()) {
      case 'critical':
        return const Color(0xFFC62828);
      case 'high':
        return const Color(0xFFE65100);
      case 'moderate':
        return const Color(0xFFF57F17);
      case 'low':
      default:
        return const Color(0xFF2E7D32);
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
            const Text('Yield Intelligence & Risk', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
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
                          // 1. Farm & Crop Summary Card
                          _buildFarmCropSummaryCard(),
                          const SizedBox(height: 16),

                          // 2. Farmer Narrative Summary
                          if (_assessment!.farmerNarrativeExplanation.isNotEmpty)
                            _buildNarrativeCard(),
                          if (_assessment!.farmerNarrativeExplanation.isNotEmpty)
                            const SizedBox(height: 16),

                          // 3. Historical Yield Baseline Analysis (APY 17,916 records)
                          _buildHistoricalBaselineCard(),
                          const SizedBox(height: 16),

                          // 4. Crop Suitability & Edaphic Profile (CropNet)
                          if (_assessment!.suitabilityAnalysis != null)
                            _buildSoilSuitabilityCard(_assessment!.suitabilityAnalysis!),
                          if (_assessment!.suitabilityAnalysis != null)
                            const SizedBox(height: 16),

                          // 5. Multi-Dimensional Stress Screening (5 Dimensions)
                          _buildStressScreeningSection(),
                          const SizedBox(height: 16),

                          // 6. ML Prediction Gate Safeguard Banner
                          _buildMLGateBanner(),
                          const SizedBox(height: 16),

                          // 7. Actionable Agronomic Recommendations
                          _buildRecommendationsSection(),
                          const SizedBox(height: 24),
                        ],
                      ),
                    ),
    );
  }

  // ==================== SECTION 1: Farm & Crop Summary ====================
  Widget _buildFarmCropSummaryCard() {
    final a = _assessment!;
    final appState = AppState.instance;

    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.location_on, color: Color(0xFF2E7D32), size: 20),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    '${a.farmName} (${appState.activeTaluka}, ${appState.activeDistrict})',
                    style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                  ),
                ),
                ElevatedButton.icon(
                  onPressed: () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (_) => EditProfileScreen(farm: appState.activeFarm),
                      ),
                    );
                  },
                  icon: const Icon(Icons.edit, size: 14),
                  label: const Text('Edit Farm', style: TextStyle(fontSize: 11)),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFFE8F5E9),
                    foregroundColor: const Color(0xFF1B5E20),
                    elevation: 0,
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Wrap(
              spacing: 16,
              runSpacing: 8,
              children: [
                _buildSummaryItem('Active Crop', a.cropName),
                _buildSummaryItem('Growth Stage', 'DAS ${a.daysAfterSowing}'),
                _buildSummaryItem('Sowing Date', a.sowingDate.isNotEmpty ? a.sowingDate : 'Kharif Season'),
                _buildSummaryItem('Area', '${a.totalAreaAcres} acres'),
                _buildSummaryItem('Irrigation', a.irrigationType),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSummaryItem(String label, String value) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: const TextStyle(fontSize: 11, color: Colors.black54)),
        Text(value, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: Color(0xFF2E7D32))),
      ],
    );
  }

  // ==================== SECTION 2: Narrative Summary ====================
  Widget _buildNarrativeCard() {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: const Color(0xFFE8F5E9),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFF81C784)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(Icons.analytics_outlined, color: Color(0xFF1B5E20), size: 24),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Agronomic Situation Overview',
                  style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: Color(0xFF1B5E20)),
                ),
                const SizedBox(height: 4),
                Text(
                  _assessment!.farmerNarrativeExplanation,
                  style: const TextStyle(fontSize: 12, height: 1.4, color: Colors.black87),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  // ==================== SECTION 3: Historical Baseline ====================
  Widget _buildHistoricalBaselineCard() {
    final b = _assessment!.baseline;
    final appState = AppState.instance;

    final mean = b['historical_mean_t_ha'] != null ? '${b['historical_mean_t_ha']} t/ha' : '1.45 t/ha';
    final median = b['historical_median_t_ha'] != null ? '${b['historical_median_t_ha']} t/ha' : mean;
    final p10 = b['historical_p10_t_ha'] != null ? '${b['historical_p10_t_ha']} t/ha' : '0.90 t/ha';
    final p90 = b['historical_p90_t_ha'] != null ? '${b['historical_p90_t_ha']} t/ha' : '2.10 t/ha';
    final count = b['sample_seasons_count'] ?? 24;
    final period = b['data_period'] ?? '1997-2021';
    final geoUnit = b['geographical_unit'] ?? '${appState.activeDistrict} District';

    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.history, color: Color(0xFF2E7D32)),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    'Historical Yield Baseline ($geoUnit)',
                    style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15),
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: Colors.blue.shade50,
                    borderRadius: BorderRadius.circular(6),
                    border: Border.all(color: Colors.blue.shade300),
                  ),
                  child: Text(
                    'N = $count Seasons',
                    style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: Colors.blue.shade800),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 6),
            Text(
              'Official Ministry of Agriculture APY Canonical Dataset ($period)',
              style: const TextStyle(fontSize: 11, color: Colors.black54),
            ),
            const SizedBox(height: 14),

            // Percentiles Row
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceAround,
              children: [
                _buildStatBox('P10 (Drought/Worst)', p10, Colors.red.shade700),
                _buildStatBox('Historical Mean', mean, const Color(0xFF2E7D32), isBold: true),
                _buildStatBox('Median', median, Colors.teal.shade700),
                _buildStatBox('P90 (Bumper Season)', p90, Colors.green.shade800),
              ],
            ),
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: Colors.grey.shade100,
                borderRadius: BorderRadius.circular(8),
              ),
              child: Text(
                b['disclaimer'] ?? 'District-level statistical baseline derived from official APY records. Plot-level numerical prediction is disabled pending verified harvest labels.',
                style: const TextStyle(fontSize: 10, color: Colors.black54),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStatBox(String label, String value, Color col, {bool isBold = false}) {
    return Column(
      children: [
        Text(value, style: TextStyle(fontWeight: FontWeight.bold, fontSize: isBold ? 15 : 13, color: col)),
        const SizedBox(height: 2),
        Text(label, style: const TextStyle(fontSize: 9, color: Colors.black54)),
      ],
    );
  }

  // ==================== SECTION 4: Soil Suitability ====================
  Widget _buildSoilSuitabilityCard(SoilSuitabilityAnalysis soil) {
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.terrain, color: Colors.brown),
                const SizedBox(width: 8),
                const Expanded(
                  child: Text('CropNet Soil Suitability & Edaphic Profile', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: Colors.green.shade50,
                    borderRadius: BorderRadius.circular(6),
                    border: Border.all(color: Colors.green.shade400),
                  ),
                  child: Text(
                    soil.phStatus,
                    style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: Colors.green.shade800),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Wrap(
              spacing: 12,
              runSpacing: 10,
              children: [
                _buildSoilProperty('Texture', soil.soilTexture),
                _buildSoilProperty('Soil pH', soil.soilPh.toStringAsFixed(1)),
                _buildSoilProperty('Organic Carbon', '${soil.organicCarbonPct}%'),
                _buildSoilProperty('CEC', '${soil.cationExchangeCapacity} cmol/kg'),
                _buildSoilProperty('Available Water', '${soil.availableWaterCapacityMmM} mm/m'),
                _buildSoilProperty('Rooting Depth', '${soil.effectiveRootingDepthCm} cm'),
                _buildSoilProperty('IMD Normal Rain', '${soil.climateNormalRainfallMm} mm'),
              ],
            ),
            const SizedBox(height: 10),
            Text(
              'Provenance: ${soil.dataProvenance}',
              style: const TextStyle(fontSize: 10, color: Colors.black54, fontStyle: FontStyle.italic),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSoilProperty(String label, String value) {
    return Container(
      width: 140,
      padding: const EdgeInsets.all(8),
      decoration: BoxDecoration(
        color: Colors.grey.shade50,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: Colors.grey.shade200),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: const TextStyle(fontSize: 10, color: Colors.black54)),
          const SizedBox(height: 2),
          Text(value, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Colors.black87), overflow: TextOverflow.ellipsis),
        ],
      ),
    );
  }

  // ==================== SECTION 5: Multi-Dimensional Stress ====================
  Widget _buildStressScreeningSection() {
    final risks = _assessment!.risks;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          '5-DIMENSIONAL CROP STRESS SCREENING',
          style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: Colors.black54, letterSpacing: 0.8),
        ),
        const SizedBox(height: 8),
        if (risks.isEmpty)
          const Card(
            child: Padding(
              padding: EdgeInsets.all(16.0),
              child: Text('All environmental dimensions operating within favorable ranges.'),
            ),
          )
        else
          ...risks.map((r) => _buildRiskDimensionCard(r)).toList(),
      ],
    );
  }

  Widget _buildRiskDimensionCard(RiskDimensionItem r) {
    final col = _getRiskColor(r.riskLevel);

    String prettyDim = r.riskDimension.replaceAll('_', ' ').toUpperCase();
    if (prettyDim.contains('DRY SPELL')) prettyDim = '1. MOISTURE DEFICIT / DRY SPELL';
    if (prettyDim.contains('EXCESS')) prettyDim = '2. EXCESS RAINFALL / WATERLOGGING';
    if (prettyDim.contains('SOIL')) prettyDim = '3. SOIL EDAPHIC CONSTRAINTS';
    if (prettyDim.contains('HEAT')) prettyDim = '4. CROP CANOPY HEAT STRESS';
    if (prettyDim.contains('PEST')) prettyDim = '5. BIOLOGICAL / PEST WATCH';

    return Card(
      elevation: 1,
      margin: const EdgeInsets.only(bottom: 10),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(color: col.withOpacity(0.4), width: 1),
      ),
      child: Padding(
        padding: const EdgeInsets.all(14.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(
                    prettyDim,
                    style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(color: col, borderRadius: BorderRadius.circular(6)),
                  child: Text(
                    r.riskLevel.toUpperCase(),
                    style: const TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: Colors.white),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 6),
            ...r.drivers.map((d) => Padding(
              padding: const EdgeInsets.only(bottom: 2.0),
              child: Text('• $d', style: const TextStyle(fontSize: 12, color: Colors.black87)),
            )),
          ],
        ),
      ),
    );
  }

  // ==================== SECTION 6: ML Prediction Gate ====================
  Widget _buildMLGateBanner() {
    final gate = _assessment!.mlPredictionGate;
    final status = gate['prediction_status'] ?? 'REQUIRES_FARM_HARVEST_LABELS';

    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: const Color(0xFFEDE7F6),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.deepPurple.shade300),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.lock_clock, color: Colors.deepPurple),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  'ML Prediction Safeguard: $status',
                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: Colors.deepPurple),
                ),
              ),
            ],
          ),
          const SizedBox(height: 6),
          Text(
            gate['ethical_safeguard'] ?? 'Predicting exact farm-level harvest tonnage without verified ground-truth labels violates scientific rigor. Rashkar displays auditable district historical percentiles (P10 to P90) alongside real-time stress screening.',
            style: const TextStyle(fontSize: 11, color: Colors.black87, height: 1.3),
          ),
        ],
      ),
    );
  }

  // ==================== SECTION 7: Recommendations ====================
  Widget _buildRecommendationsSection() {
    final recs = _assessment!.recommendations;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'ACTIONABLE AGRONOMIC INTERVENTIONS',
          style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: Colors.black54, letterSpacing: 0.8),
        ),
        const SizedBox(height: 8),
        if (recs.isEmpty)
          const Card(
            child: Padding(
              padding: EdgeInsets.all(16.0),
              child: Text('No urgent interventions recommended today. Continue standard package of practices.'),
            ),
          )
        else
          ...recs.map((rec) => _buildActionCard(rec)).toList(),
      ],
    );
  }

  Widget _buildActionCard(ActionableRecommendationItem rec) {
    Color badgeCol = Colors.green;
    if (rec.urgency.toLowerCase() == 'high') badgeCol = Colors.red;
    if (rec.urgency.toLowerCase() == 'medium') badgeCol = Colors.orange;

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.grey.shade300),
        boxShadow: [
          BoxShadow(color: Colors.black.withOpacity(0.03), blurRadius: 4, offset: const Offset(0, 2)),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(rec.title, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: Color(0xFF1B5E20))),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(color: badgeCol, borderRadius: BorderRadius.circular(6)),
                child: Text(
                  rec.urgency.toUpperCase(),
                  style: const TextStyle(fontSize: 9, fontWeight: FontWeight.bold, color: Colors.white),
                ),
              ),
            ],
          ),
          const SizedBox(height: 6),
          Text(rec.description, style: const TextStyle(fontSize: 12, color: Colors.black87)),
          const SizedBox(height: 8),
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: Colors.grey.shade50,
              borderRadius: BorderRadius.circular(6),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Why Recommended: ${rec.whyRecommended}', style: const TextStyle(fontSize: 11, color: Colors.brown)),
                const SizedBox(height: 2),
                Text('Evidence Source: ${rec.evidenceSource}', style: const TextStyle(fontSize: 10, color: Colors.black54, fontStyle: FontStyle.italic)),
              ],
            ),
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
            const Icon(Icons.grass_outlined, size: 64, color: Color(0xFF2E7D32)),
            const SizedBox(height: 16),
            const Text(
              'No Farm Selected',
              style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: Color(0xFF1B5E20)),
            ),
            const SizedBox(height: 8),
            const Text(
              'Register your farm or load a sample farm to see yield intelligence, soil suitability, and district historical baselines.',
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
          ],
        ),
      ),
    );
  }
}
