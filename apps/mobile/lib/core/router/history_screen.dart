import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:cropnet_mobile/core/router/farm_state.dart';
import 'package:cropnet_mobile/core/router/route_paths.dart';

/// Assessment record model for historical soil and crop analyses
class AssessmentHistoryRecord {
  final String id;
  final String farmId;
  final String farmName;
  final String taluka;
  final String assessmentType;
  final DateTime date;
  final String summary;
  final String provenance;
  final Map<String, String> keyMetrics;

  const AssessmentHistoryRecord({
    required this.id,
    required this.farmId,
    required this.farmName,
    required this.taluka,
    required this.assessmentType,
    required this.date,
    required this.summary,
    required this.provenance,
    required this.keyMetrics,
  });
}

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

  late List<AssessmentHistoryRecord> _records;

  @override
  void initState() {
    super.initState();
    _initializeHistoryRecords();
  }

  void _initializeHistoryRecords() {
    _records = [];
  }

  @override
  Widget build(BuildContext context) {
    final filtered = _records.where((r) {
      if (_selectedFilter == 'All') return true;
      return r.taluka == _selectedFilter;
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
                _buildMetricCard('Total Runs', '${_records.length}', Icons.analytics_outlined),
                _buildMetricCard('Soil Profiles', '${_records.where((r) => r.assessmentType.contains("Soil")).length}', Icons.terrain_outlined),
                _buildMetricCard('Crop Feasibility', '${_records.where((r) => r.assessmentType.contains("Crop")).length}', Icons.grass_outlined),
                _buildMetricCard('Regions', '${_records.map((r) => r.taluka).toSet().length}', Icons.location_on_outlined),
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
                  label: Text(filter, style: TextStyle(fontSize: 12, color: isSelected ? Colors.white : Colors.black87)),
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
                ? const Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(Icons.history, size: 48, color: Colors.grey),
                        SizedBox(height: 12),
                        Text('No assessment history yet.', style: TextStyle(color: Colors.black54, fontSize: 16)),
                        SizedBox(height: 4),
                        Text('Assessments will appear here once you run soil or crop evaluations.', style: TextStyle(color: Colors.black38, fontSize: 13)),
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
                    color: const Color(0xFFE8F5E9),
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: Text(
                    record.assessmentType,
                    style: const TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.bold,
                      color: Color(0xFF1B5E20),
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
                      Text(e.value, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12, color: Color(0xFF1B5E20))),
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
            Row(
              mainAxisAlignment: MainAxisAlignment.end,
              children: [
                if (farmExists) ...[
                  OutlinedButton.icon(
                    onPressed: () => context.push(RoutePaths.soilDetailPath(record.farmId)),
                    icon: const Icon(Icons.terrain, size: 16),
                    label: const Text('View Soil Report', style: TextStyle(fontSize: 12)),
                    style: OutlinedButton.styleFrom(
                      foregroundColor: const Color(0xFF1B5E20),
                    ),
                  ),
                  const SizedBox(width: 8),
                ],
                ElevatedButton.icon(
                  onPressed: () => context.go(RoutePaths.cropRecommendation),
                  icon: const Icon(Icons.menu_book, size: 16),
                  label: const Text('Crop Guides', style: TextStyle(fontSize: 12)),
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
    if (diff.inHours < 1) return 'Just now';
    if (diff.inHours < 24) return '${diff.inHours}h ago';
    if (diff.inDays < 7) return '${diff.inDays}d ago';
    return '${dt.day}/${dt.month}/${dt.year}';
  }
}
