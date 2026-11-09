import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:go_router/go_router.dart';

import '../../../../shared/responsive/breakpoints.dart';
import '../../../../shared/widgets/app_decorations.dart';
import '../../../../shared/widgets/app_spacing.dart';
import '../../../../shared/widgets/centered_page_container.dart';
import '../../../../shared/widgets/responsive_scaffold.dart';
import '../../data/scheme_repository.dart';
import '../../models/scheme_models.dart';
import '../widgets/scheme_card.dart';

/// Individual Government Scheme detail page.
class SchemeDetailScreen extends StatefulWidget {
  final String schemeId;
  final SchemeRepository? repository;

  const SchemeDetailScreen({super.key, required this.schemeId, this.repository});

  @override
  State<SchemeDetailScreen> createState() => _SchemeDetailScreenState();
}

class _SchemeDetailScreenState extends State<SchemeDetailScreen> {
  late final SchemeRepository _repository;
  GovernmentScheme? _scheme;
  bool _isLoading = true;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _repository = widget.repository ?? SchemeRepository.instance;
    _fetch();
  }

  Future<void> _fetch() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });
    try {
      final scheme = await _repository.getScheme(widget.schemeId);
      if (!mounted) return;
      setState(() {
        _scheme = scheme;
        _isLoading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _isLoading = false;
        _errorMessage = e.toString().replaceAll('Exception: ', '');
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return ResponsiveScaffold(
      currentIndex: 0,
      destinations: const [],
      appBar: AppBar(
        title: Text(
          _scheme?.schemeName ?? 'Scheme Details',
          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 17),
        ),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          tooltip: 'Back',
          onPressed: () => context.pop(),
        ),
      ),
      body: CenteredPageContainer(
        maxWidth: AppBreakpoints.maxContentWidthReadable,
        scrollable: true,
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
        child: _buildBody(),
      ),
    );
  }

  Widget _buildBody() {
    if (_isLoading) {
      return const Padding(
        padding: EdgeInsets.symmetric(vertical: 80),
        child: Center(child: CircularProgressIndicator()),
      );
    }

    if (_errorMessage != null || _scheme == null) {
      return Padding(
        padding: const EdgeInsets.symmetric(vertical: 60),
        child: Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.error_outline, size: 48, color: Colors.redAccent),
              AppSpacing.verticalSpaceMD,
              Text(_errorMessage ?? 'Scheme not found.', textAlign: TextAlign.center),
              AppSpacing.verticalSpaceMD,
              FilledButton.icon(
                onPressed: _fetch,
                icon: const Icon(Icons.refresh),
                label: const Text('Retry'),
              ),
            ],
          ),
        ),
      );
    }

    final scheme = _scheme!;
    final accent = schemeCategoryColor(scheme.category);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _header(scheme, accent),
        AppSpacing.verticalSpaceMD,
        if (scheme.description != null && scheme.description!.isNotEmpty)
          _sectionCard('About', [scheme.description!]),
        if (scheme.benefits.isNotEmpty) _sectionCard('Benefits', scheme.benefits),
        if (scheme.eligibility.isNotEmpty) _sectionCard('Eligibility', scheme.eligibility),
        if (scheme.requiredDocuments.isNotEmpty)
          _sectionCard('Required Documents', scheme.requiredDocuments),
        if (scheme.applicationSteps.isNotEmpty)
          _sectionCard('How to Apply', scheme.applicationSteps),
        _detailsCard(scheme),
        if (scheme.applicationUrl != null && scheme.applicationUrl!.isNotEmpty)
          _urlCard('Official Application Link', scheme.applicationUrl!),
        if (scheme.sourceUrl != null && scheme.sourceUrl!.isNotEmpty)
          _urlCard('Source / Official Website', scheme.sourceUrl!),
        AppSpacing.verticalSpaceLG,
      ],
    );
  }

  Widget _header(GovernmentScheme scheme, Color accent) {
    return Container(
      width: double.infinity,
      decoration: AppDecorations.accentCard(accentColor: accent),
      padding: AppSpacing.paddingAllLG,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              CircleAvatar(
                radius: 22,
                backgroundColor: accent.withValues(alpha: 0.12),
                foregroundColor: accent,
                child: Icon(schemeCategoryIcon(scheme.category), size: 24),
              ),
              AppSpacing.horizontalSpaceMD,
              Expanded(
                child: Text(
                  scheme.schemeName,
                  style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w700),
                ),
              ),
            ],
          ),
          AppSpacing.verticalSpaceSM,
          Wrap(
            spacing: AppSpacing.xs,
            runSpacing: AppSpacing.xs,
            children: [
              _badge(scheme.category, accent),
              _badge(scheme.governmentLevel, Colors.blueGrey),
              if (scheme.state != null && scheme.state!.isNotEmpty)
                _badge(scheme.state!, Colors.indigo),
              _badge(scheme.isVerified ? 'Verified' : 'Not verified',
                  scheme.isVerified ? Colors.green : Colors.orange),
              _badge(scheme.isActive ? 'Active' : scheme.status, scheme.isActive ? Colors.teal : Colors.grey),
            ],
          ),
        ],
      ),
    );
  }

  Widget _sectionCard(String title, List<String> items) {
    return Container(
      width: double.infinity,
      margin: const EdgeInsets.only(bottom: AppSpacing.md),
      decoration: AppDecorations.card(),
      padding: AppSpacing.paddingAllLG,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 16)),
          AppSpacing.verticalSpaceSM,
          for (final item in items)
            Padding(
              padding: const EdgeInsets.only(bottom: AppSpacing.xs),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Icon(Icons.check_circle_outline, size: 18, color: AppDecorations.leafGreen),
                  AppSpacing.horizontalSpaceSM,
                  Expanded(child: Text(item, style: const TextStyle(fontSize: 14))),
                ],
              ),
            ),
        ],
      ),
    );
  }

  Widget _detailsCard(GovernmentScheme scheme) {
    return Container(
      width: double.infinity,
      margin: const EdgeInsets.only(bottom: AppSpacing.md),
      decoration: AppDecorations.card(),
      padding: AppSpacing.paddingAllLG,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('Details', style: TextStyle(fontWeight: FontWeight.w700, fontSize: 16)),
          AppSpacing.verticalSpaceSM,
          _detailRow('Department', scheme.department),
          _detailRow('Category', scheme.category),
          _detailRow('Level', scheme.governmentLevel),
          _detailRow('State', scheme.state),
          _detailRow('Status', scheme.status),
          _detailRow('Verification', scheme.verificationStatus),
          _detailRow('Last Verified', _formatDate(scheme.lastVerifiedDate)),
        ],
      ),
    );
  }

  Widget _detailRow(String label, String? value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: AppSpacing.xs),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 130,
            child: Text(label, style: const TextStyle(fontWeight: FontWeight.w600, color: Colors.blueGrey)),
          ),
          Expanded(child: Text(value == null || value.isEmpty ? 'Not verified' : value)),
        ],
      ),
    );
  }

  Widget _urlCard(String label, String url) {
    return Container(
      width: double.infinity,
      margin: const EdgeInsets.only(bottom: AppSpacing.md),
      decoration: AppDecorations.card(),
      padding: AppSpacing.paddingAllLG,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 16)),
          AppSpacing.verticalSpaceSM,
          InkWell(
            onTap: () => _copyUrl(url),
            child: Row(
              children: [
                const Icon(Icons.copy, size: 16, color: Colors.blue),
                AppSpacing.horizontalSpaceSM,
                Expanded(
                  child: Text(url, style: const TextStyle(color: Colors.blue, decoration: TextDecoration.underline)),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _badge(String label, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.10),
        borderRadius: AppBorderRadius.pill,
      ),
      child: Text(label, style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: color)),
    );
  }

  String? _formatDate(DateTime? date) {
    if (date == null) return null;
    final y = date.year.toString().padLeft(4, '0');
    final m = date.month.toString().padLeft(2, '0');
    final d = date.day.toString().padLeft(2, '0');
    return '$y-$m-$d';
  }

  Future<void> _copyUrl(String url) async {
    await Clipboard.setData(ClipboardData(text: url));
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Link copied to clipboard')),
    );
  }
}
