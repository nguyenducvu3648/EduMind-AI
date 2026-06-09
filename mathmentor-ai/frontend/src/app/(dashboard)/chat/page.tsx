"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  Send,
  Sparkles,
  BookOpen,
  Lightbulb,
  Zap,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { toast } from "sonner";
import { sendMessageStream } from "@/lib/chat";
import { ChatResponse } from "@/types";
import type { ChunkReference } from "@/types";
import ReactMarkdown from "react-markdown";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import remarkGfm from "remark-gfm";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: ChunkReference[];
  strategy?: string;
  bloom?: string;
  followUps?: string[];
}

function StrategyBadge({ strategy }: { strategy: string }) {
  const colors: Record<string, string> = {
    socratic: "bg-amber-100 text-amber-800 border-amber-200",
    step_by_step: "bg-blue-100 text-blue-800 border-blue-200",
    direct: "bg-green-100 text-green-800 border-green-200",
    hint_first: "bg-purple-100 text-purple-800 border-purple-200",
    worked_example: "bg-indigo-100 text-indigo-800 border-indigo-200",
    metacognitive: "bg-rose-100 text-rose-800 border-rose-200",
  };
  const labels: Record<string, string> = {
    socratic: "Socratic",
    step_by_step: "Từng bước",
    direct: "Giải thích",
    hint_first: "Gợi ý",
    worked_example: "Ví dụ mẫu",
    metacognitive: "Siêu nhận thức",
  };
  return (
    <Badge
      variant="outline"
      className={`${colors[strategy] || "bg-slate-100 text-slate-800"} text-xs`}
    >
      <Lightbulb className="w-3 h-3 mr-1" />
      {labels[strategy] || strategy}
    </Badge>
  );
}

