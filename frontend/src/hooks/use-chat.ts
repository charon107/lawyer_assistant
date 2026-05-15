"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { nanoid } from "nanoid";
import { useWebSocket } from "./use-websocket";
import { useChatStore, useAuthStore } from "@/stores";
import type { WSEvent, PendingApproval, Decision } from "@/types";
import { getWsUrl } from "@/lib/constants";
import { useConversationStore } from "@/stores";
interface UseChatOptions {
  conversationId?: string | null;
  caseId?: string | null;
  onConversationCreated?: (conversationId: string) => void;
}

export function useChat(options: UseChatOptions = {}) {
  const { conversationId, caseId, onConversationCreated } = options;
  const { setCurrentConversationId, currentConversationId: currentConversationIdFromStore } =
    useConversationStore();
  const { messages, addMessage, updateMessage, setToolStatus, clearMessages } = useChatStore();

  const [isProcessing, setIsProcessing] = useState(false);
  const [currentMessageId, setCurrentMessageId] = useState<string | null>(null);
  const currentGroupIdRef = useRef<string | null>(null);
  const messageQueueRef = useRef<{ content: string; fileIds?: string[] }[]>([]);
  const modelRef = useRef<string | null>(null);
  // Human-in-the-Loop: pending tool approval state
  const [pendingApproval, setPendingApproval] = useState<PendingApproval | null>(null);

  const handleWebSocketMessage = useCallback(
    (event: MessageEvent) => {
      const wsEvent: WSEvent = JSON.parse(event.data);

      // Helper to create a new message
      const createNewMessage = (content: string): string => {
        // Mark previous message as not streaming before creating new one
        if (currentMessageId) {
          updateMessage(currentMessageId, (msg) => ({
            ...msg,
            isStreaming: false,
          }));
        }

        const newMsgId = nanoid();
        // Use current conversationId from store to avoid closure issues
        const effectiveConversationId =
          currentConversationIdFromStore || conversationId || undefined;
        addMessage({
          id: newMsgId,
          role: "assistant",
          content,
          timestamp: new Date(),
          isStreaming: true,
          toolCalls: [],
          groupId: currentGroupIdRef.current || undefined,
          conversationId: effectiveConversationId,
          isTemporaryId: true,
        });
        setCurrentMessageId(newMsgId);
        return newMsgId;
      };

      switch (wsEvent.type) {
        case "conversation_created": {
          // Handle new conversation created by backend
          const { conversation_id } = wsEvent.data as { conversation_id: string };
          setCurrentConversationId(conversation_id);
          // Update all messages that don't have a conversationId yet
          const { updateMessagesWhere } = useChatStore.getState();
          updateMessagesWhere(
            (msg) => !msg.conversationId,
            (msg) => ({ ...msg, conversationId: conversation_id }),
          );
          onConversationCreated?.(conversation_id);
          break;
        }

        case "message_saved": {
          // Assistant message was saved to database, update local ID to real database ID
          const { message_id } = wsEvent.data as { message_id: string };
          if (currentMessageId) {
            // Update the current streaming message's ID to the real database ID
            updateMessage(currentMessageId, (msg) => ({
              ...msg,
              id: message_id,
              isTemporaryId: false,
            }));
          } else {
            // Fallback: find the last assistant message with a temp ID
            // This handles cases where currentMessageId was already cleared
            const messages = useChatStore.getState().messages;
            const lastTemp = [...messages]
              .reverse()
              .find((msg) => msg.role === "assistant" && !!msg.isTemporaryId);
            if (lastTemp) {
              updateMessage(lastTemp.id, (msg) => ({
                ...msg,
                id: message_id,
                isTemporaryId: false,
              }));
            }
          }
          break;
        }

        case "model_request_start": {
          // PydanticAI/LangChain - only create message once per turn
          if (!currentMessageId) {
            createNewMessage("");
          }
          break;
        }

        case "crew_start":
        case "crew_started": {
          // CrewAI - only create message once per turn
          if (!currentMessageId) {
            currentGroupIdRef.current = nanoid();
            createNewMessage("");
          }
          break;
        }

        case "text_delta": {
          // Append text delta to current message
          if (currentMessageId) {
            const content = (wsEvent.data as { index: number; content: string }).content;
            updateMessage(currentMessageId, (msg) => ({
              ...msg,
              content: msg.content + content,
            }));
          }
          break;
        }

        // CrewAI agent events - update single message content
        case "agent_started": {
          if (currentMessageId) {
            const { agent } = wsEvent.data as { agent: string; task: string };
            updateMessage(currentMessageId, (msg) => ({
              ...msg,
              content: `🤖 **${agent}** 正在处理...`,
            }));
          }
          break;
        }

        case "agent_completed": {
          if (currentMessageId) {
            const { agent, output } = wsEvent.data as { agent: string; output: string };
            updateMessage(currentMessageId, (msg) => ({
              ...msg,
              content: msg.content ? `${msg.content}\n\n${output}` : `✅ **${agent}**\n\n${output}`,
            }));
          }
          break;
        }

        // CrewAI task events - update single message content
        case "task_started": {
          if (currentMessageId) {
            const { description, agent } = wsEvent.data as {
              task_id: string;
              description: string;
              agent: string;
            };
            updateMessage(currentMessageId, (msg) => ({
              ...msg,
              content: `📋 **${agent}**: ${description}`,
            }));
          }
          break;
        }

        case "task_completed": {
          if (currentMessageId) {
            const { output } = wsEvent.data as {
              task_id: string;
              output: string;
              agent: string;
            };
            updateMessage(currentMessageId, (msg) => ({
              ...msg,
              content: msg.content ? `${msg.content}\n\n${output}` : output,
            }));
          }
          break;
        }

        // CrewAI tool events
        case "tool_started": {
          // CrewAI tool — show status indicator instead of individual card
          const { tool_name: crewToolName } = wsEvent.data as {
            tool_name: string;
            tool_args: string;
            agent: string;
          };
          setToolStatus({ label: `正在执行 ${crewToolName}`, toolName: crewToolName });
          break;
        }

        case "tool_finished": {
          // CrewAI tool finished — status stays until next tool or final_result
          break;
        }

        // LLM events (can be used for showing thinking status)
        case "llm_started":
        case "llm_completed": {
          // LLM lifecycle events - optionally show status
          break;
        }

        case "tool_status": {
          // ChatGPT-style: update active tool status for display
          const { label, tool_name: statusToolName } = wsEvent.data as {
            label: string;
            tool_name: string;
          };
          setToolStatus({ label, toolName: statusToolName });
          break;
        }

        case "tool_call": {
          // Intentionally no-op during streaming — tool_status handles display.
          // Tool calls are persisted by the backend and loaded from DB on history reload.
          break;
        }

        case "tool_result": {
          // Intentionally no-op during streaming — tool_status handles display.
          break;
        }

        case "final_result": {
          // Clear tool status when final response arrives
          setToolStatus(null);
          // Finalize message
          if (currentMessageId) {
            const { output } = wsEvent.data as { output: string };
            if (output) {
              updateMessage(currentMessageId, (msg) => ({
                ...msg,
                content: msg.content || output,
                isStreaming: false,
              }));
            } else {
              updateMessage(currentMessageId, (msg) => ({
                ...msg,
                isStreaming: false,
              }));
            }
          }
          setIsProcessing(false);
          // Don't clear currentMessageId yet - we need it for message_saved event
          currentGroupIdRef.current = null;
          break;
        }

        case "error": {
          // Handle error
          if (currentMessageId) {
            const { message } = wsEvent.data as { message: string };
            updateMessage(currentMessageId, (msg) => ({
              ...msg,
              content: msg.content + `\n\n❌ Error: ${message || "Unknown error"}`,
              isStreaming: false,
            }));
          }
          setIsProcessing(false);
          break;
        }

        case "tool_approval_required": {
          // Human-in-the-Loop: AI wants to execute tools that need approval
          const { action_requests, review_configs } = wsEvent.data as {
            action_requests: Array<{
              id: string;
              tool_name: string;
              args: Record<string, unknown>;
            }>;
            review_configs: Array<{
              tool_name: string;
              allow_edit?: boolean;
              timeout?: number;
            }>;
          };
          setPendingApproval({
            actionRequests: action_requests,
            reviewConfigs: review_configs,
          });
          // Show pending tools in the current message
          if (currentMessageId) {
            const toolNames = action_requests.map((ar) => ar.tool_name).join(", ");
            updateMessage(currentMessageId, (msg) => ({
              ...msg,
              content: msg.content + `\n\n⏸️ Waiting for approval: ${toolNames}`,
            }));
          }
          break;
        }

        case "complete": {
          setIsProcessing(false);
          // Don't clear currentMessageId here — it persists until the user sends the next message.
          // This prevents model_request_start from creating duplicate bubbles during tool-call loops.
          break;
        }
      }
    },
    [
      currentMessageId,
      addMessage,
      updateMessage,
      setToolStatus,
      setCurrentConversationId,
      onConversationCreated,
      currentConversationIdFromStore,
      conversationId,
    ],
  );

  // Access token lives in memory only (populated by login/refresh responses).
  // It is sent to the WS via Sec-WebSocket-Protocol rather than a URL query
  // string so it does not end up in access logs or Referer headers.
  const accessToken = useAuthStore((state) => state.accessToken);

  const wsUrl = `${getWsUrl()}/api/v1/ws/agent`;
  const wsProtocols = useMemo(
    () => (accessToken ? [`access_token.${accessToken}`, "chat"] : undefined),
    [accessToken],
  );

  const { isConnected, connect, disconnect, sendMessage } = useWebSocket({
    url: wsUrl,
    protocols: wsProtocols,
    onMessage: handleWebSocketMessage,
  });

  const doSend = useCallback(
    (content: string, fileIds?: string[]) => {
      // Reset currentMessageId so the next model_request_start creates a fresh bubble
      setCurrentMessageId(null);
      addMessage({
        id: nanoid(),
        role: "user",
        content,
        timestamp: new Date(),
        conversationId: conversationId || undefined,
        fileIds,
      });
      setIsProcessing(true);
      const payload: Record<string, unknown> = {
        message: content,
        conversation_id: conversationId || null,
      };
      if (caseId) payload.case_id = caseId;
      if (fileIds?.length) payload.file_ids = fileIds;
      if (modelRef.current) payload.model = modelRef.current;
      sendMessage(payload);
    },
    [addMessage, sendMessage, conversationId, caseId],
  );

  const sendChatMessage = useCallback(
    (content: string, fileIds?: string[]) => {
      if (isProcessing) {
        messageQueueRef.current.push({ content, fileIds });
        addMessage({
          id: nanoid(),
          role: "user",
          content,
          timestamp: new Date(),
          conversationId: conversationId || undefined,
          fileIds,
        });
        return;
      }
      doSend(content, fileIds);
    },
    [isProcessing, doSend, addMessage, conversationId],
  );

  // Human-in-the-Loop: send resume message with user decisions
  const sendResumeDecisions = useCallback(
    (decisions: Decision[]) => {
      // Clear pending approval state
      setPendingApproval(null);

      // Update message to show decisions were made
      if (currentMessageId) {
        const approvedCount = decisions.filter((d) => d.type === "approve").length;
        const editedCount = decisions.filter((d) => d.type === "edit").length;
        const rejectedCount = decisions.filter((d) => d.type === "reject").length;

        const summaryParts: string[] = [];
        if (approvedCount > 0) summaryParts.push(`${approvedCount} approved`);
        if (editedCount > 0) summaryParts.push(`${editedCount} edited`);
        if (rejectedCount > 0) summaryParts.push(`${rejectedCount} rejected`);

        updateMessage(currentMessageId, (msg) => ({
          ...msg,
          content: msg.content.replace(
            /\n\n⏸️ Waiting for approval:.*$/,
            `\n\n✅ Decisions: ${summaryParts.join(", ")}`,
          ),
        }));
      }

      // Send resume message to WebSocket
      sendMessage({
        type: "resume",
        decisions: decisions.map((d) => {
          if (d.type === "edit" && d.editedAction) {
            return {
              type: "edit",
              edited_action: d.editedAction,
            };
          }
          return { type: d.type };
        }),
      });
    },
    [currentMessageId, updateMessage, sendMessage],
  );

  // Drain message queue when processing finishes
  useEffect(() => {
    if (!isProcessing && messageQueueRef.current.length > 0) {
      const next = messageQueueRef.current.shift();
      if (next) {
        setTimeout(() => doSend(next.content, next.fileIds), 100);
      }
    }
  }, [isProcessing, doSend]);

  return {
    messages,
    isConnected,
    isProcessing,
    connect,
    disconnect,
    sendMessage: sendChatMessage,
    clearMessages,
    setModel: (model: string | null) => {
      modelRef.current = model;
    },
    // Human-in-the-Loop support
    pendingApproval,
    sendResumeDecisions,
  };
}
