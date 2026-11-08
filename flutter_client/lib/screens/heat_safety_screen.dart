import 'package:flutter/material.dart';
import '../models/farm_models.dart';
import '../services/api_service.dart';
import '../localization/app_localizations.dart';

class HeatSafetyScreen extends StatefulWidget {
  final String lang;

  const HeatSafetyScreen({Key? key, required this.lang}) : super(key: key);

  @override
  State<HeatSafetyScreen> createState() => _HeatSafetyScreenState();
}

class _HeatSafetyScreenState extends State<HeatSafetyScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  WorkerHeatResponse? _heatData;
  bool _isLoading = true;
  String _workload = 'moderate';
  String _sunExposure = 'direct_sun';
  int _waterGlasses = 0;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    _loadHeatData();
  }

  Future<void> _loadHeatData() async {
    setState(() => _isLoading = true);
    final data = await ApiService.getWorkerHeatHazard(
      latitude: 18.1512,
      longitude: 74.5768,
      workload: _workload,
      sunExposure: _sunExposure,
    );
    if (mounted) {
      setState(() {
        _heatData = data;
        _isLoading = false;
      });
    }
  }

  Color _getHazardColor(String level) {
    switch (level.toLowerCase()) {
      case 'extreme':
        return const Color(0xFFB71C1C); // Deep Crimson
      case 'high':
        return const Color(0xFFD32F2F); // Red
      case 'moderate':
        return const Color(0xFFF57C00); // Amber Orange
      case 'low':
      default:
        return const Color(0xFF2E7D32); // Forest Green
    }
  }

  @override
  Widget build(BuildContext context) {
    final lang = widget.lang;

    return Scaffold(
      appBar: AppBar(
        title: Text(
          lang == 'mr' ? 'उष्णता व मजूर सुरक्षा' : 'Heat & Worker Safety',
          style: const TextStyle(fontWeight: FontWeight.bold),
        ),
        backgroundColor: const Color(0xFFD84315),
        foregroundColor: Colors.white,
        bottom: TabBar(
          controller: _tabController,
          indicatorColor: Colors.white,
          indicatorWeight: 3.5,
          labelStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
          tabs: [
            Tab(text: AppStrings.get('worker_heat_tab', lang: lang)),
            Tab(text: AppStrings.get('crop_heat_tab', lang: lang)),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          // 1. Worker Heat Safety Tab
          _isLoading
              ? const Center(child: CircularProgressIndicator(color: Color(0xFFD84315)))
              : ListView(
                  padding: const EdgeInsets.all(12.0),
                  children: [
                    // Main Gauge / Status Card
                    Card(
                      elevation: 3.0,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(14.0),
                        side: BorderSide(
                          color: _getHazardColor(_heatData?.currentHazardLevel ?? 'low'),
                          width: 2.0,
                        ),
                      ),
                      child: Padding(
                        padding: const EdgeInsets.all(16.0),
                        child: Column(
                          children: [
                            Text(
                              AppStrings.get('wbgt_title', lang: lang),
                              style: const TextStyle(fontSize: 16, color: Colors.black54),
                            ),
                            const SizedBox(height: 6),
                            Row(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                Text(
                                  '${_heatData?.maxWbgtEffectiveC.toStringAsFixed(1)}°C',
                                  style: TextStyle(
                                    fontSize: 44,
                                    fontWeight: FontWeight.bold,
                                    color: _getHazardColor(_heatData?.currentHazardLevel ?? 'low'),
                                  ),
                                ),
                                const SizedBox(width: 14),
                                Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                                  decoration: BoxDecoration(
                                    color: _getHazardColor(_heatData?.currentHazardLevel ?? 'low'),
                                    borderRadius: BorderRadius.circular(20),
                                  ),
                                  child: Text(
                                    _heatData?.currentHazardLevel.toUpperCase() ?? 'LOW',
                                    style: const TextStyle(
                                      color: Colors.white,
                                      fontWeight: FontWeight.bold,
                                      fontSize: 15,
                                    ),
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 8),
                            Text(
                              lang == 'mr'
                                  ? 'कामाची मर्यादा (थ्रेशोल्ड): ${_heatData?.screeningThresholdC}°C WBGT'
                                  : 'Screening Limit: ${_heatData?.screeningThresholdC}°C WBGT',
                              style: const TextStyle(fontSize: 14, color: Colors.black87),
                            ),
                          ],
                        ),
                      ),
                    ),

                    const SizedBox(height: 12),

                    // Workload Selector Buttons (Large Touch Targets >= 48dp)
                    Text(
                      AppStrings.get('workload_label', lang: lang),
                      style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 8),
                    Row(
                      children: [
                        Expanded(
                          child: OutlinedButton(
                            style: OutlinedButton.styleFrom(
                              minimumSize: const Size(0, 48),
                              backgroundColor: _workload == 'light' ? const Color(0xFFFFCCBC) : null,
                              side: BorderSide(color: _workload == 'light' ? const Color(0xFFD84315) : Colors.grey),
                            ),
                            onPressed: () {
                              setState(() => _workload = 'light');
                              _loadHeatData();
                            },
                            child: Text(AppStrings.get('light_work', lang: lang)),
                          ),
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: OutlinedButton(
                            style: OutlinedButton.styleFrom(
                              minimumSize: const Size(0, 48),
                              backgroundColor: _workload == 'moderate' ? const Color(0xFFFFCCBC) : null,
                              side: BorderSide(color: _workload == 'moderate' ? const Color(0xFFD84315) : Colors.grey),
                            ),
                            onPressed: () {
                              setState(() => _workload = 'moderate');
                              _loadHeatData();
                            },
                            child: Text(AppStrings.get('mod_work', lang: lang)),
                          ),
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: OutlinedButton(
                            style: OutlinedButton.styleFrom(
                              minimumSize: const Size(0, 48),
                              backgroundColor: _workload == 'heavy' ? const Color(0xFFFFCCBC) : null,
                              side: BorderSide(color: _workload == 'heavy' ? const Color(0xFFD84315) : Colors.grey),
                            ),
                            onPressed: () {
                              setState(() => _workload = 'heavy');
                              _loadHeatData();
                            },
                            child: Text(AppStrings.get('heavy_work', lang: lang)),
                          ),
                        ),
                      ],
                    ),

                    const SizedBox(height: 12),

                    // Sun / Shade Toggle
                    Row(
                      children: [
                        Expanded(
                          child: ElevatedButton.icon(
                            style: ElevatedButton.styleFrom(
                              minimumSize: const Size(0, 48),
                              backgroundColor: _sunExposure == 'direct_sun' ? const Color(0xFFD84315) : Colors.grey.shade200,
                              foregroundColor: _sunExposure == 'direct_sun' ? Colors.white : Colors.black87,
                            ),
                            onPressed: () {
                              setState(() => _sunExposure = 'direct_sun');
                              _loadHeatData();
                            },
                            icon: const Icon(Icons.wb_sunny_outlined),
                            label: Text(AppStrings.get('sun_exposure', lang: lang)),
                          ),
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: ElevatedButton.icon(
                            style: ElevatedButton.styleFrom(
                              minimumSize: const Size(0, 48),
                              backgroundColor: _sunExposure == 'shade' ? const Color(0xFF2E7D32) : Colors.grey.shade200,
                              foregroundColor: _sunExposure == 'shade' ? Colors.white : Colors.black87,
                            ),
                            onPressed: () {
                              setState(() => _sunExposure = 'shade');
                              _loadHeatData();
                            },
                            icon: const Icon(Icons.beach_access_outlined),
                            label: Text(AppStrings.get('shade_exposure', lang: lang)),
                          ),
                        ),
                      ],
                    ),

                    const SizedBox(height: 16),

                    // 0-6 Hour Timeline Projection (Horizontal Scroll)
                    Text(
                      lang == 'mr' ? '० ते ६ तास हवामान व उष्णता अंदाज' : '0 to 6 Hour Forecast Projection',
                      style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 8),
                    SizedBox(
                      height: 110,
                      child: ListView.builder(
                        scrollDirection: Axis.horizontal,
                        itemCount: _heatData?.projections.length ?? 0,
                        itemBuilder: (context, index) {
                          final p = _heatData!.projections[index];
                          final pColor = _getHazardColor(p.hazardLevel);
                          return Container(
                            width: 85,
                            margin: const EdgeInsets.only(right: 8),
                            padding: const EdgeInsets.all(8),
                            decoration: BoxDecoration(
                              color: pColor.withOpacity(0.1),
                              borderRadius: BorderRadius.circular(10),
                              border: BorderSide(color: pColor, width: 1.5),
                            ),
                            child: Column(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                Text(
                                  index == 0 ? (lang == 'mr' ? 'आता' : 'Now') : '+${index}h',
                                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
                                ),
                                const SizedBox(height: 4),
                                Text(
                                  '${p.wbgtEffectiveC.toStringAsFixed(1)}°',
                                  style: TextStyle(
                                    fontSize: 18,
                                    fontWeight: FontWeight.bold,
                                    color: pColor,
                                  ),
                                ),
                                const SizedBox(height: 2),
                                Text(
                                  '${p.airTempC.toStringAsFixed(0)}°C',
                                  style: const TextStyle(fontSize: 12, color: Colors.black54),
                                ),
                              ],
                            ),
                          );
                        },
                      ),
                    ),

                    const SizedBox(height: 16),

                    // Hydration Tracker (NIOSH 1 glass every 20 min)
                    Container(
                      padding: const EdgeInsets.all(14),
                      decoration: BoxDecoration(
                        color: const Color(0xFFE1F5FE),
                        borderRadius: BorderRadius.circular(12),
                        border: BorderSide(color: Colors.lightBlue.shade300),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: const [
                              Icon(Icons.local_drink, color: Color(0xFF0288D1), size: 24),
                              SizedBox(width: 8),
                              Expanded(
                                child: Text(
                                  'पाणी पिण्याची आठवण (NIOSH मानक)',
                                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Color(0xFF01579B)),
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 6),
                          Text(
                            AppStrings.get('hydration_reminder', lang: lang),
                            style: const TextStyle(fontSize: 14, color: Colors.black87),
                          ),
                          const SizedBox(height: 10),
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              Text(
                                '${AppStrings.get('glasses_logged', lang: lang)} $_waterGlasses (${_waterGlasses * 250} ml)',
                                style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                              ),
                              ElevatedButton(
                                style: ElevatedButton.styleFrom(
                                  backgroundColor: const Color(0xFF0288D1),
                                  foregroundColor: Colors.white,
                                ),
                                onPressed: () {
                                  setState(() => _waterGlasses += 1);
                                },
                                child: Text(AppStrings.get('water_drank_btn', lang: lang)),
                              )
                            ],
                          ),
                        ],
                      ),
                    ),

                    const SizedBox(height: 16),

                    // Non-Medical Disclaimer Banner
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: Colors.amber.shade50,
                        borderRadius: BorderRadius.circular(8),
                        border: BorderSide(color: Colors.amber.shade400),
                      ),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Icon(Icons.info_outline, color: Colors.amber, size: 20),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              AppStrings.get('non_medical_disclaimer', lang: lang),
                              style: const TextStyle(fontSize: 13, color: Colors.black87),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),

          // 2. Crop Heat Risk Tab
          ListView(
            padding: const EdgeInsets.all(12.0),
            children: [
              Card(
                elevation: 2.0,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12.0),
                  side: const BorderSide(color: Color(0xFFD84315), width: 1.5),
                ),
                child: Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: const [
                          CircleAvatar(
                            radius: 20,
                            backgroundColor: Color(0xFFFFCCBC),
                            child: Icon(Icons.thermostat, color: Color(0xFFD84315)),
                          ),
                          SizedBox(width: 12),
                          Expanded(
                            child: Text(
                              'कापूस व सोयाबीन उष्माघात जोखीम',
                              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 12),
                      Text(
                        lang == 'mr'
                            ? 'आजचे कमाल तापमान ३९.५°से. (मर्यादा ३८.०°से.)'
                            : 'Forecast Peak Temp: 39.5°C (Critical Limit: 38.0°C)',
                        style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Color(0xFFD84315)),
                      ),
                      const SizedBox(height: 6),
                      Text(
                        lang == 'mr'
                            ? 'फुलोरा अवस्थेत तापमान ३८°से. पेक्षा जास्त राहिल्यास परागकण सुकतात व पाते/फुलगळ होते.'
                            : 'High temperatures during flowering cause pollen desiccation and boll shedding.',
                        style: const TextStyle(fontSize: 14, color: Colors.black87),
                      ),
                      const SizedBox(height: 6),
                      const Text(
                        'संदर्भ: ICAR-CICR नागपूर वार्षिक वैज्ञानिक अहवाल २०२३',
                        style: TextStyle(fontSize: 12, color: Colors.black54, fontStyle: FontStyle.italic),
                      ),
                    ],
                  ),
                ),
              ),

              const SizedBox(height: 12),

              // Warm Night Respiration Card
              Card(
                elevation: 2.0,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12.0),
                  side: const BorderSide(color: Color(0xFFF57C00), width: 1.5),
                ),
                child: Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: const [
                          Icon(Icons.nightlight_round, color: Color(0xFFF57C00), size: 24),
                          SizedBox(width: 10),
                          Expanded(
                            child: Text(
                              'उबदार रात्र श्वसन जोखीम (>२४°से.)',
                              style: TextStyle(fontSize: 17, fontWeight: FontWeight.bold),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 8),
                      Text(
                        lang == 'mr'
                            ? 'रात्रीचे तापमान २५.५°से. राहण्याचा अंदाज आहे. यामुळे पिकाची अंधार-श्वसनक्रिया वाढून कर्बोदके खर्च होतात.'
                            : 'Forecast night min 25.5°C exceeds the 24°C threshold, increasing dark respiration.',
                        style: const TextStyle(fontSize: 14),
                      ),
                    ],
                  ),
                ),
              ),

              const SizedBox(height: 12),

              // Recommended Agronomic Interventions
              Card(
                elevation: 2.0,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12.0)),
                child: Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        AppStrings.get('recommended_action', lang: lang),
                        style: const TextStyle(fontSize: 17, fontWeight: FontWeight.bold, color: Color(0xFF2E7D32)),
                      ),
                      const Divider(height: 16),
                      const ListTile(
                        leading: Icon(Icons.water, color: Color(0xFF0288D1)),
                        title: Text('संध्याकाळी सूक्ष्म सिंचन (Micro-irrigation)'),
                        subtitle: Text('पिकाच्या पानांभोवतालचे तापमान २-३°से. कमी करण्यासाठी संध्याकाळी तुषार सिंचनाने हलके पाणी द्यावे.'),
                      ),
                      const ListTile(
                        leading: Icon(Icons.science, color: Color(0xFF6A1B9A)),
                        title: Text('२% पोटॅशियम नायट्रेटची फवारणी'),
                        subtitle: Text('उष्णतेचा ताण सहन करण्यासाठी १०० लिटर पाण्यात २ किलो १३:०:४५ विरघळवून फवारणी करावी (ICAR शिफारस).'),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
