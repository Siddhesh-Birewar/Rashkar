import 'package:flutter/material.dart';

import '../../../../shared/widgets/app_decorations.dart';
import '../../../../shared/widgets/app_spacing.dart';
import '../../models/scheme_models.dart';

/// Colour and icon accent for each scheme category.
Color schemeCategoryColor(String category) {
  switch (category) {
    case 'Crop Insurance':
      return const Color(0xFF00695C);
    case 'Financial Assistance':
      return const Color(0xFF2E7D32);
    case 'Loans':
      return const Color(0xFF1565C0);
    case 'Irrigation':
      return const Color(0xFF0277BD);
    case 'Soil Health':
      return const Color(0xFF5D4037);
    case 'Machinery':
      return const Color(0xFF546E7A);
    case 'Seeds & Fertilizers':
      return const Color(0xFF6A1B9A);
    case 'Infrastructure':
      return const Color(0xFFE65100);
    case 'State Schemes':
      return const Color(0xFFAD1457);
    default:
      return AppDecorations.leafGreen;
  }
}

IconData schemeCategoryIcon(String category) {
  switch (category) {
    case 'Crop Insurance':
      return Icons.shield_outlined;
    case 'Financial Assistance':
      return Icons.account_balance_wallet_outlined;
    case 'Loans':
      return Icons.credit_card_outlined;
    case 'Irrigation':
      return Icons.water_drop_outlined;
    case 'Soil Health':
      return Icons.science_outlined;
    case 'Machinery':
      return Icons.agriculture_outlined;
    case 'Seeds & Fertilizers':
      return Icons.grass_outlined;
    case 'Infrastructure':
      return Icons.warehouse_outlined;
    case 'State Schemes':
      return Icons.location_city_outlined;
    default:
      return Icons.account_balance_outlined;
  }
}

/// A compact Government Scheme card shown in the dashboard grid.
class SchemeCard extends StatelessWidget {
  final GovernmentScheme scheme;
  final VoidCallback onTap;

  const SchemeCard({super.key, required this.scheme, required this.onTap});

  @override
  Widget build(BuildContext context) {
    final accent = schemeCategoryColor(scheme.category);
    return InkWell(
      onTap: onTap,
      borderRadius: AppBorderRadius.card,
      child: Container(
        decoration: AppDecorations.accentCard(accentColor: accent),
        padding: AppSpacing.paddingAllMD,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                CircleAvatar(
                  radius: 18,
                  backgroundColor: accent.withValues(alpha: 0.12),
                  foregroundColor: accent,
                  child: Icon(schemeCategoryIcon(scheme.category), size: 20),
                ),
                AppSpacing.horizontalSpaceSM,
                Expanded(
                  child: Text(
                    scheme.schemeName,
                    style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 15),
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
              ],
            ),
            AppSpacing.verticalSpaceSM,
            Wrap(
              spacing: AppSpacing.xs,
              runSpacing: AppSpacing.xs,
              children: [
                _chip(scheme.category, accent),
                _chip(scheme.governmentLevel, Colors.blueGrey),
                if (scheme.state != null && scheme.state!.isNotEmpty)
                  _chip(scheme.state!, Colors.indigo),
                if (!scheme.isVerified) _chip('Not verified', Colors.orange),
              ],
            ),
            if (scheme.description != null && scheme.description!.isNotEmpty) ...[
              AppSpacing.verticalSpaceSM,
              Text(
                scheme.description!,
                style: const TextStyle(fontSize: 13, color: Colors.black87),
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _chip(String label, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.10),
        borderRadius: AppBorderRadius.pill,
      ),
      child: Text(
        label,
        style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: color),
      ),
    );
  }
}
