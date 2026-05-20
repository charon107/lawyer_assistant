"use client";

import { useCallback, useState } from "react";

export interface SystemLog {
  id: string;
  level: string;
  category: string;
  action: string;
  user_id: string | null;
  resource_type: string | null;
  resource_id: string | null;
  metadata_json: string | null;
  ip_address: string | null;
  request_id: string | null;
  created_at: string;
}

export interface SystemLogList {
  items: SystemLog[];
  total: number;
}

export interface SystemLogSummary {
  period_days: number;
  by_category: Record<string, number>;
  by_action: Record<string, number>;
  total: number;
}

export interface ConversationStats {
  period_days: number;
  total_messages: number;
  user_messages: number;
  rag_calls: number;
  avg_rag_duration_ms: number | null;
  tool_breakdown: Record<string, number>;
}

export interface FileReviewStats {
  period_days: number;
  by_status: Record<string, number>;
  by_file_type: Record<string, number>;
  avg_duration_seconds: number | null;
  total: number;
}

export interface RagStatus {
  checked_at: string;
  qdrant: {
    reachable: boolean;
    collection_exists: boolean;
    article_count: number;
  };
  embedding_model: {
    loaded: boolean;
    model_name: string;
  };
  redis: {
    available: boolean;
  };
}

export function useAdminLogs() {
  const [logs, setLogs] = useState<SystemLog[]>([]);
  const [logsTotal, setLogsTotal] = useState(0);
  const [summary, setSummary] = useState<SystemLogSummary | null>(null);
  const [convStats, setConvStats] = useState<ConversationStats | null>(null);
  const [fileStats, setFileStats] = useState<FileReviewStats | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchLogs = useCallback(
    async (params?: {
      skip?: number;
      limit?: number;
      category?: string;
      action?: string;
      user_id?: string;
      days?: number;
    }) => {
      setIsLoading(true);
      setError(null);
      try {
        const query = new URLSearchParams();
        if (params?.skip) query.set("skip", String(params.skip));
        if (params?.limit) query.set("limit", String(params.limit));
        if (params?.category) query.set("category", params.category);
        if (params?.action) query.set("action", params.action);
        if (params?.user_id) query.set("user_id", params.user_id);
        if (params?.days) query.set("days", String(params.days));

        const res = await fetch(`/api/admin/logs?${query.toString()}`, {
          credentials: "include",
        });
        if (!res.ok) throw new Error(`Failed to fetch logs: ${res.status}`);
        const data: SystemLogList = await res.json();
        setLogs(data.items);
        setLogsTotal(data.total);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load logs");
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  const fetchSummary = useCallback(async (days = 30) => {
    try {
      const res = await fetch(`/api/admin/logs/summary?days=${days}`, {
        credentials: "include",
      });
      if (!res.ok) return;
      const data: SystemLogSummary = await res.json();
      setSummary(data);
    } catch {
      // non-critical
    }
  }, []);

  const fetchConvStats = useCallback(async (days = 30) => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await fetch(`/api/admin/logs/stats/conversations?days=${days}`, {
        credentials: "include",
      });
      if (!res.ok) throw new Error(`Failed to fetch conversation stats: ${res.status}`);
      const data: ConversationStats = await res.json();
      setConvStats(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load conversation stats");
    } finally {
      setIsLoading(false);
    }
  }, []);

  const fetchFileStats = useCallback(async (days = 30) => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await fetch(`/api/admin/logs/stats/file-reviews?days=${days}`, {
        credentials: "include",
      });
      if (!res.ok) throw new Error(`Failed to fetch file review stats: ${res.status}`);
      const data: FileReviewStats = await res.json();
      setFileStats(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load file review stats");
    } finally {
      setIsLoading(false);
    }
  }, []);

  const fetchRagStatus = useCallback(async (): Promise<RagStatus | null> => {
    try {
      const res = await fetch("/api/admin/system/rag-status", {
        credentials: "include",
      });
      if (!res.ok) throw new Error(`Failed to fetch RAG status: ${res.status}`);
      return await res.json();
    } catch {
      return null;
    }
  }, []);

  return {
    logs,
    logsTotal,
    summary,
    convStats,
    fileStats,
    isLoading,
    error,
    fetchLogs,
    fetchSummary,
    fetchConvStats,
    fetchFileStats,
    fetchRagStatus,
  };
}
