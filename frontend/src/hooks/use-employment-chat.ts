"use client";

import { useCallback, useMemo, useRef, useState } from "react";
import { useWebSocket } from "./use-websocket";
import { useAuthStore } from "@/stores";
import { getWsUrl } from "@/lib/constants";
import type { EmploymentWsEvent, EmploymentWsMessage } from "@/types/employment";

export type EmploymentRunStatus = "idle" | "connecting" | "running" | "done" | "error";

export interface EmploymentChatState {
  streamingText: string;
  finalOutput: string;
  status: EmploymentRunStatus;
  error: string | null;
}

const INITIAL: EmploymentChatState = {
  streamingText: "",
  finalOutput: "",
  status: "idle",
  error: null,
};

/**
 * Drives one employment-legal Agent skill over `/api/v1/ws/employment`.
 * Mirrors `useCorporateChat` — a one-shot streamed run, not a conversation.
 */
export function useEmploymentChat(onComplete?: () => void) {
  const [state, setState] = useState<EmploymentChatState>(INITIAL);
  const pendingMessageRef = useRef<EmploymentWsMessage | null>(null);
  const onCompleteRef = useRef(onComplete);
  onCompleteRef.current = onComplete;

  const accessToken = useAuthStore((s) => s.accessToken);

  const wsUrl = `${getWsUrl()}/api/v1/ws/employment`;
  const wsProtocols = useMemo(
    () => (accessToken ? [`access_token.${accessToken}`, "employment"] : undefined),
    [accessToken],
  );

  const handleMessage = useCallback((event: MessageEvent) => {
    let parsed: EmploymentWsEvent;
    try {
      parsed = JSON.parse(event.data) as EmploymentWsEvent;
    } catch {
      return;
    }
    switch (parsed.type) {
      case "text_delta":
        setState((p) => ({ ...p, streamingText: p.streamingText + parsed.data.content }));
        break;
      case "final_result":
        setState((p) => ({
          ...p,
          finalOutput: parsed.data.output || p.streamingText,
          status: "done",
        }));
        break;
      case "complete":
        setState((p) => ({ ...p, status: p.status === "error" ? "error" : "done" }));
        onCompleteRef.current?.();
        break;
      case "error":
        setState((p) => ({
          ...p,
          status: "error",
          error: parsed.data.message || "运行过程中发生未知错误",
        }));
        break;
      default:
        break;
    }
  }, []);

  const sendMessageRef = useRef<((m: EmploymentWsMessage) => void) | null>(null);

  const handleOpen = useCallback(() => {
    const pending = pendingMessageRef.current;
    if (!pending) return;
    pendingMessageRef.current = null;
    setState((p) => ({ ...p, status: "running" }));
    sendMessageRef.current?.(pending);
  }, []);

  const { isConnected, connect, disconnect, sendMessage } = useWebSocket({
    url: wsUrl,
    protocols: wsProtocols,
    onMessage: handleMessage,
    onOpen: handleOpen,
    reconnect: false,
  });
  sendMessageRef.current = sendMessage;

  const runSkill = useCallback(
    (message: EmploymentWsMessage) => {
      pendingMessageRef.current = message;
      setState({ ...INITIAL, status: "connecting" });
      if (isConnected) {
        pendingMessageRef.current = null;
        setState((p) => ({ ...p, status: "running" }));
        sendMessage(message);
      } else {
        connect();
      }
    },
    [isConnected, connect, sendMessage],
  );

  const reset = useCallback(() => {
    pendingMessageRef.current = null;
    setState(INITIAL);
  }, []);

  return { ...state, isConnected, runSkill, reset, disconnect };
}
