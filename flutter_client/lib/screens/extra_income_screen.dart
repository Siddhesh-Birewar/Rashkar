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
  List<IncomeOpportunity> _opportunities = [];
  IncomeOpportunity? _selectedOpportunity;
  IncomeScenario? _scenario;
  double _customBudget = 25000.0;
  bool _isLoading = true;
  bool _isCalculating = false;

  @override
  void initState() {
    super.initState();
    AppState.instance.addListener(_onStateChange);
    _loadOpportunities();
  }

  @override
  void dispose() {
    AppState.instance.removeListener(_onStateChange);
    super.dispose();
  }

  void _onStateChange() {
    _loadOpportunities();
  }

  Future<void> _loadOpportunities() async {
    setState(() => _isLoading = true);
    final crop = AppState.instance.activeCropCode;
    var opps = await ApiService.getIncomeOpportunities(cropCode: crop);
    if (opps.isEmpty) {
      // Fallback to general opportunities if no crop-specific match
      opps = await ApiService.getIncomeOpportunities();
    }

    if (mounted) {
      setState(() {
        _opportunities = opps;
        if (opps.isNotEmpty) {
          _selectedOpportunity = opps.first;
          _customBudget = opps.first.minInvestmentInr;
        } else {
          _selectedOpportunity = null;
        }
        _isLoading = false;
      });
      if (_selectedOpportunity != null) {
        _calculateScenario();
      }
    }
  }

  Future<void> _calculateScenario() async {
    if (_selectedOpportunity == null) return;
    setState(() => _isCalculating = true);
    final sc = await ApiService.calculateIncomeScenario(
      opportunityId: _selectedOpportunity!.opportunityId,
      customBudgetInr: _customBudget,
    );
    if (mounted) {
      setState(() {
        _scenario = sc;
        _isCalculating = false;
      });
    }
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
            const Text('Extra Income & Diversification', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
            Text(
              'For ${appState.activeCropName} · ${appState.activeTaluka}, ${appState.activeDistrict}',
              style: const TextStyle(fontSize: 12, color: Colors.white70),
            ),
          ],
        ),
        backgroundColor: const Color(0xFF00695C),
        foregroundColor: Colors.white,
        actions: [
          IconButton(icon: const Icon(Icons.refresh), onPressed: _loadOpportunities),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator(color: Color(0xFF00695C)))
          : SingleChildScrollView(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  // Crop Context Tag
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                    decoration: BoxDecoration(
                      color: const Color(0xFFE0F2F1),
                      borderRadius: BorderRadius.circular(10),
                      border: Border.all(color: const Color(0xFF80CBC4)),
                    ),
                    child: Row(
                      children: [
                        const Icon(Icons.eco, size: 16, color: Color(0xFF004D40)),
                        const SizedBox(width: 6),
                        Expanded(
                          child: Text(
                            'Enterprises compatible with ${appState.activeCropName} residues & resources in ${appState.activeDistrict}',
                            style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Color(0xFF004D40)),
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 16),

                  const Text(
                    'CURATED AGRO-ENTERPRISES',
                    style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: Color(0xFF333333), letterSpacing: 0.8),
                  ),
                  const SizedBox(height: 8),

                  // Opportunity Selector Horizontal Cards
                  SizedBox(
                    height: 125,
                    child: ListView.builder(
                      scrollDirection: Axis.horizontal,
                      itemCount: _opportunities.length,
                      itemBuilder: (context, idx) {
                        final opp = _opportunities[idx];
                        final isSel = _selectedOpportunity?.opportunityId == opp.opportunityId;
                        return InkWell(
                          onTap: () {
                            setState(() {
                              _selectedOpportunity = opp;
                              _customBudget = opp.minInvestmentInr;
                            });
                            _calculateScenario();
                          },
                          child: Container(
                            width: 230,
                            margin: const EdgeInsets.only(right: 12),
                            padding: const EdgeInsets.all(12),
                            decoration: BoxDecoration(
                              color: isSel ? const Color(0xFFE0F2F1) : Colors.white,
                              borderRadius: BorderRadius.circular(14),
                              border: Border.all(
                                color: isSel ? const Color(0xFF00695C) : Colors.black12,
                                width: isSel ? 2.0 : 1.0,
                              ),
                            ),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  opp.title,
                                  maxLines: 2,
                                  overflow: TextOverflow.ellipsis,
                                  style: TextStyle(
                                    fontWeight: FontWeight.bold,
                                    fontSize: 13,
                                    color: isSel ? const Color(0xFF004D40) : Colors.black87,
                                  ),
                                ),
                                const Spacer(),
                                Text(
                                  'From ₹${opp.minInvestmentInr.toInt()}',
                                  style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: Color(0xFF00695C)),
                                ),
                                Text(
                                  'Payback: ~${opp.paybackPeriodMonths} mos · Profit: ₹${opp.potentialAnnualProfitInr.toInt()}/yr',
                                  style: const TextStyle(fontSize: 11, color: Colors.black54),
                                ),
                              ],
                            ),
                          ),
                        );
                      },
                    ),
                  ),
                  const SizedBox(height: 20),

                  // Selected Opportunity Details & Calculator
                  if (_selectedOpportunity != null) ...[
                    Card(
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                      child: Padding(
                        padding: const EdgeInsets.all(16.0),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              _selectedOpportunity!.title,
                              style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Color(0xFF004D40)),
                            ),
                            const SizedBox(height: 6),
                            Text(
                              _selectedOpportunity!.summary,
                              style: const TextStyle(fontSize: 14, color: Colors.black87),
                            ),
                            const SizedBox(height: 16),

                            // Interactive Budget Slider
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                const Text('Investment Budget:', style: TextStyle(fontWeight: FontWeight.w600, fontSize: 14)),
                                Text('₹${_customBudget.toInt()}', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18, color: Color(0xFF00695C))),
                              ],
                            ),
                            Slider(
                              value: _customBudget,
                              min: _selectedOpportunity!.minInvestmentInr,
                              max: _selectedOpportunity!.maxInvestmentInr * 1.5,
                              divisions: 15,
                              activeColor: const Color(0xFF00695C),
                              onChanged: (val) {
                                setState(() => _customBudget = val);
                              },
                              onChangeEnd: (_) => _calculateScenario(),
                            ),
                          ],
                        ),
                      ),
                    ),
                    const SizedBox(height: 16),

                    // Financial Scenario Calculation Results
                    if (_isCalculating)
                      const Center(child: CircularProgressIndicator(color: Color(0xFF00695C)))
                    else if (_scenario != null) ...[
                      Card(
                        color: const Color(0xFFF1F8E9),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                        child: Padding(
                          padding: const EdgeInsets.all(16.0),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Text('ESTIMATED FINANCIAL RETURN', style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: Color(0xFF2E7D32))),
                              const SizedBox(height: 12),
                              Row(
                                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                children: [
                                  _buildFinanceColumn('Capital (CAPEX)', '₹${_scenario!.calculatedCapexInr.toInt()}'),
                                  _buildFinanceColumn('Yearly Operating', '₹${_scenario!.calculatedOpexAnnualInr.toInt()}'),
                                  _buildFinanceColumn('Net Profit / Yr', '₹${_scenario!.calculatedNetProfitAnnualInr.toInt()}', isHighlight: true),
                                ],
                              ),
                              const Divider(height: 24),
                              Row(
                                children: [
                                  const Icon(Icons.timer_outlined, size: 20, color: Color(0xFF2E7D32)),
                                  const SizedBox(width: 8),
                                  Text(
                                    'Estimated Break-even: ${_scenario!.calculatedBreakEvenMonths} months',
                                    style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                                  ),
                                ],
                              ),
                            ],
                          ),
                        ),
                      ),
                      const SizedBox(height: 16),

                      // Assumptions & Sourced Citations
                      Card(
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                        child: Padding(
                          padding: const EdgeInsets.all(16.0),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Text('Model Assumptions & Benchmarks', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                              const SizedBox(height: 6),
                              ..._scenario!.assumptionsApplied.map((a) => Text('• $a', style: const TextStyle(fontSize: 13, color: Colors.black87))).toList(),
                              const SizedBox(height: 12),
                              const Text('Key Operational Risks to Monitor:', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                              const SizedBox(height: 4),
                              ..._scenario!.risksToMonitor.map((r) => Text('• $r', style: const TextStyle(fontSize: 12, color: Colors.black54))).toList(),
                              const Divider(height: 20),
                              Text('Source: ${_scenario!.sourceAttribution}', style: const TextStyle(fontSize: 12, color: Colors.black54, fontStyle: FontStyle.italic)),
                            ],
                          ),
                        ),
                      ),
                    ],
                  ]
                ],
              ),
            ),
    );
  }

  Widget _buildFinanceColumn(String label, String value, {bool isHighlight = false}) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: const TextStyle(fontSize: 11, color: Colors.black54)),
        const SizedBox(height: 2),
        Text(
          value,
          style: TextStyle(
            fontSize: isHighlight ? 18 : 15,
            fontWeight: FontWeight.bold,
            color: isHighlight ? const Color(0xFF1B5E20) : Colors.black87,
          ),
        ),
      ],
    );
  }
}
