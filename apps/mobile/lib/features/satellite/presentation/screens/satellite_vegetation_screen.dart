import 'package:flutter/material.dart';
import '../../../../shared/widgets/centered_page_container.dart';
import '../../models/satellite_models.dart';
import '../../data/satellite_repository.dart';

/// Screen displaying Sentinel-2 Level-2A Satellite-Based Vegetation Intelligence.
class SatelliteVegetationScreen extends StatefulWidget {
  final String farmId;
  final String farmName;

  const SatelliteVegetationScreen({
    super.key,
    required this.farmId,
    this.farmName = 'Farm',
  });

  @override
  State<SatelliteVegetationScreen> createState() => _SatelliteVegetationScreenState();
}

class _SatelliteVegetationScreenState extends State<SatelliteVegetationScreen> {
  final SatelliteRepository _repository = SatelliteRepository();

  bool _isLoading = true;
  bool _isSyncing = false;
  String? _errorMessage;

  SatelliteObservation? _latest;
  VegetationTimeSeriesData? _timeSeries;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final latestFuture = _repository.getLatestObservation(widget.farmId);
      final tsFuture = _repository.getTimeSeries(widget.farmId, months: 6);

      final results = await Future.wait([latestFuture, tsFuture]);

      setState(() {
        _latest = results[0] as SatelliteObservation?;
        _timeSeries = results[1] as VegetationTimeSeriesData?;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _errorMessage = 'Failed to load satellite vegetation data: $e';
        _isLoading = false;
      });
    }
  }

  Future<void> _handleSync() async {
    setState(() => _isSyncing = true);
    try {
      final obs = await _repository.syncObservations(widget.farmId);
      final ts = await _repository.getTimeSeries(widget.farmId, months: 6);
      setState(() {
        _latest = obs;
        _timeSeries = ts;
        _isSyncing = false;
      });
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Sentinel-2 imagery successfully synced!')),
        );
      }
    } catch (e) {
      setState(() => _isSyncing = false);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed to sync imagery: $e')),
        );
      }
    }
  }

  Color _getNdviColor(double? val) {
    if (val == null) return Colors.grey;
    if (val >= 0.6) return const Color(0xFF2E7D32); // Lush dark green
    if (val >= 0.4) return const Color(0xFF689F38); // Healthy light green
    if (val >= 0.2) return const Color(0xFFFBC02D); // Moderate yellowish green
    return const Color(0xFFE65100); // Sparse / bare
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('${widget.farmName} — Satellite Vegetation'),
        backgroundColor: const Color(0xFF2E7D32),
        foregroundColor: Colors.white,
        actions: [
          IconButton(
            tooltip: 'Sync Copernicus Imagery',
            icon: _isSyncing
                ? const SizedBox(
                    width: 20,
                    height: 20,
                    child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                  )
                : const Icon(Icons.sync),
            onPressed: _isSyncing ? null : _handleSync,
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _errorMessage != null
              ? Center(
                  child: Padding(
                    padding: const EdgeInsets.all(24.0),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        const Icon(Icons.satellite_alt, size: 48, color: Colors.orange),
                        const SizedBox(height: 12),
                        Text(_errorMessage!, textAlign: TextAlign.center),
                        const SizedBox(height: 16),
                        FilledButton(onPressed: _handleSync, child: const Text('Sync First Observation')),
                      ],
                    ),
                  ),
                )
              : CenteredPageContainer(
                  scrollable: true,
                  child: Padding(
                    padding: const EdgeInsets.all(16.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        // SECTION 1: LATEST OBSERVATION CARD
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  'Sentinel-2 Surface Reflectance (L2A)',
                                  style: Theme.of(context).textTheme.titleLarge?.copyWith(
                                        fontWeight: FontWeight.bold,
                                      ),
                                ),
                                const SizedBox(height: 4),
                                const Text(
                                  'Copernicus 10m Multi-Spectral Instrument (B04 Red, B08 NIR, B11 SWIR).',
                                  style: TextStyle(color: Colors.black54),
                                ),
                              ],
                            ),
                            FilledButton.icon(
                              onPressed: _isSyncing ? null : _handleSync,
                              icon: const Icon(Icons.cloud_sync),
                              label: const Text('Refresh Pass'),
                              style: FilledButton.styleFrom(backgroundColor: const Color(0xFF1B5E20)),
                            ),
                          ],
                        ),

                        const SizedBox(height: 16),

                        if (_latest != null) ...[
                          Card(
                            elevation: 2,
                            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                            child: Padding(
                              padding: const EdgeInsets.all(20.0),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Row(
                                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                    children: [
                                      Row(
                                        children: [
                                          const Icon(Icons.satellite, color: Color(0xFF1976D2)),
                                          const SizedBox(width: 8),
                                          Text(
                                            'Product: ${_latest!.productId}',
                                            style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
                                          ),
                                        ],
                                      ),
                                      Chip(
                                        label: Text(_latest!.qualityStatus),
                                        backgroundColor: _latest!.qualityStatus == 'VALID_OBSERVATION'
                                            ? Colors.green.shade100
                                            : Colors.amber.shade100,
                                        visualDensity: VisualDensity.compact,
                                      ),
                                    ],
                                  ),
                                  const Divider(height: 24),
                                  Row(
                                    children: [
                                      // NDVI
                                      Expanded(
                                        child: Column(
                                          crossAxisAlignment: CrossAxisAlignment.start,
                                          children: [
                                            const Text(
                                              'Mean NDVI (Canopy Vigor)',
                                              style: TextStyle(fontSize: 13, color: Colors.black54),
                                            ),
                                            const SizedBox(height: 4),
                                            Text(
                                              _latest!.meanNdvi != null
                                                  ? '${_latest!.meanNdvi}'
                                                  : 'N/A',
                                              style: TextStyle(
                                                fontSize: 32,
                                                fontWeight: FontWeight.bold,
                                                color: _getNdviColor(_latest!.meanNdvi),
                                              ),
                                            ),
                                            const SizedBox(height: 4),
                                            Text(
                                              'Range: [${_latest!.minNdvi ?? 0} — ${_latest!.maxNdvi ?? 0}] (Std: ${_latest!.stdNdvi ?? 0})',
                                              style: const TextStyle(fontSize: 11, color: Colors.black54),
                                            ),
                                          ],
                                        ),
                                      ),
                                      // NDMI
                                      Expanded(
                                        child: Column(
                                          crossAxisAlignment: CrossAxisAlignment.start,
                                          children: [
                                            const Text(
                                              'Mean NDMI (Canopy Moisture)',
                                              style: TextStyle(fontSize: 13, color: Colors.black54),
                                            ),
                                            const SizedBox(height: 4),
                                            Text(
                                              _latest!.meanNdmi != null
                                                  ? '${_latest!.meanNdmi}'
                                                  : 'N/A',
                                              style: const TextStyle(
                                                fontSize: 32,
                                                fontWeight: FontWeight.bold,
                                                color: Color(0xFF0288D1),
                                              ),
                                            ),
                                            const SizedBox(height: 4),
                                            const Text(
                                              'B08 (NIR) vs B11 (SWIR) resampled at 10m',
                                              style: TextStyle(fontSize: 11, color: Colors.black54),
                                            ),
                                          ],
                                        ),
                                      ),
                                      // SCL Masking & Pixels
                                      Expanded(
                                        child: Column(
                                          crossAxisAlignment: CrossAxisAlignment.start,
                                          children: [
                                            const Text(
                                              'SCL Cloud Masking',
                                              style: TextStyle(fontSize: 13, color: Colors.black54),
                                            ),
                                            const SizedBox(height: 4),
                                            Text(
                                              '${_latest!.cloudMaskedPercent}%',
                                              style: TextStyle(
                                                fontSize: 24,
                                                fontWeight: FontWeight.bold,
                                                color: _latest!.cloudMaskedPercent > 30 ? Colors.red : Colors.black87,
                                              ),
                                            ),
                                            const SizedBox(height: 4),
                                            Text(
                                              '${_latest!.validPixelCount} / ${_latest!.totalPixelCount} valid 10m pixels',
                                              style: const TextStyle(fontSize: 11, color: Colors.black54),
                                            ),
                                          ],
                                        ),
                                      ),
                                    ],
                                  ),
                                  if (_latest!.isSmallFarmWarning) ...[
                                    const SizedBox(height: 16),
                                    Container(
                                      padding: const EdgeInsets.all(12),
                                      decoration: BoxDecoration(
                                        color: Colors.orange.shade50,
                                        border: Border.all(color: Colors.orange.shade300),
                                        borderRadius: BorderRadius.circular(8),
                                      ),
                                      child: Row(
                                        children: [
                                          const Icon(Icons.warning_amber_rounded, color: Colors.orange),
                                          const SizedBox(width: 8),
                                          Expanded(
                                            child: Text(
                                              'Spatial Representativeness Safeguard: ${_latest!.qualityNotes ?? "Small parcel subject to boundary mixed pixels."}',
                                              style: const TextStyle(fontSize: 12, color: Colors.black87),
                                            ),
                                          ),
                                        ],
                                      ),
                                    ),
                                  ],
                                ],
                              ),
                            ),
                          ),
                        ] else ...[
                          Card(
                            elevation: 0,
                            color: Colors.grey.shade100,
                            child: const Padding(
                              padding: EdgeInsets.all(32.0),
                              child: Center(
                                child: Text('No satellite observation recorded yet. Click "Refresh Pass" to retrieve imagery.'),
                              ),
                            ),
                          ),
                        ],

                        const SizedBox(height: 32),

                        // SECTION 2: HISTORICAL TIME-SERIES
                        Text(
                          'Multi-Month Canopy Reflectance Trend',
                          style: Theme.of(context).textTheme.titleLarge?.copyWith(
                                fontWeight: FontWeight.bold,
                              ),
                        ),
                        const SizedBox(height: 4),
                        if (_timeSeries != null)
                          Text(
                            _timeSeries!.vegetationInterpretation,
                            style: const TextStyle(fontWeight: FontWeight.w600, color: Color(0xFF2E7D32)),
                          ),
                        const SizedBox(height: 16),

                        if (_timeSeries != null && _timeSeries!.series.isNotEmpty)
                          Card(
                            elevation: 1,
                            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                            child: Padding(
                              padding: const EdgeInsets.all(16.0),
                              child: SingleChildScrollView(
                                scrollDirection: Axis.horizontal,
                                child: DataTable(
                                  columns: const [
                                    DataColumn(label: Text('Acquisition Date')),
                                    DataColumn(label: Text('Mean NDVI')),
                                    DataColumn(label: Text('Mean NDMI')),
                                    DataColumn(label: Text('Valid Pixels')),
                                    DataColumn(label: Text('Cloud Masked')),
                                    DataColumn(label: Text('Quality Status')),
                                  ],
                                  rows: _timeSeries!.series.reversed.map((pt) {
                                    return DataRow(cells: [
                                      DataCell(Text(pt.date.toIso8601String().split('T').first)),
                                      DataCell(
                                        Row(
                                          children: [
                                            Container(
                                              width: 12,
                                              height: 12,
                                              decoration: BoxDecoration(
                                                color: _getNdviColor(pt.meanNdvi),
                                                shape: BoxShape.circle,
                                              ),
                                            ),
                                            const SizedBox(width: 8),
                                            Text('${pt.meanNdvi ?? "N/A"}'),
                                          ],
                                        ),
                                      ),
                                      DataCell(Text('${pt.meanNdmi ?? "N/A"}')),
                                      DataCell(Text('${pt.validPixels}')),
                                      DataCell(Text('${pt.cloudMaskedPercent}%')),
                                      DataCell(Text(pt.qualityStatus)),
                                    ]);
                                  }).toList(),
                                ),
                              ),
                            ),
                          ),

                        const SizedBox(height: 32),

                        // SECTION 3: SCIENTIFIC DISCLAIMER
                        Container(
                          padding: const EdgeInsets.all(16.0),
                          decoration: BoxDecoration(
                            color: Colors.blueGrey.shade50,
                            border: Border.all(color: Colors.blueGrey.shade200),
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: const Row(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Icon(Icons.shield_outlined, color: Colors.blueGrey, size: 24),
                              SizedBox(width: 12),
                              Expanded(
                                child: Text(
                                  'SCIENTIFIC SAFEGUARD NOTICE: Sentinel-2 Level-2A NDVI and NDMI reflect surface '
                                  'canopy spectral reflectance at 10-meter spatial resolution. '
                                  'They serve as indirect indicators of vegetative vigor and moisture status. '
                                  'They MUST NEVER be used as direct diagnoses of specific plant diseases, pest infestations, '
                                  'nitrogen deficiencies, or absolute crop yield predictions without field ground-truthing.',
                                  style: TextStyle(fontSize: 12, height: 1.4, color: Colors.black87),
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
    );
  }
}
