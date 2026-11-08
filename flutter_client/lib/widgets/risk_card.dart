import 'package:flutter/material.dart';

class RiskCard extends StatelessWidget {
  final String title;
  final String riskLevel;
  final IconData iconData;
  final List<String> drivers;
  final List<Map<String, dynamic>> actions;
  final String lang;

  const RiskCard({
    Key? key,
    required this.title,
    required this.riskLevel,
    required this.iconData,
    required this.drivers,
    required this.actions,
    this.lang = 'mr',
  }) : super(key: key);

  Color _getLevelColor(String level) {
    switch (level.toLowerCase()) {
      case 'critical':
      case 'high':
        return const Color(0xFFD32F2F); // Deep Red
      case 'moderate':
        return const Color(0xFFF57C00); // Amber Orange
      case 'low':
      default:
        return const Color(0xFF2E7D32); // Forest Green
    }
  }

  String _getLevelText(String level) {
    if (lang == 'mr') {
      switch (level.toLowerCase()) {
        case 'critical':
          return 'अति-गंभीर';
        case 'high':
          return 'तीव्र जोखीम';
        case 'moderate':
          return 'मध्यम दक्षता';
        case 'low':
        default:
          return 'कमी जोखीम';
      }
    } else {
      switch (level.toLowerCase()) {
        case 'critical':
          return 'Critical';
        case 'high':
          return 'High Risk';
        case 'moderate':
          return 'Moderate';
        case 'low':
        default:
          return 'Low Risk';
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final color = _getLevelColor(riskLevel);

    return Card(
      elevation: 2.0,
      margin: const EdgeInsets.symmetric(vertical: 8.0, horizontal: 12.0),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12.0),
        side: BorderSide(color: color.withOpacity(0.4), width: 1.5),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                CircleAvatar(
                  radius: 22,
                  backgroundColor: color.withOpacity(0.15),
                  child: Icon(iconData, color: color, size: 26),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(
                    title,
                    style: const TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                      color: Color(0xFF1B2E1D),
                    ),
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: color,
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: Text(
                    _getLevelText(riskLevel),
                    style: const TextStyle(
                      color: Colors.white,
                      fontWeight: FontWeight.bold,
                      fontSize: 13,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            if (drivers.isNotEmpty)
              ...drivers.map(
                (d) => Padding(
                  padding: const EdgeInsets.only(bottom: 6.0),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text('• ', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                      Expanded(
                        child: Text(
                          d,
                          style: const TextStyle(fontSize: 15, color: Color(0xFF333333)),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            if (actions.isNotEmpty) ...[
              const Divider(height: 20),
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: const Color(0xFFF1F8E9),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        const Icon(Icons.check_circle_outline, color: Color(0xFF2E7D32), size: 18),
                        const SizedBox(width: 6),
                        Text(
                          lang == 'mr' ? 'कृषी सल्ला:' : 'Agricultural Advisory:',
                          style: const TextStyle(fontWeight: FontWeight.bold, color: Color(0xFF2E7D32)),
                        ),
                      ],
                    ),
                    const SizedBox(height: 4),
                    ...actions.map(
                      (act) => Text(
                        lang == 'mr'
                            ? (act['title_mr'] ?? act['title_en'] ?? '')
                            : (act['title_en'] ?? ''),
                        style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600),
                      ),
                    ),
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