function BloomBadge({ bloom }: { bloom: string }) {
  const colors: Record<string, string> = {
    remember: "bg-slate-100 text-slate-700",
    understand: "bg-blue-100 text-blue-700",
    apply: "bg-green-100 text-green-700",
    analyze: "bg-purple-100 text-purple-700",
    evaluate: "bg-amber-100 text-amber-700",
    create: "bg-rose-100 text-rose-700",
  };
  return (
    <Badge
      variant="outline"
      className={`${colors[bloom] || "bg-slate-100"} text-xs`}
    >
      <Zap className="w-3 h-3 mr-1" />
      Bloom: {bloom}
    </Badge>
  );
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Auto scroll to bottom when messages change
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages]);

  const handleSend = async () => {
    const text = input.trim();
    if (!text || sending) return;
    setInput("");
    setSending(true);

    const userMsg: Message = {
      id: `user-${Date.now()}`,
      role: "user",
      content: text,
    };
    setMessages((prev) => [...prev, userMsg]);

    // Tạo message assistant rỗng trước, stream sẽ fill dần
    const assistantId = `assistant-${Date.now()}`;
    setMessages((prev) => [
      ...prev,
      {
        id: assistantId,
        role: "assistant",
        content: "",
        sources: [],
      },
    ]);

    try {
      let fullContent = "";

      await sendMessageStream(
        text,
        sessionId,
        (token) => {
          fullContent += token;
          setMessages((prev) =>
            prev.map((m) => (m.id === assistantId ? { ...m, content: fullContent } : m))
          );
        },
        (data) => {
          setSessionId(data.session_id as string);
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId ? { ...m, sources: [], strategy: data.teaching_strategy_used as string } : m
            )
          );
        }
      );
    } catch {
      toast.error("Không thể gửi câu hỏi. Vui lòng thử lại.");
    } finally {
      setSending(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const SourceCard = ({ source }: { source: ChunkReference }) => (
    <div className="text-xs bg-muted/50 rounded p-2 border border-border/50">
      <p className="font-medium truncate">{source.article_title}</p>
      {source.section_header && (
        <p className="text-muted-foreground truncate">{source.section_header}</p>
      )}
    </div>
  );

  return (
    <div className="flex flex-col h-full">
      {/* Empty State */}
      {messages.length === 0 ? (
        <div className="flex-1 flex flex-col items-center justify-center px-4">
          <div className="w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center mb-4">
            <Sparkles className="w-8 h-8 text-primary" />
          </div>
          <h2 className="text-xl font-semibold mb-2">
            Bạn cần giúp đỡ gì hôm nay?
          </h2>
          <p className="text-muted-foreground text-sm text-center max-w-md">
            MathMentor AI sẽ phân tích trình độ của bạn và đưa ra phương pháp
            giảng dạy phù hợp nhất — từ gợi ý từng bước đến câu hỏi Socratic.
          </p>
          <div className="grid grid-cols-2 gap-2 mt-6 w-full max-w-md">
            {[
              "Giải thích phương trình bậc hai",
              "Đạo hàm là gì?",
              "Cho em bài tập tích phân",
              "Em yếu hình học vector",
            ].map((q) => (
              <Button
                key={q}
                variant="outline"
                className="text-xs h-auto py-2 justify-start text-left whitespace-normal"
                onClick={() => {
                  setInput(q);
                  inputRef.current?.focus();
                }}
              >
                <BookOpen className="w-3 h-3 mr-1.5 shrink-0 text-muted-foreground" />
                {q}
              </Button>
            ))}
          </div>
        </div>
      ) : (
        <>
          {/* Messages */}
          <div className="flex-1 overflow-y-auto px-4 py-4">
            <div className="max-w-3xl mx-auto space-y-4">
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className="chat-message flex gap-3"
                >
                  {msg.role === "assistant" && (
                    <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center shrink-0 mt-1">
                      <Sparkles className="w-4 h-4 text-primary-foreground" />
                    </div>
                  )}
                  <div className={`flex-1 min-w-0 ${msg.role === "user" ? "pl-11" : ""}`}>
                    {msg.role === "user" ? (
                      <div className="bg-muted rounded-2xl rounded-tl-sm px-4 py-3 inline-block max-w-[85%]">
                        <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                      </div>
                    ) : (
                      <div className="space-y-2">
                        {/* Strategy & Bloom badges */}
                        {(msg.strategy || msg.bloom) && (
                          <div className="flex items-center gap-2 flex-wrap">
                            {msg.strategy && (
                              <StrategyBadge strategy={msg.strategy} />
                            )}
                            {msg.bloom && (
                              <BloomBadge bloom={msg.bloom} />
                            )}
                          </div>
                        )}

                        {/* Response content */}
                        <div className="prose prose-sm max-w-none dark:prose-invert">
                          <ReactMarkdown
                            remarkPlugins={[remarkMath, remarkGfm]}
                            rehypePlugins={[rehypeKatex]}
                          >
                            {msg.content}
                          </ReactMarkdown>
                        </div>

                        {/* Sources */}
                        {msg.sources && msg.sources.length > 0 && (
                          <Details summary="Nguồn tham khảo">
                            <div className="grid grid-cols-2 gap-2 pt-2 max-h-40 overflow-y-auto">
                              {msg.sources.map((src, i) => (
                                <SourceCard key={i} source={src} />
                              ))}
                            </div>
                          </Details>
                        )}

                        {/* Follow-up suggestions */}
                        {msg.followUps && msg.followUps.length > 0 && (
                          <div className="pt-1">
                            <p className="text-xs text-muted-foreground mb-1.5">
                              Gợi ý:
                            </p>
                            <div className="flex flex-wrap gap-1.5">
                              {msg.followUps.map((fu, i) => (
                                <Button
                                  key={i}
                                  variant="outline"
                                  size="sm"
                                  className="text-xs h-auto py-1 px-2"
                                  onClick={() => {
                                    setInput(fu);
                                    inputRef.current?.focus();
                                  }}
                                >
                                  {fu}
                                </Button>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              ))}

              {sending && (
                <div className="chat-message flex gap-3">
                  <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center shrink-0">
                    <Sparkles className="w-4 h-4 text-primary-foreground" />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
                      <span className="w-2 h-2 rounded-full bg-primary animate-bounce" />
                      <span
                        className="w-2 h-2 rounded-full bg-primary animate-bounce"
                        style={{ animationDelay: "0.1s" }}
                      />
                      <span
                        className="w-2 h-2 rounded-full bg-primary animate-bounce"
                        style={{ animationDelay: "0.2s" }}
                      />
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          </div>
        </>
      )}

      {/* Input */}
      <div className="border-t border-border bg-background px-4 py-3">
        <div className="max-w-3xl mx-auto flex gap-2 items-end">
          <Textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Nhập câu hỏi của bạn... (Enter để gửi, Shift+Enter để xuống dòng)"
            className="min-h-[48px] max-h-[160px] resize-none"
            rows={1}
            disabled={sending}
          />
          <Button
            onClick={handleSend}
            disabled={!input.trim() || sending}
            size="icon"
            className="h-[48px] w-[48px] shrink-0"
          >
            <Send className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}

function Details({
  summary,
  children,
}: {
  summary: string;
  children: React.ReactNode;
}) {
  const [open, setOpen] = useState(false);
  return (
    <div className="border border-border/50 rounded-lg overflow-hidden">
      <button
        className="flex items-center gap-2 w-full px-3 py-2 text-xs font-medium text-muted-foreground hover:bg-muted/50 transition-colors"
        onClick={() => setOpen(!open)}
      >
        <BookOpen className="w-3.5 h-3.5" />
        {summary}
        {open ? (
          <ChevronUp className="w-3 h-3 ml-auto" />
        ) : (
          <ChevronDown className="w-3 h-3 ml-auto" />
        )}
      </button>
      {open && <div className="px-3 pb-2">{children}</div>}
    </div>
  );
}
