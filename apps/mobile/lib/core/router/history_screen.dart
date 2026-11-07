import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:cropnet_mobile/core/router/farm_state.dart';
import 'package:cropnet_mobile/core/router/route_paths.dart';
import 'package:cropnet_mobile/features/history/assessment_history_repository.dart';

export 'package:cropnet_mobile/features/history/assessment_history_repository.dart'
    show AssessmentHistoryRecord, AssessmentHistoryRepository;

/// Soil & Crop Assessment History Screen
/// Displays chronological record of digital soil profiling, weather intelligence, and crop evaluations.
class AssessmentHistoryScreen extends StatefulWidget {
  const AssessmentHistoryScreen({super.key});

  @override
  State<AssessmentHistoryScreen> createState() => _AssessmentHistoryScreenState();
}

class _AssessmentHistoryScreenState extends State<AssessmentHistoryScreen> {
  String _selectedFilter = 'All';

  final List<String> _filters = ['All', 'Baramati', 'Indapur', 'Maval', 'Mulshi'];

  @override
  Widget build(BuildContext context) {
    return ListenableBuilder(
      listenable: AssessmentHistoryRepository.instance,
      builder: (context, _) {
        final allRecords = AssessmentHistoryRepository.instance.records;
        final filtered = allRecords.where((r) {
          if (_selectedFilter == 'All') return true;
          return r.taluka.toLowerCase() == _selectedFilter.toLowerCase();
        }).toList();

        return Scaffold(
          appBar: AppBar(
            title: const Text('Assessment History', style: TextStyle(fontWeight: FontWeight.bold)),
            backgroundColor: const Color(0xFF1B5E20),
            foregroundColor: Colors.white,
          ),
          body: Column(
            children: [
              // Metrics Header
              Container(
                padding: const EdgeInsets.all(16),
                color: const Color(0xFFF1F8E9),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceAround,
                  children: [
                    _buildMetricCard('Total Runs', '${allRecords.length}', Icons.analytics_outlined),
                    _buildMetricCard(
                      'Soil Profiles',
                      '${allRecords.where((r) => r.assessmentType.contains("Soil")).length}',
                      Icons.terrain_outlined,
                    ),
                    _buildMetricCard(
                      'Crop Feasibility',
                      '${allRecords.where((r) => r.assessmentType.contains("Crop")).length}',
                      Icons.grass_outlined,
                    ),
                    _buildMetricCard(
                      'Regions',
                      '${allRecords.map((r) => r.taluka).toSet().length}',
                      Icons.location_on_outlined,
                    ),
                  ],
                ),
              ),

              // Filter Chips
              SizedBox(
                height: 48,
                child: ListView.separated(
                  scrollDirection: Axis.horizontal,
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                  itemCount: _filters.length,
                  separatorBuilder: (_, __) => const SizedBox(width: 8),
                  itemBuilder: (ctx, idx) {
                    final filter = _filters[idx];
                    final isSelected = filter == _selectedFilter;
                    return ChoiceChip(
                      label: Text(
                        filter,
                        style: TextStyle(
                          fontSize: 12,
                          color: isSelected ? Colors.white : Colors.black87,
                        ),
                      ),
                      selected: isSelected,
                      selectedColor: const Color(0xFF1B5E20),
                      backgroundColor: Colors.white,
                      onSelected: (val) {
                        if (val) setState(() => _selectedFilter = filter);
                      },
                    );
                  },
                ),
              ),

              const Divider(height: 1),

              // List of Records
              Expanded(
                child: filtered.isEmpty
                    ? Center(
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            const Icon(Icons.history, size: 54, color: Colors.grey),
                            const SizedBox(height: 12),
                            const Text(
                              'No assessment history yet.',
                              style: TextStyle(color: Colors.black87, fontSize: 16, fontWeight: FontWeight.bold),
                            ),
                            const SizedBox(height: 6),
                            const Padding(
                              padding: EdgeInsets.symmetric(horizontal: 32.0),
                              child: Text(
                                'Assessments will be automatically recorded here when you run Soil Intelligence extractions, Crop Feasibility evaluations, or AI Advisory dialogues.',
                                textAlign: TextAlign.center,
                                style: TextStyle(color: Colors.black54, fontSize: 13),
                              ),
                            ),
                            const SizedBox(height: 20),
                            ElevatedButton.icon(
                              style: ElevatedButton.styleFrom(
                                backgroundColor: const Color(0xFF1B5E20),
                                foregroundColor: Colors.white,
                              ),
                              onPressed: () => context.go(RoutePaths.soilTesting),
                              icon: const Icon(Icons.science),
                              label: const Text('Analyse Soil Profile Now'),
                            ),
                          ],
                        ),
                      )
                    : ListView.builder(
                        padding: const EdgeInsets.all(16),
                        itemCount: filtered.length,
                        itemBuilder: (ctx, idx) {
                          final record = filtered[idx];
                          return _buildRecordCard(record);
                        },
                      ),
              ),
            ],
          ),
        );
      },
    );
  }

  Widget _buildMetricCard(String label, String value, IconData icon) {
    return Column(
      children: [
        Icon(icon, color: const Color(0xFF1B5E20), size: 22),
        const SizedBox(height: 4),
        Text(value, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: Color(0xFF1B5E20))),
        Text(label, style: const TextStyle(fontSize: 11, color: Colors.black54)),
      ],
    );
  }

  Widget _buildRecordCard(AssessmentHistoryRecord record) {
    final farmExists = FarmRepository.instance.getFarmById(record.farmId) != null;
    final isSoil = record.assessmentType.contains('Soil');

    return Card(
      elevation: 2,
      margin: const EdgeInsets.only(bottom: 14),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: isSoil ? const Color(0xFFE8F5E9) : const Color(0xFFE3F2FD),
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: Text(
                    record.assessmentType,
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.bold,
                      color: isSoil ? const Color(0xFF1B5E20) : const Color(0xFF0277BD),
                    ),
                  ),
                ),
                const Spacer(),
                Text(
                  _formatDate(record.date),
                  style: const TextStyle(fontSize: 11, color: Colors.black54),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Text(
              '${record.farmName} (${record.taluka})',
              style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
            ),
            const SizedBox(height: 6),
            Text(
              record.summary,
              style: const TextStyle(fontSize: 13, color: Colors.black87, height: 1.3),
            ),
            const SizedBox(height: 10),

            // Key Metrics Grid
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: const Color(0xFFFAFAFA),
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: Colors.grey.shade200),
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceAround,
                children: record.keyMetrics.entries.map((e) {
                  return Column(
                    children: [
                      Text(e.key, style: const TextStyle(fontSize: 10, color: Colors.black54)),
                      const SizedBox(height: 2),
                      Text(
                        e.value,
                        style: const TextStyle(
                          fontWeight: FontWeight.bold,
                          fontSize: 12,
                          color: Color(0xFF1B5E20),
                        ),
                      ),
                    ],
                  );
                }).toList(),
              ),
            ),

            const SizedBox(height: 10),
            Row(
              children: [
                const Icon(Icons.verified, size: 14, color: Color(0xFF2E7D32)),
                const SizedBox(width: 4),
                Expanded(
                  child: Text(
                    'Provenance: ${record.provenance}',
                    style: const TextStyle(fontSize: 10, color: Colors.black54, fontStyle: FontStyle.italic),
                  ),
                ),
              ],
            ),

            const SizedBox(height: 12),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              alignment: WrapAlignment.end,
              children: [
                // Button to View Details
                if (farmExists && isSoil)
                  OutlinedButton.icon(
                    onPressed: () => context.push(RoutePaths.soilDetailPath(record.farmId)),
                    icon: const Icon(Icons.terrain, size: 16),
                    label: const Text('View Soil Report', style: TextStyle(fontSize: 12)),
                    style: OutlinedButton.styleFrom(
                      foregroundColor: const Color(0xFF1B5E20),
                    ),
                  )
                else if (record.cropId != null)
                  OutlinedButton.icon(
                    onPressed: () => context.push(RoutePaths.cropDetailPath(record.cropId!)),
                    icon: const Icon(Icons.grass, size: 16),
                    label: Text(
                      record.cropName != null ? 'View ${record.cropName}' : 'View Crop Guide',
                      style: const TextStyle(fontSize: 12),
                    ),
                    style: OutlinedButton.styleFrom(
                      foregroundColor: const Color(0xFF1B5E20),
                    ),
                  )
                else if (farmExists)
                  OutlinedButton.icon(
                    onPressed: () => context.push(RoutePaths.farmDetailPath(record.farmId)),
                    icon: const Icon(Icons.pin_drop, size: 16),
                    label: const Text('View Farm', style: TextStyle(fontSize: 12)),
                    style: OutlinedButton.styleFrom(
                      foregroundColor: const Color(0xFF1B5E20),
                    ),
                  ),

                // Button to jump directly to advisory with this farm selected
                ElevatedButton.icon(
                  onPressed: () {
                    FarmRepository.instance.selectedFarmId = record.farmId;
                    context.go(RoutePaths.advisory);
                  },
                  icon: const Icon(Icons.psychology, size: 16),
                  label: const Text('Jump to Advisory', style: TextStyle(fontSize: 12)),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF1B5E20),
                    foregroundColor: Colors.white,
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  String _formatDate(DateTime dt) {
    final diff = DateTime.now().difference(dt);
    if (diff.inMinutes < 1) return 'Just now';
    if (diff.inHours < 1) return '${diff.inMinutes}m ago';
    if (diff.inHours < 24) return '${diff.inHours}h ago';
    if (diff.inDays < 7) return '${diff.inDays}d ago';
    return '${dt.day}/${dt.month}/${dt.year}';
  }
}
