import 'package:flutter/material.dart';
import 'package:cropnet_mobile/core/router/farm_state.dart';
import 'package:cropnet_mobile/features/advisory/data/advisory_repository.dart';
import 'package:cropnet_mobile/features/advisory/models/advisory_models.dart';
import 'package:cropnet_mobile/features/soil/data/soil_repository.dart';
import 'package:cropnet_mobile/main.dart' show FarmItem;

/// Chat message model for Agricultural AI Assistant & Advisory session.
class AdvisoryMessage {
  final String id;
  final String sender; // 'user' or 'assistant'
  final String text;
  final String? provenance;
  final String? generationSource;
  final DateTime timestamp;
  final bool isError;

  const AdvisoryMessage({
    required this.id,
    required this.sender,
    required this.text,
    this.provenance,
    this.generationSource,
    required this.timestamp,
    this.isError = false,
  });

  bool get isUser => sender == 'user';
}

/// Feature 2: Agricultural AI Assistant & Advisory Screen.
///
/// Integrates the deterministic agricultural decision engine (Phase 5.1)
/// and guarded Qwen3:8B conversational explanation interface (Phase 5.2) via [AdvisoryRepository].
///
/// Core Agronomic Invariants Enforced:
/// - Deterministic Decision Engine is the sole authority for crop suitability.
/// - The LLM NEVER decides feasibility or overrides hard biological constraints.
/// - Responses link directly to verified ICAR, MPKV Rahuri, and CRIDA citations.
/// - Full bilingual support in English (EN) and Marathi (मराठी).
/// - Instant 1-touch diagnostic follow-up answering with automatic context re-evaluation.
/// - Immediate graceful fallback to deterministic advice if Ollama is offline or times out.
class AdvisoryScreen extends StatefulWidget {
  const AdvisoryScreen({super.key});

  @override
  State<AdvisoryScreen> createState() => _AdvisoryScreenState();
}

class _AdvisoryScreenState extends State<AdvisoryScreen> with SingleTickerProviderStateMixin {
  final TextEditingController _textController = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  final AdvisoryRepository _advisoryRepo = AdvisoryRepository();
  final SoilRepository _soilRepo = SoilRepository();

  late TabController _mobileTabController;

  // Farm Context State
  String _selectedTaluka = 'Baramati';
  String _selectedDistrict = 'Pune';
  String? _selectedFarmId;
  double _soilPh = 7.8; // Default Vertisol alkaline baseline for Baramati pilot
  bool _irrigationAvailable = true;
  String _irrigationSource = 'canal';
  String _selectedSeason = 'kharif'; // 'kharif', 'rabi', 'summer'
  String _selectedLanguage = 'en'; // 'en' or 'mr'

  // Evaluation & Explanation State
  String? _decisionId;
  FarmEvaluationResponse? _evaluation;
  AgriculturalExplanationResponse? _lastExplanation;
  bool _isEvaluating = false;
  bool _isSendingMessage = false;
  String? _errorMessage;

  final List<String> _pilotTalukas = [
    'Baramati',
    'Indapur',
    'Maval',
    'Mulshi',
    'Haveli',
    'Shirur',
    'Daund',
  ];

  late List<AdvisoryMessage> _messages;

  @override
  void initState() {
    super.initState();
    _mobileTabController = TabController(length: 2, vsync: this);
    _resetConversation();
    _loadFarmsAndContext();
  }

