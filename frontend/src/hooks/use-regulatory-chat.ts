"use client";

import { useCallback, useMemo, useRef, useState } from "react";
import { useWebSocket } from "./use-websocket";
import { useAuthStore } from "@/stores";
import { getWsUrl } from "@/lib/constants";
import type { RegulatoryWsEvent, RegulatoryWsMessage } from "@/types/regulatory";

export type RegulatoryRunStatus = "idle" | "connecting" | "running" | "done" | "error";

export interface RegulatoryChatState {
  streamingText: string;
  finalOutput: string;
  analysisId: string | null;
  status: RegulatoryRunStatus;
  error: string | null;
}

const INITIAL: RegulatoryChatState = {
  streamingText: "",
  finalOutput: "",
  analysisId: null,
  status: "idle",
  error: null,
};

/**
 * Drives one regulatory-legal Agent skill over `/api/v1/ws/regulatory`.
 * Mirrors `useLitigationChat` — a one-shot streamed run, not a conversation.
 */
export function useRegulatoryChat(onComplete?: () => void) {
  const [state, setState] = useState<RegulatoryChatState>(INITIAL);
  const pendingMessageRef = useRef<RegulatoryWsMessage | null>(null);
  const onCompleteRef = useRef(onComplete);
  onCompleteRef.current = onComplete;

  const accessToken = useAuthStore((s) => s.accessToken);

  const wsUrl = `${getWsUrl()}/api/v1/ws/regulatory`;
  const wsProtocols = useMemo(
    () => (accessToken ? [`access_token.${accessToken}`, "regulatory"] : undefined),
    [accessToken],
  );

  const handleMessage = useCallback((event: MessageEvent) => {
    let parsed: RegulatoryWsEvent;
    try {
      parsed = JSON.parse(event.data) as RegulatoryWsEvent;
    } catch {
      return;
    }
    switch (parsed.type) {
      case "analysis_started":
        setState((p) => ({ ...p, analysisId: parsed.data.analysis_id }));
        break;
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

  const sendMessageRef = useRef<((m: RegulatoryWsMessage) => void) | null>(null);

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
    (message: RegulatoryWsMessage) => {
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
