"use client";

import { useCallback, useMemo, useRef, useState } from "react";
import { useWebSocket } from "./use-websocket";
import { useAuthStore } from "@/stores";
import { getWsUrl } from "@/lib/constants";
import type { CommercialWsEvent, CommercialWsStartMessage } from "@/types/commercial";

/** A tool call surfaced during the review stream. */
export interface CommercialToolCall {
  id: string;
  name: string;
  args: Record<string, unknown>;
  result?: string;
  status: "running" | "completed";
}

export type CommercialReviewStatus =
  | "idle"
  | "connecting"
  | "running"
  | "done"
  | "error";

/** Everything a review-page component needs to render one streamed review. */
export interface CommercialChatState {
  reviewId: string | null;
  /** Markdown the agent has streamed so far (text deltas concatenated). */
  streamingText: string;
  /** Final output once `final_result` arrives (falls back to streamingText). */
  finalOutput: string;
  toolCalls: CommercialToolCall[];
  status: CommercialReviewStatus;
  error: string | null;
}

type StartPayload = Omit<CommercialWsStartMessage, "action">;

const INITIAL: CommercialChatState = {
  reviewId: null,
  streamingText: "",
  finalOutput: "",
  toolCalls: [],
  status: "idle",
  error: null,
};

/**
 * Drives one vendor-agreement review over the commercial WebSocket
 * (`/api/v1/ws/commercial`). Unlike `useChat`, this keeps its own
 * self-contained state instead of writing into the shared chat store —
 * a review is a one-shot streamed document, not a conversation.
 */
export function useCommercialChat() {
  const [state, setState] = useState<CommercialChatState>(INITIAL);
  // Holds the start payload until the socket reports OPEN, so we never
  // send before the connection is ready.
  const pendingStartRef = useRef<StartPayload | null>(null);

  const accessToken = useAuthStore((s) => s.accessToken);

  const wsUrl = `${getWsUrl()}/api/v1/ws/commercial`;
  const wsProtocols = useMemo(
    () => (accessToken ? [`access_token.${accessToken}`, "commercial"] : undefined),
    [accessToken],
  );

  const handleMessage = useCallback((event: MessageEvent) => {
    let parsed: CommercialWsEvent;
    try {
      parsed = JSON.parse(event.data) as CommercialWsEvent;
    } catch {
      return;
    }

    switch (parsed.type) {
      case "review_started": {
        setState((prev) => ({ ...prev, reviewId: parsed.data.review_id }));
        break;
      }
      case "text_delta": {
        setState((prev) => ({
          ...prev,
          streamingText: prev.streamingText + parsed.data.content,
        }));
        break;
      }
      case "tool_call": {
        const { tool_call_id, tool_name, args } = parsed.data;
        setState((prev) => ({
          ...prev,
          toolCalls: [
            ...prev.toolCalls,
            { id: tool_call_id, name: tool_name, args, status: "running" },
          ],
        }));
        break;
      }
      case "tool_result": {
        const { tool_call_id, content } = parsed.data;
        setState((prev) => ({
          ...prev,
          toolCalls: prev.toolCalls.map((tc) =>
            tc.id === tool_call_id
              ? { ...tc, result: content, status: "completed" }
              : tc,
          ),
        }));
        break;
      }
      case "final_result": {
        const { output, review_id } = parsed.data;
        setState((prev) => ({
          ...prev,
          reviewId: prev.reviewId ?? review_id,
          finalOutput: output || prev.streamingText,
          status: "done",
        }));
        break;
      }
      case "model_request_end":
        // Streaming marker — nothing to render directly.
        break;
      case "complete": {
        setState((prev) => ({
          ...prev,
          status: prev.status === "error" ? "error" : "done",
        }));
        break;
      }
      case "error": {
        setState((prev) => ({
          ...prev,
          status: "error",
          error: parsed.data.message || "审查过程中发生未知错误",
        }));
        break;
      }
    }
  }, []);

  const handleOpen = useCallback(() => {
    const pending = pendingStartRef.current;
    if (!pending) return;
    pendingStartRef.current = null;
    setState((prev) => ({ ...prev, status: "running" }));
    sendMessageRef.current?.({ action: "start", ...pending });
  }, []);

  const { isConnected, connect, disconnect, sendMessage } = useWebSocket({
    url: wsUrl,
    protocols: wsProtocols,
    onMessage: handleMessage,
    onOpen: handleOpen,
    reconnect: false,
  });

  // sendMessage identity is stable, but capture it in a ref so handleOpen
  // (defined above the hook call) can reach it without a circular dep.
  const sendMessageRef = useRef(sendMessage);
  sendMessageRef.current = sendMessage;

  const startReview = useCallback(
    (payload: StartPayload) => {
      pendingStartRef.current = payload;
      setState({ ...INITIAL, status: "connecting" });
      // If the socket is already open (sequential review on same page),
      // fire immediately; otherwise connect and let onOpen flush it.
      if (isConnected) {
        pendingStartRef.current = null;
        setState((prev) => ({ ...prev, status: "running" }));
        sendMessage({ action: "start", ...payload });
      } else {
        connect();
      }
    },
    [isConnected, connect, sendMessage],
  );

  const reset = useCallback(() => {
    pendingStartRef.current = null;
    setState(INITIAL);
  }, []);

  return {
    ...state,
    isConnected,
    startReview,
    reset,
    disconnect,
  };
}
