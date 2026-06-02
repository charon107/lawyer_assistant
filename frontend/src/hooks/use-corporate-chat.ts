"use client";

import { useCallback, useMemo, useRef, useState } from "react";
import { useWebSocket } from "./use-websocket";
import { useAuthStore } from "@/stores";
import { getWsUrl } from "@/lib/constants";
import type { CorporateWsEvent, CorporateWsMessage } from "@/types/corporate";

export type CorporateRunStatus = "idle" | "connecting" | "running" | "done" | "error";

export interface CorporateChatState {
  streamingText: string;
  finalOutput: string;
  status: CorporateRunStatus;
  error: string | null;
}

const INITIAL: CorporateChatState = {
  streamingText: "",
  finalOutput: "",
  status: "idle",
  error: null,
};

/**
 * Drives one corporate-legal Agent skill over `/api/v1/ws/corporate`.
 * Mirrors `useCommercialChat` — a one-shot streamed run, not a conversation.
 * On `complete` the caller typically reloads the deal's lists.
 */
export function useCorporateChat(onComplete?: () => void) {
  const [state, setState] = useState<CorporateChatState>(INITIAL);
  const pendingMessageRef = useRef<CorporateWsMessage | null>(null);
  const onCompleteRef = useRef(onComplete);
  onCompleteRef.current = onComplete;

  const accessToken = useAuthStore((s) => s.accessToken);

  const wsUrl = `${getWsUrl()}/api/v1/ws/corporate`;
  const wsProtocols = useMemo(
    () => (accessToken ? [`access_token.${accessToken}`, "corporate"] : undefined),
    [accessToken],
  );

  const handleMessage = useCallback((event: MessageEvent) => {
    let parsed: CorporateWsEvent;
    try {
      parsed = JSON.parse(event.data) as CorporateWsEvent;
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

  const sendMessageRef = useRef<((m: CorporateWsMessage) => void) | null>(null);

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
    (message: CorporateWsMessage) => {
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
