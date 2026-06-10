"use client";

import { useCallback, useMemo, useRef, useState } from "react";
import { useWebSocket } from "./use-websocket";
import { useAuthStore } from "@/stores";
import { getWsUrl } from "@/lib/constants";
import type { IpWsEvent, IpWsMessage } from "@/types/ip";

export type IpRunStatus = "idle" | "connecting" | "running" | "done" | "error";

export interface IpChatState {
  streamingText: string;
  finalOutput: string;
  reviewId: string | null;
  status: IpRunStatus;
  error: string | null;
}

const INITIAL: IpChatState = {
  streamingText: "",
  finalOutput: "",
  reviewId: null,
  status: "idle",
  error: null,
};

/**
 * Drives one ip-legal Agent skill over `/api/v1/ws/ip`.
 * Mirrors `usePrivacyChat` — a one-shot streamed run, not a conversation.
 */
export function useIpChat(onComplete?: () => void) {
  const [state, setState] = useState<IpChatState>(INITIAL);
  const pendingMessageRef = useRef<IpWsMessage | null>(null);
  const onCompleteRef = useRef(onComplete);
  onCompleteRef.current = onComplete;

  const accessToken = useAuthStore((s) => s.accessToken);

  const wsUrl = `${getWsUrl()}/api/v1/ws/ip`;
  const wsProtocols = useMemo(
    () => (accessToken ? [`access_token.${accessToken}`, "ip"] : undefined),
    [accessToken],
  );

  const handleMessage = useCallback((event: MessageEvent) => {
    let parsed: IpWsEvent;
    try {
      parsed = JSON.parse(event.data) as IpWsEvent;
    } catch {
      return;
    }
    switch (parsed.type) {
      case "review_started":
        setState((p) => ({ ...p, reviewId: parsed.data.review_id }));
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

  const sendMessageRef = useRef<((m: IpWsMessage) => void) | null>(null);

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
    (message: IpWsMessage) => {
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
