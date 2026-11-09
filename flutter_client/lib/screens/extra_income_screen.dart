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
  // Farmer Resource Profile State
  double _availableInvestment = 0.0; // Defaults to ZERO CASH
  double _monthlyOperatingBudget = 0.0;
  double _availableLand = 0.25;
  double _unusedLand = 0.1;
  String _waterAvailability = 'seasonal_canal';
  double _familyLaborHours = 2.0;
  String _existingLivestock = 'none';
  bool _hasStorageRoom = false;
  bool _hasAnimalShed = false;
  bool _hasShadedSpace = false;
  List<String> _cropByproducts = ['soybean_straw', 'cow_dung'];
  List<String> _interests = ['composting', 'livestock', 'nursery'];
  String _riskTolerance = 'moderate';
  String _selectedCategory = 'all'; // all, zero_cash, very_low_cost, moderate_enterprise, crop_diversification, group_external
  String _ageRange = '36_to_45';
  String _workPreference = 'active_physical';
  String _paybackHorizon = 'within_1_year';
  String _familyManagementRole = 'personal_direct';

  List<ScoredOpportunityItem> _discoveredOpportunities = [];
  ScoredOpportunityItem? _selectedOpportunity;
  IncomeScenario? _scenario;
  List<OpportunityComparisonItem> _comparisons = [];
  List<SavedIncomePlan> _savedPlans = [];

  bool _isLoading = true;
  bool _isCalculating = false;
  bool _isSavingPlan = false;

  @override
  void initState() {
    super.initState();
    AppState.instance.addListener(_onStateChange);
    _initializeData();
  }

  @override
  void dispose() {
    AppState.instance.removeListener(_onStateChange);
    super.dispose();
  }

  void _onStateChange() {
    _discoverOpportunities();
  }

  Future<void> _initializeData() async {
    setState(() => _isLoading = true);
    final farmId = AppState.instance.activeFarmId ?? 'farm_demo_pune_01';

    try {
      final profile = await ApiService.getFarmResourceProfile(farmId);
      _availableInvestment = profile.availableInvestmentInr;
      _monthlyOperatingBudget = profile.monthlyOperatingBudgetInr;
      _availableLand = profile.availableLandAcres > 0 ? profile.availableLandAcres : 0.25;
      _unusedLand = profile.unusedLandAcres;
      _waterAvailability = profile.waterAvailability;
      _familyLaborHours = profile.familyLaborHoursDay;
      _existingLivestock = profile.existingLivestock;
      _hasStorageRoom = profile.hasStorageRoom;
      _hasAnimalShed = profile.hasAnimalShed;
      _hasShadedSpace = profile.hasShadedSpace;
      if (profile.cropByproducts.isNotEmpty) {
        _cropByproducts = List<String>.from(profile.cropByproducts);
      }
      if (profile.interests.isNotEmpty) {
        _interests = List<String>.from(profile.interests);
      }
    } catch (_) {}

    await _discoverOpportunities();
    await _loadSavedPlans();
  }

  Future<void> _discoverOpportunities() async {
    final farmId = AppState.instance.activeFarmId ?? 'farm_demo_pune_01';
    setState(() => _isLoading = true);

    try {
      final items = await ApiService.discoverFarmOpportunities(
        farmId,
        customBudgetInr: _availableInvestment,
      );

      if (mounted) {
        setState(() {
          _discoveredOpportunities = items;
          if (items.isNotEmpty) {
            _selectedOpportunity = items.first;
          } else {
            _selectedOpportunity = null;
          }
          _isLoading = false;
        });

        if (_selectedOpportunity != null) {
          _calculateScenario();
          _loadComparisons();
        }
      }
    } catch (_) {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _loadSavedPlans() async {
    final farmId = AppState.instance.activeFarmId ?? 'farm_demo_pune_01';
    try {
      final plans = await ApiService.getSavedIncomePlans(farmId);
      if (mounted) {
        setState(() => _savedPlans = plans);
      }
    } catch (_) {}
  }

  Future<void> _calculateScenario() async {
    if (_selectedOpportunity == null) return;
    setState(() => _isCalculating = true);

    try {
      final sc = await ApiService.calculateIncomeScenario(
        opportunityId: _selectedOpportunity!.opportunity.opportunityId,
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
    } catch (_) {
      if (mounted) setState(() => _isCalculating = false);
    }
  }

  Future<void> _loadComparisons() async {
    if (_discoveredOpportunities.isEmpty) return;
    final topIds = _discoveredOpportunities
        .take(3)
        .map((s) => s.opportunity.opportunityId)
        .toList();

    try {
      final comp = await ApiService.compareOpportunities(
        opportunityIds: topIds,
        customBudgetInr: _availableInvestment,
      );
      if (mounted) {
        setState(() => _comparisons = comp);
      }
    } catch (_) {}
  }

  Future<void> _handleSavePlan() async {
    if (_selectedOpportunity == null) return;
    setState(() => _isSavingPlan = true);
    final farmId = AppState.instance.activeFarmId ?? 'farm_demo_pune_01';

    final res = await ApiService.saveIncomePlan(
      farmId: farmId,
      opportunityId: _selectedOpportunity!.opportunity.opportunityId,
      plannedInvestmentInr: _selectedOpportunity!.opportunity.minInvestmentInr,
      notes: 'Plan saved from Extra Income discovery interface.',
    );

    if (mounted) {
      setState(() => _isSavingPlan = false);
      if (res != null) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            backgroundColor: const Color(0xFF1B5E20),
            content: Text('Saved "${_selectedOpportunity!.opportunity.title}" to your farm plans!'),
          ),
        );
        _loadSavedPlans();
      }
    }
  }

  String _formatCurrency(num amount) {
    if (amount == 0) return '₹0';
    if (amount >= 100000) {
      return '₹${(amount / 100000).toStringAsFixed(1)} Lakh';
    }
    return '₹${amount.toStringAsFixed(0)}';
  }

  List<ScoredOpportunityItem> get _filteredOpportunities {
    if (_selectedCategory == 'all') return _discoveredOpportunities;
    return _discoveredOpportunities
        .where((o) => o.opportunity.category == _selectedCategory)
        .toList();
  }

  @override
  Widget build(BuildContext context) {
    final appState = AppState.instance;

    return Scaffold(
      backgroundColor: const Color(0xFFF7F9F7),
      appBar: AppBar(
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Extra Farm Income',
              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18),
            ),
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
            tooltip: 'Discover Possibilities',
            icon: const Icon(Icons.refresh),
            onPressed: _discoverOpportunities,
          ),
        ],
      ),
      body: _isLoading
          ? const Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  CircularProgressIndicator(color: Color(0xFF1B5E20)),
                  SizedBox(height: 12),
                  Text(
                    'Discovering feasible opportunities for your farm...',
                    style: TextStyle(fontSize: 13, color: Colors.black54),
                  ),
                ],
              ),
            )
          : SingleChildScrollView(
              padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 14.0),
              child: Center(
                child: ConstrainedBox(
                  constraints: const BoxConstraints(maxWidth: 840),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      // 1. Overview & Resource Summary Card
                      _buildOverviewCard(),
                      const SizedBox(height: 16),

                      // 2. Category Filter Chips
                      _buildCategoryFilterBar(),
                      const SizedBox(height: 16),

                      // 3. Discovered Opportunities Feed
                      _buildOpportunitiesSection(),
                      const SizedBox(height: 16),

                      // 4. Detailed Outlook & Cashflow Timeline
                      if (_scenario != null && _selectedOpportunity != null) ...[
                        _buildOpportunityDetailCard(),
                        const SizedBox(height: 16),
                      ],

                      // 5. Reconciled Side-by-Side Comparison
                      if (_comparisons.isNotEmpty) ...[
                        _buildComparisonCard(),
                        const SizedBox(height: 16),
                      ],

                      // 6. Saved Farm Plans
                      if (_savedPlans.isNotEmpty) ...[
                        _buildSavedPlansCard(),
                        const SizedBox(height: 16),
                      ],

                      // 7. Grounding, Provenance & Transparent Methodology
                      _buildProvenanceCard(),
                      const SizedBox(height: 24),
                    ],
                  ),
                ),
              ),
            ),
    );
  }

  // ==================== 1. OVERVIEW & RESOURCE CARD ====================
  Widget _buildOverviewCard() {
    return Card(
      elevation: 1.5,
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
                  decoration: const BoxDecoration(
                    color: Color(0xFFE8F5E9),
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
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                          color: Color(0xFF1B5E20),
                        ),
                      ),
                      SizedBox(height: 2),
                      Text(
                        'Start with zero additional cash. Then explore affordable low-investment options.',
                        style: TextStyle(fontSize: 12, color: Colors.black54),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 14),

            // Resource indicators
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
              decoration: BoxDecoration(
                color: Colors.grey.shade50,
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: Colors.grey.shade200),
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceAround,
                children: [
                  _buildResourceMini(
                    'Budget',
                    _availableInvestment == 0 ? '₹0 (Zero Cash)' : _formatCurrency(_availableInvestment),
                    Icons.account_balance_wallet_outlined,
                  ),
                  _buildResourceMini(
                    'Spare Land',
                    '${_availableLand.toStringAsFixed(2)} ac',
                    Icons.landscape_outlined,
                  ),
                  _buildResourceMini(
                    'Water',
                    _getWaterLabel(_waterAvailability),
                    Icons.water_drop_outlined,
                  ),
                  _buildResourceMini(
                    'Family Labor',
                    '${_familyLaborHours.toStringAsFixed(1)} h/day',
                    Icons.people_outline,
                  ),
                ],
              ),
            ),
            const SizedBox(height: 12),

            SizedBox(
              width: double.infinity,
              child: OutlinedButton.icon(
                style: OutlinedButton.styleFrom(
                  foregroundColor: const Color(0xFF1B5E20),
                  side: const BorderSide(color: Color(0xFF2E7D32)),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                  padding: const EdgeInsets.symmetric(vertical: 10),
                ),
                icon: const Icon(Icons.tune, size: 18),
                label: const Text(
                  'Change Farm Resources & Affordability',
                  style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
                ),
                onPressed: () => _showResourceSettingsBottomSheet(context),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildResourceMini(String label, String value, IconData icon) {
    return Column(
      children: [
        Icon(icon, size: 18, color: const Color(0xFF2E7D32)),
        const SizedBox(height: 3),
        Text(value, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 11)),
        Text(label, style: const TextStyle(fontSize: 10, color: Colors.black54)),
      ],
    );
  }

  String _getWaterLabel(String code) {
    switch (code) {
      case 'reliable_year_round':
        return 'Perennial';
      case 'seasonal_canal':
        return 'Seasonal';
      case 'rainfed_limited':
      case 'rainfed_only':
        return 'Rainfed';
      default:
        return 'Seasonal';
    }
  }

  // ==================== 2. CATEGORY FILTER BAR ====================
  Widget _buildCategoryFilterBar() {
    final categories = [
      {'id': 'all', 'label': 'All Possibilities'},
      {'id': 'zero_cash', 'label': 'Zero Cash / Savings'},
      {'id': 'very_low_cost', 'label': 'Very Low Cost (< ₹15k)'},
      {'id': 'moderate_enterprise', 'label': 'Commercial Units'},
      {'id': 'crop_diversification', 'label': 'Crop Options'},
      {'id': 'group_external', 'label': 'FPO / Collective'},
    ];

    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: Row(
        children: categories.map((cat) {
          final isSelected = _selectedCategory == cat['id'];
          return Padding(
            padding: const EdgeInsets.only(right: 8.0),
            child: FilterChip(
              label: Text(
                cat['label']!,
                style: TextStyle(
                  fontSize: 12,
                  fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                  color: isSelected ? Colors.white : const Color(0xFF1B5E20),
                ),
              ),
              selected: isSelected,
              selectedColor: const Color(0xFF1B5E20),
              backgroundColor: Colors.white,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(20),
                side: BorderSide(
                  color: isSelected ? const Color(0xFF1B5E20) : Colors.grey.shade300,
                ),
              ),
              onSelected: (bool selected) {
                setState(() {
                  _selectedCategory = selected ? cat['id']! : 'all';
                });
              },
            ),
          );
        }).toList(),
      ),
    );
  }

  // ==================== 3. DISCOVERED OPPORTUNITIES FEED ====================
  Widget _buildOpportunitiesSection() {
    final list = _filteredOpportunities;

    if (list.isEmpty) {
      return Card(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
        child: Padding(
          padding: const EdgeInsets.all(20.0),
          child: Column(
            children: [
              const Icon(Icons.search_off, size: 40, color: Colors.grey),
              const SizedBox(height: 8),
              const Text(
                'No opportunities match this specific filter.',
                style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
              ),
              const SizedBox(height: 4),
              const Text(
                'Try selecting "All Possibilities" or adjust your farm resources.',
                style: TextStyle(fontSize: 12, color: Colors.black54),
              ),
              const SizedBox(height: 12),
              ElevatedButton(
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF1B5E20),
                  foregroundColor: Colors.white,
                ),
                onPressed: () => setState(() => _selectedCategory = 'all'),
                child: const Text('Show All Opportunities'),
              ),
            ],
          ),
        ),
      );
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              '${list.length} FEASIBLE POSSIBILITIES FOUND',
              style: const TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.bold,
                color: Color(0xFF1B5E20),
                letterSpacing: 0.8,
              ),
            ),
            const Text(
              'Ranked by resource fit',
              style: TextStyle(fontSize: 11, color: Colors.black54),
            ),
          ],
        ),
        const SizedBox(height: 8),
        ...list.map((item) => _buildOpportunityCard(item)).toList(),
      ],
    );
  }

  Widget _buildOpportunityCard(ScoredOpportunityItem item) {
    final isSelected = _selectedOpportunity?.opportunity.opportunityId == item.opportunity.opportunityId;
    final isFeasible = item.isFeasible;
    final opp = item.opportunity;

    // Honest status pill
    Color statusBgColor;
    Color statusTextColor;
    String statusLabel;

    if (item.feasibilityStatus == 'HIGHLY_FEASIBLE' || item.feasibilityStatus == 'FEASIBLE_NOW') {
      statusBgColor = const Color(0xFFE8F5E9);
      statusTextColor = const Color(0xFF1B5E20);
      statusLabel = opp.category == 'zero_cash' ? 'Zero Extra Cash' : 'Affordable Now';
    } else if (item.feasibilityStatus == 'NOT_CURRENTLY_AFFORDABLE') {
      statusBgColor = const Color(0xFFFFF3E0);
      statusTextColor = const Color(0xFFE65100);
      statusLabel = 'Capital Shortfall: ${_formatCurrency(item.capitalGapInr)}';
    } else {
      statusBgColor = Colors.grey.shade100;
      statusTextColor = Colors.black87;
      statusLabel = item.suitabilityVerdict;
    }

    return Card(
      elevation: isSelected ? 3 : 1,
      margin: const EdgeInsets.only(bottom: 12),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(14),
        side: BorderSide(
          color: isSelected ? const Color(0xFF1B5E20) : Colors.grey.shade200,
          width: isSelected ? 2.0 : 1.0,
        ),
      ),
      child: InkWell(
        borderRadius: BorderRadius.circular(14),
        onTap: () {
          setState(() => _selectedOpportunity = item);
          _calculateScenario();
          _loadComparisons();
        },
        child: Padding(
          padding: const EdgeInsets.all(14.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Header row
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: statusBgColor,
                      borderRadius: BorderRadius.circular(6),
                      border: Border.all(color: statusTextColor.withOpacity(0.3)),
                    ),
                    child: Text(
                      statusLabel,
                      style: TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.bold,
                        color: statusTextColor,
                      ),
                    ),
                  ),
                  const Spacer(),
                  Radio<String>(
                    value: opp.opportunityId,
                    groupValue: _selectedOpportunity?.opportunity.opportunityId,
                    activeColor: const Color(0xFF1B5E20),
                    onChanged: (val) {
                      setState(() => _selectedOpportunity = item);
                      _calculateScenario();
                      _loadComparisons();
                    },
                  ),
                ],
              ),
              const SizedBox(height: 6),

              // Title and Tagline
              Text(
                opp.title,
                style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15),
              ),
              if (opp.tagline.isNotEmpty) ...[
                const SizedBox(height: 3),
                Text(
                  opp.tagline,
                  style: const TextStyle(fontSize: 12, color: Colors.black87),
                ),
              ],
              const SizedBox(height: 10),

              // Key financial metrics
              Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: Colors.grey.shade50,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    _buildMetricCol(
                      opp.isCostSaving ? 'Cash Required' : 'Initial Outlay',
                      opp.minInvestmentInr == 0.0 ? '₹0 (Free)' : _formatCurrency(opp.minInvestmentInr),
                    ),
                    _buildMetricCol(
                      opp.isCostSaving ? 'Annual Cost Saved' : 'Expected Yearly Profit',
                      opp.isCostSaving
                          ? '${_formatCurrency(opp.potentialAnnualSavingsInr)} / yr'
                          : '${_formatCurrency(opp.potentialAnnualProfitInr)} / yr',
                      color: const Color(0xFF1B5E20),
                    ),
                    _buildMetricCol(
                      'Payback',
                      opp.minInvestmentInr == 0.0 ? 'Immediate' : '${opp.paybackPeriodMonths} mos',
                    ),
                    _buildMetricCol(
                      'Space',
                      opp.requiredLandAcres == 0.0 ? 'None' : '${opp.requiredLandAcres} ac',
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 8),

              // Matching Resources & Honest Shortfalls
              if (item.matchingResources.isNotEmpty)
                Padding(
                  padding: const EdgeInsets.only(top: 4.0),
                  child: Text(
                    '✓ ${item.matchingResources.first}',
                    style: TextStyle(
                      fontSize: 11,
                      color: Colors.green.shade900,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ),
              if (!isFeasible && item.capitalGapInr > 0)
                Padding(
                  padding: const EdgeInsets.only(top: 4.0),
                  child: Text(
                    '⚠ Available budget: ${_formatCurrency(_availableInvestment)} · Needs ${_formatCurrency(opp.minInvestmentInr)} (Shortfall: ${_formatCurrency(item.capitalGapInr)})',
                    style: TextStyle(
                      fontSize: 11,
                      color: Colors.orange.shade900,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
              const SizedBox(height: 8),
              SizedBox(
                width: double.infinity,
                child: OutlinedButton.icon(
                  onPressed: () => _showFarmerQaBottomSheet(context, item),
                  style: OutlinedButton.styleFrom(
                    foregroundColor: const Color(0xFF1B5E20),
                    side: const BorderSide(color: Color(0xFF2E7D32)),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                    padding: const EdgeInsets.symmetric(vertical: 6),
                  ),
                  icon: const Icon(Icons.help_outline, size: 14),
                  label: const Text('Farmer Summary (6 Plain Questions)', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold)),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  void _showFarmerQaBottomSheet(BuildContext context, ScoredOpportunityItem item) {
    final qa = item.farmerSummaryQa ?? {
      'what_is_it': item.opportunity.summary,
      'why_suits_my_farm': item.matchingResources.isNotEmpty ? item.matchingResources.join(' · ') : 'Matches your farm profile resources.',
      'what_will_i_need': 'Initial investment: ${_formatCurrency(item.opportunity.minInvestmentInr)} · Space: ${item.opportunity.requiredSpaceType} · Daily labor: ${item.opportunity.dailyLaborHours} hrs/day',
      'how_will_i_earn_or_save': item.opportunity.isCostSaving ? 'Saves ~${_formatCurrency(item.opportunity.potentialAnnualSavingsInr)}/year in farm inputs' : 'Earns ~${_formatCurrency(item.opportunity.potentialAnnualProfitInr)}/year in net cash income',
      'when_will_i_receive_money': 'Expected returns in ~${item.opportunity.paybackPeriodMonths} months based on regional crop and market cycle.',
      'what_to_be_careful_about': item.limitingFactors.isNotEmpty ? item.limitingFactors.first : 'Manage input hygiene and market linkage timing carefully.',
    };

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
      builder: (ctx) {
        return DraggableScrollableSheet(
          initialChildSize: 0.75,
          maxChildSize: 0.95,
          minChildSize: 0.5,
          expand: false,
          builder: (_, controller) {
            return Padding(
              padding: const EdgeInsets.all(20.0),
              child: ListView(
                controller: controller,
                children: [
                  Row(
                    children: [
                      const Icon(Icons.help_outline, color: Color(0xFF1B5E20), size: 26),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Text(
                          'Plain Farmer Summary: ${item.opportunity.title}',
                          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: Color(0xFF1B5E20)),
                        ),
                      ),
                      IconButton(icon: const Icon(Icons.close), onPressed: () => Navigator.pop(ctx)),
                    ],
                  ),
                  const Divider(),
                  const SizedBox(height: 10),
                  _buildQaItem('1. What is it?', qa['what_is_it'] ?? ''),
                  _buildQaItem('2. Why does it suit my farm?', qa['why_suits_my_farm'] ?? ''),
                  _buildQaItem('3. What will I need to start?', qa['what_will_i_need'] ?? ''),
                  _buildQaItem('4. How will I earn or save money?', qa['how_will_i_earn_or_save'] ?? ''),
                  _buildQaItem('5. When will I receive money?', qa['when_will_i_receive_money'] ?? ''),
                  _buildQaItem('6. What should I be careful about?', qa['what_to_be_careful_about'] ?? '', isWarning: true),
                  const SizedBox(height: 20),
                  ElevatedButton(
                    onPressed: () => Navigator.pop(ctx),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFF1B5E20),
                      foregroundColor: Colors.white,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                      padding: const EdgeInsets.symmetric(vertical: 12),
                    ),
                    child: const Text('Back to Opportunities'),
                  ),
                ],
              ),
            );
          },
        );
      },
    );
  }

  Widget _buildQaItem(String question, String answer, {bool isWarning = false}) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: isWarning ? const Color(0xFFFFF3E0) : const Color(0xFFF9FBE7).withOpacity(0.5),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: isWarning ? const Color(0xFFFFB74D) : const Color(0xFFDCEDC8)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(question, style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: isWarning ? const Color(0xFFE65100) : const Color(0xFF1B5E20))),
          const SizedBox(height: 4),
          Text(answer, style: const TextStyle(fontSize: 12, color: Colors.black87, height: 1.3)),
        ],
      ),
    );
  }

  Widget _buildMetricCol(String label, String value, {Color? color}) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          value,
          style: TextStyle(
            fontWeight: FontWeight.bold,
            fontSize: 12,
            color: color ?? Colors.black87,
          ),
        ),
        Text(label, style: const TextStyle(fontSize: 10, color: Colors.black54)),
      ],
    );
  }

  // ==================== 4. OPPORTUNITY DETAIL & CASHFLOW ====================
  Widget _buildOpportunityDetailCard() {
    final sc = _scenario!;
    final opp = _selectedOpportunity!.opportunity;
    final isCostSaving = opp.isCostSaving;

    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: const BorderSide(color: Color(0xFF1B5E20), width: 1.5),
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
                    'Financial Outlook: ${opp.title}',
                    style: const TextStyle(
                      fontWeight: FontWeight.bold,
                      fontSize: 15,
                      color: Color(0xFF1B5E20),
                    ),
                  ),
                ),
                if (_isCalculating)
                  const SizedBox(
                    width: 14,
                    height: 14,
                    child: CircularProgressIndicator(strokeWidth: 2, color: Color(0xFF1B5E20)),
                  ),
              ],
            ),
            const SizedBox(height: 10),

            // Honest outlay explanation
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: const Color(0xFFF1F8E9),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Text(
                isCostSaving
                    ? 'This opportunity requires ${_formatCurrency(opp.minInvestmentInr)} upfront cash and generates an estimated ${_formatCurrency(opp.potentialAnnualSavingsInr)} in annual farm input savings.'
                    : 'Initial investment: ${_formatCurrency(sc.calculatedCapexInr)} (plus ${_formatCurrency(sc.workingCapitalInr)} working capital). Net annual cash surplus: ${_formatCurrency(sc.calculatedNetProfitAnnualInr)}.',
                style: const TextStyle(fontSize: 12, color: Colors.black87, height: 1.3),
              ),
            ),
            const SizedBox(height: 14),

            // 3 Realistic Scenarios
            if (sc.scenarios.isNotEmpty) ...[
              const Text(
                'Realistic Annual Scenarios:',
                style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12),
              ),
              const SizedBox(height: 8),
              Row(
                children: [
                  if (sc.scenarios.containsKey('conservative'))
                    Expanded(
                      child: _buildScenarioCard(
                        'Low',
                        _formatCurrency(sc.scenarios['conservative']!.netAnnualProfitInr),
                        '${sc.scenarios['conservative']!.breakEvenMonths.toStringAsFixed(0)}m payback',
                        Colors.orange.shade800,
                      ),
                    ),
                  const SizedBox(width: 8),
                  if (sc.scenarios.containsKey('base'))
                    Expanded(
                      child: _buildScenarioCard(
                        'Expected',
                        _formatCurrency(sc.scenarios['base']!.netAnnualProfitInr),
                        '${sc.scenarios['base']!.breakEvenMonths.toStringAsFixed(0)}m payback',
                        const Color(0xFF1B5E20),
                        isHighlight: true,
                      ),
                    ),
                  const SizedBox(width: 8),
                  if (sc.scenarios.containsKey('optimistic'))
                    Expanded(
                      child: _buildScenarioCard(
                        'High',
                        _formatCurrency(sc.scenarios['optimistic']!.netAnnualProfitInr),
                        '${sc.scenarios['optimistic']!.breakEvenMonths.toStringAsFixed(0)}m payback',
                        Colors.green.shade800,
                      ),
                    ),
                ],
              ),
              const SizedBox(height: 14),
            ],

            // 12-Month Net Cash Flow Timeline
            if (sc.scenarios.containsKey('base') &&
                sc.scenarios['base']!.monthlyNetCashFlowInr.isNotEmpty) ...[
              const Text(
                '12-Month Cash Flow Horizon (Shows delay until first harvest/sale):',
                style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12),
              ),
              const SizedBox(height: 8),
              SingleChildScrollView(
                scrollDirection: Axis.horizontal,
                child: Row(
                  children: List.generate(
                    sc.scenarios['base']!.monthlyNetCashFlowInr.length,
                    (idx) {
                      final val = sc.scenarios['base']!.monthlyNetCashFlowInr[idx];
                      final isNegative = val < 0;
                      return Container(
                        width: 58,
                        margin: const EdgeInsets.only(right: 6),
                        padding: const EdgeInsets.all(6),
                        decoration: BoxDecoration(
                          color: isNegative ? Colors.red.shade50 : Colors.green.shade50,
                          borderRadius: BorderRadius.circular(6),
                          border: Border.all(
                            color: isNegative ? Colors.red.shade200 : Colors.green.shade200,
                          ),
                        ),
                        child: Column(
                          children: [
                            Text(
                              'Month ${idx + 1}',
                              style: const TextStyle(fontSize: 9, color: Colors.black54),
                            ),
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
                    },
                  ),
                ),
              ),
              const SizedBox(height: 14),
            ],

            // Operational Assumptions & Risks
            ExpansionTile(
              tilePadding: EdgeInsets.zero,
              title: const Text(
                'Key Operational Assumptions & Risks to Monitor',
                style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12, color: Color(0xFF1B5E20)),
              ),
              children: [
                if (opp.keyAssumptions.isNotEmpty) ...[
                  const Align(
                    alignment: Alignment.centerLeft,
                    child: Text('Assumptions:', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 11)),
                  ),
                  ...opp.keyAssumptions.map((a) => Padding(
                        padding: const EdgeInsets.only(left: 8.0, top: 2.0),
                        child: Align(
                          alignment: Alignment.centerLeft,
                          child: Text('• $a', style: const TextStyle(fontSize: 11, color: Colors.black87)),
                        ),
                      )),
                  const SizedBox(height: 6),
                ],
                if (opp.keyRisks.isNotEmpty) ...[
                  const Align(
                    alignment: Alignment.centerLeft,
                    child: Text('Risks & Precautions:', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 11, color: Colors.orange)),
                  ),
                  ...opp.keyRisks.map((r) => Padding(
                        padding: const EdgeInsets.only(left: 8.0, top: 2.0),
                        child: Align(
                          alignment: Alignment.centerLeft,
                          child: Text('• $r', style: const TextStyle(fontSize: 11, color: Colors.black87)),
                        ),
                      )),
                ],
              ],
            ),
            const SizedBox(height: 10),

            // Action Button: Save to Farm Plan
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF1B5E20),
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 12),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                ),
                icon: _isSavingPlan
                    ? const SizedBox(
                        width: 16,
                        height: 16,
                        child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                      )
                    : const Icon(Icons.bookmark_add_outlined, size: 20),
                label: Text(
                  _isSavingPlan ? 'Saving Plan...' : 'Save This Opportunity to My Farm Plan',
                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
                ),
                onPressed: _isSavingPlan ? null : _handleSavePlan,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildScenarioCard(String label, String profit, String payback, Color color, {bool isHighlight = false}) {
    return Container(
      padding: const EdgeInsets.all(8),
      decoration: BoxDecoration(
        color: color.withOpacity(0.08),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: color, width: isHighlight ? 1.5 : 0.8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: TextStyle(fontWeight: FontWeight.bold, fontSize: 10, color: color)),
          const SizedBox(height: 2),
          Text(profit, style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12, color: color)),
          Text(payback, style: const TextStyle(fontSize: 9, color: Colors.black54)),
        ],
      ),
    );
  }

  // ==================== 5. COMPARISON TABLE CARD ====================
  Widget _buildComparisonCard() {
    return Card(
      elevation: 1,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Side-by-Side Comparison of Top Options',
              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
            ),
            const SizedBox(height: 4),
            const Text(
              'All metrics calculated from identical authoritative unit cost models:',
              style: TextStyle(fontSize: 11, color: Colors.black54),
            ),
            const SizedBox(height: 8),
            SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: DataTable(
                columnSpacing: 14,
                headingRowHeight: 36,
                dataRowHeight: 44,
                columns: const [
                  DataColumn(label: Text('Enterprise', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 11))),
                  DataColumn(label: Text('Initial Cost', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 11))),
                  DataColumn(label: Text('Yearly Return / Savings', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 11))),
                  DataColumn(label: Text('Payback', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 11))),
                  DataColumn(label: Text('Water Needs', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 11))),
                ],
                rows: _comparisons.map((c) {
                  return DataRow(
                    cells: [
                      DataCell(Text(c.title, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 11))),
                      DataCell(Text(_formatCurrency(c.initialInvestmentInr), style: const TextStyle(fontSize: 11))),
                      DataCell(
                        Text(
                          c.isCostSaving
                              ? '+${_formatCurrency(c.annualSavingsInr)} (Saved)'
                              : '+${_formatCurrency(c.netAnnualProfitInr)} (Profit)',
                          style: const TextStyle(fontWeight: FontWeight.bold, color: Color(0xFF1B5E20), fontSize: 11),
                        ),
                      ),
                      DataCell(Text(c.paybackMonths <= 1 ? 'Immediate' : '${c.paybackMonths.toStringAsFixed(0)} mos', style: const TextStyle(fontSize: 11))),
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

  // ==================== 6. SAVED PLANS CARD ====================
  Widget _buildSavedPlansCard() {
    return Card(
      elevation: 1,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.bookmark_added, color: Color(0xFF1B5E20), size: 20),
                const SizedBox(width: 8),
                Text(
                  'My Saved Farm Plans (${_savedPlans.length})',
                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                ),
              ],
            ),
            const SizedBox(height: 8),
            ..._savedPlans.map((plan) {
              return Container(
                margin: const EdgeInsets.only(bottom: 8),
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: Colors.grey.shade50,
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: Colors.grey.shade200),
                ),
                child: Row(
                  children: [
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            plan.opportunityTitle,
                            style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12),
                          ),
                          Text(
                            'Planned Investment: ${_formatCurrency(plan.plannedInvestmentInr)} · Saved on ${plan.createdAt.split("T").first}',
                            style: const TextStyle(fontSize: 10, color: Colors.black54),
                          ),
                        ],
                      ),
                    ),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                      decoration: BoxDecoration(
                        color: const Color(0xFFE8F5E9),
                        borderRadius: BorderRadius.circular(6),
                      ),
                      child: Text(
                        plan.status.toUpperCase(),
                        style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 10, color: Color(0xFF1B5E20)),
                      ),
                    ),
                  ],
                ),
              );
            }).toList(),
          ],
        ),
      ),
    );
  }

  // ==================== 7. PROVENANCE & TRANSPARENCY CARD ====================
  Widget _buildProvenanceCard() {
    return Card(
      elevation: 1,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
      child: ExpansionTile(
        leading: const Icon(Icons.verified_outlined, color: Colors.blueGrey),
        title: const Text(
          'Scientific Citations, NABARD Norms & Mandi Transparency',
          style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12, color: Colors.blueGrey),
        ),
        subtitle: const Text(
          'Tap to view data sources, market benchmarks and University packages of practice',
          style: TextStyle(fontSize: 10, color: Colors.black54),
        ),
        children: [
          Padding(
            padding: const EdgeInsets.all(16.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                if (_selectedOpportunity != null) ...[
                  Text(
                    'Opportunity Provenance: ${_selectedOpportunity!.opportunity.sourceAttribution}',
                    style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 11),
                  ),
                  const SizedBox(height: 4),
                  if (_selectedOpportunity!.opportunity.marketCommodity.isNotEmpty)
                    Text(
                      'Market Commodity Benchmark: ${_selectedOpportunity!.opportunity.marketCommodity} (${_selectedOpportunity!.opportunity.marketBenchmarkPrice}) · Source: ${_selectedOpportunity!.opportunity.marketSource}',
                      style: const TextStyle(fontSize: 10, color: Colors.black87),
                    ),
                  const SizedBox(height: 8),
                ],
                Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: Colors.grey.shade100,
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: const Text(
                    'Methodology Standards: NABARD State Focus Paper for Maharashtra FY 2026-27 unit cost norms, MPKV Rahuri University Packages of Practices, ICAR-NIASM Baramati, and Agmarknet APMC modal mandi rates. No revenue guarantees provided; outputs are planning projections based on stated resource constraints.',
                    style: TextStyle(fontSize: 10, color: Colors.black54, height: 1.3),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  // ==================== 8. RESOURCE SETTINGS BOTTOM SHEET ====================
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
            final budgetChips = [0.0, 1000.0, 5000.0, 15000.0, 30000.0, 50000.0, 100000.0];

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
                        const Text(
                          'Adjust Farm Resources & Budget',
                          style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                        ),
                        IconButton(
                          icon: const Icon(Icons.close),
                          onPressed: () => Navigator.pop(ctx),
                        ),
                      ],
                    ),
                    const Divider(),
                    const SizedBox(height: 8),

                    // Age Range
                    const Text('Your Age Range (Optional):', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                    const SizedBox(height: 6),
                    DropdownButtonFormField<String>(
                      isExpanded: true,
                      value: _ageRange,
                      decoration: InputDecoration(
                        contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                        border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                      ),
                      items: const [
                        DropdownMenuItem(value: 'under_25', child: Text('Under 25 years')),
                        DropdownMenuItem(value: '25_to_35', child: Text('25 – 35 years')),
                        DropdownMenuItem(value: '36_to_45', child: Text('36 – 45 years')),
                        DropdownMenuItem(value: '46_to_55', child: Text('46 – 55 years')),
                        DropdownMenuItem(value: '56_to_65', child: Text('56 – 65 years')),
                        DropdownMenuItem(value: 'above_65', child: Text('Above 65 years')),
                        DropdownMenuItem(value: 'prefer_not_to_say', child: Text('Prefer not to say')),
                      ],
                      onChanged: (val) {
                        if (val != null) {
                          setModalState(() => _ageRange = val);
                          setState(() => _ageRange = val);
                        }
                      },
                    ),
                    const SizedBox(height: 12),

                    // Work Preference
                    const Text('Daily Work Preference:', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                    const SizedBox(height: 6),
                    DropdownButtonFormField<String>(
                      isExpanded: true,
                      value: _workPreference,
                      decoration: InputDecoration(
                        contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                        border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                      ),
                      items: const [
                        DropdownMenuItem(value: 'active_physical', child: Text('Active Physical Fieldwork (Can do heavy tasks)')),
                        DropdownMenuItem(value: 'light_physical', child: Text('Light Physical Work (Prefers less strenuous tasks)')),
                        DropdownMenuItem(value: 'manage_supervise', child: Text('Manage & Supervise (Family/hired labor will do heavy lifting)')),
                      ],
                      onChanged: (val) {
                        if (val != null) {
                          setModalState(() => _workPreference = val);
                          setState(() => _workPreference = val);
                        }
                      },
                    ),
                    const SizedBox(height: 12),

                    // Payback Horizon
                    const Text('Desired Payback Timeline:', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                    const SizedBox(height: 6),
                    DropdownButtonFormField<String>(
                      isExpanded: true,
                      value: _paybackHorizon,
                      decoration: InputDecoration(
                        contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                        border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                      ),
                      items: const [
                        DropdownMenuItem(value: 'few_weeks', child: Text('Within a few weeks (Immediate cash / quick cycle)')),
                        DropdownMenuItem(value: '3_to_6_months', child: Text('3 to 6 months (Single season crop/poultry cycle)')),
                        DropdownMenuItem(value: 'within_1_year', child: Text('Within 1 year (Annual farm cycle)')),
                        DropdownMenuItem(value: 'long_term', child: Text('Longer term (> 1 year, e.g. horticulture/livestock)')),
                      ],
                      onChanged: (val) {
                        if (val != null) {
                          setModalState(() => _paybackHorizon = val);
                          setState(() => _paybackHorizon = val);
                        }
                      },
                    ),
                    const SizedBox(height: 14),

                    // Budget Selector with ZERO CASH default
                    const Text(
                      'Starting Cash Budget Available:',
                      style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      _availableInvestment == 0.0
                          ? '₹0 — Zero Extra Cash (Recycling, Better Selling, Cost Savings)'
                          : _formatCurrency(_availableInvestment),
                      style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: Color(0xFF1B5E20)),
                    ),
                    const SizedBox(height: 6),
                    SingleChildScrollView(
                      scrollDirection: Axis.horizontal,
                      child: Row(
                        children: budgetChips.map((b) {
                          final isSel = (_availableInvestment - b).abs() < 1.0;
                          return Padding(
                            padding: const EdgeInsets.only(right: 6.0),
                            child: ChoiceChip(
                              label: Text(
                                b == 0 ? '₹0 (Free)' : _formatCurrency(b),
                                style: TextStyle(
                                  fontSize: 11,
                                  fontWeight: isSel ? FontWeight.bold : FontWeight.normal,
                                  color: isSel ? Colors.white : Colors.black87,
                                ),
                              ),
                              selected: isSel,
                              selectedColor: const Color(0xFF1B5E20),
                              onSelected: (val) {
                                if (val) {
                                  setModalState(() => _availableInvestment = b);
                                  setState(() => _availableInvestment = b);
                                }
                              },
                            ),
                          );
                        }).toList(),
                      ),
                    ),
                    const SizedBox(height: 12),

                    // Spare Land
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Text('Available Spare Land:', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                        Text(
                          '${_availableLand.toStringAsFixed(2)} acres',
                          style: const TextStyle(fontWeight: FontWeight.bold, color: Color(0xFF1B5E20)),
                        ),
                      ],
                    ),
                    Slider(
                      value: _availableLand,
                      min: 0.0,
                      max: 2.0,
                      divisions: 20,
                      activeColor: const Color(0xFF1B5E20),
                      label: '${_availableLand.toStringAsFixed(2)} ac',
                      onChanged: (val) {
                        setModalState(() => _availableLand = val);
                        setState(() => _availableLand = val);
                      },
                    ),
                    const SizedBox(height: 10),

                    // Water Availability
                    const Text('Water Availability on Farm:', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                    const SizedBox(height: 6),
                    DropdownButtonFormField<String>(
                      isExpanded: true,
                      value: _waterAvailability,
                      decoration: InputDecoration(
                        contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                        border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                      ),
                      items: const [
                        DropdownMenuItem(value: 'reliable_year_round', child: Text('Borewell / Perennial Water (All Year)')),
                        DropdownMenuItem(value: 'seasonal_canal', child: Text('Seasonal Canal / Farm Pond (Oct–Mar)')),
                        DropdownMenuItem(value: 'rainfed_limited', child: Text('Rainfed / Limited Moisture (Kharif only)')),
                      ],
                      onChanged: (val) {
                        if (val != null) {
                          setModalState(() => _waterAvailability = val);
                          setState(() => _waterAvailability = val);
                        }
                      },
                    ),
                    const SizedBox(height: 12),

                    // Family Labor Hours
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Text('Family Labor Available:', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                        Text(
                          '${_familyLaborHours.toStringAsFixed(1)} hrs/day',
                          style: const TextStyle(fontWeight: FontWeight.bold, color: Color(0xFF1B5E20)),
                        ),
                      ],
                    ),
                    Slider(
                      value: _familyLaborHours,
                      min: 0.5,
                      max: 6.0,
                      divisions: 11,
                      activeColor: const Color(0xFF1B5E20),
                      label: '${_familyLaborHours.toStringAsFixed(1)}h',
                      onChanged: (val) {
                        setModalState(() => _familyLaborHours = val);
                        setState(() => _familyLaborHours = val);
                      },
                    ),
                    const SizedBox(height: 12),

                    // Existing Assets Checkboxes
                    const Text('Existing Assets on Farm:', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                    CheckboxListTile(
                      dense: true,
                      contentPadding: EdgeInsets.zero,
                      title: const Text('Animal shed or enclosure available', style: TextStyle(fontSize: 12)),
                      value: _hasAnimalShed,
                      activeColor: const Color(0xFF1B5E20),
                      onChanged: (val) {
                        setModalState(() => _hasAnimalShed = val ?? false);
                        setState(() => _hasAnimalShed = val ?? false);
                      },
                    ),
                    CheckboxListTile(
                      dense: true,
                      contentPadding: EdgeInsets.zero,
                      title: const Text('Covered storage room / shed available', style: TextStyle(fontSize: 12)),
                      value: _hasStorageRoom,
                      activeColor: const Color(0xFF1B5E20),
                      onChanged: (val) {
                        setModalState(() => _hasStorageRoom = val ?? false);
                        setState(() => _hasStorageRoom = val ?? false);
                      },
                    ),
                    CheckboxListTile(
                      dense: true,
                      contentPadding: EdgeInsets.zero,
                      title: const Text('Surplus crop residue / cow dung on farm', style: TextStyle(fontSize: 12)),
                      value: _cropByproducts.isNotEmpty,
                      activeColor: const Color(0xFF1B5E20),
                      onChanged: (val) {
                        setModalState(() {
                          if (val == true) {
                            _cropByproducts = ['soybean_straw', 'cow_dung'];
                          } else {
                            _cropByproducts = [];
                          }
                        });
                        setState(() {
                          if (val == true) {
                            _cropByproducts = ['soybean_straw', 'cow_dung'];
                          } else {
                            _cropByproducts = [];
                          }
                        });
                      },
                    ),
                    const SizedBox(height: 14),

                    // Save and Recalculate
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
                          _saveProfileAndRecalculate();
                        },
                        child: const Text(
                          'Update & Discover Opportunities',
                          style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                        ),
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

  Future<void> _saveProfileAndRecalculate() async {
    final farmId = AppState.instance.activeFarmId ?? 'farm_demo_pune_01';
    final profile = FarmerResourceProfile(
      farmId: farmId,
      farmerId: 'farmer_demo_01',
      availableInvestmentInr: _availableInvestment,
      monthlyOperatingBudgetInr: _monthlyOperatingBudget,
      availableLandAcres: _availableLand,
      unusedLandAcres: _unusedLand,
      waterAvailability: _waterAvailability,
      familyLaborHoursDay: _familyLaborHours,
      hasAnimalShed: _hasAnimalShed,
      hasStorageRoom: _hasStorageRoom,
      hasShadedSpace: _hasShadedSpace,
      existingLivestock: _existingLivestock,
      cropByproducts: _cropByproducts,
      interests: _interests,
      riskTolerance: _riskTolerance,
      categoryPreference: _selectedCategory,
    );

    await ApiService.saveFarmResourceProfile(profile);
    await _discoverOpportunities();
  }
}
