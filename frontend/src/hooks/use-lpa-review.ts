"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import { useAuthStore } from "@/stores";

interface ReviewState {
  reviewId: string | null;
  status: string;
  progress: number;
  progressMsg: string;
  chapters: any[];
  facts: any;
  chapterReviews: any[];
  crossCheck: any;
  reportMarkdown: string | null;
  error: string | null;
  awaitingChapters: boolean;
}

function getAuthHeaders(): Record<string, string> {
  const token = useAuthStore.getState().accessToken;
  if (token) {
    return { Authorization: `Bearer ${token}` };
  }
  return {};
}

export function useLPAReview() {
  const [state, setState] = useState<ReviewState>({
    reviewId: null,
    status: "idle",
    progress: 0,
    progressMsg: "",
    chapters: [],
    facts: null,
    chapterReviews: [],
    crossCheck: null,
    reportMarkdown: null,
    error: null,
    awaitingChapters: false,
  });

  const wsRef = useRef<WebSocket | null>(null);

  const connectWS = useCallback((reviewId: string, apiBase: string) => {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = window.location.host;
    const url = `${protocol}//${host}${apiBase}/lpa/review/${reviewId}/ws`;

    let retryCount = 0;
    const maxRetries = 5;

    function createWS() {
      const token = useAuthStore.getState().accessToken;
      if (!token) {
        setState((prev) => ({
          ...prev,
          status: "error",
          error: "未登录，请先登录",
        }));
        return;
      }
      const ws = new WebSocket(url, [`access_token.${token}`, "lpa"]);
      wsRef.current = ws;

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setState((prev) => {
        switch (data.event) {
          case "progress":
            return {
              ...prev,
              status: data.stage,
              progress: data.progress,
              progressMsg: data.msg,
            };
          case "chapters_ready":
            return {
              ...prev,
              chapters: data.chapters,
              awaitingChapters: true,
            };
          case "facts_ready":
            return { ...prev, facts: data.facts };
          case "chapter_result":
            return {
              ...prev,
              chapterReviews: [...prev.chapterReviews, {
                chapter: data.chapter,
                complexity: data.complexity,
                findings: data.findings,
              }],
            };
          case "cross_check_ready":
            return { ...prev, crossCheck: data.cross_check };
          case "complete":
            return {
              ...prev,
              status: "complete",
              progress: 1.0,
              progressMsg: "审查完成",
            };
          case "error":
            return { ...prev, status: "error", error: data.message };
          default:
            return prev;
        }
      });
    };

    ws.onerror = () => {
      if (retryCount < maxRetries) {
        retryCount++;
        const delay = 1000 * 2 ** (retryCount - 1);
        setState((prev) => ({
          ...prev,
          progressMsg: `连接中断，${delay / 1000}秒后重试 (${retryCount}/${maxRetries})...`,
        }));
        setTimeout(() => createWS(), delay);
      } else {
        setState((prev) => ({
          ...prev,
          status: "error",
          error: "WebSocket 连接失败，请刷新页面重试",
        }));
      }
    };

    ws.onclose = () => {
      wsRef.current = null;
    };

    } // end createWS

    createWS();
  }, []);

  const startReview = useCallback(async (file: File, apiBase: string) => {
    setState({
      reviewId: null,
      status: "uploading",
      progress: 0,
      progressMsg: "上传中...",
      chapters: [],
      facts: null,
      chapterReviews: [],
      crossCheck: null,
      reportMarkdown: null,
      error: null,
      awaitingChapters: false,
    });

    try {
      const formData = new FormData();
      formData.append("file", file);

      const res = await fetch(`${apiBase}/lpa/review`, {
        method: "POST",
        headers: getAuthHeaders(),
        body: formData,
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "上传失败");
      }

      const { review_id } = await res.json();
      setState((prev) => ({
        ...prev,
        reviewId: review_id,
        status: "started",
        progress: 0.05,
        progressMsg: "已上传，开始审查...",
      }));

      connectWS(review_id, apiBase);
      return review_id;
    } catch (e: any) {
      setState((prev) => ({
        ...prev,
        status: "error",
        error: e.message || "上传失败",
      }));
      return null;
    }
  }, [connectWS]);

  const confirmChapters = useCallback(async (chapters: any[], apiBase: string) => {
    if (!state.reviewId) return;

    try {
      const res = await fetch(`${apiBase}/lpa/review/${state.reviewId}/chapters`, {
        method: "PUT",
        headers: { "Content-Type": "application/json", ...getAuthHeaders() },
        body: JSON.stringify({ chapters }),
      });
      if (!res.ok) {
        throw new Error("章节确认失败");
      }
      setState((prev) => ({ ...prev, awaitingChapters: false }));
    } catch (e: any) {
      setState((prev) => ({
        ...prev,
        error: e.message || "章节确认失败",
      }));
    }
  }, [state.reviewId]);

  const fetchReport = useCallback(async (apiBase: string) => {
    if (!state.reviewId) return null;
    try {
      const res = await fetch(`${apiBase}/lpa/review/${state.reviewId}/report`, {
        headers: getAuthHeaders(),
      });
      if (!res.ok) return null;
      const data = await res.json();
      setState((prev) => ({ ...prev, reportMarkdown: data.report_markdown }));
      return data.report_markdown;
    } catch {
      return null;
    }
  }, [state.reviewId]);

  const fetchFullResult = useCallback(async (apiBase: string, id?: string) => {
    const rid = id || state.reviewId;
    if (!rid) return null;
    // If an external id is provided, sync it to state
    if (id && id !== state.reviewId) {
      setState((prev) => ({ ...prev, reviewId: id }));
    }
    try {
      const res = await fetch(`${apiBase}/lpa/review/${rid}/full`, {
        headers: getAuthHeaders(),
      });
      if (!res.ok) return null;
      const data = await res.json();
      setState((prev) => ({
        ...prev,
        chapters: data.chapters || prev.chapters,
        facts: data.facts || prev.facts,
        chapterReviews: data.chapter_reviews || prev.chapterReviews,
        crossCheck: data.cross_check || prev.crossCheck,
      }));
      return data;
    } catch {
      return null;
    }
  }, [state.reviewId]);

  const sendChatMessage = useCallback(async (
    question: string,
    history: any[],
    apiBase: string
  ): Promise<string> => {
    if (!state.reviewId) return "审查会话不存在";
    try {
      const res = await fetch(`${apiBase}/lpa/review/${state.reviewId}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...getAuthHeaders() },
        body: JSON.stringify({ question, history }),
      });
      if (!res.ok) return "对话服务不可用";
      const data = await res.json();
      return data.answer;
    } catch {
      return "对话服务不可用";
    }
  }, [state.reviewId]);

  // Cleanup WS on unmount
  useEffect(() => {
    return () => {
      wsRef.current?.close();
    };
  }, []);

  return {
    ...state,
    startReview,
    confirmChapters,
    fetchReport,
    fetchFullResult,
    sendChatMessage,
  };
}
