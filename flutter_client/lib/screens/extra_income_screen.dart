import 'package:flutter/material.dart';
import '../models/farm_models.dart';
import '../services/api_service.dart';
import '../services/app_state.dart';

class ExtraIncomeScreen extends StatefulWidget {
  const ExtraIncomeScreen({Key? key}) : super(key: key);

  @override
  State<ExtraIncomeScreen> createState() => _ExtraIncomeScreenState();
}

class _ExtraIncomeScreenState extends State<ExtraIncomeScreen> {
  // Questionnaire / Resource Profile State
  double _availableInvestment = 75000.0;
  double _availableLand = 0.5;
  String _waterAvailability = 'seasonal_canal';
  double _familyLaborHours = 2.5;
  String _riskTolerance = 'moderate';
  String _categoryPreference = 'all';

  List<ScoredOpportunityItem> _scoredOpportunities = [];
  ScoredOpportunityItem? _selectedScored;
  IncomeScenario? _scenario;
  List<OpportunityComparisonItem> _comparisons = [];

  bool _isLoading = true;
  bool _isCalculating = false;

  @override
  void initState() {
    super.initState();
    AppState.instance.addListener(_onStateChange);
    _matchOpportunities();
  }

  @override
  void dispose() {
    AppState.instance.removeListener(_onStateChange);
    super.dispose();
  }

  void _onStateChange() {
    _matchOpportunities();
  }

  Future<void> _matchOpportunities() async {
    setState(() => _isLoading = true);

    final scored = await ApiService.matchIncomeOpportunities(
      availableInvestmentInr: _availableInvestment,
      workingCapitalInr: _availableInvestment * 0.2,
      availableLandAcres: _availableLand,
      unusedLandAcres: _availableLand * 0.5,
      waterAvailability: _waterAvailability,
      familyLaborHoursDay: _familyLaborHours,
      existingLivestock: 'none',
      hasStorageOrShed: false,
      riskTolerance: _riskTolerance,
      categoryPreference: _categoryPreference,
    );

    if (mounted) {
      setState(() {
        _scoredOpportunities = scored;
        if (scored.isNotEmpty) {
          _selectedScored = scored.first;
        } else {
          _selectedScored = null;
        }
        _isLoading = false;
      });

      if (_selectedScored != null) {
        _calculateScenario();
        _loadComparisons();
      }
    }
  }

  Future<void> _calculateScenario() async {
    if (_selectedScored == null) return;
    setState(() => _isCalculating = true);

    final sc = await ApiService.calculateIncomeScenario(
      opportunityId: _selectedScored!.opportunity.opportunityId,
      customBudgetInr: _availableInvestment,
      labourHours: _familyLaborHours,
      waterAvailability: _waterAvailability,
    );

    if (mounted) {
      setState(() {
        _scenario = sc;
        _isCalculating = false;
      });
    }
  }

  Future<void> _loadComparisons() async {
    if (_scoredOpportunities.length < 2) return;
    final topIds = _scoredOpportunities.take(3).map((s) => s.opportunity.opportunityId).toList();
    final comp = await ApiService.compareOpportunities(
      opportunityIds: topIds,
      customBudgetInr: _availableInvestment,
    );
    if (mounted) {
      setState(() {
        _comparisons = comp;
      });
    }
  }

  Color _getScoreColor(int score) {
    if (score >= 80) return const Color(0xFF2E7D32);
    if (score >= 60) return const Color(0xFFF57F17);
    return const Color(0xFFC62828);
  }

  String _formatCurrency(num amount) {
    if (amount >= 100000) {
      return '₹${(amount / 100000).toStringAsFixed(1)} Lakh';
    }
    return '₹${amount.toStringAsFixed(0)}';
  }

