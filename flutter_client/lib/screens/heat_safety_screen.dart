import 'package:flutter/material.dart';
import '../models/farm_models.dart';
import '../services/api_service.dart';
import '../services/app_state.dart';
import 'edit_profile_screen.dart';

class HeatSafetyScreen extends StatefulWidget {
  const HeatSafetyScreen({Key? key}) : super(key: key);

  @override
  State<HeatSafetyScreen> createState() => _HeatSafetyScreenState();
}

class _HeatSafetyScreenState extends State<HeatSafetyScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  WorkerHeatResponse? _workerHeat;
  CropHeatAssessment? _cropHeat;
  bool _isLoading = true;
  bool _isRecalculatingWorker = false;
  bool _isRecalculatingCrop = false;

  // Interactive Worker Heat State
  String _workload = 'moderate';
  String _sunExposure = 'direct_sun';
  bool _isAcclimatised = true;
  String _clothingType = 'standard_work_clothes';
  double _exposureDurationHours = 3.0;

  // Interactive Crop Heat State
  String? _selectedCropStage;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    AppState.instance.addListener(_onStateChange);
    _loadInitialData();
  }

  @override
  void dispose() {
    AppState.instance.removeListener(_onStateChange);
    _tabController.dispose();
    super.dispose();
  }

  void _onStateChange() {
    _loadInitialData();
  }

  Future<void> _loadInitialData() async {
    setState(() => _isLoading = true);
    final appState = AppState.instance;

    final w = await ApiService.getWorkerHeatHazard(
      latitude: appState.activeLatitude,
      longitude: appState.activeLongitude,
      taluka: appState.activeTaluka,
      workload: _workload,
      isAcclimatised: _isAcclimatised,
      sunExposure: _sunExposure,
      clothingType: _clothingType,
      exposureDurationHours: _exposureDurationHours,
    );

    final c = await ApiService.getCropHeatHazard(
      farmId: appState.activeFarmId,
      cropCode: appState.activeCropCode,
      stageCode: _selectedCropStage,
    );

    if (mounted) {
      setState(() {
        _workerHeat = w;
        _cropHeat = c;
        if (c.supportedStages.isNotEmpty && _selectedCropStage == null) {
          _selectedCropStage = c.growthStageCode;
        }
        _isLoading = false;
      });
    }
  }

  Future<void> _recalculateWorkerHeat() async {
    if (_workerHeat == null) return;
    setState(() => _isRecalculatingWorker = true);
    final appState = AppState.instance;

    final w = await ApiService.getWorkerHeatHazard(
      latitude: appState.activeLatitude,
      longitude: appState.activeLongitude,
      taluka: appState.activeTaluka,
      workload: _workload,
      isAcclimatised: _isAcclimatised,
      sunExposure: _sunExposure,
      clothingType: _clothingType,
      exposureDurationHours: _exposureDurationHours,
    );

    if (mounted) {
      setState(() {
        _workerHeat = w;
        _isRecalculatingWorker = false;
      });
    }
  }

  Future<void> _recalculateCropHeat(String stageCode) async {
    setState(() {
      _selectedCropStage = stageCode;
      _isRecalculatingCrop = true;
    });
    final appState = AppState.instance;

    final c = await ApiService.getCropHeatHazard(
      farmId: appState.activeFarmId,
      cropCode: appState.activeCropCode,
      stageCode: stageCode,
    );

    if (mounted) {
      setState(() {
        _cropHeat = c;
        _isRecalculatingCrop = false;
      });
    }
  }

  Color _getHazardColor(String level) {
    switch (level.toUpperCase()) {
      case 'CRITICAL':
        return const Color(0xFFC62828); // Urgent red
      case 'HIGH':
        return const Color(0xFFE65100); // Amber orange
      case 'MODERATE':
        return const Color(0xFFF57F17); // Caution yellow/amber
      case 'LOW':
      default:
        return const Color(0xFF2E7D32); // Calm green
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
            const Text('Heat Safety Assistant', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
            Text(
              '${appState.activeTaluka}, ${appState.activeDistrict} · ${appState.activeCropName}',
              style: const TextStyle(fontSize: 12, color: Colors.white70),
            ),
          ],
        ),
        backgroundColor: const Color(0xFF1B5E20),
        foregroundColor: Colors.white,
        actions: [
          IconButton(
            tooltip: 'Refresh Weather',
            icon: const Icon(Icons.refresh),
            onPressed: _loadInitialData,
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
            Tab(icon: Icon(Icons.person_outline), text: 'Worker Safety'),
            Tab(icon: Icon(Icons.eco_outlined), text: 'Crop Heat Risk'),
          ],
        ),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator(color: Color(0xFF2E7D32)))
          : TabBarView(
              controller: _tabController,
              children: [
                _buildFarmerWorkerHeatTab(),
                _buildFarmerCropHeatTab(),
              ],
            ),
    );
  }

  // =========================================================================
  // WORKER HEAT RISK TAB (FARMER-FIRST DESIGN)
  // =========================================================================
  Widget _buildFarmerWorkerHeatTab() {
    final w = _workerHeat!;
    final level = w.currentHazardLevel.toUpperCase();
    final hazardColor = _getHazardColor(level);

    // Farmer-friendly status text
    String statusTitle;
    String statusSub;
    IconData statusIcon;
    if (level == 'CRITICAL') {
      statusTitle = 'Dangerous heat outdoors';
      statusSub = 'Avoid heavy field labor during peak hours. Heat stroke hazard.';
      statusIcon = Icons.warning_amber_rounded;
    } else if (level == 'HIGH') {
      statusTitle = 'Hot conditions — take precautions';
      statusSub = 'Frequent shade breaks and regular water intake are essential today.';
      statusIcon = Icons.wb_sunny_rounded;
    } else if (level == 'MODERATE') {
      statusTitle = 'Warm outdoor conditions';
      statusSub = 'Work is manageable with scheduled water breaks and sun protection.';
      statusIcon = Icons.wb_cloudy_rounded;
    } else {
      statusTitle = 'Safe to work outdoors';
      statusSub = 'Conditions are comfortable for regular farm work.';
      statusIcon = Icons.check_circle_rounded;
    }

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16.0),
      child: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 840),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // SECTION A: Today's Outdoor Work Conditions (Main Card)
          Card(
            elevation: 2,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(16),
              side: BorderSide(color: hazardColor.withOpacity(0.4), width: 1.5),
            ),
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
                          color: hazardColor.withOpacity(0.12),
                          shape: BoxShape.circle,
                        ),
                        child: Icon(statusIcon, color: hazardColor, size: 28),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text(
                              'Outdoor Work Condition',
                              style: TextStyle(fontSize: 12, color: Colors.black54, fontWeight: FontWeight.bold),
                            ),
                            Text(
                              statusTitle,
                              style: TextStyle(
                                fontSize: 17,
                                fontWeight: FontWeight.bold,
                                color: hazardColor,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  Text(
                    w.categorySelectionReason.isNotEmpty
                        ? w.categorySelectionReason
                        : 'Current heat feels like ${w.currentWbgtEstimatedC.toStringAsFixed(1)}°C outdoors in direct sun. Follow field hydration rules.',
                    style: const TextStyle(fontSize: 13, height: 1.35, color: Colors.black87),
                  ),
                  const SizedBox(height: 12),

                  // Peak concern time & simple actionable tip
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: Colors.grey.shade50,
                      borderRadius: BorderRadius.circular(10),
                      border: Border.all(color: Colors.grey.shade200),
                    ),
                    child: Column(
                      children: [
                        Row(
                          children: [
                            const Icon(Icons.access_time_rounded, size: 18, color: Color(0xFFD84315)),
                            const SizedBox(width: 8),
                            Expanded(
                              child: Text(
                                'Peak Heat Window: ${w.peakRiskHourIst.isNotEmpty ? w.peakRiskHourIst : "12:00 PM – 3:30 PM"} (Peak: ${w.maxHazardLevelInWindow})',
                                style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: Colors.black87),
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 6),
                        Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Icon(Icons.water_drop, size: 18, color: Colors.blue),
                            const SizedBox(width: 8),
                            Expanded(
                              child: Text(
                                w.hydrationGuidance['rule_summary'] ?? 'Drink 1 glass of water every 20 minutes. Keep a covered water pot near the plot.',
                                style: const TextStyle(fontSize: 12, color: Colors.black87),
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),

          // SECTION B: Adjust My Work Conditions (Interactive Guided Dialog/Button)
          Card(
            elevation: 1,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(14),
              side: const BorderSide(color: Color(0xFFE0E0E0)),
            ),
            child: Padding(
              padding: const EdgeInsets.all(14.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Row(
                        children: [
                          Icon(Icons.tune, color: Color(0xFF2E7D32), size: 20),
                          SizedBox(width: 8),
                          Text(
                            'My Current Farm Work',
                            style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                          ),
                        ],
                      ),
                      if (_isRecalculatingWorker)
                        const SizedBox(
                          width: 16,
                          height: 16,
                          child: CircularProgressIndicator(strokeWidth: 2, color: Color(0xFF2E7D32)),
                        ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Wrap(
                    spacing: 8,
                    runSpacing: 6,
                    children: [
                      _buildSummaryPill('Work', _getWorkloadFriendlyName(_workload)),
                      _buildSummaryPill('Sun', _sunExposure == 'direct_sun' ? 'Direct Sun' : (_sunExposure == 'partial_shade' ? 'Partial Shade' : 'Full Shade')),
                      _buildSummaryPill('Heat Adapted', _isAcclimatised ? 'Yes' : 'Not used to heat'),
                      _buildSummaryPill('Shift', '${_exposureDurationHours.toStringAsFixed(1)} hrs'),
                    ],
                  ),
                  const SizedBox(height: 12),
                  SizedBox(
                    width: double.infinity,
                    child: OutlinedButton.icon(
                      style: OutlinedButton.styleFrom(
                        foregroundColor: const Color(0xFF2E7D32),
                        side: const BorderSide(color: Color(0xFF2E7D32)),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                        padding: const EdgeInsets.symmetric(vertical: 10),
                      ),
                      icon: const Icon(Icons.edit_note, size: 18),
                      label: const Text('Change My Work Details', style: TextStyle(fontWeight: FontWeight.bold)),
                      onPressed: () => _showWorkerSettingsBottomSheet(context),
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),

          // SECTION C: 6-Hour Heat Safety Timeline (Visual & Simple)
          Card(
            elevation: 1,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
            child: Padding(
              padding: const EdgeInsets.all(14.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Today\'s Hourly Work Schedule',
                    style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                  ),
                  const SizedBox(height: 4),
                  const Text(
                    'Color-coded hours: Green is safe, amber requires extra water, red means rest.',
                    style: TextStyle(fontSize: 11, color: Colors.black54),
                  ),
                  const SizedBox(height: 12),
                  if (w.hourlyProjections.isNotEmpty)
                    SingleChildScrollView(
                      scrollDirection: Axis.horizontal,
                      child: Row(
                        children: w.hourlyProjections.map((p) => _buildSimpleHourlyPill(p)).toList(),
                      ),
                    ),
                  const SizedBox(height: 10),
                  // Best & Worst window guidance
                  Container(
                    padding: const EdgeInsets.all(10),
                    decoration: BoxDecoration(
                      color: const Color(0xFFE8F5E9),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Row(
                      children: [
                        const Icon(Icons.recommend, size: 18, color: Color(0xFF2E7D32)),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            w.shiftExceedsForecastCoverage && w.coverageLimitationWarning != null
                                ? w.coverageLimitationWarning!
                                : 'Recommendation: Schedule heavy tasks before 10:30 AM or after 4:00 PM for comfort and safety.',
                            style: const TextStyle(fontSize: 11, color: Color(0xFF1B5E20), fontWeight: FontWeight.w500),
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),

          // SECTION D: Emergency Heat Illness Triage (Clear & Accessible)
          Card(
            elevation: 1,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(14),
              side: BorderSide(color: Colors.red.shade200),
            ),
            child: Theme(
              data: Theme.of(context).copyWith(dividerColor: Colors.transparent),
              child: ExpansionTile(
                leading: Container(
                  padding: const EdgeInsets.all(6),
                  decoration: BoxDecoration(color: Colors.red.shade50, shape: BoxShape.circle),
                  child: const Icon(Icons.health_and_safety, color: Colors.red, size: 22),
                ),
                title: const Text(
                  'Signs of Heat Illness & Emergency First Aid',
                  style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: Colors.red),
                ),
                subtitle: const Text('Tap to view what to do if someone falls sick', style: TextStyle(fontSize: 11, color: Colors.black54)),
                children: [
                  Padding(
                    padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            // Mild / Heat Exhaustion
                            Expanded(
                              child: Container(
                                padding: const EdgeInsets.all(10),
                                decoration: BoxDecoration(
                                  color: Colors.orange.shade50,
                                  borderRadius: BorderRadius.circular(8),
                                  border: Border.all(color: Colors.orange.shade300),
                                ),
                                child: const Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text('Mild: Heat Exhaustion', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 11, color: Colors.deepOrange)),
                                    SizedBox(height: 4),
                                    Text('• Dizziness or headache\n• Heavy sweating\n• Weakness, nausea', style: TextStyle(fontSize: 11)),
                                    SizedBox(height: 6),
                                    Text('WHAT TO DO:\nMove to shade, loosen shirt, drink cool water with a pinch of salt.', style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: Colors.brown)),
                                  ],
                                ),
                              ),
                            ),
                            const SizedBox(width: 8),
                            // Severe / Heat Stroke
                            Expanded(
                              child: Container(
                                padding: const EdgeInsets.all(10),
                                decoration: BoxDecoration(
                                  color: Colors.red.shade50,
                                  borderRadius: BorderRadius.circular(8),
                                  border: Border.all(color: Colors.red.shade400),
                                ),
                                child: const Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text('Severe: Heat Stroke (108)', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 11, color: Colors.red)),
                                    SizedBox(height: 4),
                                    Text('• High body heat\n• Confusion or fainting\n• Hot, dry or red skin', style: TextStyle(fontSize: 11)),
                                    SizedBox(height: 6),
                                    Text('URGENT:\nCall 108 immediately!\nPour water on body while waiting. Do not force drinks if unconscious.', style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: Colors.red)),
                                  ],
                                ),
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 10),
                        Container(
                          padding: const EdgeInsets.all(8),
                          decoration: BoxDecoration(
                            color: Colors.grey.shade100,
                            borderRadius: BorderRadius.circular(6),
                          ),
                          child: const Row(
                            children: [
                              Icon(Icons.phone_in_talk, size: 16, color: Colors.black87),
                              SizedBox(width: 6),
                              Text(
                                'Ambulance: 108  |  Emergency: 112  |  Kisan Call Centre: 1800-180-1551',
                                style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),

          // SECTION E: Scientific & Provenance Details (Progressive Disclosure)
          Card(
            elevation: 1,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
            child: ExpansionTile(
              leading: const Icon(Icons.biotech, color: Colors.blueGrey),
              title: const Text(
                'Scientific Details & Data Sources',
                style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: Colors.blueGrey),
              ),
              subtitle: const Text('Tap to view WBGT physics, thresholds & weather provider', style: TextStyle(fontSize: 11, color: Colors.black54)),
              children: [
                Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // Multi-Index Scores
                      Wrap(
                        spacing: 8,
                        runSpacing: 8,
                        children: [
                          _buildDetailChip('Air Temp', '${w.currentAirTempC.toStringAsFixed(1)}°C'),
                          _buildDetailChip('Humidity', '${w.currentRelativeHumidityPct.toStringAsFixed(0)}%'),
                          _buildDetailChip('Wind Speed', '${w.currentWindSpeedKmh.toStringAsFixed(1)} km/h'),
                          _buildDetailChip('Solar Radiation', '${w.currentSolarRadiationWm2.toStringAsFixed(0)} W/m²'),
                          _buildDetailChip('Effective WBGT', '${w.currentWbgtEstimatedC.toStringAsFixed(1)}°C'),
                          _buildDetailChip('Screening Limit', '${w.screeningThresholdC.toStringAsFixed(1)}°C'),
                        ],
                      ),
                      const SizedBox(height: 12),
                      Container(
                        padding: const EdgeInsets.all(10),
                        decoration: BoxDecoration(
                          color: Colors.blueGrey.shade50,
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'Threshold Comparison: ${w.thresholdComparisonMessage.isNotEmpty ? w.thresholdComparisonMessage : w.peakRiskReason}',
                              style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w600),
                            ),
                            const SizedBox(height: 4),
                            Text(
                              'Standards: ${w.methodologyStandardsVersion.isNotEmpty ? w.methodologyStandardsVersion : "ACGIH 2023 TLVs & ISO 7243:2017"}',
                              style: const TextStyle(fontSize: 10, color: Colors.black54),
                            ),
                            const SizedBox(height: 4),
                            Text(
                              'Provider: ${w.weatherSourceName} (${w.spatialResolution}) · Valid: ${w.validTimeIst} IST · Status: ${w.isObservedOrForecast}',
                              style: const TextStyle(fontSize: 10, color: Colors.black54),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        w.disclaimer.isNotEmpty ? w.disclaimer : 'Occupational heat screening based on ISO 7243 and ACGIH guidelines. Not a clinical device.',
                        style: const TextStyle(fontSize: 10, color: Colors.black54, fontStyle: FontStyle.italic),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
              const SizedBox(height: 20),
            ],
          ),
        ),
      ),
    );
  }

  // =========================================================================
  // CROP HEAT RISK TAB (FARMER-FIRST DESIGN)
  // =========================================================================
  Widget _buildFarmerCropHeatTab() {
    final c = _cropHeat!;
    final level = c.overallCropHeatRisk.toUpperCase();
    final riskColor = _getHazardColor(level);

    // Friendly crop status text
    String statusTitle;
    String statusSub;
    IconData statusIcon;
    if (level == 'CRITICAL' || level == 'HIGH') {
      statusTitle = 'High heat stress — action needed';
      statusSub = 'Temperatures are approaching or exceeding tolerance for your current growth stage.';
      statusIcon = Icons.warning_amber_rounded;
    } else if (level == 'MODERATE') {
      statusTitle = 'Moderate heat — monitor soil moisture';
      statusSub = 'Crop is experiencing warm conditions. Ensure adequate root zone moisture.';
      statusIcon = Icons.water_drop_outlined;
    } else {
      statusTitle = 'Crop is handling temperature well';
      statusSub = 'Temperatures are within the optimal growth range for this stage.';
      statusIcon = Icons.check_circle_rounded;
    }

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16.0),
      child: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 840),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // SECTION A: Crop Heat Status (Main Card)
          Card(
            elevation: 2,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(16),
              side: BorderSide(color: riskColor.withOpacity(0.4), width: 1.5),
            ),
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
                          color: riskColor.withOpacity(0.12),
                          shape: BoxShape.circle,
                        ),
                        child: Icon(statusIcon, color: riskColor, size: 28),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              '${c.cropCommonName.toUpperCase()} · ${c.growthStageNameEn ?? "Growing"} Stage',
                              style: const TextStyle(fontSize: 12, color: Colors.black54, fontWeight: FontWeight.bold),
                            ),
                            Text(
                              statusTitle,
                              style: TextStyle(
                                fontSize: 17,
                                fontWeight: FontWeight.bold,
                                color: riskColor,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  Text(
                    c.stageBiologicalVulnerability.isNotEmpty ? c.stageBiologicalVulnerability : statusSub,
                    style: const TextStyle(fontSize: 13, height: 1.35, color: Colors.black87),
                  ),
                  const SizedBox(height: 12),

                  // Today's Expected High vs Critical Threshold
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: Colors.grey.shade50,
                      borderRadius: BorderRadius.circular(10),
                      border: Border.all(color: Colors.grey.shade200),
                    ),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.spaceAround,
                      children: [
                        _buildSimpleMetric('Expected High', '${c.tmaxForecastC}°C', Icons.wb_sunny, Colors.orange.shade800),
                        _buildSimpleMetric('Critical Limit', '${c.criticalTmaxThresholdC}°C', Icons.thermostat, Colors.red.shade700),
                        _buildSimpleMetric('Optimal Range', '${c.optimalTempMinC}-${c.optimalTempMaxC}°C', Icons.check_circle_outline, Colors.green.shade800),
                      ],
                    ),
                  ),

                  // Season Expired Banner
                  if (c.isSeasonExpired || c.growthStageCode == null) ...[
                    const SizedBox(height: 12),
                    Container(
                      padding: const EdgeInsets.all(10),
                      decoration: BoxDecoration(
                        color: Colors.deepOrange.shade50,
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(color: Colors.deepOrange.shade300),
                      ),
                      child: Row(
                        children: [
                          const Icon(Icons.event_busy, color: Colors.deepOrange, size: 20),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              c.seasonExpiryMessage ?? 'Crop sowing date indicates season has completed. Update profile if newly planted.',
                              style: const TextStyle(fontSize: 11, color: Colors.deepOrange, fontWeight: FontWeight.w600),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),

          // SECTION B: Confirm Your Crop Stage (Interactive Single-Tap Chips)
          Card(
            elevation: 1,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
            child: Padding(
              padding: const EdgeInsets.all(14.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text(
                        'Confirm Crop Stage',
                        style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                      ),
                      if (_isRecalculatingCrop)
                        const SizedBox(
                          width: 16,
                          height: 16,
                          child: CircularProgressIndicator(strokeWidth: 2, color: Color(0xFF2E7D32)),
                        ),
                    ],
                  ),
                  const SizedBox(height: 4),
                  const Text(
                    'Tap your crop\'s current stage to update heat tolerance thresholds:',
                    style: TextStyle(fontSize: 11, color: Colors.black54),
                  ),
                  const SizedBox(height: 10),
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: c.supportedStages.map((s) {
                      final isSelected = (_selectedCropStage ?? c.growthStageCode) == s['stage_code'];
                      return ChoiceChip(
                        label: Text('${s['stage_name_en']} (${s['crit_tmax']}°C limit)'),
                        selected: isSelected,
                        selectedColor: const Color(0xFFE8F5E9),
                        labelStyle: TextStyle(
                          fontSize: 12,
                          fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                          color: isSelected ? const Color(0xFF1B5E20) : Colors.black87,
                        ),
                        side: BorderSide(
                          color: isSelected ? const Color(0xFF2E7D32) : Colors.grey.shade300,
                          width: isSelected ? 1.5 : 1.0,
                        ),
                        onSelected: (selected) {
                          if (selected) {
                            _recalculateCropHeat(s['stage_code']);
                          }
                        },
                      );
                    }).toList(),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),

          // SECTION C: 4-Day Crop Heat Outlook
          Card(
            elevation: 1,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
            child: Padding(
              padding: const EdgeInsets.all(14.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    '4-Day Temperature Outlook for Your Crop',
                    style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                  ),
                  const SizedBox(height: 10),
                  if (c.dailyOutlook.isNotEmpty)
                    Column(
                      children: c.dailyOutlook.map((day) => _buildSimpleDailyRow(day)).toList(),
                    )
                  else
                    const Text('Daily outlook unavailable.', style: TextStyle(fontSize: 12, color: Colors.black54)),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),

          // SECTION D: What You Should Do For Your Crop (Actionable Interventions)
          Card(
            elevation: 1,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
            child: Padding(
              padding: const EdgeInsets.all(14.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Row(
                    children: [
                      Icon(Icons.lightbulb_outline, color: Color(0xFF2E7D32), size: 20),
                      SizedBox(width: 8),
                      Text(
                        'Recommended Actions for Your Crop',
                        style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                      ),
                    ],
                  ),
                  const SizedBox(height: 10),
                  if (c.recommendedInterventions.isNotEmpty)
                    ...c.recommendedInterventions.map((rec) => _buildSimpleInterventionCard(rec)).toList()
                  else
                    const Padding(
                      padding: EdgeInsets.symmetric(vertical: 8.0),
                      child: Text('No urgent heat interventions needed today.', style: TextStyle(fontSize: 12, color: Colors.black54)),
                    ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),

          // SECTION E: Scientific & Agronomic Details (Progressive Disclosure)
          Card(
            elevation: 1,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
            child: ExpansionTile(
              leading: const Icon(Icons.science_outlined, color: Colors.blueGrey),
              title: const Text(
                'Scientific & Field Research Details',
                style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: Colors.blueGrey),
              ),
              subtitle: const Text('Tap to view GDD units, soil provenance & research citations', style: TextStyle(fontSize: 11, color: Colors.black54)),
              children: [
                Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Wrap(
                        spacing: 8,
                        runSpacing: 8,
                        children: [
                          _buildDetailChip('Base Temp', '${c.baseTempC}°C'),
                          _buildDetailChip('Exceedance Hours', '${c.hoursAboveCritical.toStringAsFixed(1)} hrs'),
                          _buildDetailChip('Consecutive Hot Days', '${c.consecutiveHotDays}'),
                          _buildDetailChip('GDD Heat Units', '${c.cumulativeHeatUnitsGdd.toStringAsFixed(1)}'),
                          _buildDetailChip('Warm Night Hazard', c.warmNightRespirationHazard ? 'YES (>22°C)' : 'NO'),
                          _buildDetailChip('Soil Type', '${c.soilTexture} (${c.soilProvenanceLabel})'),
                        ],
                      ),
                      const SizedBox(height: 12),
                      if (c.evidenceCitation.isNotEmpty)
                        Container(
                          padding: const EdgeInsets.all(10),
                          decoration: BoxDecoration(
                            color: Colors.grey.shade100,
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: Text(
                            'Scientific Evidence Citation: ${c.evidenceCitation}',
                            style: const TextStyle(fontSize: 11, color: Colors.black87, fontStyle: FontStyle.italic),
                          ),
                        ),
                    ],
                  ),
                ),
              ],
            ),
          ),
              const SizedBox(height: 20),
            ],
          ),
        ),
      ),
    );
  }

  // =========================================================================
  // HELPER WIDGETS FOR SIMPLE PRESENTATION
  // =========================================================================
  Widget _buildSummaryPill(String label, String value) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
      decoration: BoxDecoration(
        color: Colors.grey.shade100,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: Colors.grey.shade300),
      ),
      child: Text(
        '$label: $value',
        style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: Colors.black87),
      ),
    );
  }

  Widget _buildSimpleMetric(String label, String value, IconData icon, Color color) {
    return Column(
      children: [
        Icon(icon, size: 20, color: color),
        const SizedBox(height: 4),
        Text(value, style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: color)),
        Text(label, style: const TextStyle(fontSize: 10, color: Colors.black54)),
      ],
    );
  }

  Widget _buildDetailChip(String label, String value) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: Colors.grey.shade100,
        borderRadius: BorderRadius.circular(6),
        border: Border.all(color: Colors.grey.shade300),
      ),
      child: Text(
        '$label: $value',
        style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: Colors.black87),
      ),
    );
  }

  Widget _buildSimpleHourlyPill(WorkerHourlyProjection p) {
    final color = _getHazardColor(p.hazardLevel);

    return Container(
      width: 78,
      margin: const EdgeInsets.only(right: 8),
      padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 6),
      decoration: BoxDecoration(
        color: color.withOpacity(0.08),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: color, width: p.exceedsScreeningThreshold ? 1.5 : 1.0),
      ),
      child: Column(
        children: [
          Text(p.validTimeIst, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 11)),
          const SizedBox(height: 4),
          Text('${p.wbgtEffectiveC}°C', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: color)),
          const SizedBox(height: 4),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 2),
            decoration: BoxDecoration(color: color, borderRadius: BorderRadius.circular(4)),
            child: Text(
              p.hazardLevel,
              style: const TextStyle(fontSize: 8, fontWeight: FontWeight.bold, color: Colors.white),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSimpleDailyRow(CropDailyOutlook day) {
    final col = _getHazardColor(day.riskCategory);

    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: Colors.grey.shade200),
      ),
      child: Row(
        children: [
          SizedBox(
            width: 70,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(day.dayLabel, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12)),
                Text(day.date, style: const TextStyle(fontSize: 10, color: Colors.black54)),
              ],
            ),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              day.explanation,
              style: const TextStyle(fontSize: 12, color: Colors.black87),
            ),
          ),
          const SizedBox(width: 8),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text('${day.tmaxC}°C / ${day.tminC}°C', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 11)),
              const SizedBox(height: 2),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                decoration: BoxDecoration(color: col, borderRadius: BorderRadius.circular(4)),
                child: Text(
                  day.riskCategory,
                  style: const TextStyle(fontSize: 9, fontWeight: FontWeight.bold, color: Colors.white),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildSimpleInterventionCard(CropHeatIntervention rec) {
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: const Color(0xFFF1F8E9),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: Colors.green.shade300),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  rec.titleEn,
                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: Color(0xFF1B5E20)),
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                decoration: BoxDecoration(
                  color: Colors.green.shade100,
                  borderRadius: BorderRadius.circular(4),
                ),
                child: Text(
                  rec.category.replaceAll('_', ' '),
                  style: TextStyle(fontSize: 9, fontWeight: FontWeight.bold, color: Colors.green.shade900),
                ),
              ),
            ],
          ),
          const SizedBox(height: 6),
          Text(rec.descriptionEn, style: const TextStyle(fontSize: 12, color: Colors.black87, height: 1.3)),
          if (rec.applicationMethod != null) ...[
            const SizedBox(height: 4),
            Text(
              'How: ${rec.applicationMethod} ${rec.applicationDose != null ? "(${rec.applicationDose})" : ""}',
              style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: Colors.black87),
            ),
          ],
          const SizedBox(height: 4),
          Text('Why this helps: ${rec.whyAppropriate}', style: TextStyle(fontSize: 11, color: Colors.green.shade900)),
        ],
      ),
    );
  }

  String _getWorkloadFriendlyName(String code) {
    switch (code) {
      case 'light':
        return 'Light (weeding, sitting)';
      case 'moderate':
        return 'Normal Farm Work';
      case 'heavy':
        return 'Heavy (digging, lifting)';
      case 'very_heavy':
        return 'Very Heavy (strenuous)';
      default:
        return code;
    }
  }

  void _showWorkerSettingsBottomSheet(BuildContext context) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (ctx) {
        return StatefulBuilder(
          builder: (ctx, setModalState) {
            return Padding(
              padding: EdgeInsets.fromLTRB(20, 20, 20, MediaQuery.of(ctx).viewInsets.bottom + 20),
              child: SingleChildScrollView(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Text(
                          'Adjust Farm Work Details',
                          style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                        ),
                        IconButton(
                          icon: const Icon(Icons.close),
                          onPressed: () => Navigator.pop(ctx),
                        ),
                      ],
                    ),
                    const Divider(),
                    const SizedBox(height: 8),

                    // Workload Choice
                    const Text('What kind of farm work?', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                    const SizedBox(height: 6),
                    DropdownButtonFormField<String>(
                      value: _workload,
                      decoration: InputDecoration(
                        contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                        border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                      ),
                      items: const [
                        DropdownMenuItem(value: 'light', child: Text('Light (sitting, light weeding)')),
                        DropdownMenuItem(value: 'moderate', child: Text('Normal Farm Work (walking, hoeing)')),
                        DropdownMenuItem(value: 'heavy', child: Text('Heavy (digging, carrying heavy loads)')),
                        DropdownMenuItem(value: 'very_heavy', child: Text('Very Heavy (continuous strenuous labor)')),
                      ],
                      onChanged: (val) {
                        if (val != null) {
                          setModalState(() => _workload = val);
                          setState(() => _workload = val);
                        }
                      },
                    ),
                    const SizedBox(height: 14),

                    // Sun Exposure
                    const Text('Where are you working?', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                    const SizedBox(height: 6),
                    DropdownButtonFormField<String>(
                      value: _sunExposure,
                      decoration: InputDecoration(
                        contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                        border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                      ),
                      items: const [
                        DropdownMenuItem(value: 'direct_sun', child: Text('In direct sun')),
                        DropdownMenuItem(value: 'partial_shade', child: Text('Partial shade (near trees/cover)')),
                        DropdownMenuItem(value: 'full_shade', child: Text('Full shade / shed')),
                      ],
                      onChanged: (val) {
                        if (val != null) {
                          setModalState(() => _sunExposure = val);
                          setState(() => _sunExposure = val);
                        }
                      },
                    ),
                    const SizedBox(height: 14),

                    // Acclimatised switch
                    SwitchListTile(
                      contentPadding: EdgeInsets.zero,
                      title: const Text('Used to working in hot weather?', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                      subtitle: const Text('Turn off if worker is new to this region or hasn\'t worked in sun this week', style: TextStyle(fontSize: 11)),
                      value: _isAcclimatised,
                      activeColor: const Color(0xFF2E7D32),
                      onChanged: (val) {
                        setModalState(() => _isAcclimatised = val);
                        setState(() => _isAcclimatised = val);
                      },
                    ),
                    const SizedBox(height: 8),

                    // Shift Duration
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Text('Planned shift duration:', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                        Text('${_exposureDurationHours.toStringAsFixed(1)} hours', style: const TextStyle(fontWeight: FontWeight.bold, color: Color(0xFF2E7D32))),
                      ],
                    ),
                    Slider(
                      value: _exposureDurationHours,
                      min: 1.0,
                      max: 8.0,
                      divisions: 7,
                      activeColor: const Color(0xFF2E7D32),
                      label: '${_exposureDurationHours.toStringAsFixed(1)}h',
                      onChanged: (val) {
                        setModalState(() => _exposureDurationHours = val);
                        setState(() => _exposureDurationHours = val);
                      },
                    ),
                    const SizedBox(height: 16),

                    SizedBox(
                      width: double.infinity,
                      child: ElevatedButton(
                        style: ElevatedButton.styleFrom(
                          backgroundColor: const Color(0xFF1B5E20),
                          foregroundColor: Colors.white,
                          padding: const EdgeInsets.symmetric(vertical: 12),
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                        ),
                        onPressed: () {
                          Navigator.pop(ctx);
                          _recalculateWorkerHeat();
                        },
                        child: const Text('Update & Recalculate Heat Safety', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                      ),
                    ),
                  ],
                ),
              ),
            );
          },
        );
      },
    );
  }
}
