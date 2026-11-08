import 'package:flutter/material.dart';
import '../models/farm_models.dart';
import '../services/api_service.dart';

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

  final List<String> _suggestedPrompts = [
    'Why is my crop at risk today?',
    'What should I check today?',
    'Explain my farm\'s weather conditions',
    'How do I protect against heat stress?'
  ];

  @override
  void initState() {
    super.initState();
    // Initial welcome message
    _messages.add(
      AssistantChatMessage(
        sender: 'assistant',
        text: 'Namaste! I am Rashkar Assistant. I have loaded your active farm and weather conditions in Baramati. How can I help you today?',
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

    final response = await ApiService.sendAssistantMessage(
      farmerId: 'farmer_demo_01',
      farmId: 'farm_demo_pune_01',
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
    return Scaffold(
      backgroundColor: const Color(0xFFF6F8F6),
      appBar: AppBar(
        title: const Text('Ask Rashkar Assistant', style: TextStyle(fontWeight: FontWeight.bold)),
        backgroundColor: const Color(0xFF1B5E20),
        foregroundColor: Colors.white,
      ),
      body: Column(
        children: [
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
                    label: Text(_suggestedPrompts[idx], style: const TextStyle(fontSize: 12)),
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
                  Text('Retrieving farm context & reasoning...', style: TextStyle(fontSize: 12, color: Colors.black54)),
                ],
              ),
            ),

          // Text input box
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            color: Colors.white,
            child: SafeArea(
              child: Row(
                children: [
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
                  )
                ],
              ),
            ),
          )
        ],
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
              Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                    decoration: BoxDecoration(
                      color: const Color(0xFFE8F5E9),
                      borderRadius: BorderRadius.circular(6),
                    ),
                    child: Text(
                      'Provider: ${m.providerUsed}',
                      style: const TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: Color(0xFF1B5E20)),
                    ),
                  ),
                ],
              ),
            ]
          ],
        ),
      ),
    );
  }
}
