"use client";

import { useState, useEffect, useRef } from "react";
import {
  AlertCircle,
  Bot,
  CheckCircle2,
  ChevronDown,
  Globe,
  Maximize2,
  Minimize2,
  RefreshCw,
  Send,
  Sparkles,
  User,
  X,
  BookOpen,
  HelpCircle,
  MessageSquare,
} from "lucide-react";
import { advisoryApi, farmsApi } from "@/lib/api/client";
import type {
  AgriculturalExplanationResponse,
  CitationMetadata,
  FollowUpQuestion,
} from "@/lib/api/types";
import { useFarm } from "@/lib/farm-context";
import { cn } from "@/lib/utils";

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
  generationSource?: string;
  citations?: CitationMetadata[];
  followUpQuestions?: FollowUpQuestion[];
  isError?: boolean;
}

const QUICK_PROMPTS = [
  "Can I grow Sugarcane on my farm in Indapur?",
  "How much irrigation does Chickpea need in Rabi season?",
  "What fertilizer doses are recommended for Soybean by MPKV?",
  "How do I manage Fusarium wilt in tomato?",
];

export function CropNetChatbot() {
  const { selectedFarm, selectedFarmId } = useFarm();
  const [isOpen, setIsOpen] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const [language, setLanguage] = useState<"en" | "mr">("en");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [decisionId, setDecisionId] = useState<string | null>(null);
  const [hasUnread, setHasUnread] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Initialize with welcome message
  useEffect(() => {
    if (messages.length === 0) {
      setMessages([
        {
          id: "welcome",
          role: "assistant",
          content:
            language === "mr"
              ? "नमस्कार! मी क्रॉपनेट कृषी सहाय्यक (CropNet AI Agronomist) आहे. मी महात्मा फुले कृषी विद्यापीठ (MPKV) आणि ICAR च्या प्रमाणित शिफारशींवर आधारित सल्ला देतो. तुमच्या पिकाबद्दल किंवा जमिनीबद्दल विचारा!"
              : "Hello! I am CropNet AI Agronomist. I provide grounded agronomic advice backed by MPKV Rahuri research and ICAR guidelines. How can I assist your farm today?",
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
          generationSource: "deterministic_fallback",
        },
      ]);
    }
  }, [language, messages.length]);

  useEffect(() => {
    if (isOpen) {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
      inputRef.current?.focus();
      setHasUnread(false);
    }
  }, [isOpen, messages]);

  const handleSendMessage = async (textToSend?: string) => {
    const text = (textToSend || inputValue).trim();
    if (!text || isLoading) return;

    const userMessage: ChatMessage = {
      id: `usr-${Date.now()}`,
      role: "user",
      content: text,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue("");
    setIsLoading(true);

    try {
      let activeDecisionId = decisionId;

      // 1. If we don't have an active decision evaluated yet, evaluate the farm
      if (!activeDecisionId) {
        const taluka =
          selectedFarm?.taluka?.toLowerCase() ||
          (selectedFarm?.district ? selectedFarm.district.toLowerCase() : "indapur");

        // Detect candidate crops from user query
        const queryLower = text.toLowerCase();
        let crops = ["sugarcane", "soybean", "tomato", "chickpea"];
        if (queryLower.includes("sugarcane") || queryLower.includes("ऊस")) crops = ["sugarcane"];
        else if (queryLower.includes("soybean") || queryLower.includes("सोयाबीन")) crops = ["soybean"];
        else if (queryLower.includes("tomato") || queryLower.includes("टोमॅटो")) crops = ["tomato"];
        else if (queryLower.includes("chickpea") || queryLower.includes("हरभरा") || queryLower.includes("चना")) crops = ["chickpea"];
        else if (queryLower.includes("wheat") || queryLower.includes("गहू")) crops = ["wheat"];
        else if (queryLower.includes("cotton") || queryLower.includes("कापूस")) crops = ["cotton"];

        try {
          const evalRes = await advisoryApi.evaluateFarm({
            farm_id: selectedFarmId || undefined,
            taluka,
            season: "kharif",
            candidate_crops: crops,
            language,
          });
          activeDecisionId = evalRes.decision_id;
          setDecisionId(evalRes.decision_id);
        } catch (evalErr) {
          console.warn("Farm evaluation step failed, continuing fallback:", evalErr);
        }
      }

      // 2. Send conversational query
      const history = messages
        .filter((m) => !m.isError)
        .slice(-4)
        .map((m) => ({
          role: m.role,
          content: m.content,
        }));

      if (!activeDecisionId) {
        activeDecisionId = "fallback-consultation";
      }

      const res: AgriculturalExplanationResponse = await advisoryApi.conversation({
        decision_id: activeDecisionId,
        message: text,
        language,
        history,
      });

      const citations = res.authoritative_citations || res.citations || [];

      const assistantMessage: ChatMessage = {
        id: `asst-${Date.now()}`,
        role: "assistant",
        content: res.explanation_text,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        generationSource: res.generation_source,
        citations,
        followUpQuestions: res.follow_up_questions,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err: any) {
      console.error("Conversation error:", err);
      const errorMessage: ChatMessage = {
        id: `err-${Date.now()}`,
        role: "assistant",
        content:
          language === "mr"
            ? "माफ करा, तांत्रिक समस्येमुळे विनंती पूर्ण होऊ शकली नाही. कृपया पुन्हा प्रयत्न करा."
            : `I apologize, but could not complete the consultation: ${err.message || "Network issue"}. Please try again.`,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        isError: true,
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      {/* Floating Action Button */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="fixed right-4 bottom-20 z-50 flex items-center gap-2.5 rounded-full border-2 border-white bg-[#1b5e20] py-3 pr-5 pl-3.5 text-white shadow-xl transition-all hover:scale-105 hover:bg-[#2e7d32] sm:right-6 sm:bottom-6"
          aria-label="Open CropNet AI Agronomist Chatbot"
        >
          <div className="relative flex size-8 items-center justify-center rounded-full bg-white text-[#1b5e20]">
            <Bot size={20} />
            <span className="absolute -top-0.5 -right-0.5 size-2.5 rounded-full border-2 border-[#1b5e20] bg-[#4caf50]" />
          </div>
          <div className="text-left">
            <p className="text-xs font-black leading-none">CropNet AI</p>
            <p className="text-[10px] text-white/80">Agronomist</p>
          </div>
          {hasUnread && (
            <span className="absolute -top-1 -right-1 size-3 rounded-full bg-red-500" />
          )}
        </button>
      )}

      {/* Chat Window */}
      {isOpen && (
        <div
          className={cn(
            "fixed z-50 flex flex-col border border-[#c8e6c9] bg-white shadow-2xl transition-all duration-200",
            isExpanded
              ? "inset-4 rounded-3xl sm:inset-10"
              : "right-4 bottom-20 h-[560px] max-h-[80vh] w-[92vw] max-w-[420px] rounded-3xl sm:right-6 sm:bottom-6",
          )}
        >
          {/* Header */}
          <div className="flex items-center justify-between rounded-t-3xl border-b border-[#e8f5e9] bg-[#1b5e20] px-4 py-3 text-white">
            <div className="flex items-center gap-2.5">
              <div className="relative flex size-9 items-center justify-center rounded-xl bg-white text-[#1b5e20]">
                <Bot size={20} />
                <span className="absolute -top-0.5 -right-0.5 size-2 rounded-full border-2 border-[#1b5e20] bg-[#4caf50]" />
              </div>
              <div>
                <h3 className="text-sm font-black leading-tight">CropNet AI Agronomist</h3>
                <p className="text-[10px] text-white/80">
                  {selectedFarm ? `Grounded for ${selectedFarm.name}` : "MPKV & ICAR Verified"}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-1">
              {/* Language toggle */}
              <button
                onClick={() => setLanguage((l) => (l === "en" ? "mr" : "en"))}
                className="flex items-center gap-1 rounded-lg bg-white/15 px-2 py-1 text-[11px] font-bold text-white hover:bg-white/25"
                title="Toggle English / Marathi"
              >
                <Globe size={13} />
                <span>{language === "en" ? "EN" : "मराठी"}</span>
              </button>

              {/* Expand / Minimize toggle */}
              <button
                onClick={() => setIsExpanded((e) => !e)}
                className="hidden rounded-lg p-1.5 text-white/80 hover:bg-white/15 hover:text-white sm:block"
                aria-label={isExpanded ? "Collapse" : "Expand"}
              >
                {isExpanded ? <Minimize2 size={16} /> : <Maximize2 size={16} />}
              </button>

              {/* Close */}
              <button
                onClick={() => setIsOpen(false)}
                className="rounded-lg p-1.5 text-white/80 hover:bg-white/15 hover:text-white"
                aria-label="Close"
              >
                <X size={18} />
              </button>
            </div>
          </div>

          {/* Active Farm Context Ribbon */}
          {selectedFarm && (
            <div className="flex items-center justify-between border-b border-[#e8f5e9] bg-[#f1f8e9] px-4 py-1.5 text-[11px] text-[#2e7d32]">
              <span className="font-semibold truncate">
                📍 {selectedFarm.name} ({selectedFarm.taluka || "Indapur"}, {selectedFarm.district || "Pune"})
              </span>
              <span className="shrink-0 text-[10px] text-[#6b7280]">
                {selectedFarm.calculated_area_acres ? `${selectedFarm.calculated_area_acres.toFixed(1)} ac` : "Active Farm"}
              </span>
            </div>
          )}

          {/* Messages Container */}
          <div className="flex-1 space-y-3.5 overflow-y-auto p-4 text-xs scrollbar-thin">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={cn(
                  "flex flex-col",
                  msg.role === "user" ? "items-end" : "items-start",
                )}
              >
                <div
                  className={cn(
                    "max-w-[85%] rounded-2xl px-3.5 py-2.5 leading-relaxed shadow-sm",
                    msg.role === "user"
                      ? "rounded-br-none bg-[#1b5e20] text-white"
                      : msg.isError
                        ? "rounded-bl-none border border-red-200 bg-red-50 text-red-900"
                        : "rounded-bl-none border border-[#e8f5e9] bg-[#f9fafb] text-[#1f2937]",
                  )}
                >
                  <p className="whitespace-pre-wrap">{msg.content}</p>

                  {/* Provenance Badge */}
                  {msg.role === "assistant" && !msg.isError && (
                    <div className="mt-2 flex flex-wrap items-center gap-1.5 border-t border-[#e5e7eb] pt-2 text-[10px] text-[#4b5563]">
                      <span className="inline-flex items-center gap-1 rounded bg-[#e8f5e9] px-1.5 py-0.5 font-bold text-[#1b5e20]">
                        <CheckCircle2 size={11} />
                        {msg.generationSource === "llm_qwen3_8b"
                          ? "Qwen3:8B Verified"
                          : "Deterministic Agronomic Rule"}
                      </span>
                    </div>
                  )}

                  {/* Authoritative Citations */}
                  {msg.citations && msg.citations.length > 0 && (
                    <div className="mt-2 rounded-lg bg-white p-2 border border-[#e5e7eb]">
                      <p className="font-bold text-[10px] text-[#374151] flex items-center gap-1">
                        <BookOpen size={11} className="text-[#2e7d32]" />
                        Authoritative Citations:
                      </p>
                      <ul className="mt-1 space-y-1 text-[10px] text-[#6b7280]">
                        {msg.citations.slice(0, 2).map((c, i) => (
                          <li key={i} className="truncate">
                            • {c.organization} ({c.publication_year}): {c.publication_title}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Follow-up question chips */}
                  {msg.followUpQuestions && msg.followUpQuestions.length > 0 && (
                    <div className="mt-2.5 space-y-1">
                      <p className="text-[10px] font-bold text-[#4b5563]">
                        Targeted Clarification:
                      </p>
                      {msg.followUpQuestions.slice(0, 2).map((q) => {
                        const questionLabel =
                          (language === "mr" && q.question_text_mr)
                            ? q.question_text_mr
                            : q.question_text_en;
                        return (
                          <button
                            key={q.question_id}
                            onClick={() => handleSendMessage(questionLabel)}
                            className="block w-full text-left rounded-lg bg-[#e8f5e9] p-1.5 text-[10px] font-medium text-[#1b5e20] hover:bg-[#c8e6c9] transition-colors"
                          >
                            ❓ {questionLabel}
                          </button>
                        );
                      })}
                    </div>
                  )}
                </div>

                <span className="mt-1 px-1 text-[9px] text-[#9ca3af]">{msg.timestamp}</span>
              </div>
            ))}

            {/* Loading Indicator */}
            {isLoading && (
              <div className="flex items-center gap-2 text-xs text-[#6b7280]">
                <div className="flex size-7 items-center justify-center rounded-xl bg-[#e8f5e9] text-[#1b5e20]">
                  <Bot size={15} />
                </div>
                <div className="flex items-center gap-1.5 rounded-2xl bg-[#f3f4f6] px-3.5 py-2">
                  <span className="size-1.5 animate-bounce rounded-full bg-[#2e7d32]" />
                  <span className="size-1.5 animate-bounce rounded-full bg-[#2e7d32] [animation-delay:0.2s]" />
                  <span className="size-1.5 animate-bounce rounded-full bg-[#2e7d32] [animation-delay:0.4s]" />
                  <span className="ml-1 text-[11px] font-medium text-[#4b5563]">
                    Checking MPKV agronomic rules...
                  </span>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Quick Prompts (if chat has 1 or fewer user messages) */}
          {messages.filter((m) => m.role === "user").length <= 1 && (
            <div className="border-t border-[#f3f4f6] bg-[#fafdfa] px-3 py-2">
              <p className="mb-1.5 text-[10px] font-bold uppercase tracking-wider text-[#6b7280]">
                Suggested questions:
              </p>
              <div className="flex gap-1.5 overflow-x-auto pb-1 scrollbar-none">
                {QUICK_PROMPTS.map((prompt, i) => (
                  <button
                    key={i}
                    onClick={() => handleSendMessage(prompt)}
                    disabled={isLoading}
                    className="shrink-0 rounded-full border border-[#c8e6c9] bg-white px-2.5 py-1 text-[10px] font-medium text-[#1b5e20] hover:bg-[#e8f5e9] disabled:opacity-50"
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Input Bar */}
          <div className="rounded-b-3xl border-t border-[#e8f5e9] bg-white p-3">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSendMessage();
              }}
              className="flex items-center gap-2"
            >
              <input
                ref={inputRef}
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                placeholder={
                  language === "mr"
                    ? "पिक, खत, पाणी किंवा रोगाबद्दल विचारा..."
                    : "Ask about crops, soil, water, fertilizer..."
                }
                disabled={isLoading}
                className="flex-1 rounded-xl border border-[#d1d5db] bg-[#f9fafb] px-3.5 py-2.5 text-xs text-[#111827] placeholder:text-[#9ca3af] focus:border-[#1b5e20] focus:bg-white focus:outline-none focus:ring-1 focus:ring-[#1b5e20]"
              />
              <button
                type="submit"
                disabled={!inputValue.trim() || isLoading}
                className="flex size-9 shrink-0 items-center justify-center rounded-xl bg-[#1b5e20] text-white shadow-sm transition-colors hover:bg-[#2e7d32] disabled:opacity-40"
                aria-label="Send query"
              >
                <Send size={15} />
              </button>
            </form>
            <p className="mt-1.5 text-center text-[9px] text-[#9ca3af]">
              Grounded in MPKV Rahuri & ICAR agricultural research.
            </p>
          </div>
        </div>
      )}
    </>
  );
}
