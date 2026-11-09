import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../../shared/responsive/breakpoints.dart';
import '../../../../shared/widgets/app_spacing.dart';
import '../../../../shared/widgets/centered_page_container.dart';
import '../../../../shared/widgets/responsive_scaffold.dart';
import '../../data/scheme_repository.dart';
import '../../models/scheme_models.dart';

/// Admin create/edit form for a Government Scheme.
class SchemeEditorScreen extends StatefulWidget {
  final String? schemeId;
  final SchemeRepository? repository;

  const SchemeEditorScreen({super.key, this.schemeId, this.repository});

  bool get isEditing => schemeId != null;

  @override
  State<SchemeEditorScreen> createState() => _SchemeEditorScreenState();
}

class _SchemeEditorScreenState extends State<SchemeEditorScreen> {
  late final SchemeRepository _repository;
  final _formKey = GlobalKey<FormState>();

  final _schemeName = TextEditingController();
  final _state = TextEditingController();
  final _description = TextEditingController();
  final _benefits = TextEditingController();
  final _eligibility = TextEditingController();
  final _documents = TextEditingController();
  final _steps = TextEditingController();
  final _department = TextEditingController();
  final _applicationUrl = TextEditingController();
  final _sourceUrl = TextEditingController();

  String _category = kSchemeCategories.first;
  String _level = 'Central';
  String _status = 'DRAFT';
  String _verification = 'PENDING_REVIEW';

  bool _isLoading = false;
  bool _isSaving = false;

  @override
  void initState() {
    super.initState();
    _repository = widget.repository ?? SchemeRepository.instance;
    if (widget.isEditing) _loadExisting();
  }

