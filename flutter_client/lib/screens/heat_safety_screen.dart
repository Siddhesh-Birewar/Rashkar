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
        return const Color(0xFFC62828);
      case 'HIGH':
        return const Color(0xFFE65100);
      case 'MODERATE':
        return const Color(0xFFF57F17);
      case 'LOW':
      default:
        return const Color(0xFF2E7D32);
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
            const Text('Heat Safety Intelligence', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
            Text(
              '${appState.activeTaluka}, ${appState.activeDistrict} · ${appState.activeCropName}',
              style: const TextStyle(fontSize: 12, color: Colors.white70),
            ),
          ],
        ),
        backgroundColor: const Color(0xFFD84315),
        foregroundColor: Colors.white,
        actions: [
          IconButton(icon: const Icon(Icons.refresh), onPressed: _loadInitialData),
        ],
        bottom: TabBar(
          controller: _tabController,
          indicatorColor: Colors.white,
          indicatorWeight: 3.0,
          labelColor: Colors.white,
          unselectedLabelColor: Colors.white70,
          tabs: const [
            Tab(icon: Icon(Icons.engineering_outlined), text: 'Worker Heat Safety'),
            Tab(icon: Icon(Icons.grass), text: 'Crop Heat Risk'),
          ],
        ),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator(color: Color(0xFFD84315)))
          : TabBarView(
              controller: _tabController,
              children: [
                _buildWorkerHeatTab(),
                _buildCropHeatTab(),
              ],
            ),
    );
  }

  // =========================================================================
  // WORKER HEAT RISK TAB (5 SECTIONS)
  // =========================================================================
  Widget _buildWorkerHeatTab() {
    final w = _workerHeat!;
    final hazardColor = _getHazardColor(w.currentHazardLevel);

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // SECTION 1: Current Conditions & Provenance Card
          Card(
            elevation: 2,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
            child: Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      const Icon(Icons.location_on, size: 18, color: Color(0xFFD84315)),
                      const SizedBox(width: 6),
                      Expanded(
                        child: Text(
                          w.farmLocationDisplay.isNotEmpty ? w.farmLocationDisplay : 'Baramati Pilot Area',
                          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                        ),
                      ),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                        decoration: BoxDecoration(
                          color: Colors.green.shade50,
                          borderRadius: BorderRadius.circular(6),
                          border: Border.all(color: Colors.green.shade400),
                        ),
                        child: Text(
                          'Confidence: ${w.dataConfidence}',
                          style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: Colors.green.shade800),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'Provider: ${w.weatherSourceName} · Res: ${w.spatialResolution}\nGrid: ${w.gridCoordinates} · Retrieved: ${w.weatherRetrievalTimeIst}\nValid: ${w.validTimeIst} · Status: ${w.isObservedOrForecast}',
                    style: const TextStyle(fontSize: 11, color: Colors.black87, height: 1.3),
                  ),
                  const Divider(height: 20),
                  // Environmental Metrics Grid
                  Wrap(
                    spacing: 12,
                    runSpacing: 10,
                    children: [
                      _buildMiniMetric('Air Temp', '${w.currentAirTempC.toStringAsFixed(1)}°C', Icons.thermostat),
                      _buildMiniMetric('Dew Point', '${w.currentDewPointC.toStringAsFixed(1)}°C', Icons.water_drop_outlined),
                      _buildMiniMetric('Humidity', '${w.currentRelativeHumidityPct.toStringAsFixed(0)}%', Icons.cloud_outlined),
                      _buildMiniMetric('Wind Speed', '${w.currentWindSpeedKmh.toStringAsFixed(1)} km/h', Icons.air),
                      _buildMiniMetric('Solar Rad', '${w.currentSolarRadiationWm2.toStringAsFixed(0)} W/m²', Icons.wb_sunny_outlined),
                      _buildMiniMetric('Est. WBGT', '${w.currentWbgtEstimatedC.toStringAsFixed(1)}°C', Icons.speed, highlight: true),
                    ],
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),

          // SECTION 2: Six-Hour Interactive Timeline & Peak Risk
          Card(
            elevation: 2,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
            child: Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      const Icon(Icons.access_time_filled, size: 20, color: Color(0xFFD84315)),
                      const SizedBox(width: 8),
                      const Text(
                        '6-Hour Heat Risk Timeline',
                        style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                      ),
                      const Spacer(),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                        decoration: BoxDecoration(
                          color: hazardColor.withOpacity(0.12),
                          borderRadius: BorderRadius.circular(8),
                          border: Border.all(color: hazardColor),
                        ),
                        child: Text(
                          'Peak: ${w.maxHazardLevelInWindow}',
                          style: TextStyle(fontWeight: FontWeight.bold, fontSize: 11, color: hazardColor),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  // Precise Threshold Exceedance / Below messaging
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: w.thresholdComparisonState == 'ABOVE'
                          ? Colors.red.shade50
                          : w.thresholdComparisonState == 'AT_THRESHOLD'
                              ? Colors.amber.shade50
                              : const Color(0xFFE8F5E9),
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(
                        color: w.thresholdComparisonState == 'ABOVE'
                            ? Colors.red.shade400
                            : w.thresholdComparisonState == 'AT_THRESHOLD'
                                ? Colors.amber.shade600
                                : Colors.green.shade600,
                        width: 1.2,
                      ),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Icon(
                              w.thresholdComparisonState == 'ABOVE'
                                  ? Icons.warning_rounded
                                  : w.thresholdComparisonState == 'AT_THRESHOLD'
                                      ? Icons.info_outline
                                      : Icons.check_circle_outline,
                              size: 18,
                              color: w.thresholdComparisonState == 'ABOVE'
                                  ? Colors.red.shade800
                                  : w.thresholdComparisonState == 'AT_THRESHOLD'
                                      ? Colors.amber.shade900
                                      : Colors.green.shade800,
                            ),
                            const SizedBox(width: 8),
                            Text(
                              w.thresholdComparisonState == 'ABOVE'
                                  ? 'THRESHOLD EXCEEDED'
                                  : w.thresholdComparisonState == 'AT_THRESHOLD'
                                      ? 'AT THRESHOLD LIMIT'
                                      : 'BELOW SCREENING THRESHOLD',
                              style: TextStyle(
                                fontWeight: FontWeight.bold,
                                fontSize: 12,
                                color: w.thresholdComparisonState == 'ABOVE'
                                    ? Colors.red.shade800
                                    : w.thresholdComparisonState == 'AT_THRESHOLD'
                                        ? Colors.amber.shade900
                                        : Colors.green.shade800,
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 6),
                        Text(
                          w.thresholdComparisonMessage.isNotEmpty ? w.thresholdComparisonMessage : w.peakRiskReason,
                          style: const TextStyle(fontSize: 12, height: 1.3, color: Colors.black87),
                        ),
                      ],
                    ),
                  ),

                  // Shift Duration Coverage Limitation Warning
                  if (w.shiftExceedsForecastCoverage && w.coverageLimitationWarning != null) ...[
                    const SizedBox(height: 10),
                    Container(
                      padding: const EdgeInsets.all(10),
                      decoration: BoxDecoration(
                        color: Colors.amber.shade100,
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(color: Colors.amber.shade700),
                      ),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Icon(Icons.timelapse, size: 18, color: Colors.amber.shade900),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              w.coverageLimitationWarning!,
                              style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: Colors.amber.shade900),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                  const SizedBox(height: 14),
                  // Timeline Projections List
                  if (w.hourlyProjections.isNotEmpty)
                    SingleChildScrollView(
                      scrollDirection: Axis.horizontal,
                      child: Row(
                        children: w.hourlyProjections.map((p) => _buildHourlyTimelinePill(p)).toList(),
                      ),
                    ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),

          // SECTION 3: Interactive Work-Condition Assessment Controls
          Card(
            elevation: 3,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(14),
              side: const BorderSide(color: Color(0xFFD84315), width: 1.2),
            ),
            child: Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      const Icon(Icons.tune, color: Color(0xFFD84315)),
                      const SizedBox(width: 8),
                      const Text(
                        'Work-Condition Controls',
                        style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                      ),
                      const Spacer(),
                      if (_isRecalculatingWorker)
                        const SizedBox(
                          width: 16,
                          height: 16,
                          child: CircularProgressIndicator(strokeWidth: 2, color: Color(0xFFD84315)),
                        ),
                    ],
                  ),
                  const Text(
                    'Adjust farm labor conditions to recalculate personalized threshold limit & heat hazard:',
                    style: TextStyle(fontSize: 12, color: Colors.black54),
                  ),
                  const SizedBox(height: 14),

                  // Workload Category
                  Row(
                    children: [
                      const Expanded(
                        flex: 2,
                        child: Text('Physical Workload:', style: TextStyle(fontWeight: FontWeight.w600, fontSize: 13)),
                      ),
                      Expanded(
                        flex: 3,
                        child: DropdownButtonFormField<String>(
                          value: _workload,
                          decoration: InputDecoration(
                            contentPadding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                            border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
                          ),
                          items: const [
                            DropdownMenuItem(value: 'light', child: Text('Light (31.0°C limit)')),
                            DropdownMenuItem(value: 'moderate', child: Text('Moderate (28.0°C limit)')),
                            DropdownMenuItem(value: 'heavy', child: Text('Heavy (26.0°C limit)')),
                            DropdownMenuItem(value: 'very_heavy', child: Text('Very Heavy (25.0°C limit)')),
                          ],
                          onChanged: (val) {
                            if (val != null) {
                              setState(() => _workload = val);
                              _recalculateWorkerHeat();
                            }
                          },
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),

                  // Sun Exposure
                  Row(
                    children: [
                      const Expanded(
                        flex: 2,
                        child: Text('Sun Exposure:', style: TextStyle(fontWeight: FontWeight.w600, fontSize: 13)),
                      ),
                      Expanded(
                        flex: 3,
                        child: DropdownButtonFormField<String>(
                          value: _sunExposure,
                          decoration: InputDecoration(
                            contentPadding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                            border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
                          ),
                          items: const [
                            DropdownMenuItem(value: 'direct_sun', child: Text('Direct Sunlight (100%)')),
                            DropdownMenuItem(value: 'partial_shade', child: Text('Partial Shade (70%)')),
                            DropdownMenuItem(value: 'full_shade', child: Text('Full Shade / Indoor')),
                          ],
                          onChanged: (val) {
                            if (val != null) {
                              setState(() => _sunExposure = val);
                              _recalculateWorkerHeat();
                            }
                          },
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),

                  // Acclimatisation Toggle
                  SwitchListTile(
                    contentPadding: EdgeInsets.zero,
                    title: const Text('Worker Acclimatised to Heat', style: TextStyle(fontWeight: FontWeight.w600, fontSize: 13)),
                    subtitle: Text(
                      _isAcclimatised
                          ? 'Standard ACGIH / ISO 7243 screening threshold applied'
                          : 'Unacclimatised: Stricter threshold (-3°C) applied for first 7 days',
                      style: const TextStyle(fontSize: 11, color: Colors.black54),
                    ),
                    value: _isAcclimatised,
                    activeColor: const Color(0xFFD84315),
                    onChanged: (val) {
                      setState(() => _isAcclimatised = val);
                      _recalculateWorkerHeat();
                    },
                  ),

                  // Clothing Type
                  Row(
                    children: [
                      const Expanded(
                        flex: 2,
                        child: Text('Clothing Type:', style: TextStyle(fontWeight: FontWeight.w600, fontSize: 13)),
                      ),
                      Expanded(
                        flex: 3,
                        child: DropdownButtonFormField<String>(
                          value: _clothingType,
                          decoration: InputDecoration(
                            contentPadding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                            border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
                          ),
                          items: const [
                            DropdownMenuItem(value: 'standard_work_clothes', child: Text('Cotton Workwear (+0°C)')),
                            DropdownMenuItem(value: 'protective_coveralls', child: Text('Coveralls (+2°C CAV)')),
                            DropdownMenuItem(value: 'spray_suit_ppe', child: Text('Pesticide Suit (+3°C CAV)')),
                          ],
                          onChanged: (val) {
                            if (val != null) {
                              setState(() => _clothingType = val);
                              _recalculateWorkerHeat();
                            }
                          },
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),

                  // Duration Slider
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          const Text('Planned Shift Duration:', style: TextStyle(fontWeight: FontWeight.w600, fontSize: 13)),
                          Text('${_exposureDurationHours.toStringAsFixed(1)} hours', style: const TextStyle(fontWeight: FontWeight.bold, color: Color(0xFFD84315))),
                        ],
                      ),
                      Slider(
                        value: _exposureDurationHours,
                        min: 1.0,
                        max: 8.0,
                        divisions: 7,
                        activeColor: const Color(0xFFD84315),
                        label: '${_exposureDurationHours.toStringAsFixed(1)}h',
                        onChanged: (val) {
                          setState(() => _exposureDurationHours = val);
                          _recalculateWorkerHeat();
                        },
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),

          // SECTION 4: Risk Explanation & Contributing Factors
          Card(
            elevation: 2,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
            child: Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Risk Evaluation & Contributing Factors',
                    style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                  ),
                  const SizedBox(height: 8),
                  if (w.categorySelectionReason.isNotEmpty)
                    Text(
                      w.categorySelectionReason,
                      style: const TextStyle(fontSize: 13, height: 1.4, color: Colors.black87),
                    ),
                  const SizedBox(height: 10),
                  const Text('Key Environmental Drivers:', style: TextStyle(fontWeight: FontWeight.w600, fontSize: 12)),
                  const SizedBox(height: 4),
                  ...w.mainContributingFactors.map(
                    (factor) => Padding(
                      padding: const EdgeInsets.symmetric(vertical: 2.0),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text('• ', style: TextStyle(fontWeight: FontWeight.bold, color: Color(0xFFD84315))),
                          Expanded(child: Text(factor, style: const TextStyle(fontSize: 12, color: Colors.black87))),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 8),
                  if (w.workloadInteractionExplanation.isNotEmpty)
                    Container(
                      padding: const EdgeInsets.all(10),
                      decoration: BoxDecoration(
                        color: Colors.blueGrey.shade50,
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Text(
                        w.workloadInteractionExplanation,
                        style: const TextStyle(fontSize: 12, color: Colors.black87),
                      ),
                    ),
                  if (w.methodologyStandardsVersion.isNotEmpty) ...[
                    const SizedBox(height: 10),
                    Text(
                      'Standard: ${w.methodologyStandardsVersion}',
                      style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 11, color: Color(0xFFD84315)),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      w.thresholdMeaningExplanation,
                      style: const TextStyle(fontSize: 11, color: Colors.black87),
                    ),
                  ],
                  if (w.safetyGuaranteeDisclaimer.isNotEmpty) ...[
                    const SizedBox(height: 8),
                    Container(
                      padding: const EdgeInsets.all(8),
                      decoration: BoxDecoration(
                        color: Colors.orange.shade50,
                        borderRadius: BorderRadius.circular(6),
                        border: Border.all(color: Colors.orange.shade200),
                      ),
                      child: Text(
                        w.safetyGuaranteeDisclaimer,
                        style: TextStyle(fontSize: 10, color: Colors.brown.shade800, height: 1.3),
                      ),
                    ),
                  ],
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),

          // SECTION 5: Safety Guidance & Emergency Heat Illness Triage
          Card(
            elevation: 2,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
            child: Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Safety Guidance & Hydration Limits',
                    style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                  ),
                  const SizedBox(height: 10),
                  // Hydration Limit Alert (NIOSH Criteria)
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: const Color(0xFFE0F7FA),
                      borderRadius: BorderRadius.circular(10),
                      border: Border.all(color: Colors.cyan.shade300),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text('NIOSH Expert Hydration Protocol:', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: Colors.teal)),
                        const SizedBox(height: 4),
                        Text(
                          w.hydrationGuidance['rule_summary'] ?? 'Drink ~1 cup (250 ml) every 15-20 minutes during moderate to heavy labor under heat strain. For light work, drink according to thirst.',
                          style: const TextStyle(fontSize: 12, color: Colors.black87),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          w.hydrationGuidance['max_hourly_rate'] ?? 'Do not exceed 1 litre per hour to avoid water intoxication (hyponatremia).',
                          style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: Colors.red),
                        ),
                        if (w.hydrationGuidance['electrolyte_advice'] != null) ...[
                          const SizedBox(height: 2),
                          Text(
                            w.hydrationGuidance['electrolyte_advice'],
                            style: const TextStyle(fontSize: 11, color: Colors.black87),
                          ),
                        ],
                      ],
                    ),
                  ),
                  const SizedBox(height: 16),

                  // Emergency Triage Panel (Heat Exhaustion vs Heat Stroke)
                  const Text(
                    'EMERGENCY HEAT ILLNESS TRIAGE',
                    style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: Colors.red, letterSpacing: 0.5),
                  ),
                  const SizedBox(height: 8),
                  Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // Heat Exhaustion
                      Expanded(
                        child: Container(
                          padding: const EdgeInsets.all(10),
                          decoration: BoxDecoration(
                            color: Colors.orange.shade50,
                            borderRadius: BorderRadius.circular(10),
                            border: Border.all(color: Colors.orange.shade300),
                          ),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: const [
                              Text('Heat Exhaustion', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12, color: Colors.deepOrange)),
                              SizedBox(height: 4),
                              Text('• Heavy sweating\n• Cold, pale, clammy skin\n• Fast, weak pulse\n• Muscle cramps & nausea', style: TextStyle(fontSize: 11)),
                              SizedBox(height: 6),
                              Text('ACTION:\nMove to shade, loosen clothes. ONLY if fully conscious & able to swallow safely: sip salted water or ORS.', style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: Colors.brown)),
                            ],
                          ),
                        ),
                      ),
                      const SizedBox(width: 10),
                      // Heat Stroke
                      Expanded(
                        child: Container(
                          padding: const EdgeInsets.all(10),
                          decoration: BoxDecoration(
                            color: Colors.red.shade50,
                            borderRadius: BorderRadius.circular(10),
                            border: Border.all(color: Colors.red.shade400, width: 1.5),
                          ),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: const [
                              Text('Heat Stroke (108)', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12, color: Colors.red)),
                              SizedBox(height: 4),
                              Text('• High temp (>40°C)\n• Hot, red, dry skin\n• Confusion / delirium\n• Seizures or collapse', style: TextStyle(fontSize: 11)),
                              SizedBox(height: 6),
                              Text('CRITICAL ACTION:\nCALL 108 IMMEDIATELY!\nCool first, transport second. Drench in water.\nDO NOT give oral fluids if confused or unconscious (choking risk).', style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: Colors.red)),
                            ],
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  // Local Emergency Contacts
                  Container(
                    padding: const EdgeInsets.all(10),
                    decoration: BoxDecoration(
                      color: Colors.grey.shade100,
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: Colors.grey.shade300),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: const [
                        Text('Local Emergency Contacts:', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 11, color: Colors.black87)),
                        SizedBox(height: 4),
                        Text('• National Ambulance Service: 108 (Toll-free across Maharashtra)', style: TextStyle(fontSize: 11)),
                        Text('• Unified Emergency Helpline: 112', style: TextStyle(fontSize: 11)),
                        Text('• Kisan Call Centre / Farmer Helpline: 1800-180-1551', style: TextStyle(fontSize: 11)),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),

          // Legal Disclaimer
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: Colors.grey.shade100,
              borderRadius: BorderRadius.circular(8),
            ),
            child: Text(
              w.disclaimer.isNotEmpty ? w.disclaimer : 'Occupational heat screening based on ISO 7243 and ACGIH guidelines. Not a clinical device.',
              style: const TextStyle(fontSize: 10, color: Colors.black54),
            ),
          ),
          const SizedBox(height: 20),
        ],
      ),
    );
  }

  Widget _buildMiniMetric(String label, String val, IconData icon, {bool highlight = false}) {
    return Container(
      width: 100,
      padding: const EdgeInsets.all(8),
      decoration: BoxDecoration(
        color: highlight ? const Color(0xFFFFF3E0) : Colors.grey.shade50,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: highlight ? Colors.deepOrange : Colors.grey.shade300),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(icon, size: 14, color: highlight ? Colors.deepOrange : Colors.black54),
              const SizedBox(width: 4),
              Expanded(
                child: Text(
                  label,
                  style: TextStyle(fontSize: 10, color: highlight ? Colors.deepOrange : Colors.black54),
                  overflow: TextOverflow.ellipsis,
                ),
              ),
            ],
          ),
          const SizedBox(height: 4),
          Text(
            val,
            style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: highlight ? Colors.deepOrange : Colors.black87),
          ),
        ],
      ),
    );
  }

  Widget _buildHourlyTimelinePill(WorkerHourlyProjection p) {
    final color = _getHazardColor(p.hazardLevel);

    return Container(
      width: 85,
      margin: const EdgeInsets.only(right: 8),
      padding: const EdgeInsets.all(8),
      decoration: BoxDecoration(
        color: color.withOpacity(0.08),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: color, width: p.exceedsScreeningThreshold ? 1.5 : 0.8),
      ),
      child: Column(
        children: [
          Text(p.validTimeIst, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 11)),
          const SizedBox(height: 4),
          Text('${p.wbgtEffectiveC}°C', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: color)),
          const SizedBox(height: 2),
          Text('${p.airTempC}°C air', style: const TextStyle(fontSize: 9, color: Colors.black54)),
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

  // =========================================================================
  // CROP HEAT RISK TAB (6 SECTIONS)
  // =========================================================================
  Widget _buildCropHeatTab() {
    final c = _cropHeat!;
    final riskColor = _getHazardColor(c.overallCropHeatRisk);

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // SECTION 1: Crop Profile & Growth Stage Confirmation Dropdown
          Card(
            elevation: 2,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
            child: Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      const Icon(Icons.eco, color: Color(0xFF2E7D32)),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          '${c.cropCommonName.toUpperCase()} · ${c.cropVariety}',
                          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15),
                        ),
                      ),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                        decoration: BoxDecoration(
                          color: riskColor.withOpacity(0.12),
                          borderRadius: BorderRadius.circular(6),
                          border: Border.all(color: riskColor),
                        ),
                        child: Text(
                          'Risk: ${c.overallCropHeatRisk.toUpperCase()}',
                          style: TextStyle(fontWeight: FontWeight.bold, fontSize: 11, color: riskColor),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'DAS: ${c.daysAfterSowing} days · Area: ${c.cropAreaAcres} acres · Irrigation: ${c.irrigationStatus}',
                    style: const TextStyle(fontSize: 11, color: Colors.black87),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    'Soil: ${c.soilTexture} · ${c.soilProvenanceLabel}',
                    style: TextStyle(
                      fontSize: 11,
                      fontStyle: FontStyle.italic,
                      color: c.isSoilSynthetic ? Colors.blueGrey.shade700 : Colors.green.shade900,
                    ),
                  ),
                  if (c.isSeasonExpired || c.growthStageCode == null) ...[
                    const Divider(height: 20),
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: Colors.deepOrange.shade50,
                        borderRadius: BorderRadius.circular(10),
                        border: Border.all(color: Colors.deepOrange.shade400, width: 1.5),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: const [
                              Icon(Icons.event_busy, color: Colors.deepOrange, size: 20),
                              SizedBox(width: 8),
                              Text(
                                'CROP SEASON EXPIRED / UPDATE REQUIRED',
                                style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12, color: Colors.deepOrange),
                              ),
                            ],
                          ),
                          const SizedBox(height: 6),
                          Text(
                            c.seasonExpiryMessage ??
                                'Sowing date is ${c.daysAfterSowing} days ago (exceeds typical season bounds). Stage-specific heat risk and field interventions are suppressed.',
                            style: const TextStyle(fontSize: 12, height: 1.3, color: Colors.black87),
                          ),
                          const SizedBox(height: 10),
                          ElevatedButton.icon(
                            style: ElevatedButton.styleFrom(
                              backgroundColor: Colors.deepOrange,
                              foregroundColor: Colors.white,
                              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                            ),
                            icon: const Icon(Icons.edit_calendar, size: 16),
                            label: const Text('Update Sowing Date in Profile', style: TextStyle(fontSize: 12)),
                            onPressed: () {
                              final appState = AppState.instance;
                              if (appState.activeFarm != null) {
                                Navigator.push(
                                  context,
                                  MaterialPageRoute(
                                    builder: (_) => EditProfileScreen(farm: appState.activeFarm!),
                                  ),
                                ).then((_) => _loadInitialData());
                              }
                            },
                          ),
                        ],
                      ),
                    ),
                  ],
                  const Divider(height: 20),

                  // Interactive Stage Confirmation Selector
                  Row(
                    children: [
                      const Expanded(
                        flex: 2,
                        child: Text(
                          'Confirm Growth Stage:',
                          style: TextStyle(fontWeight: FontWeight.w600, fontSize: 13),
                        ),
                      ),
                      Expanded(
                        flex: 3,
                        child: DropdownButtonFormField<String>(
                          value: _selectedCropStage ?? (c.supportedStages.isNotEmpty ? c.supportedStages.first['stage_code'] : null),
                          decoration: InputDecoration(
                            contentPadding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                            border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
                          ),
                          items: c.supportedStages.map<DropdownMenuItem<String>>((s) {
                            return DropdownMenuItem<String>(
                              value: s['stage_code'],
                              child: Text('${s['stage_name_en']} (${s['crit_tmax']}°C)'),
                            );
                          }).toList(),
                          onChanged: (val) {
                            if (val != null) {
                              _recalculateCropHeat(val);
                            }
                          },
                        ),
                      ),
                    ],
                  ),
                  if (_isRecalculatingCrop)
                    const Padding(
                      padding: EdgeInsets.only(top: 8.0),
                      child: LinearProgressIndicator(color: Color(0xFF2E7D32)),
                    ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),

          // SECTION 2: Sourced Crop Thermal Analysis
          Card(
            elevation: 2,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
            child: Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Crop Thermal Analysis', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                  const SizedBox(height: 12),
                  // Thermal metrics row
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceAround,
                    children: [
                      _buildThermalCard('Critical Tmax', '${c.criticalTmaxThresholdC}°C', Icons.warning_amber, Colors.red),
                      _buildThermalCard('Forecast Tmax', '${c.tmaxForecastC}°C', Icons.wb_sunny, Colors.orange),
                      _buildThermalCard('Optimal Range', '${c.optimalTempMinC}-${c.optimalTempMaxC}°C', Icons.check_circle_outline, Colors.green),
                      _buildThermalCard('Base Temp', '${c.baseTempC}°C', Icons.ac_unit, Colors.blue),
                    ],
                  ),
                  const SizedBox(height: 14),
                  // Stress summary
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: Colors.grey.shade50,
                      borderRadius: BorderRadius.circular(10),
                      border: Border.all(color: Colors.grey.shade200),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Text('Exceedance Hours: ${c.hoursAboveCritical.toStringAsFixed(1)} hrs', style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 12)),
                            Text('Consecutive Hot Days: ${c.consecutiveHotDays}', style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 12)),
                          ],
                        ),
                        const SizedBox(height: 6),
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Text(
                              'Warm Night Hazard: ${c.warmNightRespirationHazard ? "YES (>22°C)" : "NO"}',
                              style: TextStyle(
                                fontSize: 12,
                                fontWeight: FontWeight.bold,
                                color: c.warmNightRespirationHazard ? Colors.deepOrange : Colors.green,
                              ),
                            ),
                            Text('Daily GDD: ${c.cumulativeHeatUnitsGdd.toStringAsFixed(1)} units', style: const TextStyle(fontSize: 12)),
                          ],
                        ),
                        const SizedBox(height: 6),
                        Text(
                          'Citation: ${c.evidenceCitation}',
                          style: const TextStyle(fontSize: 10, color: Colors.black54, fontStyle: FontStyle.italic),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),

          // SECTION 3: 4-Day Interactive Weather Outlook
          Card(
            elevation: 2,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
            child: Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('4-Day Crop Heat Outlook', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                  const SizedBox(height: 10),
                  if (c.dailyOutlook.isNotEmpty)
                    Column(
                      children: c.dailyOutlook.map((day) => _buildDailyOutlookTile(day)).toList(),
                    )
                  else
                    const Text('No 4-day outlook data available.', style: TextStyle(fontSize: 12, color: Colors.black54)),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),

          // SECTION 4: Agronomic Risk Explanation & Mechanism
          Card(
            elevation: 2,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
            child: Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Biological Mechanism & Vulnerability', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                  const SizedBox(height: 8),
                  Text(
                    c.stageBiologicalVulnerability.isNotEmpty ? c.stageBiologicalVulnerability : c.physiologicalMechanism,
                    style: const TextStyle(fontSize: 13, height: 1.4, color: Colors.black87),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),

          // SECTION 5: Field Recommendations with Evidence
          Card(
            elevation: 2,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
            child: Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Actionable Field Interventions', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                  const SizedBox(height: 10),
                  if (c.recommendedInterventions.isNotEmpty)
                    ...c.recommendedInterventions.map((rec) => _buildInterventionCard(rec)).toList()
                  else
                    const Text('No immediate agronomic heat interventions required.', style: TextStyle(fontSize: 12, color: Colors.black54)),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),

          // SECTION 6: Historical Trends
          Card(
            elevation: 2,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
            child: Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Recent Assessment History (Audited Logs)', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                  const SizedBox(height: 8),
                  if (c.assessmentHistory.isNotEmpty)
                    ...c.assessmentHistory.map((h) {
                      return Padding(
                        padding: const EdgeInsets.symmetric(vertical: 4.0),
                        child: Row(
                          children: [
                            Text(h['date'] ?? '', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12)),
                            const SizedBox(width: 12),
                            Text('${h['tmax_c']}°C max', style: const TextStyle(fontSize: 12, color: Colors.black54)),
                            const Spacer(),
                            Text(h['status'] ?? '', style: const TextStyle(fontSize: 12, color: Colors.black87)),
                          ],
                        ),
                      );
                    }).toList()
                  else
                    const Text('No prior heat assessments recorded yet for this farm plot.', style: TextStyle(fontSize: 12, color: Colors.black54)),
                ],
              ),
            ),
          ),
          const SizedBox(height: 20),
        ],
      ),
    );
  }

  Widget _buildThermalCard(String title, String val, IconData icon, Color col) {
    return Column(
      children: [
        Icon(icon, size: 20, color: col),
        const SizedBox(height: 4),
        Text(val, style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: col)),
        Text(title, style: const TextStyle(fontSize: 10, color: Colors.black54)),
      ],
    );
  }

  Widget _buildDailyOutlookTile(CropDailyOutlook day) {
    final col = _getHazardColor(day.riskCategory);

    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: col.withOpacity(0.06),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: col.withOpacity(0.4)),
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
              style: const TextStyle(fontSize: 11, color: Colors.black87),
            ),
          ),
          const SizedBox(width: 8),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text('${day.tmaxC}°C / ${day.tminC}°C', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 11)),
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

  Widget _buildInterventionCard(CropHeatIntervention rec) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: const Color(0xFFF1F8E9),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: Colors.green.shade400),
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
          if (rec.titleMr.isNotEmpty)
            Padding(
              padding: const EdgeInsets.only(top: 2.0),
              child: Text(
                rec.titleMr,
                style: TextStyle(fontSize: 11, color: Colors.green.shade800, fontStyle: FontStyle.italic),
              ),
            ),
          const SizedBox(height: 6),
          Text(rec.descriptionEn, style: const TextStyle(fontSize: 12, height: 1.3, color: Colors.black87)),
          const SizedBox(height: 6),
          if (rec.applicationMethod != null)
            Text(
              'Method & Dose: ${rec.applicationMethod} · ${rec.applicationDose ?? ""}',
              style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: Colors.black87),
            ),
          if (rec.infrastructureRequirements != null)
            Text(
              'Infrastructure: ${rec.infrastructureRequirements}',
              style: TextStyle(fontSize: 11, color: Colors.blueGrey.shade800),
            ),
          const SizedBox(height: 4),
          Text('Why: ${rec.whyAppropriate}', style: TextStyle(fontSize: 11, color: Colors.green.shade900)),
          const SizedBox(height: 4),
          Text(
            'Source: ${rec.evidenceCitation}${rec.sourcePageOrTable != null ? " (${rec.sourcePageOrTable})" : ""}',
            style: const TextStyle(fontSize: 10, color: Colors.black54, fontStyle: FontStyle.italic),
          ),
          if (rec.agronomistReviewer != null)
            Text(
              'Reviewer: ${rec.agronomistReviewer}',
              style: const TextStyle(fontSize: 10, color: Colors.black54),
            ),
        ],
      ),
    );
  }
}
