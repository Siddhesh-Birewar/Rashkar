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

  @override
  Widget build(BuildContext context) {
    final appState = AppState.instance;

    return Scaffold(
      backgroundColor: const Color(0xFFF6F8F6),
      appBar: AppBar(
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Income Diversification', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
            Text(
              'For ${appState.activeCropName} · ${appState.activeTaluka}, ${appState.activeDistrict}',
              style: const TextStyle(fontSize: 12, color: Colors.white70),
            ),
          ],
        ),
        backgroundColor: const Color(0xFF00695C),
        foregroundColor: Colors.white,
        actions: [
          IconButton(icon: const Icon(Icons.refresh), onPressed: _matchOpportunities),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator(color: Color(0xFF00695C)))
          : SingleChildScrollView(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  // SECTION 1: Interactive Farmer Resource Questionnaire
                  _buildQuestionnaireCard(),
                  const SizedBox(height: 16),

                  // SECTION 2: Scored Opportunities Catalog
                  _buildScoredOpportunitiesSection(),
                  const SizedBox(height: 16),

                  // SECTION 3: 3-Scenario Financial Simulator
                  if (_scenario != null) _buildFinancialSimulatorCard(),
                  if (_scenario != null) const SizedBox(height: 16),

                  // SECTION 4: Side-by-Side Alternative Comparison Matrix
                  if (_comparisons.isNotEmpty) _buildComparisonCard(),
                  if (_comparisons.isNotEmpty) const SizedBox(height: 16),

                  // SECTION 5: Local Mandi Benchmark & NABARD Citation
                  if (_scenario != null) _buildMarketBenchmarkCard(),
                  const SizedBox(height: 24),
                ],
              ),
            ),
    );
  }

  // ==================== SECTION 1: Questionnaire ====================
  Widget _buildQuestionnaireCard() {
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: const [
                Icon(Icons.tune, color: Color(0xFF00695C)),
                SizedBox(width: 8),
                Text('Farmer Resource Profile', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
              ],
            ),
            const Text(
              'Customize your resources to rank enterprises by real-world feasibility:',
              style: TextStyle(fontSize: 12, color: Colors.black54),
            ),
            const SizedBox(height: 14),

            // Capital Slider
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text('Available Investment Capital:', style: TextStyle(fontWeight: FontWeight.w600, fontSize: 13)),
                Text('₹${_availableInvestment.toStringAsFixed(0)}', style: const TextStyle(fontWeight: FontWeight.bold, color: Color(0xFF00695C))),
              ],
            ),
            Slider(
              value: _availableInvestment,
              min: 15000.0,
              max: 300000.0,
              divisions: 19,
              activeColor: const Color(0xFF00695C),
              label: '₹${_availableInvestment.toStringAsFixed(0)}',
              onChanged: (val) {
                setState(() => _availableInvestment = val);
                _matchOpportunities();
              },
            ),

            // Land Slider
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text('Spare / Unallocated Land:', style: TextStyle(fontWeight: FontWeight.w600, fontSize: 13)),
                Text('${_availableLand.toStringAsFixed(2)} acres', style: const TextStyle(fontWeight: FontWeight.bold, color: Color(0xFF00695C))),
              ],
            ),
            Slider(
              value: _availableLand,
              min: 0.02,
              max: 2.0,
              divisions: 20,
              activeColor: const Color(0xFF00695C),
              label: '${_availableLand.toStringAsFixed(2)} acres',
              onChanged: (val) {
                setState(() => _availableLand = val);
                _matchOpportunities();
              },
            ),

            // Water Availability Dropdown
            Row(
              children: [
                const Expanded(
                  flex: 2,
                  child: Text('Water Source:', style: TextStyle(fontWeight: FontWeight.w600, fontSize: 13)),
                ),
                Expanded(
                  flex: 3,
                  child: DropdownButtonFormField<String>(
                    value: _waterAvailability,
                    decoration: InputDecoration(
                      contentPadding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                      border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
                    ),
                    items: const [
                      DropdownMenuItem(value: 'reliable_year_round', child: Text('Borewell / Perennial Canal')),
                      DropdownMenuItem(value: 'seasonal_canal', child: Text('Seasonal Canal / Farm Pond')),
                      DropdownMenuItem(value: 'rainfed_limited', child: Text('Rainfed / Scarce')),
                    ],
                    onChanged: (val) {
                      if (val != null) {
                        setState(() => _waterAvailability = val);
                        _matchOpportunities();
                      }
                    },
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),

            // Family Labor Hours
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text('Available Family Labor:', style: TextStyle(fontWeight: FontWeight.w600, fontSize: 13)),
                Text('${_familyLaborHours.toStringAsFixed(1)} hrs/day', style: const TextStyle(fontWeight: FontWeight.bold, color: Color(0xFF00695C))),
              ],
            ),
            Slider(
              value: _familyLaborHours,
              min: 1.0,
              max: 6.0,
              divisions: 10,
              activeColor: const Color(0xFF00695C),
              label: '${_familyLaborHours.toStringAsFixed(1)}h',
              onChanged: (val) {
                setState(() => _familyLaborHours = val);
                _matchOpportunities();
              },
            ),

            // Category Preference
            Row(
              children: [
                const Expanded(
                  flex: 2,
                  child: Text('Enterprise Category:', style: TextStyle(fontWeight: FontWeight.w600, fontSize: 13)),
                ),
                Expanded(
                  flex: 3,
                  child: DropdownButtonFormField<String>(
                    value: _categoryPreference,
                    decoration: InputDecoration(
                      contentPadding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                      border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
                    ),
                    items: const [
                      DropdownMenuItem(value: 'all', child: Text('All Opportunities')),
                      DropdownMenuItem(value: 'livestock', child: Text('Livestock & Small Ruminants')),
                      DropdownMenuItem(value: 'byproduct_utilization', child: Text('Byproduct & Biomass')),
                      DropdownMenuItem(value: 'value_addition', child: Text('Processing & Value Addition')),
                      DropdownMenuItem(value: 'horticulture', child: Text('Horticulture & Nursery')),
                    ],
                    onChanged: (val) {
                      if (val != null) {
                        setState(() => _categoryPreference = val);
                        _matchOpportunities();
                      }
                    },
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  // ==================== SECTION 2: Scored Opportunities ====================
  Widget _buildScoredOpportunitiesSection() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'MATCHED ENTERPRISE OPPORTUNITIES (NABARD FY26-27)',
          style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: Colors.black54, letterSpacing: 0.8),
        ),
        const SizedBox(height: 8),
        if (_scoredOpportunities.isEmpty)
          const Card(
            child: Padding(
              padding: EdgeInsets.all(16.0),
              child: Text('No enterprises matched your exact budget/land filter. Try adjusting capital slider.'),
            ),
          )
        else
          ..._scoredOpportunities.map((s) => _buildScoredOpportunityCard(s)).toList(),
      ],
    );
  }

  Widget _buildScoredOpportunityCard(ScoredOpportunityItem s) {
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
            color: isSelected ? const Color(0xFF00695C) : Colors.grey.shade200,
            width: isSelected ? 2.0 : 1.0,
          ),
        ),
        child: Padding(
          padding: const EdgeInsets.all(14.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(8),
                    decoration: BoxDecoration(
                      color: scoreColor.withOpacity(0.12),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Text(
                      '${s.suitabilityScorePct}%',
                      style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15, color: scoreColor),
                    ),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          s.opportunity.title,
                          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                        ),
                        Text(
                          s.opportunity.tagline.isNotEmpty ? s.opportunity.tagline : s.opportunity.category,
                          style: const TextStyle(fontSize: 11, color: Colors.black54),
                        ),
                      ],
                    ),
                  ),
                  Radio<String>(
                    value: s.opportunity.opportunityId,
                    groupValue: _selectedScored?.opportunity.opportunityId,
                    activeColor: const Color(0xFF00695C),
                    onChanged: (val) {
                      setState(() => _selectedScored = s);
                      _calculateScenario();
                      _loadComparisons();
                    },
                  ),
                ],
              ),
              const SizedBox(height: 8),
              Text(s.opportunity.summary, style: const TextStyle(fontSize: 12, color: Colors.black87)),
              const SizedBox(height: 8),

              // Suitability verdict & reasons
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: s.isSuitable ? const Color(0xFFE8F5E9) : const Color(0xFFFFF3E0),
                  borderRadius: BorderRadius.circular(6),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Verdict: ${s.suitabilityVerdict}',
                      style: TextStyle(
                        fontWeight: FontWeight.bold,
                        fontSize: 11,
                        color: s.isSuitable ? const Color(0xFF1B5E20) : Colors.deepOrange,
                      ),
                    ),
                    if (s.reasonsWhySuitable.isNotEmpty)
                      Text('• ${s.reasonsWhySuitable.first}', style: const TextStyle(fontSize: 11, color: Colors.black87)),
                    if (s.reasonsWhyUnsuitable.isNotEmpty)
                      Text('• ${s.reasonsWhyUnsuitable.first}', style: TextStyle(fontSize: 11, color: Colors.red.shade900)),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  // ==================== SECTION 3: 3-Scenario Simulator ====================
  Widget _buildFinancialSimulatorCard() {
    final sc = _scenario!;
    final baseScenario = sc.scenarios['base'];
    final consScenario = sc.scenarios['conservative'];
    final optScenario = sc.scenarios['optimistic'];

    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.calculate, color: Color(0xFF00695C)),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    'Financial Simulator: ${sc.opportunityTitle}',
                    style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15),
                  ),
                ),
                if (_isCalculating)
                  const SizedBox(width: 14, height: 14, child: CircularProgressIndicator(strokeWidth: 2, color: Color(0xFF00695C))),
              ],
            ),
            const SizedBox(height: 6),
            Text(
              'Capex: ₹${sc.calculatedCapexInr.toStringAsFixed(0)} · Working Capital: ₹${sc.workingCapitalInr.toStringAsFixed(0)} · Total: ₹${sc.totalInitialOutlayInr.toStringAsFixed(0)}',
              style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: Colors.black87),
            ),
            const SizedBox(height: 14),

            // 3 Scenarios Cards
            if (baseScenario != null && consScenario != null && optScenario != null)
              Row(
                children: [
                  Expanded(child: _buildScenarioBox('Conservative', consScenario, Colors.orange.shade800)),
                  const SizedBox(width: 8),
                  Expanded(child: _buildScenarioBox('Base Case', baseScenario, const Color(0xFF00695C), isMain: true)),
                  const SizedBox(width: 8),
                  Expanded(child: _buildScenarioBox('Optimistic', optScenario, Colors.green.shade800)),
                ],
              ),
            const SizedBox(height: 14),

            // 12-Month Net Cash Flow Timeline
            if (baseScenario != null && baseScenario.monthlyNetCashFlowInr.isNotEmpty)
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('12-Month Cash Flow Horizon (Base Case):', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12)),
                  const SizedBox(height: 8),
                  SingleChildScrollView(
                    scrollDirection: Axis.horizontal,
                    child: Row(
                      children: List.generate(baseScenario.monthlyNetCashFlowInr.length, (idx) {
                        final val = baseScenario.monthlyNetCashFlowInr[idx];
                        final isNegative = val < 0;
                        return Container(
                          width: 55,
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
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildScenarioBox(String title, FinancialScenarioDetail d, Color col, {bool isMain = false}) {
    return Container(
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: col.withOpacity(0.08),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: col, width: isMain ? 1.5 : 0.8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title, style: TextStyle(fontWeight: FontWeight.bold, fontSize: 11, color: col)),
          const SizedBox(height: 6),
          Text('₹${d.netAnnualProfitInr.toStringAsFixed(0)}', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: col)),
          const Text('Net Profit/yr', style: TextStyle(fontSize: 9, color: Colors.black54)),
          const SizedBox(height: 6),
          Text('${d.breakEvenMonths.toStringAsFixed(1)} mos', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12)),
          const Text('Break-even', style: TextStyle(fontSize: 9, color: Colors.black54)),
        ],
      ),
    );
  }

  // ==================== SECTION 4: Side-by-Side Comparison ====================
  Widget _buildComparisonCard() {
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Enterprise Comparison Matrix', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
            const SizedBox(height: 8),
            SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: DataTable(
                columnSpacing: 16,
                columns: const [
                  DataColumn(label: Text('Enterprise', style: TextStyle(fontWeight: FontWeight.bold))),
                  DataColumn(label: Text('Net Profit/yr', style: TextStyle(fontWeight: FontWeight.bold))),
                  DataColumn(label: Text('Payback', style: TextStyle(fontWeight: FontWeight.bold))),
                  DataColumn(label: Text('Land', style: TextStyle(fontWeight: FontWeight.bold))),
                  DataColumn(label: Text('Water', style: TextStyle(fontWeight: FontWeight.bold))),
                  DataColumn(label: Text('Verdict', style: TextStyle(fontWeight: FontWeight.bold))),
                ],
                rows: _comparisons.map((c) {
                  return DataRow(
                    cells: [
                      DataCell(Text(c.title, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 12))),
                      DataCell(Text('₹${c.netAnnualProfitInr.toStringAsFixed(0)}', style: const TextStyle(fontWeight: FontWeight.bold, color: Color(0xFF00695C)))),
                      DataCell(Text('${c.paybackMonths.toStringAsFixed(0)} mos')),
                      DataCell(Text('${c.landRequiredAcres} ac')),
                      DataCell(Text(c.waterNeeds)),
                      DataCell(Text(c.suitabilityVerdict, style: const TextStyle(fontWeight: FontWeight.bold))),
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

  // ==================== SECTION 5: Mandi Benchmark & Citation ====================
  Widget _buildMarketBenchmarkCard() {
    final sc = _scenario!;
    final mandi = sc.localMandiBenchmark;

    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: const [
                Icon(Icons.storefront, color: Colors.blueGrey),
                SizedBox(width: 8),
                Text('Local APMC Mandi Benchmark', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
              ],
            ),
            const SizedBox(height: 8),
            Text(
              'Commodity: ${mandi['commodity'] ?? "Local Commodity"} · Benchmark: ${mandi['benchmark_price'] ?? "Prevailing Modal Price"}',
              style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Colors.black87),
            ),
            Text(
              'Reporting Source: ${mandi['reporting_mandi'] ?? "Agmarknet APMC"}',
              style: const TextStyle(fontSize: 11, color: Colors.black54),
            ),
            const SizedBox(height: 10),
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: Colors.grey.shade50,
                borderRadius: BorderRadius.circular(8),
              ),
              child: Text(
                sc.disclaimer.isNotEmpty ? sc.disclaimer : 'Financial models calibrated with official NABARD Maharashtra unit costs.',
                style: const TextStyle(fontSize: 10, color: Colors.black54),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
