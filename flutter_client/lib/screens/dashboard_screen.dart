import 'package:flutter/material.dart';
import '../models/farm_models.dart';
import '../services/api_service.dart';
import '../widgets/risk_card.dart';
import '../localization/app_localizations.dart';

class DashboardScreen extends StatefulWidget {
  final String lang;
  final VoidCallback onToggleLang;

  const DashboardScreen({
    Key? key,
    required this.lang,
    required this.onToggleLang,
  }) : super(key: key);

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  YieldAssessment? _assessment;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    setState(() => _isLoading = true);
    final data = await ApiService.getYieldAssessment(farmId: 'farm_baramati_demo');
    if (mounted) {
      setState(() {
        _assessment = data;
        _isLoading = false;
      });
    }
  }

  IconData _getIconForDimension(String dimension) {
    switch (dimension) {
      case 'weather_dry_spell':
        return Icons.water_drop_outlined;
      case 'excess_rainfall_waterlogging':
        return Icons.flood_outlined;
      case 'soil_constraint':
        return Icons.terrain_outlined;
      case 'pest_disease_watch':
        return Icons.pest_control_outlined;
      default:
        return Icons.agriculture;
    }
  }

  String _getTitleForDimension(String dimension) {
    final lang = widget.lang;
    switch (dimension) {
      case 'weather_dry_spell':
        return AppStrings.get('weather_dry_spell', lang: lang);
      case 'excess_rainfall_waterlogging':
        return AppStrings.get('excess_rainfall', lang: lang);
      case 'soil_constraint':
        return AppStrings.get('soil_constraint', lang: lang);
      case 'pest_disease_watch':
        return AppStrings.get('pest_disease_watch', lang: lang);
      default:
        return dimension;
    }
  }

  @override
  Widget build(BuildContext context) {
    final lang = widget.lang;

    return Scaffold(
      appBar: AppBar(
        title: Text(
          AppStrings.get('app_title', lang: lang),
          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 22),
        ),
        backgroundColor: const Color(0xFF2E7D32),
        foregroundColor: Colors.white,
        actions: [
          TextButton.icon(
            onPressed: widget.onToggleLang,
            icon: const Icon(Icons.language, color: Colors.white, size: 20),
            label: Text(
              AppStrings.get('switch_lang', lang: lang),
              style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 16),
            ),
          ),
          IconButton(
            icon: const Icon(Icons.refresh, size: 26),
            onPressed: _loadData,
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator(color: Color(0xFF2E7D32)))
          : RefreshIndicator(
              onRefresh: _loadData,
              child: ListView(
                padding: const EdgeInsets.only(bottom: 24.0),
                children: [
                  // Farm & Crop Status Header Banner
                  Container(
                    margin: const EdgeInsets.all(12.0),
                    padding: const EdgeInsets.all(16.0),
                    decoration: BoxDecoration(
                      gradient: const LinearGradient(
                        colors: [Color(0xFF2E7D32), Color(0xFF388E3C)],
                        begin: Alignment.topLeft,
                        end: Alignment.bottomRight,
                      ),
                      borderRadius: BorderRadius.circular(14.0),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            const Text(
                              'बारामती, पुणे | ३.० एकर',
                              style: TextStyle(color: Colors.white70, fontSize: 15),
                            ),
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                              decoration: BoxDecoration(
                                color: Colors.white24,
                                borderRadius: BorderRadius.circular(8),
                              ),
                              child: const Text(
                                'पायलट चाचणी',
                                style: TextStyle(color: Colors.white, fontSize: 12),
                              ),
                            )
                          ],
                        ),
                        const SizedBox(height: 6),
                        Text(
                          lang == 'mr' ? 'पीक: सोयाबीन (JS-335)' : 'Crop: Soybean (JS-335)',
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 22,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          '${AppStrings.get('stage', lang: lang)}: ${lang == 'mr' ? _assessment?.cropStageNameMr : _assessment?.cropStageNameEn} (${_assessment?.das} ${AppStrings.get('days_after_sowing', lang: lang)})',
                          style: const TextStyle(color: Color(0xFFE8F5E9), fontSize: 16),
                        ),
                      ],
                    ),
                  ),

                  // 5 Risk Cards
                  if (_assessment != null)
                    ..._assessment!.risks.map((r) => RiskCard(
                          title: _getTitleForDimension(r.riskDimension),
                          riskLevel: r.riskLevel,
                          iconData: _getIconForDimension(r.riskDimension),
                          drivers: r.drivers,
                          actions: r.recommendedActions,
                          lang: lang,
                        )),

                  // Historical Baseline Card
                  Card(
                    elevation: 2.0,
                    margin: const EdgeInsets.symmetric(vertical: 8.0, horizontal: 12.0),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12.0),
                      side: const BorderSide(color: Color(0xFF90CAF9), width: 1.5),
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
                                backgroundColor: Color(0xFFE3F2FD),
                                child: Icon(Icons.bar_chart, color: Color(0xFF1976D2), size: 24),
                              ),
                              SizedBox(width: 12),
                              Expanded(
                                child: Text(
                                  'जिल्हा सरासरी उत्पादन संदर्भ (APY)',
                                  style: TextStyle(
                                    fontSize: 18,
                                    fontWeight: FontWeight.bold,
                                    color: Color(0xFF0D47A1),
                                  ),
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 10),
                          Text(
                            lang == 'mr'
                                ? 'पुणे जिल्हा १० वर्षांची सरासरी: १.६२ टन / हेक्टर (± ०.२८)'
                                : 'Pune District 10-Year APY Average: 1.62 t/ha (± 0.28)',
                            style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
                          ),
                          const SizedBox(height: 6),
                          Text(
                            lang == 'mr'
                                ? 'टीप: हा जिल्हास्तरीय अधिकृत संदर्भ आहे. अचूक शेत-पातळीवरील संख्यात्मक अंदाज CCE कापणी प्रयोगांच्या आकडेवारीनंतरच उपलब्ध होईल.'
                                : 'Notice: Official district baseline derived from APY records. Farm-level numerical yield prediction is gated pending verified CCE harvest labels.',
                            style: const TextStyle(fontSize: 13, color: Colors.black54),
                          ),
                        ],
                      ),
                    ),
                  )
                ],
              ),
            ),
    );
  }
}
