import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/router/route_paths.dart';
import '../../../../shared/responsive/breakpoints.dart';
import '../../../../shared/widgets/app_decorations.dart';
import '../../../../shared/widgets/app_spacing.dart';
import '../../../../shared/widgets/centered_page_container.dart';
import '../../../../shared/widgets/responsive_scaffold.dart';
import '../../data/scheme_repository.dart';
import '../../models/scheme_models.dart';

/// Admin-only Government Schemes management screen (list + actions).
class SchemeAdminScreen extends StatefulWidget {
  final SchemeRepository? repository;

  const SchemeAdminScreen({super.key, this.repository});

  @override
  State<SchemeAdminScreen> createState() => _SchemeAdminScreenState();
}

class _SchemeAdminScreenState extends State<SchemeAdminScreen> {
  late final SchemeRepository _repository;
  List<GovernmentScheme> _schemes = const [];
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
      final schemes = await _repository.listSchemes();
      if (!mounted) return;
      setState(() {
        _schemes = schemes;
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

  Future<void> _run(Future<void> Function() action) async {
    final messenger = ScaffoldMessenger.of(context);
    try {
      await action();
      await _fetch();
    } catch (e) {
      messenger.showSnackBar(
        SnackBar(content: Text(e.toString().replaceAll('Exception: ', ''))),
      );
    }
  }

  Future<void> _seed() async {
    final messenger = ScaffoldMessenger.of(context);
    try {
      final res = await _repository.seedSchemes();
      messenger.showSnackBar(SnackBar(content: Text(res['message'] ?? 'Seeded')));
      await _fetch();
    } catch (e) {
      messenger.showSnackBar(SnackBar(content: Text(e.toString())));
    }
  }

  @override
  Widget build(BuildContext context) {
    return ResponsiveScaffold(
      currentIndex: 0,
      destinations: const [],
      appBar: AppBar(
        title: const Text('Manage Schemes', style: TextStyle(fontWeight: FontWeight.bold)),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          tooltip: 'Back',
          onPressed: () => context.pop(),
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.download_done),
            tooltip: 'Seed verified schemes',
            onPressed: _seed,
          ),
          IconButton(
            icon: const Icon(Icons.add),
            tooltip: 'New scheme',
            onPressed: () => context.push(RoutePaths.schemesAdminNew),
          ),
        ],
      ),
      body: CenteredPageContainer(
        maxWidth: AppBreakpoints.maxContentWidthStandard,
        scrollable: false,
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
        child: _buildBody(),
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => context.push(RoutePaths.schemesAdminNew),
        icon: const Icon(Icons.add),
        label: const Text('New Scheme'),
      ),
    );
  }

  Widget _buildBody() {
    if (_isLoading) {
      return const Center(child: CircularProgressIndicator());
    }
    if (_errorMessage != null) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(_errorMessage!, textAlign: TextAlign.center),
            AppSpacing.verticalSpaceMD,
            FilledButton.icon(onPressed: _fetch, icon: const Icon(Icons.refresh), label: const Text('Retry')),
          ],
        ),
      );
    }
    if (_schemes.isEmpty) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.inbox_outlined, size: 48, color: Colors.blueGrey),
            AppSpacing.verticalSpaceMD,
            const Text('No schemes yet. Tap "Seed verified schemes" or "New Scheme".'),
            AppSpacing.verticalSpaceMD,
            FilledButton.icon(onPressed: _seed, icon: const Icon(Icons.download_done), label: const Text('Seed schemes')),
          ],
        ),
      );
    }
    return ListView.separated(
      itemCount: _schemes.length,
      separatorBuilder: (_, __) => AppSpacing.verticalSpaceSM,
      itemBuilder: (context, index) => _row(_schemes[index]),
    );
  }

  Widget _row(GovernmentScheme scheme) {
    final active = scheme.isActive;
    return Container(
      decoration: AppDecorations.card(),
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(scheme.schemeName, style: const TextStyle(fontWeight: FontWeight.w600)),
                AppSpacing.verticalSpaceXS,
                Wrap(
                  spacing: 6,
                  runSpacing: 4,
                  children: [
                    _badge(scheme.category, Colors.teal),
                    _badge(scheme.governmentLevel, Colors.blueGrey),
                    _badge(active ? 'ACTIVE' : scheme.status, active ? Colors.green : Colors.grey),
                    _badge(scheme.verificationStatus,
                        scheme.isVerified ? Colors.green : Colors.orange),
                  ],
                ),
              ],
            ),
          ),
          PopupMenuButton<String>(
            tooltip: 'Actions',
            onSelected: (value) => _onAction(value, scheme),
            itemBuilder: (context) => [
              const PopupMenuItem(value: 'edit', child: Text('Edit')),
              PopupMenuItem(
                value: active ? 'deactivate' : 'publish',
                child: Text(active ? 'Deactivate' : 'Publish'),
              ),
              const PopupMenuItem(value: 'verify', child: Text('Mark verified')),
              const PopupMenuItem(value: 'delete', child: Text('Delete')),
            ],
          ),
        ],
      ),
    );
  }

  Future<void> _onAction(String action, GovernmentScheme scheme) async {
    switch (action) {
      case 'edit':
        context.push(RoutePaths.schemeAdminEditPath(scheme.id));
        return;
      case 'publish':
        await _run(() => _repository.setSchemeStatus(scheme.id, status: 'ACTIVE'));
        return;
      case 'deactivate':
        await _run(() => _repository.setSchemeStatus(scheme.id, status: 'INACTIVE'));
        return;
      case 'verify':
        await _run(() =>
            _repository.setSchemeStatus(scheme.id, verificationStatus: 'VERIFIED'));
        return;
      case 'delete':
        final confirmed = await showDialog<bool>(
          context: context,
          builder: (ctx) => AlertDialog(
            title: const Text('Delete scheme?'),
            content: Text('Delete "${scheme.schemeName}"? This cannot be undone.'),
            actions: [
              TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Cancel')),
              FilledButton(
                onPressed: () => Navigator.pop(ctx, true),
                child: const Text('Delete'),
              ),
            ],
          ),
        );
        if (confirmed == true) {
          await _run(() => _repository.deleteScheme(scheme.id));
        }
        return;
    }
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
}
