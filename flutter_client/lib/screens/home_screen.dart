import 'package:flutter/material.dart';
import '../models/farm_models.dart';
import '../services/api_service.dart';
import 'my_crop_screen.dart';
import 'heat_safety_screen.dart';
import 'extra_income_screen.dart';
import 'crop_loss_screen.dart';
import 'ask_rashkar_screen.dart';
import 'farm_registration_screen.dart';

class HomeScreen extends StatefulWidget {
  final VoidCallback? onOpenRegistration;

  const HomeScreen({Key? key, this.onOpenRegistration}) : super(key: key);

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  FarmSummary? _summary;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _fetchSummary();
  }

  Future<void> _fetchSummary() async {
    setState(() => _isLoading = true);
    final s = await ApiService.getFarmSummary();
    if (mounted) {
      setState(() {
        _summary = s;
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF6F8F6),
      appBar: AppBar(
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'RASHKAR',
              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 20, letterSpacing: 1.2),
            ),
            Text(
              _summary != null ? _summary!.locationDisplay : 'Maharashtra',
              style: const TextStyle(fontSize: 12, color: Colors.white70),
            )
          ],
        ),
        backgroundColor: const Color(0xFF1B5E20),
        foregroundColor: Colors.white,
        actions: [
          IconButton(
            icon: const Icon(Icons.add_location_alt_outlined),
            tooltip: 'Add / Register Farm',
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => const FarmRegistrationScreen()),
              ).then((_) => _fetchSummary());
            },
          ),
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _fetchSummary,
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator(color: Color(0xFF1B5E20)))
          : RefreshIndicator(
              onRefresh: _fetchSummary,
              child: SingleChildScrollView(
                physics: const AlwaysScrollableScrollPhysics(),
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    // Greeting & farm identity
                    _buildGreetingCard(),
                    const SizedBox(height: 16),

                    // Farm at a glance card
                    _buildFarmGlanceCard(),
                    const SizedBox(height: 16),

                    // Today's Farm Conditions (Weather)
                    _buildWeatherSummaryCard(),
                    const SizedBox(height: 24),

                    // WHAT WOULD YOU LIKE TO DO? (4 Large Buttons)
                    const Text(
                      'WHAT WOULD YOU LIKE TO DO?',
                      style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: Color(0xFF333333), letterSpacing: 0.8),
                    ),
                    const SizedBox(height: 12),
                    _buildFeatureGrid(),
                    const SizedBox(height: 20),

                    // ASK RASHKAR (Entry point)
                    _buildAskRashkarBanner(),
                    const SizedBox(height: 16),

                    // Active Alerts (1 to 3 items)
                    if (_summary != null && _summary!.activeAlerts.isNotEmpty) ...[
                      const Text(
                        'TODAY\'S IMPORTANT ADVISORIES',
                        style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: Color(0xFF333333), letterSpacing: 0.8),
                      ),
                      const SizedBox(height: 8),
                      ..._summary!.activeAlerts.map((a) => _buildAlertItem(a)).toList(),
                      const SizedBox(height: 16),
                    ],

                    // Footer data freshness
                    Center(
                      child: Text(
                        'Data updated: ${_summary?.dataLastUpdated ?? "Recent"}',
                        style: const TextStyle(fontSize: 12, color: Colors.black54),
                      ),
                    ),
                    const SizedBox(height: 20),
                  ],
                ),
              ),
            ),
    );
  }

  Widget _buildGreetingCard() {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Good day, ${_summary?.farmerName ?? "Farmer"}!',
              style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: Color(0xFF1B5E20)),
            ),
            const Text(
              'Your farm at a glance',
              style: TextStyle(fontSize: 14, color: Colors.black54),
            ),
          ],
        ),
        const CircleAvatar(
          radius: 22,
          backgroundColor: Color(0xFFE8F5E9),
          child: Icon(Icons.person, color: Color(0xFF1B5E20), size: 28),
        )
      ],
    );
  }

  Widget _buildFarmGlanceCard() {
    final s = _summary!;
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
                Row(
                  children: [
                    const Icon(Icons.eco, color: Color(0xFF2E7D32), size: 24),
                    const SizedBox(width: 8),
                    Text(
                      s.activeCropName ?? 'Active Crop',
                      style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                    ),
                  ],
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: const Color(0xFFE8F5E9),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text(
                    '${s.plantedAreaAcres ?? s.totalAreaAcres ?? 2.5} acres',
                    style: const TextStyle(fontWeight: FontWeight.bold, color: Color(0xFF1B5E20)),
                  ),
                )
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
                      const SizedBox(height: 2),
                      Text(s.sowingDate ?? '15 June 2024', style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14)),
                    ],
                  ),
                ),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text('Growth Stage', style: TextStyle(fontSize: 12, color: Colors.black54)),
                      const SizedBox(height: 2),
                      Text(s.estimatedStageName ?? 'Pod Development', style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14)),
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

  Widget _buildWeatherSummaryCard() {
    final w = _summary!.weatherSummary;
    return Card(
      elevation: 1,
      color: const Color(0xFFF1F8E9),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Row(
          children: [
            const Icon(Icons.wb_cloudy_outlined, size: 40, color: Color(0xFF33691E)),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    '${w['temperature_c']}°C · ${w['condition']}',
                    style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Color(0xFF1B5E20)),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    'Humidity ${w['relative_humidity_pct']}% · Wind ${w['wind_speed_kmh']} km/h',
                    style: const TextStyle(fontSize: 13, color: Colors.black87),
                  ),
                ],
              ),
            ),
            const Icon(Icons.arrow_forward_ios, size: 16, color: Colors.black45)
          ],
        ),
      ),
    );
  }

  Widget _buildFeatureGrid() {
    return Column(
      children: [
        Row(
          children: [
            Expanded(
              child: _buildLargeFeatureButton(
                icon: Icons.grass,
                title: 'My Crop',
                subtitle: 'Health & Yield',
                color: const Color(0xFF2E7D32),
                onTap: () {
                  Navigator.push(context, MaterialPageRoute(builder: (_) => const MyCropScreen()));
                },
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: _buildLargeFeatureButton(
                icon: Icons.wb_sunny_outlined,
                title: 'Heat Safety',
                subtitle: 'Worker & Crop',
                color: const Color(0xFFD84315),
                onTap: () {
                  Navigator.push(context, MaterialPageRoute(builder: (_) => const HeatSafetyScreen()));
                },
              ),
            ),
          ],
        ),
        const SizedBox(height: 12),
        Row(
          children: [
            Expanded(
              child: _buildLargeFeatureButton(
                icon: Icons.savings_outlined,
                title: 'Extra Income',
                subtitle: 'Agri-Enterprises',
                color: const Color(0xFF00695C),
                onTap: () {
                  Navigator.push(context, MaterialPageRoute(builder: (_) => const ExtraIncomeScreen()));
                },
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: _buildLargeFeatureButton(
                icon: Icons.assignment_late_outlined,
                title: 'Crop Loss',
                subtitle: 'PMFBY Evidence',
                color: const Color(0xFF4527A0),
                onTap: () {
                  Navigator.push(context, MaterialPageRoute(builder: (_) => const CropLossScreen()));
                },
              ),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildLargeFeatureButton({
    required IconData icon,
    required String title,
    required String subtitle,
    required Color color,
    required VoidCallback onTap,
  }) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(16),
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 20, horizontal: 16),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: color.withOpacity(0.3), width: 1.5),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.04),
              blurRadius: 8,
              offset: const Offset(0, 2),
            ),
          ],
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            CircleAvatar(
              radius: 20,
              backgroundColor: color.withOpacity(0.12),
              child: Icon(icon, color: color, size: 24),
            ),
            const SizedBox(height: 14),
            Text(
              title,
              style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.black87),
            ),
            const SizedBox(height: 2),
            Text(
              subtitle,
              style: const TextStyle(fontSize: 12, color: Colors.black54),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildAskRashkarBanner() {
    return InkWell(
      onTap: () {
        Navigator.push(context, MaterialPageRoute(builder: (_) => const AskRashkarScreen()));
      },
      borderRadius: BorderRadius.circular(16),
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          gradient: const LinearGradient(
            colors: [Color(0xFF1B5E20), Color(0xFF2E7D32)],
          ),
          borderRadius: BorderRadius.circular(16),
        ),
        child: Row(
          children: [
            const CircleAvatar(
              backgroundColor: Colors.white24,
              child: Icon(Icons.chat_bubble_outline, color: Colors.white),
            ),
            const SizedBox(width: 14),
            const Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'ASK RASHKAR ASSISTANT',
                    style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 15),
                  ),
                  SizedBox(height: 2),
                  Text(
                    'Ask questions about your crop or weather',
                    style: TextStyle(color: Colors.white70, fontSize: 12),
                  ),
                ],
              ),
            ),
            const Icon(Icons.arrow_forward, color: Colors.white),
          ],
        ),
      ),
    );
  }

  Widget _buildAlertItem(Map<String, dynamic> alert) {
    final isHigh = alert['urgency'] == 'high';
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: isHigh ? const Color(0xFFFFF3E0) : const Color(0xFFE8F5E9),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: isHigh ? Colors.orange : Colors.green, width: 0.8),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(
            isHigh ? Icons.warning_amber_rounded : Icons.info_outline,
            color: isHigh ? Colors.deepOrange : Colors.green[800],
            size: 22,
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  alert['title'] ?? '',
                  style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: isHigh ? Colors.deepOrange[900] : Colors.green[900]),
                ),
                const SizedBox(height: 2),
                Text(
                  alert['message'] ?? '',
                  style: const TextStyle(fontSize: 13, color: Colors.black87),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
