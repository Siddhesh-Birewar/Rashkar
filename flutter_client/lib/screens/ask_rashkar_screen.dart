import 'package:flutter/material.dart';
import '../models/farm_models.dart';
import '../services/api_service.dart';
import '../services/app_state.dart';

class AskRashkarScreen extends StatefulWidget {
  const AskRashkarScreen({Key? key}) : super(key: key);

  @override
  State<AskRashkarScreen> createState() => _AskRashkarScreenState();
}

class _AskRashkarScreenState extends State<AskRashkarScreen> {
  final TextEditingController _textController = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  final List<AssistantChatMessage> _messages = [];
  bool _isSending = false;
  String? _sessionId;
  String _contextChipLabel = 'Using your farm information...';

  final List<String> _suggestedPrompts = [
    'How is my crop doing today?',
    'Is it safe to work outside right now?',
    'What should I do on my farm this week?',
    'How can I earn extra income?',
  ];

  @override
  void initState() {
    super.initState();
    AppState.instance.addListener(_onStateChange);
    _initWelcome();
    _loadContextChip();
  }

  Future<void> _loadContextChip() async {
    final farmId = AppState.instance.activeFarmId ?? 'farm_demo_pune_01';
    try {
      final chip = await ApiService.getAssistantContextChip(farmId);
      if (mounted) setState(() => _contextChipLabel = chip);
    } catch (_) {}
  }