  Future<void> _loadExisting() async {
    setState(() => _isLoading = true);
    try {
      final scheme = await _repository.getScheme(widget.schemeId!);
      if (!mounted) return;
      setState(() {
        _schemeName.text = scheme.schemeName;
        _state.text = scheme.state ?? '';
        _description.text = scheme.description ?? '';
        _benefits.text = scheme.benefits.join('\n');
        _eligibility.text = scheme.eligibility.join('\n');
        _documents.text = scheme.requiredDocuments.join('\n');
        _steps.text = scheme.applicationSteps.join('\n');
        _department.text = scheme.department ?? '';
        _applicationUrl.text = scheme.applicationUrl ?? '';
        _sourceUrl.text = scheme.sourceUrl ?? '';
        _category = scheme.category;
        _level = scheme.governmentLevel;
        _status = scheme.status;
        _verification = scheme.verificationStatus;
        _isLoading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() => _isLoading = false);
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.toString())));
    }
  }

  List<String> _parseLines(TextEditingController controller) {
    return controller.text
        .split('\n')
        .map((s) => s.trim())
        .where((s) => s.isNotEmpty)
        .toList();
  }

  Future<void> _save() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _isSaving = true);

    final payload = <String, dynamic>{
      'scheme_name': _schemeName.text.trim(),
      'category': _category,
      'government_level': _level,
      'state': _state.text.trim().isEmpty ? null : _state.text.trim(),
      'description': _description.text.trim().isEmpty ? null : _description.text.trim(),
      'benefits': _parseLines(_benefits),
      'eligibility': _parseLines(_eligibility),
      'required_documents': _parseLines(_documents),
      'application_steps': _parseLines(_steps),
      'department': _department.text.trim().isEmpty ? null : _department.text.trim(),
      'application_url': _applicationUrl.text.trim().isEmpty ? null : _applicationUrl.text.trim(),
      'source_url': _sourceUrl.text.trim().isEmpty ? null : _sourceUrl.text.trim(),
      'status': _status,
      'verification_status': _verification,
    };

    final messenger = ScaffoldMessenger.of(context);
    try {
      if (widget.isEditing) {
        await _repository.updateScheme(widget.schemeId!, payload);
      } else {
        await _repository.createScheme(payload);
      }
      if (!mounted) return;
      messenger.showSnackBar(const SnackBar(content: Text('Scheme saved')));
      context.pop();
    } catch (e) {
      if (!mounted) return;
      setState(() => _isSaving = false);
      messenger.showSnackBar(SnackBar(content: Text(e.toString().replaceAll('Exception: ', ''))));
    }
  }

  @override
  void dispose() {
    _schemeName.dispose();
    _state.dispose();
    _description.dispose();
    _benefits.dispose();
    _eligibility.dispose();
    _documents.dispose();
    _steps.dispose();
    _department.dispose();
    _applicationUrl.dispose();
    _sourceUrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return ResponsiveScaffold(
      currentIndex: 0,
      destinations: const [],
      appBar: AppBar(
        title: Text(widget.isEditing ? 'Edit Scheme' : 'New Scheme',
            style: const TextStyle(fontWeight: FontWeight.bold)),
        leading: IconButton(icon: const Icon(Icons.arrow_back), onPressed: () => context.pop()),
        actions: [
          TextButton(
            onPressed: _isSaving ? null : _save,
            child: _isSaving
                ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2))
                : const Text('Save'),
          ),
        ],
      ),
      body: CenteredPageContainer(
        maxWidth: AppBreakpoints.maxContentWidthReadable,
        scrollable: true,
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
        child: _isLoading
            ? const Center(child: CircularProgressIndicator())
            : Form(
                key: _formKey,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _textField(_schemeName, 'Scheme name', required: true),
                    AppSpacing.verticalSpaceMD,
                    _dropdown('Category', kSchemeCategories, _category, (v) => setState(() => _category = v!)),
                    AppSpacing.verticalSpaceMD,
                    _dropdown('Level', const ['Central', 'State'], _level, (v) => setState(() => _level = v!)),
                    AppSpacing.verticalSpaceMD,
                    _textField(_state, 'State (e.g. Maharashtra) — leave blank for all-India'),
                    AppSpacing.verticalSpaceMD,
                    _textField(_department, 'Department'),
                    AppSpacing.verticalSpaceMD,
                    _multilineField(_description, 'Description'),
                    AppSpacing.verticalSpaceMD,
                    _multilineField(_benefits, 'Benefits (one per line)'),
                    AppSpacing.verticalSpaceMD,
                    _multilineField(_eligibility, 'Eligibility (one per line)'),
                    AppSpacing.verticalSpaceMD,
                    _multilineField(_documents, 'Required documents (one per line)'),
                    AppSpacing.verticalSpaceMD,
                    _multilineField(_steps, 'Application steps (one per line)'),
                    AppSpacing.verticalSpaceMD,
                    _textField(_applicationUrl, 'Official application link (URL)'),
                    AppSpacing.verticalSpaceMD,
                    _textField(_sourceUrl, 'Source link (URL)'),
                    AppSpacing.verticalSpaceMD,
                    _dropdown('Status', const ['DRAFT', 'ACTIVE', 'INACTIVE'], _status, (v) => setState(() => _status = v!)),
                    AppSpacing.verticalSpaceMD,
                    _dropdown('Verification', const ['PENDING_REVIEW', 'VERIFIED', 'NOT_VERIFIED'], _verification,
                        (v) => setState(() => _verification = v!)),
                    AppSpacing.verticalSpaceLG,
                    FilledButton.icon(
                      onPressed: _isSaving ? null : _save,
                      icon: const Icon(Icons.save_outlined),
                      label: Text(widget.isEditing ? 'Update Scheme' : 'Create Scheme'),
                    ),
                    AppSpacing.verticalSpaceXL,
                  ],
                ),
              ),
      ),
    );
  }

  Widget _textField(TextEditingController controller, String label, {bool required = false}) {
    return TextFormField(
      controller: controller,
      decoration: InputDecoration(labelText: label, border: const OutlineInputBorder()),
      validator: required
          ? (v) => (v == null || v.trim().isEmpty) ? 'Required' : null
          : null,
    );
  }

  Widget _multilineField(TextEditingController controller, String label) {
    return TextFormField(
      controller: controller,
      decoration: InputDecoration(
        labelText: label,
        alignLabelWithHint: true,
        border: const OutlineInputBorder(),
      ),
      minLines: 2,
      maxLines: 6,
    );
  }

  Widget _dropdown(String label, List<String> items, String value, ValueChanged<String?> onChanged) {
    // Controlled DropdownButton (not DropdownButtonFormField) so the displayed
    // value always reflects the current state, including after async load in
    // edit mode.
    return InputDecorator(
      decoration: InputDecoration(
        labelText: label,
        border: const OutlineInputBorder(),
        contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
      ),
      child: DropdownButtonHideUnderline(
        child: DropdownButton<String>(
          value: value,
          isExpanded: true,
          items: items.map((item) => DropdownMenuItem(value: item, child: Text(item))).toList(),
          onChanged: onChanged,
        ),
      ),
    );
  }
}
