import 'package:flutter/material.dart';
import '../models/farm_models.dart';
import '../services/app_state.dart';
import 'my_crop_screen.dart';
import 'heat_safety_screen.dart';
import 'extra_income_screen.dart';
import 'crop_loss_screen.dart';
import 'ask_rashkar_screen.dart';
import 'farm_registration_screen.dart';
import 'edit_profile_screen.dart';

class HomeScreen extends StatefulWidget {
  final VoidCallback? onOpenRegistration;

  const HomeScreen({Key? key, this.onOpenRegistration}) : super(key: key);

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  @override
  void initState() {
    super.initState();
    AppState.instance.addListener(_onStateChange);
  }

  @override
  void dispose() {
    AppState.instance.removeListener(_onStateChange);
    super.dispose();
  }

  void _onStateChange() {
    if (mounted) setState(() {});
  }

  Future<void> _refresh() async {
    await AppState.instance.refreshFarms();
  }

  @override
  Widget build(BuildContext context) {
    final appState = AppState.instance;
    final summary = appState.activeFarm;

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
              summary != null ? summary.locationDisplay : 'Maharashtra, India',
              style: const TextStyle(fontSize: 12, color: Colors.white70),
            )
          ],
        ),
        backgroundColor: const Color(0xFF1B5E20),
        foregroundColor: Colors.white,
        actions: [
          if (appState.allFarms.isNotEmpty)
            PopupMenuButton<String>(
              icon: const Icon(Icons.swap_horiz, color: Colors.white),
              tooltip: 'Switch Farm',
              onSelected: (value) async {
                if (value == '__register__') {
                  Navigator.push(
                    context,
                    MaterialPageRoute(builder: (_) => const FarmRegistrationScreen()),
                  );
                } else if (value == '__edit__') {
                  if (summary != null) {
                    Navigator.push(
                      context,
                      MaterialPageRoute(builder: (_) => EditProfileScreen(farm: summary)),
                    ).then((_) => _refresh());
                  }
                } else if (value == '__clear__') {
                  appState.clearSession();
                } else {
                  await appState.selectFarmById(value);
                }
              },
              itemBuilder: (context) {
                final items = <PopupMenuEntry<String>>[];
                items.add(
                  const PopupMenuItem<String>(
                    enabled: false,
                    child: Text('REGISTERED FARMS', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12)),
                  ),
                );
                for (final f in appState.allFarms) {
                  final isSelected = f.farmId == appState.activeFarmId;
                  items.add(
                    PopupMenuItem<String>(
                      value: f.farmId,
                      child: Row(
                        children: [
                          Icon(
                            isSelected ? Icons.check_circle : Icons.circle_outlined,
                            color: isSelected ? const Color(0xFF1B5E20) : Colors.grey,
                            size: 18,
                          ),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              '${f.farmName} (${f.activeCropName ?? "Crop"})',
                              overflow: TextOverflow.ellipsis,
                              style: TextStyle(
                                fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  );
                }
                items.add(const PopupMenuDivider());
                if (summary != null) {
                  items.add(
                    const PopupMenuItem<String>(
                      value: '__edit__',
                      child: Row(
                        children: [
                          Icon(Icons.edit, color: Color(0xFF1B5E20), size: 18),
                          SizedBox(width: 8),
                          Text('Edit Active Farm Profile', style: TextStyle(fontWeight: FontWeight.bold)),
                        ],
                      ),
                    ),
                  );
                }
                items.add(
                  const PopupMenuItem<String>(
                    value: '__register__',
                    child: Row(
                      children: [
                        Icon(Icons.add_circle_outline, color: Color(0xFF1B5E20), size: 18),
                        SizedBox(width: 8),
                        Text('Register New Farm', style: TextStyle(fontWeight: FontWeight.bold)),
                      ],
                    ),
                  ),
                );
                items.add(
                  const PopupMenuItem<String>(
                    value: '__clear__',
                    child: Row(
                      children: [
                        Icon(Icons.restart_alt, color: Colors.black54, size: 18),
                        SizedBox(width: 8),
                        Text('Start Fresh / Select Screen'),
                      ],
                    ),
                  ),
                );
                return items;
              },
            ),
          IconButton(
            icon: const Icon(Icons.add_location_alt_outlined),
            tooltip: 'Register New Farm',
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => const FarmRegistrationScreen()),
              );
            },
          ),
          IconButton(
            icon: const Icon(Icons.refresh),
            tooltip: 'Refresh',
            onPressed: _refresh,
          ),
        ],
      ),
      body: appState.isLoading
          ? const Center(child: CircularProgressIndicator(color: Color(0xFF1B5E20)))
          : summary == null
              ? _buildCleanStartScreen()
              : RefreshIndicator(
                  onRefresh: _refresh,
                  child: SingleChildScrollView(
                    physics: const AlwaysScrollableScrollPhysics(),
                    padding: const EdgeInsets.all(16.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        _buildGreetingCard(summary),
                        const SizedBox(height: 16),
                        _buildFarmGlanceCard(summary),
                        const SizedBox(height: 16),
                        _buildWeatherSummaryCard(summary),
                        const SizedBox(height: 24),
                        const Text(
                          'WHAT WOULD YOU LIKE TO DO?',
                          style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: Color(0xFF333333), letterSpacing: 0.8),
                        ),
                        const SizedBox(height: 12),
                        _buildFeatureGrid(),
                        const SizedBox(height: 20),
                        _buildAskRashkarBanner(),
                        const SizedBox(height: 16),
                        if (summary.activeAlerts.isNotEmpty) ...[
                          const Text(
                            "TODAY'S IMPORTANT ADVISORIES",
                            style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: Color(0xFF333333), letterSpacing: 0.8),
                          ),
                          const SizedBox(height: 8),
                          ...summary.activeAlerts.map((a) => _buildAlertItem(a)).toList(),
                          const SizedBox(height: 16),
                        ],
                        Center(
                          child: Text(
                            'Data updated: ${summary.dataLastUpdated}',
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

  /// Clean starting state when no farm has been loaded or selected yet
  Widget _buildCleanStartScreen() {
    final appState = AppState.instance;
    return SingleChildScrollView(
      padding: const EdgeInsets.all(20.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Hero Welcome Card
          Card(
            elevation: 2,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
            color: const Color(0xFFE8F5E9),
            child: Padding(
              padding: const EdgeInsets.all(24.0),
              child: Column(
                children: [
                  const Icon(Icons.agriculture, size: 56, color: Color(0xFF1B5E20)),
                  const SizedBox(height: 12),
                  const Text(
                    'Welcome to Rashkar',
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      fontSize: 24,
                      fontWeight: FontWeight.bold,
                      color: Color(0xFF1B5E20),
                    ),
                  ),
                  const SizedBox(height: 8),
                  const Text(
                    'Cloud-based Climate-Smart Agriculture Platform for Maharashtra',
                    textAlign: TextAlign.center,
                    style: TextStyle(fontSize: 14, color: Colors.black87),
                  ),
                  const SizedBox(height: 16),
                  const Text(
                    'To get started with personalized yield intelligence, worker heat safety, crop stress advisories, and PMFBY loss evidence, set up your farm profile.',
                    textAlign: TextAlign.center,
                    style: TextStyle(fontSize: 13, color: Colors.black54),
                  ),
                  const SizedBox(height: 20),
                  SizedBox(
                    width: double.infinity,
                    height: 50,
                    child: ElevatedButton.icon(
                      onPressed: () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(builder: (_) => const FarmRegistrationScreen()),
                        );
                      },
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xFF1B5E20),
                        foregroundColor: Colors.white,
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                        elevation: 2,
                      ),
                      icon: const Icon(Icons.add_location_alt, size: 22),
                      label: const Text(
                        'Register Your Farm',
                        style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 20),

          // Quick Demo option
          Card(
            elevation: 1,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
            child: Padding(
              padding: const EdgeInsets.all(16.0),
              child: Row(
                children: [
                  const CircleAvatar(
                    backgroundColor: Color(0xFFFFF3E0),
                    child: Icon(Icons.explore, color: Color(0xFFE65100)),
                  ),
                  const SizedBox(width: 14),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: const [
                        Text(
                          'Want to test immediately?',
                          style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                        ),
                        Text(
                          'Load Baramati (Pune) Pilot Farm (Soybean, 2.5 acres)',
                          style: TextStyle(fontSize: 12, color: Colors.black54),
                        ),
                      ],
                    ),
                  ),
                  OutlinedButton(
                    onPressed: () async {
                      await appState.loadDemoFarm();
                    },
                    style: OutlinedButton.styleFrom(
                      foregroundColor: const Color(0xFF1B5E20),
                      side: const BorderSide(color: Color(0xFF1B5E20)),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                    ),
                    child: const Text('Load Demo'),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 20),

          // If there are existing farms in the database, allow 1-tap select
          if (appState.allFarms.isNotEmpty) ...[
            const Text(
              'OR SELECT A SAVED FARM',
              style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: Color(0xFF333333), letterSpacing: 0.8),
            ),
            const SizedBox(height: 8),
            ...appState.allFarms.map((farm) {
              return Card(
                margin: const EdgeInsets.only(bottom: 10),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                  child: Row(
                    children: [
                      const CircleAvatar(
                        backgroundColor: Color(0xFFE8F5E9),
                        child: Icon(Icons.location_on, color: Color(0xFF1B5E20)),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(farm.farmName, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                            const SizedBox(height: 2),
                            Text('${farm.activeCropName ?? "Crop"} · ${farm.locationDisplay}', style: const TextStyle(color: Colors.black54, fontSize: 13)),
                          ],
                        ),
                      ),
                      ElevatedButton(
                        onPressed: () {
                          appState.setActiveFarm(farm);
                        },
                        style: ElevatedButton.styleFrom(
                          backgroundColor: const Color(0xFF1B5E20),
                          foregroundColor: Colors.white,
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                        ),
                        child: const Text('Open'),
                      ),
                      const SizedBox(width: 6),
                      IconButton(
                        icon: const Icon(Icons.edit, color: Color(0xFF1B5E20)),
                        tooltip: 'Edit Profile',
                        onPressed: () {
                          Navigator.push(
                            context,
                            MaterialPageRoute(builder: (_) => EditProfileScreen(farm: farm)),
                          ).then((_) => _refresh());
                        },
                      ),
                    ],
                  ),
                ),
              );
            }).toList(),
            const SizedBox(height: 20),
          ],

          // Coverage Highlights
          const Text(
            'DATA & MODEL FOUNDATION',
            style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: Color(0xFF333333), letterSpacing: 0.8),
          ),
          const SizedBox(height: 8),
          _buildFoundationTile(
            Icons.map_outlined,
            '36 Maharashtra Districts & 307 Talukas',
            'Full official taluka centroid coordinates for high-precision local weather matching.',
          ),
          _buildFoundationTile(
            Icons.bar_chart,
            '17,916 APY Historical Yield Records',
            'Authentic district-level historical crop yields for empirical risk scoring.',
          ),
          _buildFoundationTile(
            Icons.cloud_outlined,
            'IMD 0.25° Gridded Rainfall Normals',
            '1991–2020 official IMD Pune daily normals driving moisture anomaly detection.',
          ),
          _buildFoundationTile(
            Icons.thermostat,
            'Worker & Crop Heat Intelligence',
            'Liljegren et al. WBGT physics & ICAR-grounded crop stage thermal thresholds.',
          ),
        ],
      ),
    );
  }

  Widget _buildFoundationTile(IconData icon, String title, String subtitle) {
    return Card(
      elevation: 0,
      color: Colors.white,
      margin: const EdgeInsets.only(bottom: 8),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(10),
        side: BorderSide(color: Colors.grey.shade200),
      ),
      child: ListTile(
        leading: Icon(icon, color: const Color(0xFF1B5E20), size: 24),
        title: Text(title, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.bold)),
        subtitle: Text(subtitle, style: const TextStyle(fontSize: 11, color: Colors.black54)),
      ),
    );
  }

  Widget _buildGreetingCard(FarmSummary summary) {
    return Card(
      elevation: 0,
      color: Colors.white,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: const BorderSide(color: Color(0xFFE0E0E0)),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Good day, ${summary.farmerName}!',
                    style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: Color(0xFF1B5E20)),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    '${summary.farmName} · ${summary.locationDisplay}',
                    style: const TextStyle(fontSize: 13, color: Colors.black54),
                  ),
                ],
              ),
            ),
            ElevatedButton.icon(
              onPressed: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(builder: (_) => EditProfileScreen(farm: summary)),
                ).then((_) => _refresh());
              },
              icon: const Icon(Icons.edit, size: 16),
              label: const Text('Edit Profile'),
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFF1B5E20),
                foregroundColor: Colors.white,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildFarmGlanceCard(FarmSummary s) {
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
                      Text(s.estimatedStageName ?? 'Growth Stage', style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14)),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            SizedBox(
              width: double.infinity,
              child: OutlinedButton.icon(
                onPressed: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(builder: (_) => EditProfileScreen(farm: s)),
                  ).then((_) => _refresh());
                },
                icon: const Icon(Icons.edit_location_alt, size: 16),
                label: const Text('Edit Crop, Sowing Date or Farm Location'),
                style: OutlinedButton.styleFrom(
                  foregroundColor: const Color(0xFF1B5E20),
                  side: const BorderSide(color: Color(0xFF1B5E20)),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildWeatherSummaryCard(FarmSummary summary) {
    final w = summary.weatherSummary;
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
                  const SizedBox(height: 2),
                  Text(
                    w['source'] ?? 'IMD Maharashtra Station',
                    style: const TextStyle(fontSize: 11, color: Colors.black54),
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
            const SizedBox(height: 12),
            Text(
              title,
              style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: Color(0xFF1B5E20)),
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
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: InkWell(
        onTap: () {
          Navigator.push(context, MaterialPageRoute(builder: (_) => const AskRashkarScreen()));
        },
        borderRadius: BorderRadius.circular(16),
        child: Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            gradient: const LinearGradient(
              colors: [Color(0xFF1B5E20), Color(0xFF2E7D32)],
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
            ),
            borderRadius: BorderRadius.circular(16),
          ),
          child: Row(
            children: [
              const CircleAvatar(
                backgroundColor: Colors.white24,
                radius: 22,
                child: Icon(Icons.chat_bubble_outline, color: Colors.white, size: 24),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: const [
                    Text(
                      'Ask Rashkar AI Assistant',
                      style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 16),
                    ),
                    SizedBox(height: 2),
                    Text(
                      'Ask about crop care, heat stress or weather',
                      style: TextStyle(color: Colors.white70, fontSize: 12),
                    ),
                  ],
                ),
              ),
              const Icon(Icons.arrow_forward_ios, color: Colors.white70, size: 16),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildAlertItem(Map<String, dynamic> alert) {
    final urgency = alert['urgency'] ?? 'medium';
    final Color badgeColor = urgency == 'high' ? Colors.red.shade700 : const Color(0xFFE65100);

    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      elevation: 1,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(color: badgeColor.withOpacity(0.3)),
      ),
      child: Padding(
        padding: const EdgeInsets.all(12.0),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(Icons.warning_amber_rounded, color: badgeColor, size: 24),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    alert['title'] ?? 'Alert',
                    style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: badgeColor),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    alert['message'] ?? '',
                    style: const TextStyle(fontSize: 13, color: Colors.black87),
                  ),
                  if (alert['source'] != null) ...[
                    const SizedBox(height: 4),
                    Text(
                      'Source: ${alert['source']}',
                      style: const TextStyle(fontSize: 11, color: Colors.black45, fontStyle: FontStyle.italic),
                    ),
                  ]
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
