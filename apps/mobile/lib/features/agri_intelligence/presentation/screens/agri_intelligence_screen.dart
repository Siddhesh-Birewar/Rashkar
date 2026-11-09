import 'package:file_picker/file_picker.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';

import '../../../../core/utils/native_file_picker.dart';
import '../../../../shared/responsive/breakpoints.dart';
import '../../../../shared/widgets/app_decorations.dart';
import '../../../../shared/widgets/app_spacing.dart';
import '../../../../shared/widgets/centered_page_container.dart';
import '../../../../shared/widgets/responsive_scaffold.dart';
import '../../data/agri_repository.dart';
import '../../models/agri_models.dart';

/// Consolidated Agri Intelligence hub: Crop Doctor (image diagnosis) and Heat Risk
/// (crop heat-stress + worker heat-hazard), backed by the consolidated FastAPI APIs.
class AgriIntelligenceScreen extends StatefulWidget {
  final AgriIntelligenceRepository? repository;

  const AgriIntelligenceScreen({super.key, this.repository});

  @override
  State<AgriIntelligenceScreen> createState() => _AgriIntelligenceScreenState();
}

class _AgriIntelligenceScreenState extends State<AgriIntelligenceScreen>
    with SingleTickerProviderStateMixin {
  late final AgriIntelligenceRepository _repo;
  late final TabController _tabs;

  // Crop Doctor state
  PlatformFile? _picked;
  bool _analyzing = false;
  CropDoctorResult? _doctorResult;
  String? _doctorError;

  // Crop heat state
  String _cropCode = 'soybean';
  final _tmaxCtrl = TextEditingController(text: '38');
  final _tminCtrl = TextEditingController(text: '23');
  bool _cropHeatLoading = false;
  CropHeatResult? _cropHeatResult;
  String? _cropHeatError;

  // Worker heat state
  final _airTempCtrl = TextEditingController(text: '37');
  final _rhCtrl = TextEditingController(text: '60');
  final _windCtrl = TextEditingController(text: '1.5');
  final _solarCtrl = TextEditingController(text: '700');
  String _workload = 'moderate';
  bool _workerHeatLoading = false;
  WorkerHeatResult? _workerHeatResult;
  String? _workerHeatError;

  @override
  void initState() {
    super.initState();
    _repo = widget.repository ?? AgriIntelligenceRepository.instance;
    _tabs = TabController(length: 2, vsync: this);
  }

  @override
  void dispose() {
    _tabs.dispose();
    _tmaxCtrl.dispose();
    _tminCtrl.dispose();
    _airTempCtrl.dispose();
    _rhCtrl.dispose();
    _windCtrl.dispose();
    _solarCtrl.dispose();
    super.dispose();
  }

  Future<void> _pickAndAnalyze() async {
    PlatformFile? picked;
    try {
      if (kIsWeb) {
        picked = await pickDocumentNative(
          allowedExtensions: const ['jpg', 'jpeg', 'png'],
        );
      } else {
        picked = await FilePicker.pickFile(
          type: FileType.custom,
          allowedExtensions: const ['jpg', 'jpeg', 'png'],
        );
      }
    } catch (_) {
      picked = null;
    }
    if (picked == null) return;
    setState(() {
      _picked = picked;
      _doctorResult = null;
      _doctorError = null;
    });
  }

  Future<void> _analyzeCrop() async {
    final file = _picked;
    if (file == null) return;
    setState(() {
      _analyzing = true;
      _doctorError = null;
    });
    try {
      final bytes = await file.readAsBytes();
      final name = file.name.toLowerCase();
      final res = await _repo.analyzeCropImage(
        bytes: bytes,
        fileName: file.name,
        mimeType: name.endsWith('.png') ? 'image/png' : 'image/jpeg',
      );
      if (!mounted) return;
      setState(() {
        _doctorResult = res;
        _analyzing = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _analyzing = false;
        _doctorError = e.toString().replaceAll('Exception: ', '');
      });
    }
  }

  Future<void> _assessCropHeat() async {
    setState(() {
      _cropHeatLoading = true;
      _cropHeatError = null;
    });
    try {
      final res = await _repo.assessCropHeat(
        cropCode: _cropCode,
        tmaxC: double.tryParse(_tmaxCtrl.text) ?? 38,
        tminC: double.tryParse(_tminCtrl.text) ?? 23,
      );
      if (!mounted) return;
      setState(() {
        _cropHeatResult = res;
        _cropHeatLoading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _cropHeatLoading = false;
        _cropHeatError = e.toString().replaceAll('Exception: ', '');
      });
    }
  }

  Future<void> _assessWorkerHeat() async {
    setState(() {
      _workerHeatLoading = true;
      _workerHeatError = null;
    });
    try {
      final res = await _repo.assessWorkerHeat(
        airTempC: double.tryParse(_airTempCtrl.text) ?? 37,
        relativeHumidityPct: double.tryParse(_rhCtrl.text) ?? 60,
        windSpeedMs: double.tryParse(_windCtrl.text) ?? 1.5,
        solarIrradianceWm2: double.tryParse(_solarCtrl.text) ?? 700,
        workloadCategory: _workload,
      );
      if (!mounted) return;
      setState(() {
        _workerHeatResult = res;
        _workerHeatLoading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _workerHeatLoading = false;
        _workerHeatError = e.toString().replaceAll('Exception: ', '');
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return DefaultTabController(
      length: 2,
      child: ResponsiveScaffold(
        currentIndex: 0,
        destinations: const [],
        appBar: AppBar(
          title: const Text('Agri Intelligence', style: TextStyle(fontWeight: FontWeight.bold)),
          bottom: TabBar(
            controller: _tabs,
            tabs: const [
              Tab(icon: Icon(Icons.local_florist), text: 'Crop Doctor'),
              Tab(icon: Icon(Icons.thermostat), text: 'Heat Risk'),
            ],
          ),
        ),
        body: TabBarView(
          controller: _tabs,
          children: [_buildCropDoctorTab(), _buildHeatRiskTab()],
        ),
      ),
    );
  }

  Widget _buildCropDoctorTab() {
    return CenteredPageContainer(
      maxWidth: AppBreakpoints.maxContentWidthReadable,
      scrollable: true,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          _infoBanner(
            'Image-based crop disease screening. Upload a clear photo of the affected leaf. '
            'This is a screening aid — confirm with a local agronomist before chemical treatment.',
          ),
          AppSpacing.verticalSpaceMD,
          OutlinedButton.icon(
            onPressed: _pickAndAnalyze,
            icon: const Icon(Icons.image_outlined),
            label: Text(_picked == null ? 'Select leaf image (JPG/PNG)' : 'Change image'),
          ),
          if (_picked != null) ...[
            AppSpacing.verticalSpaceSM,
            Text('Selected: ${_picked!.name}', style: const TextStyle(fontSize: 12.5)),
            AppSpacing.verticalSpaceSM,
            FilledButton.icon(
              onPressed: _analyzing || _picked == null ? null : _analyzeCrop,
              icon: _analyzing
                  ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2))
                  : const Icon(Icons.search),
              label: Text(_analyzing ? 'Analyzing…' : 'Analyze leaf'),
            ),
          ],
          if (_doctorError != null) ...[
            AppSpacing.verticalSpaceMD,
            _errorCard(_doctorError!),
          ],
          if (_doctorResult != null) ...[
            AppSpacing.verticalSpaceMD,
            _doctorResultCard(_doctorResult!),
          ],
        ],
      ),
    );
  }

  Widget _doctorResultCard(CropDoctorResult r) {
    final color = r.isHealthy ? const Color(0xFF2E7D32) : const Color(0xFFC62828);
    return Container(
      decoration: AppDecorations.card(),
      padding: AppSpacing.paddingAllLG,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(r.isHealthy ? Icons.check_circle : Icons.warning_amber, color: color),
              AppSpacing.horizontalSpaceSM,
              Expanded(
                child: Text('${r.crop} — ${r.diagnosis}',
                    style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
              ),
            ],
          ),
          AppSpacing.verticalSpaceXS,
          Text('Confidence: ${r.confidence.toStringAsFixed(1)}%',
              style: TextStyle(color: color, fontWeight: FontWeight.w600)),
          AppSpacing.verticalSpaceSM,
          const Text('Preventive / management advice:', style: TextStyle(fontWeight: FontWeight.w600)),
          for (final tip in r.advice)
            Padding(
              padding: const EdgeInsets.only(top: 4),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Icon(Icons.chevron_right, size: 18, color: AppDecorations.leafGreen),
                  Expanded(child: Text(tip, style: const TextStyle(fontSize: 13))),
                ],
              ),
            ),
          if (r.disclaimer != null) ...[
            AppSpacing.verticalSpaceSM,
            Text(r.disclaimer!, style: const TextStyle(fontSize: 11.5, color: Colors.black54)),
          ],
        ],
      ),
    );
  }

  Widget _buildHeatRiskTab() {
    return CenteredPageContainer(
      maxWidth: AppBreakpoints.maxContentWidthReadable,
      scrollable: true,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          _sectionTitle('Crop Heat-Stress Assessment'),
          const Text('Verified thermal physiology for soybean, cotton, jowar and onion.',
              style: TextStyle(fontSize: 12, color: Colors.black54)),
          AppSpacing.verticalSpaceSM,
          DropdownButtonFormField<String>(
            initialValue: _cropCode,
            decoration: const InputDecoration(labelText: 'Crop', border: OutlineInputBorder()),
            items: const [
              DropdownMenuItem(value: 'soybean', child: Text('Soybean')),
              DropdownMenuItem(value: 'cotton', child: Text('Cotton')),
              DropdownMenuItem(value: 'jowar', child: Text('Sorghum (Jowar)')),
              DropdownMenuItem(value: 'onion', child: Text('Onion')),
            ],
            onChanged: (v) => setState(() => _cropCode = v ?? 'soybean'),
          ),
          AppSpacing.verticalSpaceSM,
          Row(
            children: [
              Expanded(child: _numberField(_tmaxCtrl, 'Forecast max °C')),
              AppSpacing.horizontalSpaceSM,
              Expanded(child: _numberField(_tminCtrl, 'Forecast min °C')),
            ],
          ),
          AppSpacing.verticalSpaceSM,
          FilledButton.icon(
            onPressed: _cropHeatLoading ? null : _assessCropHeat,
            icon: _cropHeatLoading
                ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2))
                : const Icon(Icons.thermostat),
            label: const Text('Assess crop heat'),
          ),
          if (_cropHeatError != null) ...[AppSpacing.verticalSpaceSM, _errorCard(_cropHeatError!)],
          if (_cropHeatResult != null) ...[
            AppSpacing.verticalSpaceSM,
            _cropHeatCard(_cropHeatResult!),
          ],
          const Divider(height: 32),
          _sectionTitle('Worker Heat-Hazard (WBGT)'),
          const Text('ACGIH 2023 / ISO 7243:2017 screening limits.',
              style: TextStyle(fontSize: 12, color: Colors.black54)),
          AppSpacing.verticalSpaceSM,
          Row(
            children: [
              Expanded(child: _numberField(_airTempCtrl, 'Air temp °C')),
              AppSpacing.horizontalSpaceSM,
              Expanded(child: _numberField(_rhCtrl, 'Humidity %')),
            ],
          ),
          AppSpacing.verticalSpaceSM,
          Row(
            children: [
              Expanded(child: _numberField(_windCtrl, 'Wind m/s')),
              AppSpacing.horizontalSpaceSM,
              Expanded(child: _numberField(_solarCtrl, 'Solar W/m²')),
            ],
          ),
          AppSpacing.verticalSpaceSM,
          DropdownButtonFormField<String>(
            initialValue: _workload,
            decoration: const InputDecoration(labelText: 'Workload', border: OutlineInputBorder()),
            items: const [
              DropdownMenuItem(value: 'light', child: Text('Light')),
              DropdownMenuItem(value: 'moderate', child: Text('Moderate')),
              DropdownMenuItem(value: 'heavy', child: Text('Heavy')),
              DropdownMenuItem(value: 'very_heavy', child: Text('Very heavy')),
            ],
            onChanged: (v) => setState(() => _workload = v ?? 'moderate'),
          ),
          AppSpacing.verticalSpaceSM,
          FilledButton.icon(
            onPressed: _workerHeatLoading ? null : _assessWorkerHeat,
            icon: _workerHeatLoading
                ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2))
                : const Icon(Icons.engineering),
            label: const Text('Assess worker heat'),
          ),
          if (_workerHeatError != null) ...[AppSpacing.verticalSpaceSM, _errorCard(_workerHeatError!)],
          if (_workerHeatResult != null) ...[
            AppSpacing.verticalSpaceSM,
            _workerHeatCard(_workerHeatResult!),
          ],
          AppSpacing.verticalSpaceXXL,
        ],
      ),
    );
  }

  Widget _cropHeatCard(CropHeatResult r) {
    final color = switch (r.riskCategory) {
      'CRITICAL' => const Color(0xFFC62828),
      'HIGH' => const Color(0xFFE65100),
      'MODERATE' => const Color(0xFFF9A825),
      _ => const Color(0xFF2E7D32),
    };
    return Container(
      decoration: AppDecorations.card(),
      padding: AppSpacing.paddingAllLG,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(children: [
            Icon(Icons.thermostat, color: color),
            AppSpacing.horizontalSpaceSM,
            Text('${r.riskLabel} (${r.riskCategory})',
                style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15, color: color)),
          ]),
          AppSpacing.verticalSpaceXS,
          Text(r.explanation, style: const TextStyle(fontSize: 13)),
          AppSpacing.verticalSpaceXS,
          Text('Stage: ${r.stageName} • GDD: ${r.gdd} • Warm night: ${r.warmNightHazard ? "Yes" : "No"}',
              style: const TextStyle(fontSize: 12, color: Colors.black54)),
          AppSpacing.verticalSpaceXS,
          Text(r.evidenceCitation, style: const TextStyle(fontSize: 11, color: Colors.black45)),
        ],
      ),
    );
  }

  Widget _workerHeatCard(WorkerHeatResult r) {
    final color = switch (r.hazardLevel) {
      'EXTREME' => const Color(0xFFC62828),
      'HIGH' => const Color(0xFFE65100),
      'MODERATE' => const Color(0xFFF9A825),
      _ => const Color(0xFF2E7D32),
    };
    return Container(
      decoration: AppDecorations.card(),
      padding: AppSpacing.paddingAllLG,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(children: [
            Icon(Icons.engineering, color: color),
            AppSpacing.horizontalSpaceSM,
            Text('${r.hazardLevel} hazard',
                style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15, color: color)),
          ]),
          AppSpacing.verticalSpaceXS,
          Text('WBGT: ${r.wbgt.toStringAsFixed(1)}°C • Effective: ${r.wbgtEffective.toStringAsFixed(1)}°C '
              '• Threshold: ${r.threshold.toStringAsFixed(1)}°C',
              style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600)),
          AppSpacing.verticalSpaceXS,
          Text(r.recommendation, style: const TextStyle(fontSize: 13)),
          AppSpacing.verticalSpaceXS,
          Text('Work/rest: ${r.workRestCycle}', style: const TextStyle(fontSize: 12, color: Colors.black54)),
          if (r.heatIndex != null)
            Text('Heat index: ${r.heatIndex!.toStringAsFixed(1)}°C${r.utci != null ? " • UTCI: ${r.utci!.toStringAsFixed(1)}°C" : ""}',
                style: const TextStyle(fontSize: 11.5, color: Colors.black45)),
        ],
      ),
    );
  }

  Widget _infoBanner(String text) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: const Color(0xFFFFFDE7),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: const Color(0xFFFFD54F)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(Icons.balance, color: Color(0xFFF57F17), size: 22),
          AppSpacing.horizontalSpaceSM,
          Expanded(child: Text(text, style: const TextStyle(fontSize: 12.5, height: 1.35))),
        ],
      ),
    );
  }

  Widget _sectionTitle(String text) => Padding(
        padding: const EdgeInsets.only(bottom: 2),
        child: Text(text, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
      );

  Widget _numberField(TextEditingController controller, String label) => TextField(
        controller: controller,
        keyboardType: const TextInputType.numberWithOptions(decimal: true),
        decoration: InputDecoration(labelText: label, border: const OutlineInputBorder(), isDense: true),
      );

  Widget _errorCard(String message) => Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: const Color(0xFFFFEBEE),
          borderRadius: BorderRadius.circular(8),
          border: Border.all(color: const Color(0xFFEF9A9A)),
        ),
        child: Text(message, style: const TextStyle(color: Color(0xFFB71C1C), fontSize: 12.5)),
      );
}