  @override
  Widget build(BuildContext context) {
    final appState = AppState.instance;

    return Scaffold(
      backgroundColor: const Color(0xFFF6F8F6),
      appBar: AppBar(
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Extra Farm Income', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
            Text(
              '${appState.activeTaluka}, ${appState.activeDistrict} · ${appState.activeCropName}',
              style: const TextStyle(fontSize: 12, color: Colors.white70),
            ),
          ],
        ),
        backgroundColor: const Color(0xFF1B5E20),
        foregroundColor: Colors.white,
        actions: [
          IconButton(
            tooltip: 'Refresh Options',
            icon: const Icon(Icons.refresh),
            onPressed: _matchOpportunities,
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator(color: Color(0xFF2E7D32)))
          : SingleChildScrollView(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  // SECTION A: Friendly Introduction (Main Card)
                  Card(
                    elevation: 2,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                    child: Padding(
                      padding: const EdgeInsets.all(16.0),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              Container(
                                padding: const EdgeInsets.all(10),
                                decoration: BoxDecoration(
                                  color: const Color(0xFFE8F5E9),
                                  shape: BoxShape.circle,
                                ),
                                child: const Icon(Icons.savings_outlined, color: Color(0xFF1B5E20), size: 28),
                              ),
                              const SizedBox(width: 12),
                              const Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      'Find Extra Income from Your Farm',
                                      style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Color(0xFF1B5E20)),
                                    ),
                                    SizedBox(height: 2),
                                    Text(
                                      'Practical enterprises matched to your spare land, budget & water.',
                                      style: TextStyle(fontSize: 12, color: Colors.black54),
                                    ),
                                  ],
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 14),
                          // Farm resources summary row
                          Container(
                            padding: const EdgeInsets.all(12),
                            decoration: BoxDecoration(
                              color: Colors.grey.shade50,
                              borderRadius: BorderRadius.circular(10),
                              border: Border.all(color: Colors.grey.shade200),
                            ),
                            child: Row(
                              mainAxisAlignment: MainAxisAlignment.spaceAround,
                              children: [
                                _buildResourceMini('Budget', _formatCurrency(_availableInvestment), Icons.account_balance_wallet_outlined),
                                _buildResourceMini('Spare Land', '${_availableLand.toStringAsFixed(1)} ac', Icons.landscape_outlined),
                                _buildResourceMini('Water', _getWaterFriendlyName(_waterAvailability), Icons.water_drop_outlined),
                                _buildResourceMini('Labor', '${_familyLaborHours.toStringAsFixed(0)} h/day', Icons.people_outline),
                              ],
                            ),
                          ),
                          const SizedBox(height: 12),
                          SizedBox(
                            width: double.infinity,
                            child: OutlinedButton.icon(
                              style: OutlinedButton.styleFrom(
                                foregroundColor: const Color(0xFF2E7D32),
                                side: const BorderSide(color: Color(0xFF2E7D32)),
                                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                                padding: const EdgeInsets.symmetric(vertical: 10),
                              ),
                              icon: const Icon(Icons.tune, size: 18),
                              label: const Text('Change My Farm Resources', style: TextStyle(fontWeight: FontWeight.bold)),
                              onPressed: () => _showResourceSettingsBottomSheet(context),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 16),

                  // SECTION C: Top Matched Opportunities (Shortlist of cards)
                  const Text(
                    'BEST MATCHED ENTERPRISES FOR YOU',
                    style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: Color(0xFF1B5E20), letterSpacing: 0.8),
                  ),
                  const SizedBox(height: 8),
                  if (_scoredOpportunities.isEmpty)
                    Card(
                      child: Padding(
                        padding: const EdgeInsets.all(16.0),
                        child: Column(
                          children: [
                            const Text('No enterprises matched your exact budget/land filter.'),
                            const SizedBox(height: 8),
                            ElevatedButton(
                              onPressed: () => _showResourceSettingsBottomSheet(context),
                              child: const Text('Adjust Farm Budget or Land'),
                            ),
                          ],
                        ),
                      ),
                    )
                  else
                    ..._scoredOpportunities.take(3).map((s) => _buildFarmerOpportunityCard(s)).toList(),
                  const SizedBox(height: 16),

                  // SECTION D: Opportunity Deep-Dive (When tapped / selected)
                  if (_scenario != null && _selectedScored != null) ...[
                    _buildOpportunityDeepDiveCard(),
                    const SizedBox(height: 16),
                  ],

                  // SECTION E: Side-by-Side Comparison
                  if (_comparisons.isNotEmpty) ...[
                    _buildFarmerComparisonCard(),
                    const SizedBox(height: 16),
                  ],

                  // SECTION F: Scientific & Official Sources (Progressive Disclosure)
                  Card(
                    elevation: 1,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                    child: ExpansionTile(
                      leading: const Icon(Icons.verified_outlined, color: Colors.blueGrey),
                      title: const Text(
                        'NABARD FY 2026-27 Official Benchmarks & Mandi Data',
                        style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: Colors.blueGrey),
                      ),
                      subtitle: const Text('Tap to view official state cost norms & APMC market prices', style: TextStyle(fontSize: 11, color: Colors.black54)),
                      children: [
                        Padding(
                          padding: const EdgeInsets.all(16.0),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              if (_scenario != null) ...[
                                Text(
                                  'Local APMC Mandi Benchmark: ${_scenario!.localMandiBenchmark['commodity'] ?? "Livestock/Produce"}',
                                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12),
                                ),
                                const SizedBox(height: 4),
                                Text(
                                  'Prevailing Price: ${_scenario!.localMandiBenchmark['benchmark_price'] ?? "Prevailing Modal Price"} · Source: ${_scenario!.localMandiBenchmark['reporting_mandi'] ?? "Agmarknet APMC"}',
                                  style: const TextStyle(fontSize: 11, color: Colors.black87),
                                ),
                                const SizedBox(height: 8),
                              ],
                              Container(
                                padding: const EdgeInsets.all(10),
                                decoration: BoxDecoration(
                                  color: Colors.grey.shade100,
                                  borderRadius: BorderRadius.circular(8),
                                ),
                                child: Text(
                                  _scenario?.disclaimer.isNotEmpty == true
                                      ? _scenario!.disclaimer
                                      : 'Calibrated using official NABARD Unit Cost Norms for Maharashtra State (FY 2026-27). Cash flow models reflect local agricultural seasonal patterns.',
                                  style: const TextStyle(fontSize: 11, color: Colors.black54, height: 1.3),
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 24),
                ],
              ),
            ),
    );
  }

  // ==================== HELPER WIDGETS ====================
  Widget _buildResourceMini(String label, String value, IconData icon) {
    return Column(
      children: [
        Icon(icon, size: 18, color: const Color(0xFF2E7D32)),
        const SizedBox(height: 4),
        Text(value, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12)),
        Text(label, style: const TextStyle(fontSize: 10, color: Colors.black54)),
      ],
    );
  }

  Widget _buildFarmerOpportunityCard(ScoredOpportunityItem s) {
    final isSelected = _selectedScored?.opportunity.opportunityId == s.opportunity.opportunityId;
    final scoreColor = _getScoreColor(s.suitabilityScorePct);

    return InkWell(
      onTap: () {
        setState(() => _selectedScored = s);
        _calculateScenario();
        _loadComparisons();
      },
      child: Card(
        elevation: isSelected ? 3 : 1,
        margin: const EdgeInsets.only(bottom: 12),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(14),
          side: BorderSide(
            color: isSelected ? const Color(0xFF1B5E20) : Colors.grey.shade200,
            width: isSelected ? 2.0 : 1.0,
          ),
        ),
        child: Padding(
          padding: const EdgeInsets.all(14.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                    decoration: BoxDecoration(
                      color: scoreColor.withOpacity(0.12),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Text(
                      '${s.suitabilityScorePct}% Fit',
                      style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: scoreColor),
                    ),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          s.opportunity.title,
                          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15),
                        ),
                        if (s.reasonsWhySuitable.isNotEmpty)
                          Text(
                            s.reasonsWhySuitable.first,
                            style: TextStyle(fontSize: 12, color: Colors.green.shade900, fontWeight: FontWeight.w500),
                          ),
                      ],
                    ),
                  ),
                  Radio<String>(
                    value: s.opportunity.opportunityId,
                    groupValue: _selectedScored?.opportunity.opportunityId,
                    activeColor: const Color(0xFF1B5E20),
                    onChanged: (val) {
                      setState(() => _selectedScored = s);
                      _calculateScenario();
                      _loadComparisons();
                    },
                  ),
                ],
              ),
              const SizedBox(height: 10),
              // Key highlights grid
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  _buildCardMetric('Initial Cost', _formatCurrency(s.opportunity.minInvestmentInr)),
                  _buildCardMetric('Expected Profit', '${_formatCurrency(s.opportunity.potentialAnnualProfitInr)} / yr'),
                  _buildCardMetric('Payback Time', '${s.opportunity.paybackPeriodMonths} months'),
                  _buildCardMetric('Space Needed', '${s.opportunity.requiredLandAcres} ac'),
                ],
              ),
              if (s.reasonsWhyUnsuitable.isNotEmpty) ...[
                const SizedBox(height: 8),
                Text(
                  '• Note: ${s.reasonsWhyUnsuitable.first}',
                  style: TextStyle(fontSize: 11, color: Colors.orange.shade900, fontStyle: FontStyle.italic),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildCardMetric(String label, String value) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(value, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12, color: Color(0xFF1B5E20))),
        Text(label, style: const TextStyle(fontSize: 10, color: Colors.black54)),
      ],
    );
  }

  Widget _buildOpportunityDeepDiveCard() {
    final sc = _scenario!;
    final base = sc.scenarios['base'];
    final cons = sc.scenarios['conservative'];
    final opt = sc.scenarios['optimistic'];

    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: const BorderSide(color: Color(0xFF2E7D32), width: 1.2),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.analytics_outlined, color: Color(0xFF1B5E20), size: 22),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    'Financial Outlook: ${sc.opportunityTitle}',
                    style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15, color: Color(0xFF1B5E20)),
                  ),
                ),
                if (_isCalculating)
                  const SizedBox(width: 14, height: 14, child: CircularProgressIndicator(strokeWidth: 2, color: Color(0xFF1B5E20))),
              ],
            ),
            const SizedBox(height: 10),
            Text(
              'Initial investment needed: ₹${sc.calculatedCapexInr.toStringAsFixed(0)} (plus ₹${sc.workingCapitalInr.toStringAsFixed(0)} operating cash).',
              style: const TextStyle(fontSize: 12, color: Colors.black87),
            ),
            const SizedBox(height: 14),

            // 3 Earning Scenarios
            if (base != null && cons != null && opt != null)
              Row(
                children: [
                  Expanded(
                    child: _buildScenarioPill('Low Estimate', _formatCurrency(cons.netAnnualProfitInr), '${cons.breakEvenMonths.toStringAsFixed(0)} mos payback', Colors.orange.shade800),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: _buildScenarioPill('Expected / Normal', _formatCurrency(base.netAnnualProfitInr), '${base.breakEvenMonths.toStringAsFixed(0)} mos payback', const Color(0xFF1B5E20), isHighlight: true),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: _buildScenarioPill('High Estimate', _formatCurrency(opt.netAnnualProfitInr), '${opt.breakEvenMonths.toStringAsFixed(0)} mos payback', Colors.green.shade800),
                  ),
                ],
              ),
            const SizedBox(height: 14),

            // 12-Month Net Cash Flow Horizon
            if (base != null && base.monthlyNetCashFlowInr.isNotEmpty) ...[
              const Text('12-Month Earning Timeline:', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12)),
              const SizedBox(height: 8),
              SingleChildScrollView(
                scrollDirection: Axis.horizontal,
                child: Row(
                  children: List.generate(base.monthlyNetCashFlowInr.length, (idx) {
                    final val = base.monthlyNetCashFlowInr[idx];
                    final isNegative = val < 0;
                    return Container(
                      width: 52,
                      margin: const EdgeInsets.only(right: 6),
                      padding: const EdgeInsets.all(6),
                      decoration: BoxDecoration(
                        color: isNegative ? Colors.red.shade50 : Colors.green.shade50,
                        borderRadius: BorderRadius.circular(6),
                        border: Border.all(color: isNegative ? Colors.red.shade200 : Colors.green.shade200),
                      ),
                      child: Column(
                        children: [
                          Text('M${idx + 1}', style: const TextStyle(fontSize: 9, color: Colors.black54)),
                          const SizedBox(height: 2),
                          Text(
                            '${isNegative ? "-" : "+"}₹${val.abs().toStringAsFixed(0)}',
                            style: TextStyle(
                              fontSize: 10,
                              fontWeight: FontWeight.bold,
                              color: isNegative ? Colors.red.shade800 : Colors.green.shade800,
                            ),
                          ),
                        ],
                      ),
                    );
                  }),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildScenarioPill(String title, String profit, String payback, Color color, {bool isHighlight = false}) {
    return Container(
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: color.withOpacity(0.08),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: color, width: isHighlight ? 1.5 : 0.8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title, style: TextStyle(fontWeight: FontWeight.bold, fontSize: 10, color: color)),
          const SizedBox(height: 4),
          Text(profit, style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: color)),
          const Text('per year', style: TextStyle(fontSize: 9, color: Colors.black54)),
          const SizedBox(height: 4),
          Text(payback, style: const TextStyle(fontSize: 9, color: Colors.black87, fontWeight: FontWeight.w600)),
        ],
      ),
    );
  }

  Widget _buildFarmerComparisonCard() {
    return Card(
      elevation: 1,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Compare Top Choices Side by Side', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
            const SizedBox(height: 8),
            SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: DataTable(
                columnSpacing: 14,
                headingRowHeight: 36,
                dataRowHeight: 40,
                columns: const [
                  DataColumn(label: Text('Enterprise', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12))),
                  DataColumn(label: Text('Yearly Profit', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12))),
                  DataColumn(label: Text('Payback', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12))),
                  DataColumn(label: Text('Space', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12))),
                  DataColumn(label: Text('Water Needs', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12))),
                ],
                rows: _comparisons.map((c) {
                  return DataRow(
                    cells: [
                      DataCell(Text(c.title, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 11))),
                      DataCell(Text('₹${c.netAnnualProfitInr.toStringAsFixed(0)}', style: const TextStyle(fontWeight: FontWeight.bold, color: Color(0xFF1B5E20), fontSize: 11))),
                      DataCell(Text('${c.paybackMonths.toStringAsFixed(0)} mos', style: const TextStyle(fontSize: 11))),
                      DataCell(Text('${c.landRequiredAcres} ac', style: const TextStyle(fontSize: 11))),
                      DataCell(Text(c.waterNeeds, style: const TextStyle(fontSize: 11))),
                    ],
                  );
                }).toList(),
              ),
            ),
          ],
        ),
      ),
    );
  }

  String _getWaterFriendlyName(String code) {
    switch (code) {
      case 'reliable_year_round':
        return 'Borewell / Good';
      case 'seasonal_canal':
        return 'Seasonal';
      case 'rainfed_limited':
        return 'Rainfed / Scarce';
      default:
        return code;
    }
  }

  void _showResourceSettingsBottomSheet(BuildContext context) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (ctx) {
        return StatefulBuilder(
          builder: (ctx, setModalState) {
            return Padding(
              padding: EdgeInsets.fromLTRB(20, 20, 20, MediaQuery.of(ctx).viewInsets.bottom + 20),
              child: SingleChildScrollView(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Text('Adjust My Farm Resources', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                        IconButton(icon: const Icon(Icons.close), onPressed: () => Navigator.pop(ctx)),
                      ],
                    ),
                    const Divider(),
                    const SizedBox(height: 8),

                    // Capital / Budget
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Text('Starting Investment Budget:', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                        Text('₹${_availableInvestment.toStringAsFixed(0)}', style: const TextStyle(fontWeight: FontWeight.bold, color: Color(0xFF1B5E20))),
                      ],
                    ),
                    Slider(
                      value: _availableInvestment,
                      min: 15000.0,
                      max: 300000.0,
                      divisions: 19,
                      activeColor: const Color(0xFF1B5E20),
                      label: '₹${_availableInvestment.toStringAsFixed(0)}',
                      onChanged: (val) {
                        setModalState(() => _availableInvestment = val);
                        setState(() => _availableInvestment = val);
                      },
                    ),
                    const SizedBox(height: 12),

                    // Spare Land
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Text('Available Spare Land:', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                        Text('${_availableLand.toStringAsFixed(2)} acres', style: const TextStyle(fontWeight: FontWeight.bold, color: Color(0xFF1B5E20))),
                      ],
                    ),
                    Slider(
                      value: _availableLand,
                      min: 0.02,
                      max: 2.0,
                      divisions: 20,
                      activeColor: const Color(0xFF1B5E20),
                      label: '${_availableLand.toStringAsFixed(2)} ac',
                      onChanged: (val) {
                        setModalState(() => _availableLand = val);
                        setState(() => _availableLand = val);
                      },
                    ),
                    const SizedBox(height: 12),

                    // Water Availability
                    const Text('Water Source Available:', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                    const SizedBox(height: 6),
                    DropdownButtonFormField<String>(
                      isExpanded: true,
                      value: _waterAvailability,
                      decoration: InputDecoration(
                        contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                        border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                      ),
                      items: const [
                        DropdownMenuItem(value: 'reliable_year_round', child: Text('Borewell / Perennial Canal (Good all year)')),
                        DropdownMenuItem(value: 'seasonal_canal', child: Text('Seasonal Canal / Farm Pond')),
                        DropdownMenuItem(value: 'rainfed_limited', child: Text('Rainfed / Scarce')),
                      ],
                      onChanged: (val) {
                        if (val != null) {
                          setModalState(() => _waterAvailability = val);
                          setState(() => _waterAvailability = val);
                        }
                      },
                    ),
                    const SizedBox(height: 14),

                    // Family Labor Hours
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Text('Daily Family Labor Time:', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                        Text('${_familyLaborHours.toStringAsFixed(1)} hrs/day', style: const TextStyle(fontWeight: FontWeight.bold, color: Color(0xFF1B5E20))),
                      ],
                    ),
                    Slider(
                      value: _familyLaborHours,
                      min: 1.0,
                      max: 6.0,
                      divisions: 10,
                      activeColor: const Color(0xFF1B5E20),
                      label: '${_familyLaborHours.toStringAsFixed(1)}h',
                      onChanged: (val) {
                        setModalState(() => _familyLaborHours = val);
                        setState(() => _familyLaborHours = val);
                      },
                    ),
                    const SizedBox(height: 16),

                    SizedBox(
                      width: double.infinity,
                      child: ElevatedButton(
                        style: ElevatedButton.styleFrom(
                          backgroundColor: const Color(0xFF1B5E20),
                          foregroundColor: Colors.white,
                          padding: const EdgeInsets.symmetric(vertical: 12),
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                        ),
                        onPressed: () {
                          Navigator.pop(ctx);
                          _matchOpportunities();
                        },
                        child: const Text('Update & Recalculate Opportunities', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                      ),
                    ),
                  ],
                ),
              ),
            );
          },
        );
      },
    );
  }
}