  @override
  void dispose() {
    AppState.instance.removeListener(_onStateChange);
    _textController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  void _onStateChange() {
    if (mounted) {
      setState(() {
        _initWelcome();
      });
    }
  }

  void _initWelcome() {
    final appState = AppState.instance;
    final farm = appState.activeFarm;
    final loc = farm != null ? '${appState.activeTaluka}, ${appState.activeDistrict}' : 'Maharashtra';
    final crop = farm != null ? appState.activeCropName : 'crops';

    _messages.clear();
    _messages.add(
      AssistantChatMessage(
        sender: 'assistant',
        text: 'Namaste! I am Rashkar, your farm assistant. I have checked the live weather and crop status for your $crop in $loc.\n\nType your question below, or tap one of the suggested topics to begin.',
        timestamp: DateTime.now(),
      ),
    );
  }

  Future<void> _sendMessage(String text) async {
    final clean = text.trim();
    if (clean.isEmpty) return;

    _textController.clear();
    setState(() {
      _messages.add(
        AssistantChatMessage(
          sender: 'user',
          text: clean,
          timestamp: DateTime.now(),
        ),
      );
      _isSending = true;
    });

    _scrollToBottom();

    final appState = AppState.instance;
    final farmerId = appState.activeFarmerId ?? 'farmer_demo_01';
    final farmId = appState.activeFarmId ?? 'farm_demo_pune_01';

    final response = await ApiService.sendAssistantMessage(
      farmerId: farmerId,
      farmId: farmId,
      message: clean,
      sessionId: _sessionId,
    );

    if (mounted) {
      setState(() {
        _sessionId = response['session_id'];
        _messages.add(
          AssistantChatMessage(
            sender: 'assistant',
            text: response['reply'] ?? 'Unable to process inquiry at this moment.',
            providerUsed: response['provider_used'],
            citations: List<Map<String, String>>.from(
              (response['citations'] as List? ?? []).map((c) => Map<String, String>.from(c)),
            ),
            timestamp: DateTime.now(),
          ),
        );
        _isSending = false;
      });
      _scrollToBottom();
    }
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
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
            const Text('Ask Rashkar Assistant', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
            Text(
              '${appState.activeFarm?.farmName ?? "Farm"} · ${appState.activeTaluka}, ${appState.activeDistrict}',
              style: const TextStyle(fontSize: 12, color: Colors.white70),
            ),
          ],
        ),
        backgroundColor: const Color(0xFF1B5E20),
        foregroundColor: Colors.white,
      ),
      body: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 840),
          child: Column(
            children: [
              // Grounded farm context chip banner
              Container(
                margin: const EdgeInsets.fromLTRB(12, 10, 12, 4),
                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                decoration: BoxDecoration(
                  color: const Color(0xFFE8F5E9),
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(color: const Color(0xFFA5D6A7)),
                ),
                child: Row(
                  children: [
                    const Icon(Icons.verified, size: 16, color: Color(0xFF2E7D32)),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        _contextChipLabel,
                        style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: Color(0xFF1B5E20)),
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                    const SizedBox(width: 6),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                      decoration: BoxDecoration(
                        color: const Color(0xFF2E7D32),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: const Text('Ollama AI', style: TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.bold)),
                    ),
                  ],
                ),
              ),

              // Suggested prompts chips
          Container(
            height: 52,
            padding: const EdgeInsets.symmetric(vertical: 8),
            child: ListView.builder(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: 12),
              itemCount: _suggestedPrompts.length,
              itemBuilder: (context, idx) {
                return Padding(
                  padding: const EdgeInsets.only(right: 8),
                  child: ActionChip(
                    avatar: const Icon(Icons.help_outline, size: 16, color: Color(0xFF1B5E20)),
                    label: Text(_suggestedPrompts[idx], style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w500)),
                    backgroundColor: Colors.white,
                    side: const BorderSide(color: Color(0xFF2E7D32), width: 0.8),
                    onPressed: () => _sendMessage(_suggestedPrompts[idx]),
                  ),
                );
              },
            ),
          ),
          const Divider(height: 1),

          // Message history list
          Expanded(
            child: ListView.builder(
              controller: _scrollController,
              padding: const EdgeInsets.all(16),
              itemCount: _messages.length,
              itemBuilder: (context, idx) {
                final m = _messages[idx];
                final isUser = m.sender == 'user';
                return _buildMessageBubble(m, isUser);
              },
            ),
          ),

          if (_isSending)
            const Padding(
              padding: EdgeInsets.symmetric(vertical: 8.0),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2, color: Color(0xFF1B5E20))),
                  SizedBox(width: 10),
                  Text('Checking farm data & preparing answer...', style: TextStyle(fontSize: 12, color: Colors.black54)),
                ],
              ),
            ),

          // Text input box with Voice Placeholder
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            decoration: BoxDecoration(
              color: Colors.white,
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.05),
                  blurRadius: 4,
                  offset: const Offset(0, -2),
                ),
              ],
            ),
            child: SafeArea(
              child: Row(
                children: [
                  IconButton(
                    icon: const Icon(Icons.mic_none, color: Color(0xFF1B5E20)),
                    tooltip: 'Voice input (Coming soon)',
                    onPressed: () {
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(
                          content: Text('Voice input will be enabled in the upcoming Marathi/Hindi speech release.'),
                          duration: Duration(seconds: 2),
                        ),
                      );
                    },
                  ),
                  Expanded(
                    child: TextField(
                      controller: _textController,
                      decoration: InputDecoration(
                        hintText: 'Ask a question about your farm...',
                        hintStyle: const TextStyle(fontSize: 14),
                        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                        border: OutlineInputBorder(borderRadius: BorderRadius.circular(24), borderSide: const BorderSide(color: Colors.black26)),
                        focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(24), borderSide: const BorderSide(color: Color(0xFF1B5E20), width: 1.5)),
                      ),
                      onSubmitted: _sendMessage,
                    ),
                  ),
                  const SizedBox(width: 8),
                  CircleAvatar(
                    backgroundColor: const Color(0xFF1B5E20),
                    child: IconButton(
                      icon: const Icon(Icons.send, color: Colors.white, size: 20),
                      onPressed: () => _sendMessage(_textController.text),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    ),
  ),
);
}

  Widget _buildMessageBubble(AssistantChatMessage m, bool isUser) {
    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.only(bottom: 12),
        constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.8),
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: isUser ? const Color(0xFF1B5E20) : Colors.white,
          borderRadius: BorderRadius.circular(16).copyWith(
            bottomRight: isUser ? const Radius.circular(0) : const Radius.circular(16),
            bottomLeft: !isUser ? const Radius.circular(0) : const Radius.circular(16),
          ),
          border: isUser ? null : Border.all(color: Colors.grey.shade200),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.04),
              blurRadius: 6,
              offset: const Offset(0, 2),
            )
          ],
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (!isUser) ...[
              Row(
                mainAxisSize: MainAxisSize.min,
                children: const [
                  Icon(Icons.smart_toy_outlined, size: 16, color: Color(0xFF1B5E20)),
                  SizedBox(width: 6),
                  Text('Rashkar Farm Assistant', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 11, color: Color(0xFF1B5E20))),
                ],
              ),
              const SizedBox(height: 6),
            ],
            Text(
              m.text,
              style: TextStyle(
                fontSize: 14,
                color: isUser ? Colors.white : Colors.black87,
                height: 1.35,
              ),
            ),
            if (!isUser && m.providerUsed != null) ...[
              const SizedBox(height: 8),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                decoration: BoxDecoration(
                  color: const Color(0xFFE8F5E9),
                  borderRadius: BorderRadius.circular(6),
                ),
                child: Text(
                  'Powered by: ${m.providerUsed}',
                  style: const TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: Color(0xFF1B5E20)),
                ),
              ),
            ]
          ],
        ),
      ),
    );
  }
}
