"use client";

import { useEffect, useRef, useState } from "react";
import { useParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Send, Sparkles, Loader2, MessageSquare, BookOpen, Lightbulb, Zap, ChevronDown, ChevronUp } from "lucide-react";
import { toast } from "sonner";
import { sendMessageStream, getSessionMessages } from "@/lib/chat";
import type { MessageItem, ChunkReference } from "@/types";
import ReactMarkdown from "react-markdown";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import remarkGfm from "remark-gfm";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
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
    <Badge variant="outline" className={`${colors[strategy] || "bg-slate-100 text-slate-800"} text-xs`}>
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
    <Badge variant="outline" className={`${colors[bloom] || "bg-slate-100"} text-xs`}>
      <Zap className="w-3 h-3 mr-1" />
      Bloom: {bloom}
    </Badge>
  );
}

export default function SessionChatPage() {
  const params = useParams();
  const sessionId = params.id as string;
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [loading, setLoading] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages]);

  useEffect(() => {
    async function load() {
      try {
        const detail = await getSessionMessages(sessionId);
        const mapped: Message[] = detail.messages.flatMap((m: MessageItem) => [
          { id: `user-${m.id}`, role: "user", content: m.query },
          { id: m.id, role: "assistant", content: m.response },
        ]);
        setMessages(mapped);
      } catch {
        toast.error("Không thể tải lịch sử hội thoại");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [sessionId]);

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

    const assistantId = `assistant-${Date.now()}`;
    setMessages((prev) => [
      ...prev,
      { id: assistantId, role: "assistant", content: "", followUps: [] },
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
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId
                ? {
                    ...m,
                    strategy: data.teaching_strategy_used as string,
                    bloom: data.bloom_level as string,
                    followUps: (data.follow_up_suggestions as string[]) || [],
                  }
                : m
            )
          );
        }
      );
    } catch {
      toast.error("Không thể gửi câu hỏi");
    } finally {
      setSending(false);
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

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (messages.length === 0) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center gap-3">
        <MessageSquare className="w-10 h-10 text-muted-foreground" />
        <p className="text-muted-foreground text-sm">
          Hội thoại này chưa có tin nhắn
        </p>
        <Button variant="outline" size="sm" onClick={() => window.location.href = "/chat"}>
          Bắt đầu trò chuyện
        </Button>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto px-4 py-4">
        <div className="max-w-3xl mx-auto space-y-4">
          {messages.map((msg) => (
            <div key={msg.id} className="chat-message flex gap-3">
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
                    {(msg.strategy || msg.bloom) && (
                      <div className="flex items-center gap-2 flex-wrap">
                        {msg.strategy && <StrategyBadge strategy={msg.strategy} />}
                        {msg.bloom && <BloomBadge bloom={msg.bloom} />}
                      </div>
                    )}
                    <div className="prose prose-sm max-w-none dark:prose-invert">
                      <ReactMarkdown
                        remarkPlugins={[remarkMath, remarkGfm]}
                        rehypePlugins={[rehypeKatex]}
                      >
                        {msg.content}
                      </ReactMarkdown>
                    </div>
                    {msg.followUps && msg.followUps.length > 0 && (
                      <div className="pt-1">
                        <p className="text-xs text-muted-foreground mb-1.5">Gợi ý:</p>
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
            <div className="flex gap-3">
              <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center">
                <Sparkles className="w-4 h-4 text-primary-foreground" />
              </div>
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
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      <div className="border-t border-border bg-background px-4 py-3">
        <div className="max-w-3xl mx-auto flex gap-2 items-end">
          <Textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Tiếp tục hỏi..."
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
