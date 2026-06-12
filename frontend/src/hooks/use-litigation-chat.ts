"use client";

import { useCallback, useMemo, useRef, useState } from "react";
import { useWebSocket } from "./use-websocket";
import { useAuthStore } from "@/stores";
import { getWsUrl } from "@/lib/constants";
import type { LitigationWsEvent, LitigationWsMessage } from "@/types/litigation";

export type LitigationRunStatus = "idle" | "connecting" | "running" | "done" | "error";

export interface LitigationChatState {
  streamingText: string;
  finalOutput: string;
  analysisId: string | null;
  status: LitigationRunStatus;
  error: string | null;
}

const INITIAL: LitigationChatState = {
  streamingText: "",
  finalOutput: "",
  analysisId: null,
  status: "idle",
  error: null,
};

/**
 * Drives one litigation-legal Agent skill over `/api/v1/ws/litigation`.
 * Mirrors `useIpChat` — a one-shot streamed run, not a conversation.
 */
export function useLitigationChat(onComplete?: () => void) {
  const [state, setState] = useState<LitigationChatState>(INITIAL);
  const pendingMessageRef = useRef<LitigationWsMessage | null>(null);
  const onCompleteRef = useRef(onComplete);
  onCompleteRef.current = onComplete;

  const accessToken = useAuthStore((s) => s.accessToken);

  const wsUrl = `${getWsUrl()}/api/v1/ws/litigation`;
  const wsProtocols = useMemo(
    () => (accessToken ? [`access_token.${accessToken}`, "litigation"] : undefined),
    [accessToken],
  );

  const handleMessage = useCallback((event: MessageEvent) => {
    let parsed: LitigationWsEvent;
    try {
      parsed = JSON.parse(event.data) as LitigationWsEvent;
    } catch {
      return;
    }
    switch (parsed.type) {
      case "analysis_started":
        setState((p) => ({ ...p, analysisId: parsed.data.analysis_id }));
        break;
      case "text_delta":
        setState((p) => ({
          ...p,
          streamingText: p.streamingText + parsed.data.content,
        }));
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

  const sendMessageRef = useRef<((m: LitigationWsMessage) => void) | null>(null);

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
    (message: LitigationWsMessage) => {
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