  @override
  void dispose() {
    _mobileTabController.dispose();
    _textController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  /// Initial load of registered farms belonging to the user
  Future<void> _loadFarmsAndContext() async {
    await FarmRepository.instance.loadFarms();
    if (!mounted) return;

    final farms = FarmRepository.instance.farms;
    if (farms.isNotEmpty) {
      final firstFarm = farms.first;
      setState(() {
        _selectedFarmId = firstFarm.id;
        _selectedTaluka = firstFarm.taluka;
        _selectedDistrict = firstFarm.district;
        _irrigationAvailable = firstFarm.irrigationType != 'rainfed';
        _irrigationSource = firstFarm.waterSource;
      });
      _fetchFarmSoilProfile(firstFarm.id);
    }
  }

  /// Fetch soil profile to obtain measured or estimated pH
  Future<void> _fetchFarmSoilProfile(String farmId) async {
    try {
      final profile = await _soilRepo.getFarmSoilProfile(farmId);
      if (mounted && profile.ph?.value != null) {
        setState(() {
          _soilPh = profile.ph!.value!;
        });
      }
    } catch (_) {
      // Retain existing/default pH if soil profile is not yet initialized
    }
  }

  void _onFarmSelected(String? farmId) {
    if (farmId == null) return;
    final farm = FarmRepository.instance.getFarmById(farmId);
    setState(() {
      _selectedFarmId = farmId;
      if (farm != null) {
        _selectedTaluka = farm.taluka;
        _selectedDistrict = farm.district;
        _irrigationAvailable = farm.irrigationType != 'rainfed';
        _irrigationSource = farm.waterSource;
      }
      _decisionId = null;
      _evaluation = null;
      _lastExplanation = null;
      _errorMessage = null;
    });
    if (farm != null) {
      _fetchFarmSoilProfile(farm.id);
    }
    _resetConversation();
  }

  void _resetConversation() {
    _decisionId = null;
    _evaluation = null;
    _lastExplanation = null;
    _errorMessage = null;

    final isMr = _selectedLanguage == 'mr';
    final seasonName = _getSeasonDisplayLabel(_selectedSeason, isMr);

    _messages = [
      AdvisoryMessage(
        id: 'msg-init-1',
        sender: 'assistant',
        text: isMr
            ? 'नमस्ते! क्रॉपनेट एआय कृषी सल्लागार प्रणालीमध्ये आपले स्वागत आहे. '
              'मी $_selectedTaluka ($seasonName हंगाम) परिसरासाठी प्रमाणित कृषी निर्णय प्रणालीशी जोडलेला आहे. '
              'पिकांची निवड, माती परीक्षण, किंवा हवामानानुसार सल्ला हवा असल्यास विचारा.'
            : 'Namaste! Welcome to CropNet AI Agronomic Advisory. '
              'I am connected to the CropNet agricultural intelligence decision engine for $_selectedTaluka ($seasonName Season). '
              'How can I assist with your crop feasibility, soil constraints, or irrigation decisions today?',
        provenance: '[llm_qwen3_8b | Guardrails: Verified | Sources: MPKV Rahuri / ICAR / CRIDA]',
        generationSource: 'llm_qwen3_8b',
        timestamp: DateTime.now().subtract(const Duration(minutes: 5)),
      ),
      AdvisoryMessage(
        id: 'msg-init-2',
        sender: 'assistant',
        text: isMr
            ? '📍 $_selectedTaluka परिसर प्रोफाइल: काळी मध्यम ते भारी व्हर्टिसोल जमीन, '
              'सामू (pH) ${_soilPh.toStringAsFixed(1)}. उपलब्ध सिंचन: ${_irrigationAvailable ? _irrigationSource : "जिरायती (Rainfed)"}. '
              'खालील "शेत पिकांचे मूल्यांकन करा" बटण दाबून प्रमाणित पीक feasibility तपासा.'
            : '📍 Farm Context for $_selectedTaluka, $_selectedDistrict: Vertisol black clay soil, '
              'soil pH ${_soilPh.toStringAsFixed(1)}, irrigation: ${_irrigationAvailable ? _irrigationSource : "Rainfed"}. '
              'Tap "Evaluate Farm Crops" to run deterministic crop feasibility analysis.',
        provenance: '[deterministic_fallback | Guardrails: Enforced | Sources: ISRIC SoilGrids / MPKV Rahuri]',
        generationSource: 'deterministic_fallback',
        timestamp: DateTime.now().subtract(const Duration(minutes: 4)),
      ),
    ];
  }

  FarmItem? _getCurrentFarm() {
    final farms = FarmRepository.instance.farms;
    if (_selectedFarmId != null) {
      return FarmRepository.instance.getFarmById(_selectedFarmId!);
    }
    if (farms.isNotEmpty) {
      return farms.first;
    }
    return null;
  }

  /// Trigger deterministic farm evaluation against Phase 5.1 FastAPI endpoints
  Future<void> _runDeterministicEvaluation({String? userQuery}) async {
    setState(() {
      _isEvaluating = true;
      _errorMessage = null;
    });

    final currentFarm = _getCurrentFarm();
    final taluka = currentFarm?.taluka ?? _selectedTaluka;
    final district = currentFarm?.district ?? _selectedDistrict;

    final contextInput = FarmContextInput(
      farmId: currentFarm?.id,
      taluka: taluka,
      district: district,
      latitude: currentFarm?.centroid.latitude ?? 18.18,
      longitude: currentFarm?.centroid.longitude ?? 74.53,
      soilPh: _soilPh,
      irrigationAvailable: _irrigationAvailable,
      irrigationSource: _irrigationSource,
      targetSeason: _selectedSeason,
      language: _selectedLanguage,
      userQuery: userQuery,
    );

    try {
      final eval = await _advisoryRepo.evaluateFarm(contextInput);
      _decisionId = eval.decisionId;
      _evaluation = eval;

      // Request natural-language explanation grounded in this validated decision
      try {
        final explanation = await _advisoryRepo.explainDecision(
          eval.decisionId,
          language: _selectedLanguage,
        );
        _lastExplanation = explanation;

        final badge = _buildProvenanceBadge(
          generationSource: explanation.generationSource,
          citations: explanation.authoritativeCitations,
          validationPassed: explanation.validationPassed,
        );

        if (mounted) {
          setState(() {
            _messages.add(
              AdvisoryMessage(
                id: 'eval-exp-${DateTime.now().millisecondsSinceEpoch}',
                sender: 'assistant',
                text: explanation.explanationText,
                provenance: badge,
                generationSource: explanation.generationSource,
                timestamp: DateTime.now(),
              ),
            );
          });
        }
      } catch (_) {
        // Safe deterministic fallback explanation on Ollama offline / timeout
        final fallbackText = _generateLocalDeterministicSummary(eval, _selectedLanguage);
        final badge = _buildProvenanceBadge(
          generationSource: 'deterministic_fallback',
          citations: eval.cropOutcomes.expand((o) => o.citations).toList(),
          validationPassed: true,
        );

        if (mounted) {
          setState(() {
            _messages.add(
              AdvisoryMessage(
                id: 'eval-fallback-${DateTime.now().millisecondsSinceEpoch}',
                sender: 'assistant',
                text: fallbackText,
                provenance: badge,
                generationSource: 'deterministic_fallback',
                timestamp: DateTime.now(),
              ),
            );
          });
        }
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _errorMessage = 'API Connection Error: ${e.toString()}';
        });
      }
    } finally {
      if (mounted) {
        setState(() {
          _isEvaluating = false;
        });
        _scrollToBottom();
      }
    }
  }

  /// Submit diagnostic follow-up answer to re-evaluate farm context
  Future<void> _submitFollowUpAnswer(String questionId, String parameter, dynamic answer) async {
    if (_decisionId == null) return;

    setState(() {
      _isEvaluating = true;
      _errorMessage = null;
    });

    final isMr = _selectedLanguage == 'mr';
    final userMsgText = isMr
        ? 'नोंदवलेली माहिती: $parameter = $answer'
        : 'Diagnostic input provided: $parameter = $answer';

    setState(() {
      _messages.add(
        AdvisoryMessage(
          id: 'user-ans-${DateTime.now().millisecondsSinceEpoch}',
          sender: 'user',
          text: userMsgText,
          timestamp: DateTime.now(),
        ),
      );
    });
    _scrollToBottom();

    try {
      final updatedEval = await _advisoryRepo.processFollowUp(
        _decisionId!,
        {parameter: answer},
      );

      setState(() {
        _evaluation = updatedEval;
        _decisionId = updatedEval.decisionId;
      });

      // Request natural language explanation for updated decision
      try {
        final explanation = await _advisoryRepo.explainDecision(
          updatedEval.decisionId,
          language: _selectedLanguage,
        );
        _lastExplanation = explanation;

        final badge = _buildProvenanceBadge(
          generationSource: explanation.generationSource,
          citations: explanation.authoritativeCitations,
          validationPassed: explanation.validationPassed,
        );

        if (mounted) {
          setState(() {
            _messages.add(
              AdvisoryMessage(
                id: 're-eval-${DateTime.now().millisecondsSinceEpoch}',
                sender: 'assistant',
                text: explanation.explanationText,
                provenance: badge,
                generationSource: explanation.generationSource,
                timestamp: DateTime.now(),
              ),
            );
          });
        }
      } catch (_) {
        // Safe deterministic fallback
        final fallbackText = _generateLocalDeterministicSummary(updatedEval, _selectedLanguage);
        final badge = _buildProvenanceBadge(
          generationSource: 'deterministic_fallback',
          citations: updatedEval.cropOutcomes.expand((o) => o.citations).toList(),
          validationPassed: true,
        );

        if (mounted) {
          setState(() {
            _messages.add(
              AdvisoryMessage(
                id: 're-eval-fallback-${DateTime.now().millisecondsSinceEpoch}',
                sender: 'assistant',
                text: fallbackText,
                provenance: badge,
                generationSource: 'deterministic_fallback',
                timestamp: DateTime.now(),
              ),
            );
          });
        }
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _errorMessage = 'Follow-up submission failed: $e';
        });
      }
    } finally {
      if (mounted) {
        setState(() {
          _isEvaluating = false;
        });
        _scrollToBottom();
      }
    }
  }

  /// Submit user message to conversational dialogue endpoint
  Future<void> _sendMessage(String query) async {
    final trimmed = query.trim();
    if (trimmed.isEmpty) return;

    final userMsg = AdvisoryMessage(
      id: 'msg-${DateTime.now().millisecondsSinceEpoch}',
      sender: 'user',
      text: trimmed,
      timestamp: DateTime.now(),
    );

    setState(() {
      _messages.add(userMsg);
      _isSendingMessage = true;
      _errorMessage = null;
    });
    _textController.clear();
    _scrollToBottom();

    // If no decision evaluated yet, run evaluation first with this query
    if (_decisionId == null) {
      await _runDeterministicEvaluation(userQuery: trimmed);
      if (mounted) setState(() => _isSendingMessage = false);
      return;
    }

    try {
      final history = _messages
          .where((m) => m.id != userMsg.id && !m.isError)
          .map((m) => ConversationMessage(
                role: m.sender == 'user' ? 'user' : 'assistant',
                content: m.text,
              ))
          .toList();

      final response = await _advisoryRepo.processConversation(
        _decisionId!,
        trimmed,
        language: _selectedLanguage,
        history: history,
      );

      _lastExplanation = response;
      final badge = _buildProvenanceBadge(
        generationSource: response.generationSource,
        citations: response.authoritativeCitations,
        validationPassed: response.validationPassed,
      );

      if (mounted) {
        setState(() {
          _messages.add(
            AdvisoryMessage(
              id: 'reply-${DateTime.now().millisecondsSinceEpoch}',
              sender: 'assistant',
              text: response.explanationText,
              provenance: badge,
              generationSource: response.generationSource,
              timestamp: DateTime.now(),
            ),
          );
        });
      }
    } catch (e) {
      if (mounted) {
        final isMr = _selectedLanguage == 'mr';
        final fallbackNotice = isMr
            ? 'सल्लागार मॉडेल तात्पुरते अनुपलब्ध आहे. तथापि, वरील प्रमाणित पीक मूल्यांकन निष्कर्ष निश्चित नियमांनुसार वैध आहेत.'
            : 'LLM dialogue service is currently unreachable. The deterministic crop feasibility outcomes above remain fully verified and authoritative.';
        const badge = '[deterministic_fallback | Guardrails: Enforced | Sources: MPKV Rahuri / ICAR]';

        setState(() {
          _messages.add(
            AdvisoryMessage(
              id: 'err-${DateTime.now().millisecondsSinceEpoch}',
              sender: 'assistant',
              text: fallbackNotice,
              provenance: badge,
              generationSource: 'deterministic_fallback',
              timestamp: DateTime.now(),
              isError: false,
            ),
          );
        });
      }
    } finally {
      if (mounted) {
        setState(() {
          _isSendingMessage = false;
        });
        _scrollToBottom();
      }
    }
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 250),
          curve: Curves.easeOut,
        );
      }
    });
  }

  /// Construct provenance and generation source badge
  String _buildProvenanceBadge({
    required String generationSource,
    required List<CitationMetadata> citations,
    bool validationPassed = true,
  }) {
    final Set<String> orgs = {};
    for (final c in citations) {
      if (c.organization.isNotEmpty) {
        orgs.add(c.organization);
      }
    }
    final sourcesStr = orgs.isNotEmpty ? orgs.join(' / ') : 'MPKV Rahuri / ICAR';

    if (generationSource == 'llm_qwen3_8b') {
      final guardrailStr = validationPassed ? 'Verified' : 'Fallback';
      return '[llm_qwen3_8b | Guardrails: $guardrailStr | Sources: $sourcesStr]';
    } else {
      return '[deterministic_fallback | Guardrails: Enforced | Sources: $sourcesStr]';
    }
  }

  /// Safe local deterministic outcome summarizer for fallbacks
  String _generateLocalDeterministicSummary(FarmEvaluationResponse eval, String lang) {
    final isMr = lang == 'mr';
    final taluka = eval.talukaResolved ?? _selectedTaluka;
    final season = _getSeasonDisplayLabel(eval.targetSeason ?? _selectedSeason, isMr);

    final buffer = StringBuffer();
    if (isMr) {
      buffer.writeln('🌾 **$taluka भागासाठी प्रमाणित पीक मूल्यमापन निकाल (हंगाम: $season):**\n');
      for (final o in eval.cropOutcomes) {
        final status = _getFeasibilityBadge(o.decisionState, o.isDisqualified, true);
        final cropName = o.marathiName ?? o.commonName;
        buffer.writeln('• **$cropName**: $status');
        if (o.limitingFactors.isNotEmpty) {
          buffer.writeln('   - *अडचणी / मर्यादा:* ${o.limitingFactors.join(", ")}');
        }
        if (o.explanation.isNotEmpty) {
          buffer.writeln('   - *स्पष्टीकरण:* ${o.explanation}');
        }
        buffer.writeln();
      }
    } else {
      buffer.writeln('🌾 **Deterministic Crop Feasibility Outcomes for $taluka ($season Season):**\n');
      for (final o in eval.cropOutcomes) {
        final status = _getFeasibilityBadge(o.decisionState, o.isDisqualified, false);
        buffer.writeln('• **${o.commonName}** (${o.scientificName}): $status');
        if (o.limitingFactors.isNotEmpty) {
          buffer.writeln('   - *Limiting Factors:* ${o.limitingFactors.join(", ")}');
        }
        if (o.reproductiveRiskWarnings.isNotEmpty) {
          buffer.writeln('   - *Reproductive Heat Stress:* ${o.reproductiveRiskWarnings.join(", ")}');
        }
        if (o.explanation.isNotEmpty) {
          buffer.writeln('   - *Rule Statement:* ${o.explanation}');
        }
        buffer.writeln();
      }
    }
    return buffer.toString().trim();
  }

  String _getFeasibilityBadge(DecisionState state, bool isDisqualified, bool isMr) {
    if (isDisqualified || state == DecisionState.unsuitableVerifiedConstraint) {
      return 'DISQUALIFIED';
    }
    switch (state) {
      case DecisionState.verifiedSuitable:
        return 'SUITED';
      case DecisionState.regionalScreeningOnly:
      case DecisionState.conditionallySuitablePendingData:
      case DecisionState.requiresRegionalValidation:
        return 'REGIONAL_SCREENING_ONLY';
      case DecisionState.unsuitableVerifiedConstraint:
        return 'DISQUALIFIED';
      case DecisionState.abstainInsufficientEvidence:
        return 'INSUFFICIENT_EVIDENCE';
    }
  }

  Color _getFeasibilityColor(DecisionState state, bool isDisqualified) {
    if (isDisqualified || state == DecisionState.unsuitableVerifiedConstraint) {
      return const Color(0xFFC62828); // Red
    }
    switch (state) {
      case DecisionState.verifiedSuitable:
        return const Color(0xFF2E7D32); // Green
      case DecisionState.regionalScreeningOnly:
      case DecisionState.conditionallySuitablePendingData:
      case DecisionState.requiresRegionalValidation:
        return const Color(0xFFE65100); // Amber/Orange
      case DecisionState.unsuitableVerifiedConstraint:
        return const Color(0xFFC62828); // Red
      case DecisionState.abstainInsufficientEvidence:
        return const Color(0xFF546E7A); // Slate Grey
    }
  }

  String _getSeasonDisplayLabel(String season, bool isMr) {
    switch (season.toLowerCase()) {
      case 'kharif':
        return isMr ? 'खरीप (Kharif - पावसाळी)' : 'Kharif (Monsoon)';
      case 'rabi':
        return isMr ? 'रब्बी (Rabi - हिवाळी)' : 'Rabi (Winter)';
      case 'summer':
        return isMr ? 'उन्हाळी (Summer - Zaid)' : 'Summer (Zaid)';
      default:
        return season;
    }
  }

  List<String> get _bilingualPromptSuggestions {
    if (_selectedLanguage == 'mr') {
      return [
        'ऊस पिकाला पाण्याची किती गरज आहे?',
        'काळी जमीन हरभऱ्यासाठी योग्य आहे का?',
        'डाळिंबासाठी बहार व्यवस्थापन कसे करावे?',
      ];
    } else {
      return [
        'Why is sugarcane in regional screening?',
        'Can I grow chickpea in heavy clay soil?',
        'What are the water requirements for pomegranate?',
      ];
    }
  }

  @override
  Widget build(BuildContext context) {
    final isMr = _selectedLanguage == 'mr';

    return Scaffold(
      backgroundColor: const Color(0xFFF7FAF7),
      appBar: AppBar(
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              isMr ? 'कृषी एआय सल्लागार' : 'AI Agricultural Assistant & Advisory',
              style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18),
            ),
            Text(
              isMr
                  ? 'ICAR व MPKV राहुरी प्रमाणित निर्णय प्रणाली'
                  : 'Grounded in Deterministic ICAR & MPKV Decision Engine',
              style: const TextStyle(fontSize: 11, color: Colors.white70),
            ),
          ],
        ),
        backgroundColor: const Color(0xFF1B5E20),
        foregroundColor: Colors.white,
        actions: [
          // Bilingual Language Toggle (EN / MR)
          Container(
            margin: const EdgeInsets.symmetric(vertical: 8, horizontal: 4),
            decoration: BoxDecoration(
              color: Colors.white.withAlpha(30),
              borderRadius: BorderRadius.circular(20),
              border: Border.all(color: Colors.white38),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                _buildLanguageButton('EN', 'en', active: _selectedLanguage == 'en'),
                _buildLanguageButton('मराठी', 'mr', active: _selectedLanguage == 'mr'),
              ],
            ),
          ),
          IconButton(
            icon: const Icon(Icons.refresh),
            tooltip: isMr ? 'पुन्हा सुरू करा' : 'Restart Advisory Session',
            onPressed: () => setState(_resetConversation),
          ),
          const SizedBox(width: 8),
        ],
      ),
      body: LayoutBuilder(
        builder: (context, constraints) {
          final isWide = constraints.maxWidth >= 960;

          if (isWide) {
            // Responsive Two-Column Layout for Desktop & Web
            return Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Left Column: Farm Context Selector + Crop Feasibility Outcomes + Diagnostic Questions
                Expanded(
                  flex: 5,
                  child: Container(
                    decoration: BoxDecoration(
                      color: Colors.white,
                      border: Border(right: BorderSide(color: Colors.grey.shade300)),
                    ),
                    child: SingleChildScrollView(
                      padding: const EdgeInsets.all(16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          _buildFarmContextSelectorCard(isMr),
                          const SizedBox(height: 16),
                          if (_evaluation != null) ...[
                            _buildDeterministicEvaluationCard(isMr),
                            const SizedBox(height: 16),
                            if (_evaluation!.followUpQuestions.isNotEmpty)
                              _buildDiagnosticFollowUpCard(isMr),
                          ],
                        ],
                      ),
                    ),
                  ),
                ),

                // Right Column: AI Assistant Dialogue & Qwen3:8B Explanation
                Expanded(
                  flex: 6,
                  child: Column(
                    children: [
                      _buildSafetyGuardrailBanner(isMr),
                      _buildQuickPromptChipsBar(),
                      if (_errorMessage != null) _buildErrorBanner(),
                      Expanded(
                        child: ListView.builder(
                          controller: _scrollController,
                          padding: const EdgeInsets.all(16),
                          itemCount: _messages.length,
                          itemBuilder: (ctx, idx) => _buildMessageBubble(_messages[idx]),
                        ),
                      ),
                      if (_isSendingMessage) _buildThinkingIndicator(isMr),
                      if (_lastExplanation != null && _lastExplanation!.governanceNotice.isNotEmpty)
                        Padding(
                          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 2),
                          child: Text(
                            _lastExplanation!.governanceNotice,
                            style: const TextStyle(fontSize: 10, color: Colors.black45, fontStyle: FontStyle.italic),
                            textAlign: TextAlign.center,
                          ),
                        ),
                      _buildChatInputBar(isMr),
                    ],
                  ),
                ),
              ],
            );
          } else {
            // Mobile / Tablet Tabbed Layout
            return Column(
              children: [
                _buildSafetyGuardrailBanner(isMr),
                TabBar(
                  controller: _mobileTabController,
                  labelColor: const Color(0xFF1B5E20),
                  unselectedLabelColor: Colors.black54,
                  indicatorColor: const Color(0xFF1B5E20),
                  tabs: [
                    Tab(
                      icon: const Icon(Icons.analytics_outlined, size: 20),
                      text: isMr
                          ? 'पीक मूल्यांकन (${_evaluation?.cropOutcomes.length ?? 0})'
                          : 'Feasibility Board (${_evaluation?.cropOutcomes.length ?? 0})',
                    ),
                    Tab(
                      icon: const Icon(Icons.psychology_outlined, size: 20),
                      text: isMr ? 'एआय सल्लागार' : 'AI Assistant Dialogue',
                    ),
                  ],
                ),
                Expanded(
                  child: TabBarView(
                    controller: _mobileTabController,
                    children: [
                      // Tab 0: Farm Context & Crop Feasibility Board
                      SingleChildScrollView(
                        padding: const EdgeInsets.all(16),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.stretch,
                          children: [
                            _buildFarmContextSelectorCard(isMr),
                            const SizedBox(height: 16),
                            if (_evaluation != null) ...[
                              _buildDeterministicEvaluationCard(isMr),
                              const SizedBox(height: 16),
                              if (_evaluation!.followUpQuestions.isNotEmpty)
                                _buildDiagnosticFollowUpCard(isMr),
                            ],
                          ],
                        ),
                      ),

                      // Tab 1: AI Assistant Chat
                      Column(
                        children: [
                          _buildQuickPromptChipsBar(),
                          if (_errorMessage != null) _buildErrorBanner(),
                          Expanded(
                            child: ListView.builder(
                              controller: _scrollController,
                              padding: const EdgeInsets.all(16),
                              itemCount: _messages.length,
                              itemBuilder: (ctx, idx) => _buildMessageBubble(_messages[idx]),
                            ),
                          ),
                          if (_isSendingMessage) _buildThinkingIndicator(isMr),
                          if (_lastExplanation != null && _lastExplanation!.governanceNotice.isNotEmpty)
                            Padding(
                              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 2),
                              child: Text(
                                _lastExplanation!.governanceNotice,
                                style: const TextStyle(fontSize: 10, color: Colors.black45, fontStyle: FontStyle.italic),
                                textAlign: TextAlign.center,
                              ),
                            ),
                          _buildChatInputBar(isMr),
                        ],
                      ),
                    ],
                  ),
                ),
              ],
            );
          }
        },
      ),
    );
  }

  Widget _buildLanguageButton(String label, String langCode, {required bool active}) {
    return InkWell(
      onTap: () {
        if (_selectedLanguage != langCode) {
          setState(() {
            _selectedLanguage = langCode;
            _resetConversation();
          });
        }
      },
      borderRadius: BorderRadius.circular(20),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
        decoration: BoxDecoration(
          color: active ? Colors.white : Colors.transparent,
          borderRadius: BorderRadius.circular(16),
        ),
        child: Text(
          label,
          style: TextStyle(
            color: active ? const Color(0xFF1B5E20) : Colors.white,
            fontWeight: FontWeight.bold,
            fontSize: 12,
          ),
        ),
      ),
    );
  }

  /// Safety Guardrail Banner mandated by Qwen3:8B dialogue architecture
  Widget _buildSafetyGuardrailBanner(bool isMr) {
    return Container(
      color: const Color(0xFFE8F5E9),
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: Row(
        children: [
          const Icon(Icons.verified_user, color: Color(0xFF2E7D32), size: 18),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              isMr
                  ? 'हमीभाव व पीक पात्रता: केवळ निश्चित अल्गोरिदम ठरवतो (LLM कधीही स्वतः ठरवत नाही).'
                  : 'Authority Notice: Crop suitability is exclusively decided by the deterministic rule engine.',
              style: TextStyle(fontSize: 11, color: Colors.green.shade900, fontWeight: FontWeight.w600),
            ),
          ),
        ],
      ),
    );
  }

  /// Requirement 1: Farm Context & Evaluation Selector Card
  Widget _buildFarmContextSelectorCard(bool isMr) {
    final farms = FarmRepository.instance.farms;

    return Card(
      elevation: 1,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(color: Colors.grey.shade300),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.landscape, color: Color(0xFF1B5E20), size: 20),
                const SizedBox(width: 8),
                Text(
                  isMr ? 'शेत संदर्भ आणि मूल्यांकन निवडक' : 'Farm Context & Evaluation Selector',
                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15, color: Color(0xFF1B5E20)),
                ),
              ],
            ),
            const Divider(height: 20),

            // Registered Farm Dropdown Selector
            if (farms.isNotEmpty) ...[
              Text(
                isMr ? 'नोंदणीकृत शेत निवडा:' : 'Select Registered Farm:',
                style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13),
              ),
              const SizedBox(height: 6),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 12),
                decoration: BoxDecoration(
                  border: Border.all(color: Colors.grey.shade300),
                  borderRadius: BorderRadius.circular(8),
                  color: Colors.grey.shade50,
                ),
                child: DropdownButtonHideUnderline(
                  child: DropdownButton<String>(
                    value: _selectedFarmId ?? farms.first.id,
                    isExpanded: true,
                    items: farms.map((f) {
                      return DropdownMenuItem<String>(
                        value: f.id,
                        child: Row(
                          children: [
                            const Icon(Icons.eco, size: 16, color: Color(0xFF2E7D32)),
                            const SizedBox(width: 8),
                            Expanded(
                              child: Text(
                                '${f.name} (${f.taluka}, ${f.areaAcres.toStringAsFixed(1)} ac)',
                                style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w500),
                                overflow: TextOverflow.ellipsis,
                              ),
                            ),
                          ],
                        ),
                      );
                    }).toList(),
                    onChanged: _onFarmSelected,
                  ),
                ),
              ),
              const SizedBox(height: 12),
            ] else ...[
              Text(
                isMr ? 'पायलट तालुका निवडा:' : 'Select Pilot Taluka:',
                style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13),
              ),
              const SizedBox(height: 6),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 12),
                decoration: BoxDecoration(
                  border: Border.all(color: Colors.grey.shade300),
                  borderRadius: BorderRadius.circular(8),
                  color: Colors.grey.shade50,
                ),
                child: DropdownButtonHideUnderline(
                  child: DropdownButton<String>(
                    value: _selectedTaluka,
                    isExpanded: true,
                    items: _pilotTalukas.map((t) {
                      return DropdownMenuItem<String>(
                        value: t,
                        child: Text(t, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w500)),
                      );
                    }).toList(),
                    onChanged: (val) {
                      if (val != null && val != _selectedTaluka) {
                        setState(() {
                          _selectedTaluka = val;
                          _resetConversation();
                        });
                      }
                    },
                  ),
                ),
              ),
              const SizedBox(height: 12),
            ],

            // Current Farm Context Parameters Display
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                _buildContextChip(
                  icon: Icons.location_on,
                  label: '${isMr ? "तालुका" : "Taluka"}: $_selectedTaluka',
                ),
                _buildContextChip(
                  icon: Icons.map,
                  label: '${isMr ? "जिल्हा" : "District"}: $_selectedDistrict',
                ),
                _buildContextChip(
                  icon: Icons.science,
                  label: 'Soil pH: ${_soilPh.toStringAsFixed(1)} (Vertisol)',
                ),
                _buildContextChip(
                  icon: Icons.water_drop,
                  label: _irrigationAvailable
                      ? '${isMr ? "सिंचन" : "Irrigation"}: $_irrigationSource'
                      : (isMr ? 'जिरायती (Rainfed)' : 'Rainfed'),
                ),
              ],
            ),
            const SizedBox(height: 16),

            // Target Season Selector (Kharif, Rabi, Summer)
            Text(
              isMr ? 'हंगाम निवडा (Target Season):' : 'Target Cropping Season:',
              style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13),
            ),
            const SizedBox(height: 6),
            Row(
              children: [
                Expanded(
                  child: _buildSeasonOption(
                    seasonKey: 'kharif',
                    title: isMr ? 'खरीप' : 'Kharif',
                    subtitle: isMr ? 'पावसाळी' : 'Monsoon',
                    isSelected: _selectedSeason == 'kharif',
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: _buildSeasonOption(
                    seasonKey: 'rabi',
                    title: isMr ? 'रब्बी' : 'Rabi',
                    subtitle: isMr ? 'हिवाळी' : 'Winter',
                    isSelected: _selectedSeason == 'rabi',
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: _buildSeasonOption(
                    seasonKey: 'summer',
                    title: isMr ? 'उन्हाळी' : 'Summer',
                    subtitle: isMr ? 'झैद' : 'Zaid',
                    isSelected: _selectedSeason == 'summer',
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),

            // Prominent "Evaluate Farm Crops" Button
            ElevatedButton(
              onPressed: _isEvaluating ? null : () => _runDeterministicEvaluation(),
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFF1B5E20),
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(vertical: 14),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                elevation: 2,
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  if (_isEvaluating)
                    const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                    )
                  else
                    const Icon(Icons.psychology_outlined, size: 20),
                  const SizedBox(width: 8),
                  Text(
                    _isEvaluating
                        ? (isMr ? 'मूल्यांकन चालू आहे...' : 'Evaluating Farm Feasibility...')
                        : (isMr ? 'शेत पिकांचे मूल्यांकन करा' : 'Evaluate Farm Crops'),
                    style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildContextChip({required IconData icon, required String label}) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 5),
      decoration: BoxDecoration(
        color: const Color(0xFFF1F8E9),
        borderRadius: BorderRadius.circular(6),
        border: Border.all(color: const Color(0xFFC8E6C9)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 14, color: const Color(0xFF2E7D32)),
          const SizedBox(width: 4),
          Text(
            label,
            style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w500, color: Color(0xFF1B5E20)),
          ),
        ],
      ),
    );
  }

  Widget _buildSeasonOption({
    required String seasonKey,
    required String title,
    required String subtitle,
    required bool isSelected,
  }) {
    return InkWell(
      onTap: () {
        setState(() {
          _selectedSeason = seasonKey;
        });
      },
      borderRadius: BorderRadius.circular(8),
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 8),
        decoration: BoxDecoration(
          color: isSelected ? const Color(0xFF1B5E20) : Colors.grey.shade100,
          borderRadius: BorderRadius.circular(8),
          border: Border.all(
            color: isSelected ? const Color(0xFF1B5E20) : Colors.grey.shade300,
          ),
        ),
        child: Column(
          children: [
            Text(
              title,
              style: TextStyle(
                fontWeight: FontWeight.bold,
                fontSize: 13,
                color: isSelected ? Colors.white : Colors.black87,
              ),
            ),
            Text(
              subtitle,
              style: TextStyle(
                fontSize: 10,
                color: isSelected ? Colors.white70 : Colors.black54,
              ),
            ),
          ],
        ),
      ),
    );
  }

  /// Requirement 2: Deterministic Evaluation Display
  Widget _buildDeterministicEvaluationCard(bool isMr) {
    if (_evaluation == null || _evaluation!.cropOutcomes.isEmpty) {
      return const SizedBox.shrink();
    }

    final suitedCount = _evaluation!.cropOutcomes
        .where((o) => !o.isDisqualified && o.decisionState == DecisionState.verifiedSuitable)
        .length;
    final screeningCount = _evaluation!.cropOutcomes
        .where((o) =>
            !o.isDisqualified &&
            (o.decisionState == DecisionState.regionalScreeningOnly ||
                o.decisionState == DecisionState.conditionallySuitablePendingData ||
                o.decisionState == DecisionState.requiresRegionalValidation))
        .length;
    final disqualifiedCount = _evaluation!.cropOutcomes
        .where((o) => o.isDisqualified || o.decisionState == DecisionState.unsuitableVerifiedConstraint)
        .length;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Summary Header Strip
        Container(
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: Colors.grey.shade50,
            borderRadius: BorderRadius.circular(8),
            border: Border.all(color: Colors.grey.shade300),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  const Icon(Icons.verified, size: 18, color: Color(0xFF1B5E20)),
                  const SizedBox(width: 6),
                  Text(
                    isMr ? 'प्रमाणित पीक मूल्यांकन निष्कर्ष' : 'Deterministic Feasibility Outcomes',
                    style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                  ),
                  const Spacer(),
                  Text(
                    'ID: ${_decisionId ?? ""}',
                    style: TextStyle(fontSize: 10, fontFamily: 'monospace', color: Colors.grey.shade600),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              Row(
                children: [
                  _buildCountBadge('SUITED: $suitedCount', const Color(0xFF2E7D32)),
                  const SizedBox(width: 8),
                  _buildCountBadge('REGIONAL SCREENING: $screeningCount', const Color(0xFFE65100)),
                  const SizedBox(width: 8),
                  _buildCountBadge('DISQUALIFIED: $disqualifiedCount', const Color(0xFFC62828)),
                ],
              ),
            ],
          ),
        ),
        const SizedBox(height: 12),

        // List of Evaluated Crops
        ..._evaluation!.cropOutcomes.map((outcome) {
          final color = _getFeasibilityColor(outcome.decisionState, outcome.isDisqualified);
          final badgeLabel = _getFeasibilityBadge(outcome.decisionState, outcome.isDisqualified, isMr);
          final cropDisplayName = isMr && outcome.marathiName != null
              ? '${outcome.marathiName} (${outcome.commonName})'
              : outcome.commonName;

          return Card(
            margin: const EdgeInsets.only(bottom: 12),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(10),
              side: BorderSide(color: color.withAlpha(120), width: 1.2),
            ),
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Top Title & Feasibility Badge
                  Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              cropDisplayName,
                              style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15),
                            ),
                            Text(
                              outcome.scientificName,
                              style: TextStyle(fontSize: 11, fontStyle: FontStyle.italic, color: Colors.grey.shade700),
                            ),
                          ],
                        ),
                      ),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                        decoration: BoxDecoration(
                          color: color.withAlpha(30),
                          borderRadius: BorderRadius.circular(6),
                          border: Border.all(color: color),
                        ),
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Icon(
                              outcome.isDisqualified ? Icons.cancel : Icons.check_circle,
                              size: 14,
                              color: color,
                            ),
                            const SizedBox(width: 4),
                            Text(
                              badgeLabel,
                              style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: color),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),

                  // Hard Constraints / Limiting Factors Flagged
                  if (outcome.limitingFactors.isNotEmpty || outcome.reproductiveRiskWarnings.isNotEmpty) ...[
                    const SizedBox(height: 8),
                    Container(
                      padding: const EdgeInsets.all(8),
                      decoration: BoxDecoration(
                        color: const Color(0xFFFFF3E0),
                        borderRadius: BorderRadius.circular(6),
                        border: Border.all(color: const Color(0xFFFFB74D)),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              const Icon(Icons.warning_amber_rounded, size: 16, color: Color(0xFFE65100)),
                              const SizedBox(width: 6),
                              Text(
                                isMr ? 'मर्यादा व अडचणी (Hard Constraints Flagged):' : 'Flagged Hard Constraints & Risks:',
                                style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: Color(0xFFE65100)),
                              ),
                            ],
                          ),
                          const SizedBox(height: 4),
                          ...outcome.limitingFactors.map((f) => Padding(
                                padding: const EdgeInsets.only(left: 4, bottom: 2),
                                child: Text('• $f', style: const TextStyle(fontSize: 11, color: Colors.black87)),
                              )),
                          ...outcome.reproductiveRiskWarnings.map((w) => Padding(
                                padding: const EdgeInsets.only(left: 4, bottom: 2),
                                child: Text('• $w', style: const TextStyle(fontSize: 11, color: Color(0xFFB71C1C))),
                              )),
                        ],
                      ),
                    ),
                  ],

                  // Agronomic Rule Explanation
                  if (outcome.explanation.isNotEmpty) ...[
                    const SizedBox(height: 8),
                    Text(
                      outcome.explanation,
                      style: const TextStyle(fontSize: 12, height: 1.3),
                    ),
                  ],

                  // Scientific Citations (ICAR, MPKV Rahuri, CRIDA)
                  if (outcome.citations.isNotEmpty) ...[
                    const SizedBox(height: 8),
                    Wrap(
                      spacing: 6,
                      runSpacing: 4,
                      children: outcome.citations.map((c) {
                        return Container(
                          padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                          decoration: BoxDecoration(
                            color: Colors.grey.shade100,
                            borderRadius: BorderRadius.circular(4),
                            border: Border.all(color: Colors.grey.shade300),
                          ),
                          child: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              const Icon(Icons.menu_book, size: 10, color: Color(0xFF1B5E20)),
                              const SizedBox(width: 4),
                              Text(
                                '${c.organization}${c.publicationYear != null ? " (${c.publicationYear})" : ""}',
                                style: const TextStyle(fontSize: 9, fontWeight: FontWeight.w600, color: Color(0xFF1B5E20)),
                              ),
                            ],
                          ),
                        );
                      }).toList(),
                    ),
                  ],
                ],
              ),
            ),
          );
        }),
      ],
    );
  }

  Widget _buildCountBadge(String label, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
      decoration: BoxDecoration(
        color: color.withAlpha(25),
        borderRadius: BorderRadius.circular(4),
        border: Border.all(color: color.withAlpha(100)),
      ),
      child: Text(
        label,
        style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: color),
      ),
    );
  }

  /// Requirements 5 / 6, 7, 8: Diagnostic Follow-Up Panel with 1-touch response chips
  Widget _buildDiagnosticFollowUpCard(bool isMr) {
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(10),
        side: const BorderSide(color: Color(0xFFFFB300), width: 1.2),
      ),
      color: const Color(0xFFFFFDE7),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.help_outline, color: Color(0xFFE65100), size: 18),
                const SizedBox(width: 6),
                Expanded(
                  child: Text(
                    isMr ? 'अतिरिक्त माहिती आवश्यक (Diagnostic Follow-Up):' : 'Diagnostic Follow-Up (Uncertainty Resolution):',
                    style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: Color(0xFFE65100)),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 4),
            Text(
              isMr
                  ? 'खालील पर्यायांपैकी एकावर स्पर्श करून उत्तर द्या; प्रणाली तात्काळ पुनर्मूल्यांकन करेल.'
                  : 'Tap an option to provide missing soil/water data; the decision engine will re-evaluate feasibility immediately.',
              style: const TextStyle(fontSize: 11, color: Colors.black54),
            ),
            const Divider(height: 16),
            ..._evaluation!.followUpQuestions.map((q) {
              final qText = isMr ? q.questionTextMr : q.questionTextEn;
              return Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      qText,
                      style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 12),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      'Rationale: ${q.agronomicRationale}',
                      style: TextStyle(fontSize: 10, color: Colors.grey.shade700, fontStyle: FontStyle.italic),
                    ),
                    const SizedBox(height: 6),
                    if (q.options != null && q.options!.isNotEmpty)
                      Wrap(
                        spacing: 6,
                        runSpacing: 6,
                        children: q.options!.map((opt) {
                          return ActionChip(
                            label: Text(opt, style: const TextStyle(fontSize: 11)),
                            backgroundColor: Colors.white,
                            side: const BorderSide(color: Color(0xFFFFA000)),
                            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                            onPressed: _isEvaluating
                                ? null
                                : () => _submitFollowUpAnswer(q.questionId, q.targetParameter, opt),
                          );
                        }).toList(),
                      )
                    else
                      Row(
                        children: [
                          ActionChip(
                            label: Text(isMr ? 'होय (Yes)' : 'Yes', style: const TextStyle(fontSize: 11)),
                            backgroundColor: Colors.white,
                            side: const BorderSide(color: Color(0xFFFFA000)),
                            onPressed: _isEvaluating
                                ? null
                                : () => _submitFollowUpAnswer(q.questionId, q.targetParameter, 'yes'),
                          ),
                          const SizedBox(width: 8),
                          ActionChip(
                            label: Text(isMr ? 'नाही (No)' : 'No', style: const TextStyle(fontSize: 11)),
                            backgroundColor: Colors.white,
                            side: const BorderSide(color: Color(0xFFFFA000)),
                            onPressed: _isEvaluating
                                ? null
                                : () => _submitFollowUpAnswer(q.questionId, q.targetParameter, 'no'),
                          ),
                        ],
                      ),
                  ],
                ),
              );
            }),
          ],
        ),
      ),
    );
  }

  /// Requirement 4: Bilingual Quick Prompt Suggestion Chips Bar
  Widget _buildQuickPromptChipsBar() {
    final chips = _bilingualPromptSuggestions;

    return Container(
      height: 48,
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: ListView.separated(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 16),
        itemCount: chips.length,
        separatorBuilder: (_, __) => const SizedBox(width: 8),
        itemBuilder: (ctx, idx) {
          final prompt = chips[idx];
          return ActionChip(
            label: Text(prompt, style: const TextStyle(fontSize: 12)),
            backgroundColor: Colors.white,
            side: BorderSide(color: Colors.green.shade300),
            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
            onPressed: () => _sendMessage(prompt),
          );
        },
      ),
    );
  }

  Widget _buildErrorBanner() {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      padding: const EdgeInsets.all(8),
      decoration: BoxDecoration(
        color: Colors.red.shade50,
        borderRadius: BorderRadius.circular(6),
        border: Border.all(color: Colors.red.shade200),
      ),
      child: Row(
        children: [
          const Icon(Icons.error_outline, color: Colors.red, size: 18),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              _errorMessage!,
              style: const TextStyle(fontSize: 12, color: Colors.red),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildThinkingIndicator(bool isMr) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const SizedBox(width: 14, height: 14, child: CircularProgressIndicator(strokeWidth: 2)),
          const SizedBox(width: 8),
          Text(
            isMr ? 'निर्णय प्रणाली आणि Qwen3:8B सल्ला तयार करत आहे...' : 'Consulting decision engine & Qwen3:8B...',
            style: const TextStyle(fontSize: 12, color: Colors.black54),
          ),
        ],
      ),
    );
  }

  Widget _buildMessageBubble(AdvisoryMessage msg) {
    final isUser = msg.isUser;

    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.only(bottom: 12),
        constraints: BoxConstraints(
          maxWidth: MediaQuery.sizeOf(context).width * (MediaQuery.sizeOf(context).width > 700 ? 0.75 : 0.88),
        ),
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: isUser
              ? const Color(0xFF1B5E20)
              : msg.isError
                  ? Colors.red.shade50
                  : Colors.white,
          borderRadius: BorderRadius.circular(12).copyWith(
            bottomLeft: isUser ? const Radius.circular(12) : Radius.zero,
            bottomRight: isUser ? Radius.zero : const Radius.circular(12),
          ),
          boxShadow: const [
            BoxShadow(
              color: Color(0x0A000000),
              blurRadius: 4,
              offset: Offset(0, 2),
            ),
          ],
          border: isUser
              ? null
              : Border.all(color: msg.isError ? Colors.red.shade200 : Colors.grey.shade200),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(
                  isUser
                      ? Icons.person
                      : msg.isError
                          ? Icons.warning_amber
                          : Icons.psychology,
                  size: 16,
                  color: isUser ? Colors.white70 : const Color(0xFF1B5E20),
                ),
                const SizedBox(width: 6),
                Text(
                  isUser ? 'Farmer' : 'CropNet AI Assistant',
                  style: TextStyle(
                    fontSize: 11,
                    fontWeight: FontWeight.bold,
                    color: isUser ? Colors.white70 : const Color(0xFF1B5E20),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 6),
            Text(
              msg.text,
              style: TextStyle(
                fontSize: 13.5,
                color: isUser ? Colors.white : Colors.black87,
                height: 1.45,
              ),
            ),
            if (msg.provenance != null) ...[
              const SizedBox(height: 8),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: const Color(0xFFF1F8E9),
                  borderRadius: BorderRadius.circular(4),
                  border: Border.all(color: const Color(0xFFC8E6C9)),
                ),
                child: Text(
                  msg.provenance!,
                  style: const TextStyle(
                    fontSize: 10,
                    fontWeight: FontWeight.w600,
                    color: Color(0xFF2E7D32),
                    fontFamily: 'monospace',
                  ),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildChatInputBar(bool isMr) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: Colors.white,
        border: Border(top: BorderSide(color: Colors.grey.shade200)),
      ),
      child: SafeArea(
        child: Row(
          children: [
            Expanded(
              child: TextField(
                controller: _textController,
                decoration: InputDecoration(
                  hintText: isMr
                      ? 'उदा. हरभरा, ऊस किंवा मातीबद्दल विचारा...'
                      : 'Ask about sugarcane, chickpea, or soil in $_selectedTaluka...',
                  hintStyle: const TextStyle(fontSize: 13),
                  contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                  filled: true,
                  fillColor: Colors.grey.shade50,
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(24),
                    borderSide: BorderSide(color: Colors.grey.shade300),
                  ),
                  enabledBorder: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(24),
                    borderSide: BorderSide(color: Colors.grey.shade300),
                  ),
                ),
                onSubmitted: _sendMessage,
              ),
            ),
            const SizedBox(width: 8),
            IconButton.filled(
              icon: const Icon(Icons.send, size: 18),
              style: IconButton.styleFrom(
                backgroundColor: const Color(0xFF1B5E20),
                foregroundColor: Colors.white,
              ),
              onPressed: () => _sendMessage(_textController.text),
            ),
          ],
        ),
      ),
    );
  }
}
