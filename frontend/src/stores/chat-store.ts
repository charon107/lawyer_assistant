"use client";

import { create } from "zustand";
import type { ChatMessage, ToolCall } from "@/types";

interface ActiveToolStatus {
  label: string;
  toolName: string;
}

interface ChatState {
  messages: ChatMessage[];
  isStreaming: boolean;
  activeToolStatus: ActiveToolStatus | null;

  addMessage: (message: ChatMessage) => void;
  updateMessage: (id: string, updater: (msg: ChatMessage) => ChatMessage) => void;
  updateMessagesWhere: (
    predicate: (msg: ChatMessage) => boolean,
    updater: (msg: ChatMessage) => ChatMessage,
  ) => void;
  addToolCall: (messageId: string, toolCall: ToolCall) => void;
  updateToolCall: (messageId: string, toolCallId: string, update: Partial<ToolCall>) => void;
  setStreaming: (streaming: boolean) => void;
  setToolStatus: (status: ActiveToolStatus | null) => void;
  clearMessages: () => void;
}

export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  isStreaming: false,
  activeToolStatus: null,

  addMessage: (message) =>
    set((state) => ({
      messages: [...state.messages, message],
    })),

  updateMessage: (id, updater) =>
    set((state) => ({
      messages: state.messages.map((msg) => (msg.id === id ? updater(msg) : msg)),
    })),

  updateMessagesWhere: (predicate, updater) =>
    set((state) => ({
      messages: state.messages.map((msg) => (predicate(msg) ? updater(msg) : msg)),
    })),

  addToolCall: (messageId, toolCall) =>
    set((state) => ({
      messages: state.messages.map((msg) =>
        msg.id === messageId ? { ...msg, toolCalls: [...(msg.toolCalls || []), toolCall] } : msg,
      ),
    })),

  updateToolCall: (messageId, toolCallId, update) =>
    set((state) => ({
      messages: state.messages.map((msg) =>
        msg.id === messageId
          ? {
              ...msg,
              toolCalls: msg.toolCalls?.map((tc) =>
                tc.id === toolCallId ? { ...tc, ...update } : tc,
              ),
            }
          : msg,
      ),
    })),

  setStreaming: (streaming) => set({ isStreaming: streaming }),

  setToolStatus: (status) => set({ activeToolStatus: status }),

  clearMessages: () => set({ messages: [], activeToolStatus: null }),
}));
