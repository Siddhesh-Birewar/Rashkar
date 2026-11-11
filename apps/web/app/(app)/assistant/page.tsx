"use client";

import { useState, useEffect, useRef } from "react";
import {
  AlertCircle,
  Bot,
  CheckCircle2,
  Globe,
  Send,
  Sparkles,
  BookOpen,
  Sprout,
  HelpCircle,
  ShieldCheck,
} from "lucide-react";
import { advisoryApi } from "@/lib/api/client";
import type {
  AgriculturalExplanationResponse,
  CitationMetadata,
  FollowUpQuestion,
} from "@/lib/api/types";
import { useFarm } from "@/lib/farm-context";
import { cn } from "@/lib/utils";
import { BackButton } from "@/components/back-button";

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
  "What government subsidies apply for drip irrigation under PMKSY?",
];

export default function AssistantPage() {
  const { selectedFarm, selectedFarmId } = useFarm();
  const [language, setLanguage] = useState<"en" | "mr">("en");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [decisionId, setDecisionId] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (messages.length === 0) {
      setMessages([
        {
          id: "welcome",
          role: "assistant",
          content:
            language === "mr"
              ? "नमस्कार! मी क्रॉपनेट कृषी सहाय्यक (CropNet AI Agronomist) आहे. मी महात्मा फुले कृषी विद्यापीठ (MPKV) आणि ICAR च्या प्रमाणित शिफारशींवर आधारित सल्ला देतो. तुमच्या पिकाबद्दल किंवा जमिनीबद्दल विचारा!"
              : "Hello! I am your CropNet AI Agronomist assistant. All recommendations are derived from Mahatma Phule Krishi Vidyapeeth (MPKV), Rahuri research recommendations and ICAR field agronomy guidelines. What would you like to evaluate today?",
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
          generationSource: "deterministic_fallback",
        },
      ]);
    }
  }, [language, messages.length]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

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

      if (!activeDecisionId) {
        const taluka =
          selectedFarm?.taluka?.toLowerCase() ||
          (selectedFarm?.district ? selectedFarm.district.toLowerCase() : "indapur");

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

      const history = messages
        .filter((m) => !m.isError)
        .slice(-6)
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
    <div className="mx-auto flex h-[calc(100vh-140px)] max-w-4xl flex-col space-y-4">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-[#dde7df] bg-white p-4 shadow-sm">
        <div className="flex items-center gap-3">
          <BackButton fallbackHref="/" />
          <div className="flex size-11 items-center justify-center rounded-2xl bg-[#1b5e20] text-white">
            <Bot size={24} />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-black text-[#111827]">CropNet AI Agronomist</h1>
              <span className="inline-flex items-center gap-1 rounded-full bg-[#e8f5e9] px-2 py-0.5 text-[10px] font-bold text-[#1b5e20]">
                <ShieldCheck size={11} />
                MPKV Grounded
              </span>
            </div>
            <p className="text-xs text-[#6b7280]">
              {selectedFarm
                ? `Target Farm: ${selectedFarm.name} (${selectedFarm.taluka || "Indapur"}, ${selectedFarm.district || "Pune"})`
                : "Select a farm or query directly for general Maharashtra agro-ecological advice"}
            </p>
          </div>
        </div>

        {/* Language selector */}
        <div className="flex items-center gap-2">
          <span className="text-xs font-bold text-[#6b7280]">Language:</span>
          <div className="flex rounded-xl border border-[#e5e7eb] bg-[#f9fafb] p-1">
            <button
              onClick={() => setLanguage("en")}
              className={cn(
                "rounded-lg px-2.5 py-1 text-xs font-bold transition-all",
                language === "en" ? "bg-white text-[#1b5e20] shadow-sm" : "text-[#6b7280]",
              )}
            >
              English
            </button>
            <button
              onClick={() => setLanguage("mr")}
              className={cn(
                "rounded-lg px-2.5 py-1 text-xs font-bold transition-all",
                language === "mr" ? "bg-white text-[#1b5e20] shadow-sm" : "text-[#6b7280]",
              )}
            >
              मराठी
            </button>
          </div>
        </div>
      </div>

      {/* Chat Messages */}
      <div className="flex-1 space-y-4 overflow-y-auto rounded-3xl border border-[#dde7df] bg-white p-5 shadow-sm scrollbar-thin">
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
                "max-w-[85%] rounded-2xl px-4 py-3 leading-relaxed shadow-sm sm:max-w-[75%]",
                msg.role === "user"
                  ? "rounded-br-none bg-[#1b5e20] text-white"
                  : msg.isError
                    ? "rounded-bl-none border border-red-200 bg-red-50 text-red-900"
                    : "rounded-bl-none border border-[#e8f5e9] bg-[#f9fafb] text-[#1f2937]",
              )}
            >
              <p className="whitespace-pre-wrap text-sm">{msg.content}</p>

              {/* Provenance Badge */}
              {msg.role === "assistant" && !msg.isError && (
                <div className="mt-3 flex flex-wrap items-center gap-2 border-t border-[#e5e7eb] pt-2.5 text-xs text-[#4b5563]">
                  <span className="inline-flex items-center gap-1 rounded-md bg-[#e8f5e9] px-2 py-0.5 text-[11px] font-bold text-[#1b5e20]">
                    <CheckCircle2 size={12} />
                    {msg.generationSource === "llm_qwen3_8b"
                      ? "LLM Verified (Qwen3:8B)"
                      : "Deterministic Agricultural Engine"}
                  </span>
                </div>
              )}

              {/* Citations */}
              {msg.citations && msg.citations.length > 0 && (
                <div className="mt-2.5 rounded-xl border border-[#e5e7eb] bg-white p-2.5">
                  <p className="flex items-center gap-1.5 text-xs font-bold text-[#374151]">
                    <BookOpen size={13} className="text-[#2e7d32]" />
                    Authoritative Citations:
                  </p>
                  <ul className="mt-1.5 space-y-1 text-xs text-[#6b7280]">
                    {msg.citations.map((c, i) => (
                      <li key={i}>
                        • <span className="font-semibold text-[#374151]">{c.organization}</span> ({c.publication_year}): {c.publication_title}
                        {c.section_or_pages && <span className="text-[#9ca3af]"> — {c.section_or_pages}</span>}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Follow-up question chips */}
              {msg.followUpQuestions && msg.followUpQuestions.length > 0 && (
                <div className="mt-3 space-y-1.5">
                  <p className="text-xs font-bold text-[#4b5563]">
                    Targeted Clarifications from Deterministic Engine:
                  </p>
                  {msg.followUpQuestions.map((q) => {
                    const questionLabel =
                      (language === "mr" && q.question_text_mr)
                        ? q.question_text_mr
                        : q.question_text_en;
                    return (
                      <button
                        key={q.question_id}
                        onClick={() => handleSendMessage(questionLabel)}
                        className="block w-full rounded-xl bg-[#e8f5e9] p-2 text-left text-xs font-medium text-[#1b5e20] transition-colors hover:bg-[#c8e6c9]"
                      >
                        ❓ {questionLabel}
                      </button>
                    );
                  })}
                </div>
              )}
            </div>

            <span className="mt-1 px-1 text-[10px] text-[#9ca3af]">{msg.timestamp}</span>
          </div>
        ))}

        {isLoading && (
          <div className="flex items-center gap-3 text-sm text-[#6b7280]">
            <div className="flex size-8 items-center justify-center rounded-xl bg-[#e8f5e9] text-[#1b5e20]">
              <Bot size={18} />
            </div>
            <div className="flex items-center gap-2 rounded-2xl bg-[#f3f4f6] px-4 py-2.5">
              <span className="size-2 animate-bounce rounded-full bg-[#2e7d32]" />
              <span className="size-2 animate-bounce rounded-full bg-[#2e7d32] [animation-delay:0.2s]" />
              <span className="size-2 animate-bounce rounded-full bg-[#2e7d32] [animation-delay:0.4s]" />
              <span className="ml-1 text-xs font-medium text-[#4b5563]">
                Evaluating agricultural rules & MPKV recommendations...
              </span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Suggested Questions */}
      {messages.filter((m) => m.role === "user").length <= 1 && (
        <div className="flex gap-2 overflow-x-auto pb-1 scrollbar-none">
          {QUICK_PROMPTS.map((prompt, i) => (
            <button
              key={i}
              onClick={() => handleSendMessage(prompt)}
              disabled={isLoading}
              className="shrink-0 rounded-full border border-[#c8e6c9] bg-white px-3 py-1.5 text-xs font-medium text-[#1b5e20] shadow-sm hover:bg-[#e8f5e9] disabled:opacity-50"
            >
              {prompt}
            </button>
          ))}
        </div>
      )}

      {/* Input Form */}
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
              ? "तुमच्या शेतासाठी पीक, खत, पाणी किंवा रोगाबद्दल विचारा..."
              : "Ask about crops, soil suitability, fertilizer doses, disease control..."
          }
          disabled={isLoading}
          className="flex-1 rounded-2xl border border-[#d1d5db] bg-white px-4 py-3 text-sm text-[#111827] shadow-sm placeholder:text-[#9ca3af] focus:border-[#1b5e20] focus:outline-none focus:ring-1 focus:ring-[#1b5e20]"
        />
        <button
          type="submit"
          disabled={!inputValue.trim() || isLoading}
          className="flex size-12 shrink-0 items-center justify-center rounded-2xl bg-[#1b5e20] text-white shadow-md transition-all hover:bg-[#2e7d32] disabled:opacity-40"
          aria-label="Send message"
        >
          <Send size={18} />
        </button>
      </form>
    </div>
  );
}
