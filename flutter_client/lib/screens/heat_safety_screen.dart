import 'package:flutter/material.dart';
import '../models/farm_models.dart';
import '../services/api_service.dart';
import '../services/app_state.dart';

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

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    AppState.instance.addListener(_onStateChange);
    _loadData();
  }

  @override
  void dispose() {
    AppState.instance.removeListener(_onStateChange);
    _tabController.dispose();
    super.dispose();
  }

  void _onStateChange() {
    _loadData();
  }

  Future<void> _loadData() async {
    setState(() => _isLoading = true);
    final appState = AppState.instance;

    final w = await ApiService.getWorkerHeatHazard(
      latitude: appState.activeLatitude,
      longitude: appState.activeLongitude,
      taluka: appState.activeTaluka,
    );
    final c = await ApiService.getCropHeatHazard(
      cropCode: appState.activeCropCode,
      stageCode: 'stage_pod_development',
    );

    if (mounted) {
      setState(() {
        _workerHeat = w;
        _cropHeat = c;
        _isLoading = false;
      });
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
          IconButton(icon: const Icon(Icons.refresh), onPressed: _loadData),
        ],
        bottom: TabBar(
          controller: _tabController,
          indicatorColor: Colors.white,
          labelColor: Colors.white,
          unselectedLabelColor: Colors.white70,
          tabs: const [
            Tab(icon: Icon(Icons.person_outline), text: 'Worker Heat Safety'),
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

  // --- Pathway 1: Worker Heat Risk ---
  Widget _buildWorkerHeatTab() {
    final w = _workerHeat!;
    final appState = AppState.instance;

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Location Context Badge
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
            decoration: BoxDecoration(
              color: const Color(0xFFFFF3E0),
              borderRadius: BorderRadius.circular(10),
              border: Border.all(color: Colors.orange.shade200),
            ),
            child: Row(
              children: [
                const Icon(Icons.location_on, size: 16, color: Color(0xFFD84315)),
                const SizedBox(width: 6),
                Expanded(
                  child: Text(
                    'Location: ${appState.activeTaluka}, ${appState.activeDistrict} (${appState.activeLatitude.toStringAsFixed(3)}°N, ${appState.activeLongitude.toStringAsFixed(3)}°E)',
                    style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Color(0xFFD84315)),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 14),

          // Plain Language Question
          const Text(
            'Is the weather suitable for outdoor farm work over the next few hours?',
            style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Color(0xFF333333)),
          ),
          const SizedBox(height: 12),

          // Hazard Banner
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: const Color(0xFFFFF3E0),
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: Colors.orange, width: 1.5),
            ),
            child: Row(
              children: [
                const Icon(Icons.warning_amber_rounded, color: Colors.deepOrange, size: 36),
                const SizedBox(width: 14),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Hazard Level: ${w.hazardLevel.toUpperCase()}',
                        style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: Colors.deepOrange),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        w.advice,
                        style: const TextStyle(fontSize: 13, color: Colors.black87),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 20),

          // Sun vs Shade Differential
          const Text(
            'SUN VS SHADE DIFFERENTIAL',
            style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: Colors.black54, letterSpacing: 0.8),
          ),
          const SizedBox(height: 8),
          Row(
            children: [
              Expanded(
                child: _buildMetricCard(
                  title: 'In Direct Sun',
                  tempStr: '${w.wbgtSunC}°C',
                  subtitle: 'Outdoor Heat Stress Proxy',
                  color: Colors.deepOrange,
                  icon: Icons.wb_sunny,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: _buildMetricCard(
                  title: 'Under Shade',
                  tempStr: '${w.wbgtShadeC}°C',
                  subtitle: 'Tree/Shed Heat Stress Proxy',
                  color: Colors.green[700]!,
                  icon: Icons.park_outlined,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Text(
            'Working under shade reduces thermal strain by ${(w.wbgtSunC - w.wbgtShadeC).toStringAsFixed(1)}°C.',
            style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: Color(0xFF1B5E20)),
          ),
          const SizedBox(height: 20),

          // Weather observations used
          Card(
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
            child: Padding(
              padding: const EdgeInsets.all(14),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Input Weather Baseline', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                  const SizedBox(height: 6),
                  Text('Air Temperature: ${w.airTempC}°C · Relative Humidity: ${w.rhPct}%', style: const TextStyle(fontSize: 13, color: Colors.black87)),
                  Text('Methodology: ${w.methodology}', style: const TextStyle(fontSize: 12, color: Colors.black54)),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),

          // Safety Boundaries & Disclaimer
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: Colors.grey.withOpacity(0.1),
              borderRadius: BorderRadius.circular(12),
            ),
            child: const Text(
              'Safety Notice: Heat stress proxies are calculated using meteorological observations and Liljegren et al. (2008) wet-bulb globe temperature formulas. This is an occupational screening advisory, not a clinical wearable monitor. Always rest and hydrate if fatigued.',
              style: TextStyle(fontSize: 12, color: Colors.black54, fontStyle: FontStyle.italic),
            ),
          ),
        ],
      ),
    );
  }

  // --- Pathway 2: Crop Heat Risk ---
  Widget _buildCropHeatTab() {
    final c = _cropHeat!;
    final isSafe = c.riskLevel == 'low';
    final appState = AppState.instance;

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Plain Language Question
          const Text(
            'Could heat affect my crop at its current growth stage?',
            style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Color(0xFF333333)),
          ),
          const SizedBox(height: 12),

          // Crop Risk Card
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: isSafe ? const Color(0xFFE8F5E9) : const Color(0xFFFFEBEE),
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: isSafe ? Colors.green : Colors.red, width: 1.5),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      'Crop: ${appState.activeCropName.toUpperCase()} (${c.stageCode.replaceAll("stage_", "").replaceAll("_", " ").toUpperCase()})',
                      style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15, color: isSafe ? Colors.green[900] : Colors.red[900]),
                    ),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                      decoration: BoxDecoration(
                        color: isSafe ? Colors.green : Colors.red,
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Text(
                        isSafe ? 'SAFE' : 'ELEVATED HEAT',
                        style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 11),
                      ),
                    )
                  ],
                ),
                const SizedBox(height: 12),
                Text(
                  isSafe
                      ? 'Maximum forecasted temperature (${c.maxForecastTempC}°C) remains below the critical physiological threshold (${c.criticalThresholdC}°C).'
                      : 'Temperatures exceed critical threshold (${c.criticalThresholdC}°C) for ${c.exceedanceHours} consecutive hours during sensitive flowering.',
                  style: const TextStyle(fontSize: 14, color: Colors.black87),
                ),
              ],
            ),
          ),
          const SizedBox(height: 20),

          // Sourced Agronomic Threshold Card
          Card(
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Stage-Specific Thermal Threshold', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
                  const SizedBox(height: 8),
                  Text('Critical Upper Limit: ${c.criticalThresholdC}°C', style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600, color: Color(0xFFD84315))),
                  const SizedBox(height: 4),
                  Text(
                    'Physiological Risk for ${appState.activeCropName}: Flower abortion, reduced pollen viability, or accelerated senescence occur when temperatures exceed ${c.criticalThresholdC}°C.',
                    style: const TextStyle(fontSize: 13, color: Colors.black87),
                  ),
                  const Divider(height: 20),
                  Text('Verified Source: ${c.citation}', style: const TextStyle(fontSize: 12, color: Colors.black54)),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMetricCard({
    required String title,
    required String tempStr,
    required String subtitle,
    required Color color,
    required IconData icon,
  }) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: color.withOpacity(0.3), width: 1.5),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(title, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: Colors.black87)),
              Icon(icon, color: color, size: 20),
            ],
          ),
          const SizedBox(height: 8),
          Text(tempStr, style: TextStyle(fontSize: 26, fontWeight: FontWeight.bold, color: color)),
          const SizedBox(height: 4),
          Text(subtitle, style: const TextStyle(fontSize: 11, color: Colors.black54)),
        ],
      ),
    );
  }
}
