import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/router/farm_state.dart';
import '../../../../core/router/route_paths.dart';
import '../../data/satellite_repository.dart';
import '../../models/satellite_models.dart';

/// Summary card displaying latest Sentinel-2 Vegetation Health on the Farm Details dashboard.
class SatelliteVegetationSummaryCard extends StatefulWidget {
  final String farmId;

  const SatelliteVegetationSummaryCard({
    super.key,
    required this.farmId,
  });

  @override
  State<SatelliteVegetationSummaryCard> createState() => _SatelliteVegetationSummaryCardState();
}

class _SatelliteVegetationSummaryCardState extends State<SatelliteVegetationSummaryCard> {
  final SatelliteRepository _repository = SatelliteRepository.instance;
  SatelliteObservation? _latest;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadLatest();
  }

  @override
  void didUpdateWidget(covariant SatelliteVegetationSummaryCard oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.farmId != widget.farmId) {
      _loadLatest();
    }
  }

  Future<void> _loadLatest() async {
    setState(() => _isLoading = true);
    try {
      final obs = await _repository.getLatestObservation(widget.farmId);
      if (!mounted) return;
      setState(() {
        _latest = obs;
        _isLoading = false;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() => _isLoading = false);
    }
  }

  Color _getNdviColor(double? val) {
    if (val == null) return Colors.grey;
    if (val >= 0.6) return const Color(0xFF2E7D32); // Lush dark green
    if (val >= 0.4) return const Color(0xFF689F38); // Healthy light green
    if (val >= 0.2) return const Color(0xFFFBC02D); // Moderate yellowish green
    return const Color(0xFFE65100); // Sparse / bare
  }

  String _formatDate(DateTime dt) {
    return '${dt.year}-${dt.month.toString().padLeft(2, '0')}-${dt.day.toString().padLeft(2, '0')}';
  }

  void _navigateToVegetation(BuildContext context) {
    FarmRepository.instance.selectedFarmId = widget.farmId;
    context.push(RoutePaths.farmVegetationPath(widget.farmId));
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return Card(
        elevation: 1,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        child: const Padding(
          padding: EdgeInsets.all(16.0),
          child: Row(
            children: [
              SizedBox(
                width: 20,
                height: 20,
                child: CircularProgressIndicator(strokeWidth: 2, color: Color(0xFF2E7D32)),
              ),
              SizedBox(width: 12),
              Text(
                'Checking Sentinel-2 satellite passes...',
                style: TextStyle(fontSize: 13, color: Colors.black54),
              ),
            ],
          ),
        ),
      );
    }

    if (_latest == null) {
      return Card(
        elevation: 1,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        child: InkWell(
          borderRadius: BorderRadius.circular(12),
          onTap: () => _navigateToVegetation(context),
          child: Padding(
            padding: const EdgeInsets.all(16.0),
            child: Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: const Color(0xFF2E7D32).withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: const Icon(Icons.satellite_alt, color: Color(0xFF2E7D32), size: 24),
                ),
                const SizedBox(width: 14),
                const Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Sentinel-2 Satellite Vegetation Health',
                        style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: Colors.black87),
                      ),
                      SizedBox(height: 2),
                      Text(
                        'No satellite observation synced yet. Tap to retrieve 10m Copernicus surface reflectance.',
                        style: TextStyle(fontSize: 12, color: Colors.black54),
                      ),
                    ],
                  ),
                ),
                const Icon(Icons.chevron_right, color: Colors.black45),
              ],
            ),
          ),
        ),
      );
    }

    final obs = _latest!;
    final hasPureCanopy = obs.vegetationMeanNdvi != null;
    final canopyNdvi = hasPureCanopy ? obs.vegetationMeanNdvi : obs.meanNdvi;
    final canopyNdmi = obs.vegetationMeanNdmi ?? obs.meanNdmi;
    final ndviTitle = hasPureCanopy ? 'Canopy NDVI' : 'Mixed-Surface NDVI';
    final ndviSubtitle = hasPureCanopy ? 'Photosynthetic Vigor (Class 4)' : 'Mixed Surface Composite';
    final ndmiTitle = obs.vegetationMeanNdmi != null ? 'Canopy NDMI' : 'Mixed-Surface NDMI';
    final ndmiSubtitle = obs.vegetationMeanNdmi != null ? 'Canopy Moisture Reflectance' : 'Mixed Surface Reflectance';
    final vegPct = obs.vegetationCoveragePercent?.toStringAsFixed(1);

    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(color: const Color(0xFF2E7D32).withValues(alpha: 0.2)),
      ),
      child: InkWell(
        borderRadius: BorderRadius.circular(12),
        onTap: () => _navigateToVegetation(context),
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Header Row
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(8),
                    decoration: BoxDecoration(
                      color: const Color(0xFF2E7D32).withValues(alpha: 0.12),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: const Icon(Icons.satellite_alt, color: Color(0xFF1B5E20), size: 22),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          'Sentinel-2 Vegetation Health',
                          style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15, color: Color(0xFF1B5E20)),
                        ),
                        Text(
                          'Observation: ${_formatDate(obs.observationDate)} (${obs.sensor})',
                          style: const TextStyle(fontSize: 11, color: Colors.black54),
                        ),
                      ],
                    ),
                  ),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                    decoration: BoxDecoration(
                      color: Colors.green.shade50,
                      borderRadius: BorderRadius.circular(10),
                      border: Border.all(color: Colors.green.shade200),
                    ),
                    child: Text(
                      obs.qualityStatus.replaceAll('_', ' '),
                      style: TextStyle(
                        fontSize: 10,
                        fontWeight: FontWeight.bold,
                        color: Colors.green.shade800,
                      ),
                    ),
                  ),
                ],
              ),
              const Divider(height: 20),

              // Metric Chips Row
              Row(
                children: [
                  // Canopy NDVI
                  Expanded(
                    child: Container(
                      padding: const EdgeInsets.all(10),
                      decoration: BoxDecoration(
                        color: Colors.grey.shade50,
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(color: Colors.grey.shade200),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(ndviTitle, style: const TextStyle(fontSize: 11, color: Colors.black54)),
                          const SizedBox(height: 2),
                          Row(
                            children: [
                              Container(
                                width: 10,
                                height: 10,
                                decoration: BoxDecoration(
                                  color: _getNdviColor(canopyNdvi),
                                  shape: BoxShape.circle,
                                ),
                              ),
                              const SizedBox(width: 6),
                              Text(
                                canopyNdvi != null ? canopyNdvi.toStringAsFixed(3) : 'N/A',
                                style: TextStyle(
                                  fontSize: 16,
                                  fontWeight: FontWeight.bold,
                                  color: _getNdviColor(canopyNdvi),
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 2),
                          Text(ndviSubtitle, style: const TextStyle(fontSize: 10, color: Colors.black45)),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),

                  // Canopy NDMI
                  Expanded(
                    child: Container(
                      padding: const EdgeInsets.all(10),
                      decoration: BoxDecoration(
                        color: Colors.grey.shade50,
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(color: Colors.grey.shade200),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(ndmiTitle, style: const TextStyle(fontSize: 11, color: Colors.black54)),
                          const SizedBox(height: 2),
                          Row(
                            children: [
                              Container(
                                width: 10,
                                height: 10,
                                decoration: const BoxDecoration(
                                  color: Color(0xFF0288D1),
                                  shape: BoxShape.circle,
                                ),
                              ),
                              const SizedBox(width: 6),
                              Text(
                                canopyNdmi != null ? canopyNdmi.toStringAsFixed(3) : 'N/A',
                                style: const TextStyle(
                                  fontSize: 16,
                                  fontWeight: FontWeight.bold,
                                  color: Color(0xFF0288D1),
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 2),
                          Text(ndmiSubtitle, style: const TextStyle(fontSize: 10, color: Colors.black45)),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 10),

              // Surface Cover note & Action
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  if (vegPct != null)
                    Text(
                      'Canopy: $vegPct% | Valid Cells: ${obs.validPixelCount}',
                      style: const TextStyle(fontSize: 11, color: Colors.black54),
                    )
                  else
                    const SizedBox.shrink(),
                  Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Text(
                        'View Full Satellite Intelligence',
                        style: TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.bold,
                          color: Theme.of(context).primaryColor,
                        ),
                      ),
                      const SizedBox(width: 2),
                      Icon(Icons.chevron_right, size: 16, color: Theme.of(context).primaryColor),
                    ],
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
