"use client";

import { useEffect, useRef, useCallback, useState } from "react";
import { useChat } from "@/hooks";
import { MessageList } from "./message-list";
import { ChatInput } from "./chat-input";
import { ToolApprovalDialog } from "./tool-approval-dialog";
import { Bot, ChevronDown, Check, Settings, Cpu } from "lucide-react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, Accordion, AccordionItem, AccordionTrigger, AccordionContent } from "@/components/ui";
import Link from "next/link";
import { getProvider } from "@/lib/providers";
import type { PendingApproval, Decision } from "@/types";
import { useConversationStore, useChatStore, useAuthStore } from "@/stores";
import { useConversations } from "@/hooks";

export function ChatContainer() {
  return <AuthenticatedChatContainer />;
}

function AuthenticatedChatContainer() {
  const { currentConversationId, currentMessages } = useConversationStore();
  const { addMessage: addChatMessage } = useChatStore();
  const { fetchConversations } = useConversations();
  const prevConversationIdRef = useRef<string | null | undefined>(undefined);

  const handleConversationCreated = useCallback((conversationId: string) => {
    fetchConversations();
  }, [fetchConversations]);

  const {
    messages,
    isConnected,
    isProcessing,
    connect,
    disconnect,
    sendMessage,
    clearMessages,
    setModel,
    pendingApproval,
    sendResumeDecisions,
  } = useChat({
    conversationId: currentConversationId,
    onConversationCreated: handleConversationCreated,
  });

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  // Clear messages when conversation changes, but NOT when going from null to a new ID
  // (that happens when a new chat is saved - we want to keep the messages)
  useEffect(() => {
    const prevId = prevConversationIdRef.current;
    const currId = currentConversationId;

    // Skip initial mount
    if (prevId === undefined) {
      prevConversationIdRef.current = currId;
      return;
    }

    // Clear messages when:
    // 1. Going from a conversation to null (new chat)
    // 2. Switching between two different conversations
    // Do NOT clear when going from null to a conversation (new chat being saved)
    const shouldClear =
      currId === null || // Going to new chat
      (prevId !== null && prevId !== currId); // Switching between conversations

    if (shouldClear) {
      clearMessages();
    }

    prevConversationIdRef.current = currId;
  }, [currentConversationId, clearMessages]);

  // Load messages from conversation store when switching to a saved conversation
  useEffect(() => {
    if (currentMessages.length > 0) {
      clearMessages();
      currentMessages.forEach((msg) => {
        addChatMessage({
          id: msg.id,
          role: msg.role,
          content: msg.content,
          timestamp: new Date(msg.created_at),
          conversationId: msg.conversation_id,
          toolCalls: msg.tool_calls?.map((tc) => ({
            id: tc.tool_call_id,
            name: tc.tool_name,
            args: tc.args,
            result: tc.result,
            status: tc.status === "failed" ? "error" : tc.status,
          })),
          user_rating: msg.user_rating ?? undefined,
          rating_count: msg.rating_count ?? undefined,
          fileIds: "files" in msg && Array.isArray((msg as unknown as { files?: unknown[] }).files)
            ? ((msg as unknown as { files: { id: string }[] }).files).map((f) => f.id)
            : undefined,
        });
      });
    }
  }, [currentMessages, addChatMessage, clearMessages]);

  useEffect(() => {
    // Only connect WebSocket once we have an auth token (prevents 4001 errors)
    const token = useAuthStore.getState().accessToken;
    if (token) {
      connect();
      return () => disconnect();
    }
  }, [connect, disconnect]);

  // When auth token becomes available after initial load, connect
  const hasToken = useAuthStore((s) => !!s.accessToken);
  useEffect(() => {
    if (hasToken) connect();
  }, [hasToken, connect]);

  useEffect(() => {
    const container = scrollContainerRef.current;
    if (!container) return;
    // Only auto-scroll if user is already near the bottom
    const isNearBottom = container.scrollHeight - container.scrollTop - container.clientHeight < 150;
    if (isNearBottom) {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages]);

  return (
    <ChatUI
      messages={messages}
      isConnected={isConnected}
      isProcessing={isProcessing}
      sendMessage={sendMessage}
      onModelChange={setModel}
      messagesEndRef={messagesEndRef}
      scrollContainerRef={scrollContainerRef}
      pendingApproval={pendingApproval}
      onResumeDecisions={sendResumeDecisions}
    />
  );
}

interface ProviderModels {
  provider: string;
  providerName: string;
  models: string[];
}

function ModelSelector({ onChange }: { onChange: (model: string | null) => void }) {
  const [providers, setProviders] = useState<ProviderModels[]>([]);
  const [selected, setSelected] = useState<{value: string; label: string}>({ value: "", label: "选择模型" });
  const [configured, setConfigured] = useState(true);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    fetch("/api/v1/agent/models", { credentials: "include" })
      .then(r => r.ok ? r.json() : null)
      .then(data => {
        if (data) {
          setConfigured(data.configured !== false);
          if (data.configured !== false) {
            const grouped: ProviderModels[] = [];
            if (data.providers?.length) {
              for (const p of data.providers) {
                const meta = getProvider(p.provider);
                grouped.push({
                  provider: p.provider,
                  providerName: meta?.name || p.provider,
                  models: p.models || [],
                });
              }
            } else if (data.models?.length) {
              grouped.push({
                provider: data.provider,
                providerName: getProvider(data.provider)?.name || data.provider,
                models: data.models,
              });
            }
            setProviders(grouped);
          }
        }
      })
      .catch(() => {});
  }, []);

  if (!configured) {
    return (
      <Link
        href="/profile"
        className="text-muted-foreground hover:text-foreground inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs font-medium transition-colors"
      >
        <Settings className="h-3 w-3" />
        配置模型
      </Link>
    );
  }

  const handleSelect = (model: string) => {
    setSelected({ value: model, label: model });
    onChange(model || null);
    setOpen(false);
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <button className="text-muted-foreground hover:text-foreground inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs font-medium transition-colors">
          <Cpu className="h-3 w-3" />
          {selected.label}
          <ChevronDown className="h-3 w-3" />
        </button>
      </DialogTrigger>
      <DialogContent className="max-w-lg max-h-[70vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle>选择模型</DialogTitle>
        </DialogHeader>
        <div className="flex-1 overflow-y-auto -mx-6 px-6 pb-4">
          {providers.length === 0 ? (
            <p className="text-center text-sm text-muted-foreground py-8">暂无可用模型</p>
          ) : (
            <Accordion type="multiple" className="w-full">
              {providers.map((p) => (
                <AccordionItem key={p.provider} value={p.provider} className="border-b">
                  <AccordionTrigger className="py-3 text-sm">
                    <div className="flex items-center gap-2">
                      <Bot className="h-4 w-4 text-muted-foreground" />
                      <span className="font-medium">{p.providerName}</span>
                      <span className="text-muted-foreground text-xs">({p.models.length})</span>
                    </div>
                  </AccordionTrigger>
                  <AccordionContent>
                    <div className="space-y-0.5 pb-1">
                      {p.models.map((model) => (
                        <button
                          key={model}
                          onClick={() => handleSelect(model)}
                          className="flex w-full items-center justify-between rounded-lg px-3 py-2 text-sm hover:bg-accent transition-colors"
                        >
                          <span className="truncate">{model}</span>
                          {selected.value === model && <Check className="h-4 w-4 text-primary shrink-0" />}
                        </button>
                      ))}
                    </div>
                  </AccordionContent>
                </AccordionItem>
              ))}
            </Accordion>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}

interface ChatUIProps {
  messages: import("@/types").ChatMessage[];
  isConnected: boolean;
  isProcessing: boolean;
  sendMessage: (content: string, fileIds?: string[]) => void;
  onModelChange?: (model: string | null) => void;
  messagesEndRef: React.RefObject<HTMLDivElement | null>;
  scrollContainerRef: React.RefObject<HTMLDivElement | null>;
  pendingApproval?: PendingApproval | null;
  onResumeDecisions?: (decisions: Decision[]) => void;
}

function ChatUI({
  messages,
  isConnected,
  isProcessing,
  sendMessage,
  onModelChange,
  messagesEndRef,
  scrollContainerRef,
  pendingApproval,
  onResumeDecisions,
}: ChatUIProps) {
  return (
    <div className="flex flex-col h-full max-w-4xl mx-auto w-full">
      <div ref={scrollContainerRef} className="flex-1 overflow-y-auto px-2 py-4 sm:px-4 sm:py-6 scrollbar-thin">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-muted-foreground gap-4">
            <div className="w-14 h-14 sm:w-16 sm:h-16 rounded-full bg-secondary flex items-center justify-center">
              <Bot className="h-7 w-7 sm:h-8 sm:w-8" />
            </div>
            <div className="text-center px-4">
              <p className="text-base sm:text-lg font-medium text-foreground">AI 助手</p>
              <p className="text-sm">开始对话以获取帮助</p>
            </div>
          </div>
        ) : (
          <MessageList messages={messages} />
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Human-in-the-Loop: Tool Approval Dialog */}
      {pendingApproval && onResumeDecisions && (
        <div className="px-2 pb-2 sm:px-4 sm:pb-2">
          <ToolApprovalDialog
            actionRequests={pendingApproval.actionRequests}
            reviewConfigs={pendingApproval.reviewConfigs}
            onDecisions={onResumeDecisions}
            disabled={!isConnected}
          />
        </div>
      )}

      <div className="px-2 pb-2 sm:px-4 sm:pb-4">
        <div className="rounded-xl border bg-card shadow-sm">
          <div className="px-3 pt-3 sm:px-4 sm:pt-4">
            <ChatInput
              onSend={sendMessage}
              disabled={!isConnected || !!pendingApproval}
              isProcessing={isProcessing}
            />
          </div>
          <div className="flex items-center justify-between px-3 pb-2 sm:px-4 sm:pb-3">
            <div className="flex items-center gap-1">
              <span
                className={`inline-block h-1.5 w-1.5 rounded-full ${isConnected ? "bg-green-500" : "bg-red-500"}`}
              />
            </div>
            {onModelChange && (
              <ModelSelector onChange={onModelChange} />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
