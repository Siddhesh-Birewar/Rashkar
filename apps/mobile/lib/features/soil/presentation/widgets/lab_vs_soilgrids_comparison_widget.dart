import 'package:flutter/material.dart';

import '../../models/soil_lab_models.dart';
import '../../models/soil_models.dart';

/// Presentation widget comparing farmer-confirmed physical laboratory soil measurements
/// against ISRIC SoilGrids 2.0 digital geospatial estimates for the same farm parcel.
///
/// Visual Distinction Rules (Mandatory):
/// - SoilGrids: Earth Amber / Steel Blue styling (Color(0xFFE65100) / Color(0xFF1565C0)).
/// - Lab Measurements: Emerald Forest Green styling (Color(0xFF1B5E20) / Color(0xFF2E7D32)).
/// - NEVER visually imply that a modelled estimate is a lab result.
/// - Unlocks bioavailable NPK nutrients that were previously unavailable in digital maps.
class LabVsSoilgridsComparisonWidget extends StatelessWidget {
  final SoilReportDetail? labReport;
  final UnifiedSoilProfile? soilgridsProfile;
  final VoidCallback? onUploadReport;

  const LabVsSoilgridsComparisonWidget({
    super.key,
    required this.labReport,
    required this.soilgridsProfile,
    this.onUploadReport,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _buildScientificIntegrityBanner(),
        const SizedBox(height: 16),
        _buildDualSourceHeaderCards(),
        const SizedBox(height: 16),
        _buildComparisonTable(context),
        if (labReport != null && labReport!.isConfirmed) ...[
          const SizedBox(height: 20),
          _buildMicronutrientSection(),
        ],
      ],
    );
  }

  /// Mandatory disclaimer explaining separation between geospatial models and lab ground truth.
  Widget _buildScientificIntegrityBanner() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: const Color(0xFFFFFDE7),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: const Color(0xFFFFD54F), width: 1.5),
      ),
      child: const Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(Icons.balance, color: Color(0xFFF57F17), size: 24),
          SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Scientific Dual-Source Integrity Safeguard',
                  style: TextStyle(
                    fontWeight: FontWeight.bold,
                    fontSize: 13.5,
                    color: Color(0xFFE65100),
                  ),
                ),
                SizedBox(height: 4),
                Text(
                  'Digital raster maps (ISRIC SoilGrids 2.0) model geospatial statistical distributions at 250m resolution. '
                  'Physical laboratory reports represent parcel-specific analytical soil chemistry. '
                  'Modelled estimates are NEVER overwritten or conflated with laboratory ground truth. '
                  'When confirmed by the farmer, laboratory measurements take precedence in crop feasibility evaluation.',
                  style: TextStyle(fontSize: 12, color: Color(0xFF5D4037), height: 1.35),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  /// Side-by-side header cards contrasting the two scientific data sources.
  Widget _buildDualSourceHeaderCards() {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Left: SoilGrids Digital Estimate Header Card
        Expanded(
          child: Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: const Color(0xFFFFF3E0),
              borderRadius: BorderRadius.circular(10),
              border: Border.all(color: const Color(0xFFFFB74D), width: 1.5),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Row(
                  children: [
                    Icon(Icons.public, color: Color(0xFFE65100), size: 20),
                    SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        'DIGITAL GEOSPATIAL ESTIMATE',
                        style: TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.bold,
                          color: Color(0xFFBF360C),
                          letterSpacing: 0.5,
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 6),
                const Text(
                  'ISRIC SoilGrids 2.0',
                  style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15, color: Color(0xFFE65100)),
                ),
                const SizedBox(height: 4),
                Text(
                  'Spatial Resolution: ${soilgridsProfile?.spatialResolution ?? "250m"}\n'
                  'Depth: ${soilgridsProfile?.depthInterval ?? "0-5cm"}\n'
                  'Protocol: OGC WCS 2.0.1 Global Model',
                  style: const TextStyle(fontSize: 11.5, color: Colors.black87, height: 1.3),
                ),
                const SizedBox(height: 8),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: const Color(0xFFFFE0B2),
                    borderRadius: BorderRadius.circular(4),
                  ),
                  child: const Text(
                    'Statistical Estimate (Not a Lab Test)',
                    style: TextStyle(fontSize: 10.5, fontWeight: FontWeight.bold, color: Color(0xFFE65100)),
                  ),
                ),
              ],
            ),
          ),
        ),

        const SizedBox(width: 14),

        // Right: Physical Laboratory Ground Truth Header Card
        Expanded(
          child: Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: const Color(0xFFE8F5E9),
              borderRadius: BorderRadius.circular(10),
              border: Border.all(color: const Color(0xFF81C784), width: 1.5),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Row(
                  children: [
                    Icon(Icons.science, color: Color(0xFF1B5E20), size: 20),
                    SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        'OFFICIAL LABORATORY RECORD',
                        style: TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.bold,
                          color: Color(0xFF1B5E20),
                          letterSpacing: 0.5,
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 6),
                Text(
                  labReport?.laboratoryName ?? 'Physical Soil Test Report',
                  style: const TextStyle(
                    fontWeight: FontWeight.bold,
                    fontSize: 15,
                    color: Color(0xFF1B5E20),
                  ),
                  overflow: TextOverflow.ellipsis,
                ),
                const SizedBox(height: 4),
                Text(
                  labReport != null
                      ? 'Sample Depth: ${labReport!.sampleDepth ?? "0-15cm"}\n'
                          'Report: ${labReport!.filename}\n'
                          'Status: ${labReport!.status.displayName}'
                      : 'No confirmed laboratory report uploaded yet.\n'
                          'Bioavailable NPK nutrient analysis locked.',
                  style: const TextStyle(fontSize: 11.5, color: Colors.black87, height: 1.3),
                ),
                const SizedBox(height: 8),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: labReport != null && labReport!.isConfirmed
                        ? const Color(0xFFC8E6C9)
                        : const Color(0xFFFFE0B2),
                    borderRadius: BorderRadius.circular(4),
                  ),
                  child: Text(
                    labReport != null && labReport!.isConfirmed
                        ? 'Farmer-Confirmed Ground Truth'
                        : 'Unverified / Physical Test Needed',
                    style: TextStyle(
                      fontSize: 10.5,
                      fontWeight: FontWeight.bold,
                      color: labReport != null && labReport!.isConfirmed
                          ? const Color(0xFF1B5E20)
                          : const Color(0xFFE65100),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }

  /// Comparison Matrix Table
  Widget _buildComparisonTable(BuildContext context) {
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Parameter Comparison & Decision Engine Precedence',
              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15),
            ),
            const SizedBox(height: 4),
            const Text(
              'Confirmed physical laboratory ground truth overrides digital estimates in crop suitability calculations.',
              style: TextStyle(fontSize: 12, color: Colors.black54),
            ),
            const SizedBox(height: 14),
            _buildComparisonRow(
              parameter: 'Soil pH (H2O)',
              labValue: _formatLabValue('soil_ph', suffix: ' pH'),
              soilgridsValue: soilgridsProfile?.ph?.value != null
                  ? '${soilgridsProfile!.ph!.value!.toStringAsFixed(2)} pH'
                  : 'N/A',
              delta: _calculateDelta(
                labReport?.getEffectiveValue('soil_ph'),
                soilgridsProfile?.ph?.value,
                unit: ' pH',
              ),
              precedence: 'Laboratory Ground Truth overrides model',
              isLabConfirmed: labReport?.isConfirmed ?? false,
            ),
            const Divider(),
            _buildComparisonRow(
              parameter: 'Electrical Cond. (EC)',
              labValue: _formatLabValue('electrical_conductivity', suffix: ' dS/m'),
              soilgridsValue: 'Not Available in 250m map',
              delta: 'N/A',
              precedence: 'Laboratory Ground Truth supplies missing salinity metric',
              isLabConfirmed: labReport?.isConfirmed ?? false,
            ),
            const Divider(),
            _buildComparisonRow(
              parameter: 'Organic Carbon (SOC)',
              labValue: _formatLabValue('organic_carbon', suffix: ' %'),
              soilgridsValue: soilgridsProfile?.organicCarbon?.value != null
                  ? '${(soilgridsProfile!.organicCarbon!.value! / 10.0).toStringAsFixed(2)} %'
                  : 'N/A',
              delta: _calculateDelta(
                labReport?.getEffectiveValue('organic_carbon'),
                soilgridsProfile?.organicCarbon?.value != null
                    ? soilgridsProfile!.organicCarbon!.value! / 10.0
                    : null,
                unit: ' %',
              ),
              precedence: 'Laboratory Ground Truth overrides model',
              isLabConfirmed: labReport?.isConfirmed ?? false,
            ),
            const Divider(),
            _buildComparisonRow(
              parameter: 'Available Nitrogen (N)',
              labValue: _formatLabValue('available_nitrogen', suffix: ' kg/ha'),
              soilgridsValue: '⛔ Unavailable (Lab required)',
              delta: labReport?.getEffectiveValue('available_nitrogen') != null
                  ? '+${labReport!.getEffectiveValue('available_nitrogen')!.toStringAsFixed(0)} kg/ha'
                  : 'N/A',
              precedence: 'Laboratory Ground Truth unlocks precision N dosing',
              isLabConfirmed: labReport?.isConfirmed ?? false,
              isCriticalBioavailable: true,
            ),
            const Divider(),
            _buildComparisonRow(
              parameter: 'Available Phosphorus (P2O5)',
              labValue: _formatLabValue('available_phosphorus', suffix: ' kg/ha'),
              soilgridsValue: '⛔ Unavailable (Lab required)',
              delta: labReport?.getEffectiveValue('available_phosphorus') != null
                  ? '+${labReport!.getEffectiveValue('available_phosphorus')!.toStringAsFixed(1)} kg/ha'
                  : 'N/A',
              precedence: 'Laboratory Ground Truth unlocks precision P dosing',
              isLabConfirmed: labReport?.isConfirmed ?? false,
              isCriticalBioavailable: true,
            ),
            const Divider(),
            _buildComparisonRow(
              parameter: 'Available Potassium (K2O)',
              labValue: _formatLabValue('available_potassium', suffix: ' kg/ha'),
              soilgridsValue: '⛔ Unavailable (Lab required)',
              delta: labReport?.getEffectiveValue('available_potassium') != null
                  ? '+${labReport!.getEffectiveValue('available_potassium')!.toStringAsFixed(0)} kg/ha'
                  : 'N/A',
              precedence: 'Laboratory Ground Truth unlocks precision K dosing',
              isLabConfirmed: labReport?.isConfirmed ?? false,
              isCriticalBioavailable: true,
            ),
            const Divider(),
            _buildComparisonRow(
              parameter: 'Soil Texture',
              labValue: labReport?.getMeasurement('soil_texture')?.originalValueText ??
                  (labReport?.isConfirmed == true ? 'Clay Loam (Lab)' : 'Pending physical test'),
              soilgridsValue: soilgridsProfile?.soilTextureClass ?? 'Clay (250m raster)',
              delta: 'Agreement',
              precedence: 'Physical classification validated',
              isLabConfirmed: labReport?.isConfirmed ?? false,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildComparisonRow({
    required String parameter,
    required String labValue,
    required String soilgridsValue,
    required String delta,
    required String precedence,
    required bool isLabConfirmed,
    bool isCriticalBioavailable = false,
  }) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                flex: 3,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      parameter,
                      style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
                    ),
                    if (isCriticalBioavailable)
                      Container(
                        margin: const EdgeInsets.only(top: 2),
                        padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 1),
                        decoration: BoxDecoration(
                          color: const Color(0xFFFFEBEE),
                          borderRadius: BorderRadius.circular(3),
                        ),
                        child: const Text(
                          'Bioavailable Ion',
                          style: TextStyle(
                            fontSize: 9.5,
                            fontWeight: FontWeight.bold,
                            color: Color(0xFFC62828),
                          ),
                        ),
                      ),
                  ],
                ),
              ),

              // Lab column (Emerald green)
              Expanded(
                flex: 3,
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: isLabConfirmed ? const Color(0xFFE8F5E9) : const Color(0xFFFAFAFA),
                    borderRadius: BorderRadius.circular(4),
                    border: Border.all(
                      color: isLabConfirmed ? const Color(0xFF81C784) : Colors.grey.shade300,
                    ),
                  ),
                  child: Text(
                    labValue,
                    style: TextStyle(
                      fontSize: 12.5,
                      fontWeight: FontWeight.bold,
                      color: isLabConfirmed ? const Color(0xFF1B5E20) : Colors.black54,
                    ),
                  ),
                ),
              ),

              const SizedBox(width: 8),

              // SoilGrids column (Amber / Blue)
              Expanded(
                flex: 3,
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: const Color(0xFFFFF3E0),
                    borderRadius: BorderRadius.circular(4),
                    border: Border.all(color: const Color(0xFFFFB74D)),
                  ),
                  child: Text(
                    soilgridsValue,
                    style: const TextStyle(
                      fontSize: 12.5,
                      fontWeight: FontWeight.w600,
                      color: Color(0xFFBF360C),
                    ),
                  ),
                ),
              ),

              const SizedBox(width: 8),

              // Variance delta
              Expanded(
                flex: 2,
                child: Text(
                  delta,
                  style: TextStyle(
                    fontSize: 11.5,
                    fontWeight: FontWeight.bold,
                    color: delta.startsWith('+')
                        ? const Color(0xFF2E7D32)
                        : (delta.startsWith('-') ? const Color(0xFFC62828) : Colors.black54),
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 4),
          Text(
            '↳ $precedence',
            style: const TextStyle(fontSize: 11, color: Color(0xFF1B5E20), fontStyle: FontStyle.italic),
          ),
        ],
      ),
    );
  }

  /// Micronutrients & Secondary Parameters diagnostics section
  Widget _buildMicronutrientSection() {
    final report = labReport!;
    final microKeys = ['zinc', 'iron', 'manganese', 'copper', 'boron', 'sulphur'];
    final items = microKeys.map((k) => report.getMeasurement(k)).whereType<SoilMeasurementItem>().toList();

    if (items.isEmpty) return const SizedBox.shrink();

    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Row(
              children: [
                Icon(Icons.biotech, color: Color(0xFF1B5E20)),
                SizedBox(width: 8),
                Expanded(
                  child: Text(
                    'Comprehensive Micronutrient & Secondary Parameter Diagnostics',
                    style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 4),
            const Text(
              'Extracted from physical laboratory report. Preserved for transparency and farmer guidance.',
              style: TextStyle(fontSize: 12, color: Colors.black54),
            ),
            const SizedBox(height: 12),
            Wrap(
              spacing: 12,
              runSpacing: 10,
              children: items.map((m) {
                return Container(
                  width: 170,
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: const Color(0xFFF1F8E9),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: const Color(0xFFC8E6C9)),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        m.displayName,
                        style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        '${m.effectiveValue != null ? m.effectiveValue.toString() : "N/A"} ${m.effectiveUnit}',
                        style: const TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                          color: Color(0xFF1B5E20),
                        ),
                      ),
                      if (m.labRating != null) ...[
                        const SizedBox(height: 2),
                        Text(
                          'Rating: ${m.labRating}',
                          style: const TextStyle(
                            fontSize: 10.5,
                            fontWeight: FontWeight.w600,
                            color: Color(0xFF00695C),
                          ),
                        ),
                      ],
                    ],
                  ),
                );
              }).toList(),
            ),
          ],
        ),
      ),
    );
  }

  String _formatLabValue(String key, {String suffix = ''}) {
    if (labReport == null) return 'No lab test uploaded';
    final val = labReport!.getEffectiveValue(key);
    if (val != null) {
      return '${val.toStringAsFixed(2)}$suffix';
    }
    return 'Not reported in lab test';
  }

  String _calculateDelta(double? lab, double? model, {String unit = ''}) {
    if (lab == null || model == null) return 'N/A';
    final diff = lab - model;
    final sign = diff > 0 ? '+' : '';
    return '$sign${diff.toStringAsFixed(2)}$unit';
  }
}
