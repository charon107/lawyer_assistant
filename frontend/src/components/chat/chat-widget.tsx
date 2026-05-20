"use client";

import { useState, useRef, useEffect } from "react";

interface ChatWidgetProps {
  reviewId: string;
  apiBase: string;
  enabled: boolean;
}

interface Message {
  role: "user" | "assistant";
  content: string;
}

export function ChatWidget({ reviewId, apiBase, enabled }: ChatWidgetProps) {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    { role: "assistant", content: "你好！我是 LexMind 法律助手。你可以基于审查结果向我提问，也可以咨询任何法律问题，例如：\n\n- \"第 3.4 条为什么标记为中风险？\"\n- \"这个条款的法律依据是什么？\"\n- \"帮我总结前三大风险\"" },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;
    const question = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: question }]);
    setLoading(true);

    try {
      const history = messages.slice(-6).map((m) => ({
        role: m.role,
        content: m.content,
      }));

      const res = await fetch(`${apiBase}/review/${reviewId}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question, history }),
      });

      const data = await res.json();
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: data.answer || "抱歉，无法获取回答。" },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "对话服务暂时不可用，请稍后重试。" },
      ]);
    } finally {
      setLoading(false);
    }
  };

  if (!enabled) return null;

  return (
    <>
      {/* Floating button */}
      <button
        onClick={() => setOpen(!open)}
        className="fixed bottom-6 right-6 w-14 h-14 bg-blue-600 text-white rounded-full shadow-lg
                   hover:bg-blue-500 transition-all flex items-center justify-center text-2xl z-50"
        title="审查助手"
      >
        {open ? "✕" : "💬"}
      </button>

      {/* Chat panel */}
      {open && (
        <div className="fixed bottom-24 right-6 w-96 h-[500px] bg-zinc-900 border border-zinc-700
                        rounded-xl shadow-2xl flex flex-col z-50">
          {/* Header */}
          <div className="p-3 border-b border-zinc-700 flex items-center justify-between">
            <span className="text-sm font-medium">LexMind</span>
            <span className="text-xs text-zinc-500">基于当前审查结果回答</span>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-3 space-y-3">
            {messages.map((msg, i) => (
              <div
                key={i}
                className={`text-sm ${
                  msg.role === "user"
                    ? "ml-8 bg-blue-600/20 border border-blue-500/30 rounded-lg p-2"
                    : "mr-8 bg-zinc-800 rounded-lg p-2"
                }`}
              >
                <p className="whitespace-pre-wrap text-zinc-300">{msg.content}</p>
              </div>
            ))}
            {loading && (
              <div className="text-xs text-zinc-500 animate-pulse mr-8 bg-zinc-800 rounded-lg p-2">
                思考中...
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="p-3 border-t border-zinc-700 flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSend()}
              placeholder="追问审查结果..."
              className="flex-1 bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-sm
                         text-white placeholder-zinc-500 focus:outline-none focus:border-blue-500"
              disabled={loading}
            />
            <button
              onClick={handleSend}
              disabled={loading || !input.trim()}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-500
                         disabled:opacity-50 disabled:cursor-not-allowed"
            >
              发送
            </button>
          </div>
        </div>
      )}
    </>
  );
}
