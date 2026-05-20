"use client";

import { useEffect, useState, useCallback } from "react";
import { useAuthStore } from "@/stores";
import { useAdminLogs, type SystemLog } from "@/hooks/use-admin-logs";
import { cn } from "@/lib/utils";
import { formatDate } from "@/lib/utils";
import { Shield, Users, MessageSquare, FileSearch, ChevronLeft, ChevronRight } from "lucide-react";

type Tab = "auth" | "audit" | "conversations" | "files";

const PAGE_SIZE = 50;

function Badge({ children, variant = "default" }: { children: React.ReactNode; variant?: "default" | "warning" | "error" | "success" }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded px-1.5 py-0.5 text-[11px] font-medium",
        variant === "default" && "bg-muted text-muted-foreground",
        variant === "warning" && "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200",
        variant === "error" && "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200",
        variant === "success" && "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200",
      )}
    >
      {children}
    </span>
  );
}

function levelVariant(level: string): "default" | "warning" | "error" | "success" {
  if (level === "warning") return "warning";
  if (level === "error") return "error";
  if (level === "info") return "success";
  return "default";
}

function LogTable({ items, total, page, onPage }: {
  items: SystemLog[];
  total: number;
  page: number;
  onPage: (p: number) => void;
}) {
  const totalPages = Math.ceil(total / PAGE_SIZE);

  return (
    <div className="space-y-3">
      <div className="overflow-x-auto rounded-lg border">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b bg-muted/40 text-muted-foreground text-xs uppercase tracking-wider">
              <th className="px-4 py-3 text-left">时间</th>
              <th className="px-4 py-3 text-left">级别</th>
              <th className="px-4 py-3 text-left">操作</th>
              <th className="px-4 py-3 text-left">用户</th>
              <th className="px-4 py-3 text-left">IP</th>
              <th className="px-4 py-3 text-left">资源</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {items.length === 0 && (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-muted-foreground">
                  暂无记录
                </td>
              </tr>
            )}
            {items.map((log) => (
              <tr key={log.id} className="hover:bg-muted/20 transition-colors">
                <td className="px-4 py-2.5 font-mono text-xs text-muted-foreground whitespace-nowrap">
                  {formatDate(log.created_at)}
                </td>
                <td className="px-4 py-2.5">
                  <Badge variant={levelVariant(log.level)}>{log.level}</Badge>
                </td>
                <td className="px-4 py-2.5 font-medium">{log.action}</td>
                <td className="px-4 py-2.5 font-mono text-xs text-muted-foreground">
                  {log.user_id ? log.user_id.slice(0, 8) + "…" : "—"}
                </td>
                <td className="px-4 py-2.5 text-xs text-muted-foreground">{log.ip_address ?? "—"}</td>
                <td className="px-4 py-2.5 text-xs text-muted-foreground">
                  {log.resource_type && log.resource_id
                    ? `${log.resource_type}/${log.resource_id.slice(0, 8)}…`
                    : "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {totalPages > 1 && (
        <div className="flex items-center justify-between text-sm">
          <span className="text-muted-foreground">共 {total} 条</span>
          <div className="flex items-center gap-1">
            <button
              onClick={() => onPage(page - 1)}
              disabled={page === 0}
              className="rounded p-1 hover:bg-muted disabled:opacity-40"
            >
              <ChevronLeft className="h-4 w-4" />
            </button>
            <span className="px-2">
              第 {page + 1} / {totalPages} 页
            </span>
            <button
              onClick={() => onPage(page + 1)}
              disabled={page >= totalPages - 1}
              className="rounded p-1 hover:bg-muted disabled:opacity-40"
            >
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function StatCard({ label, value, sub }: { label: string; value: string | number; sub?: string }) {
  return (
    <div className="rounded-lg border bg-card p-4">
      <p className="text-sm text-muted-foreground">{label}</p>
      <p className="text-2xl font-bold mt-1">{value}</p>
      {sub && <p className="text-xs text-muted-foreground mt-0.5">{sub}</p>}
    </div>
  );
}

function ConversationStatsTab() {
  const { convStats, isLoading, error, fetchConvStats } = useAdminLogs();
  const [days, setDays] = useState(30);

  useEffect(() => {
    fetchConvStats(days);
  }, [days, fetchConvStats]);

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <label className="text-sm text-muted-foreground">时间范围</label>
        <select
          value={days}
          onChange={(e) => setDays(Number(e.target.value))}
          className="rounded border bg-background px-2 py-1 text-sm"
        >
          <option value={7}>最近 7 天</option>
          <option value={30}>最近 30 天</option>
          <option value={90}>最近 90 天</option>
        </select>
      </div>

      {isLoading && <div className="text-muted-foreground text-sm">加载中...</div>}
      {error && <div className="text-red-600 text-sm">{error}</div>}

      {convStats && !isLoading && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <StatCard label="总消息数" value={convStats.total_messages.toLocaleString()} />
            <StatCard label="用户消息" value={convStats.user_messages.toLocaleString()} />
            <StatCard label="RAG 检索调用" value={convStats.rag_calls.toLocaleString()} />
            <StatCard
              label="平均检索耗时"
              value={convStats.avg_rag_duration_ms ? `${Math.round(convStats.avg_rag_duration_ms)} ms` : "—"}
            />
          </div>

          {Object.keys(convStats.tool_breakdown).length > 0 && (
            <div className="rounded-lg border bg-card p-4">
              <p className="text-sm font-medium mb-3">工具调用分布</p>
              <div className="space-y-2">
                {Object.entries(convStats.tool_breakdown).map(([tool, count]) => (
                  <div key={tool} className="flex items-center justify-between text-sm">
                    <span className="font-mono text-muted-foreground">{tool}</span>
                    <span className="font-semibold">{(count as number).toLocaleString()}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

function FileStatsTab() {
  const { fileStats, isLoading, error, fetchFileStats } = useAdminLogs();
  const [days, setDays] = useState(30);

  useEffect(() => {
    fetchFileStats(days);
  }, [days, fetchFileStats]);

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <label className="text-sm text-muted-foreground">时间范围</label>
        <select
          value={days}
          onChange={(e) => setDays(Number(e.target.value))}
          className="rounded border bg-background px-2 py-1 text-sm"
        >
          <option value={7}>最近 7 天</option>
          <option value={30}>最近 30 天</option>
          <option value={90}>最近 90 天</option>
        </select>
      </div>

      {isLoading && <div className="text-muted-foreground text-sm">加载中...</div>}
      {error && <div className="text-red-600 text-sm">{error}</div>}

      {fileStats && !isLoading && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            <StatCard label="总审查数" value={fileStats.total.toLocaleString()} />
            <StatCard
              label="平均处理耗时"
              value={fileStats.avg_duration_seconds ? `${Math.round(fileStats.avg_duration_seconds)} 秒` : "—"}
            />
            <StatCard
              label="完成率"
              value={
                fileStats.total > 0
                  ? `${Math.round(((fileStats.by_status["completed"] ?? 0) / fileStats.total) * 100)}%`
                  : "—"
              }
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {Object.keys(fileStats.by_status).length > 0 && (
              <div className="rounded-lg border bg-card p-4">
                <p className="text-sm font-medium mb-3">按状态分布</p>
                <div className="space-y-2">
                  {Object.entries(fileStats.by_status).map(([status, count]) => (
                    <div key={status} className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground capitalize">{status}</span>
                      <span className="font-semibold">{(count as number).toLocaleString()}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {Object.keys(fileStats.by_file_type).length > 0 && (
              <div className="rounded-lg border bg-card p-4">
                <p className="text-sm font-medium mb-3">按文件类型分布</p>
                <div className="space-y-2">
                  {Object.entries(fileStats.by_file_type).map(([type, count]) => (
                    <div key={type} className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground font-mono">{type}</span>
                      <span className="font-semibold">{(count as number).toLocaleString()}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}

function AuthLogsTab() {
  const { logs, logsTotal, isLoading, error, fetchLogs } = useAdminLogs();
  const [page, setPage] = useState(0);
  const [days, setDays] = useState(30);

  const load = useCallback(() => {
    fetchLogs({ category: "auth", skip: page * PAGE_SIZE, limit: PAGE_SIZE, days });
  }, [fetchLogs, page, days]);

  useEffect(() => { load(); }, [load]);

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <label className="text-sm text-muted-foreground">时间范围</label>
        <select
          value={days}
          onChange={(e) => { setDays(Number(e.target.value)); setPage(0); }}
          className="rounded border bg-background px-2 py-1 text-sm"
        >
          <option value={7}>最近 7 天</option>
          <option value={30}>最近 30 天</option>
          <option value={90}>最近 90 天</option>
          <option value={365}>最近 1 年</option>
        </select>
      </div>
      {isLoading && <div className="text-muted-foreground text-sm">加载中...</div>}
      {error && <div className="text-red-600 text-sm">{error}</div>}
      {!isLoading && (
        <LogTable items={logs} total={logsTotal} page={page} onPage={setPage} />
      )}
    </div>
  );
}

function AuditLogsTab() {
  const { logs, logsTotal, isLoading, error, fetchLogs } = useAdminLogs();
  const [page, setPage] = useState(0);
  const [days, setDays] = useState(30);

  const load = useCallback(() => {
    fetchLogs({ category: "admin", skip: page * PAGE_SIZE, limit: PAGE_SIZE, days });
  }, [fetchLogs, page, days]);

  useEffect(() => { load(); }, [load]);

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <label className="text-sm text-muted-foreground">时间范围</label>
        <select
          value={days}
          onChange={(e) => { setDays(Number(e.target.value)); setPage(0); }}
          className="rounded border bg-background px-2 py-1 text-sm"
        >
          <option value={7}>最近 7 天</option>
          <option value={30}>最近 30 天</option>
          <option value={90}>最近 90 天</option>
          <option value={365}>最近 1 年</option>
        </select>
      </div>
      {isLoading && <div className="text-muted-foreground text-sm">加载中...</div>}
      {error && <div className="text-red-600 text-sm">{error}</div>}
      {!isLoading && (
        <LogTable items={logs} total={logsTotal} page={page} onPage={setPage} />
      )}
    </div>
  );
}

const TABS: { id: Tab; label: string; icon: React.ElementType }[] = [
  { id: "auth", label: "认证日志", icon: Shield },
  { id: "audit", label: "管理审计", icon: Users },
  { id: "conversations", label: "对话统计", icon: MessageSquare },
  { id: "files", label: "文件审查", icon: FileSearch },
];

export default function AdminLogsPage() {
  const { user } = useAuthStore();
  const [activeTab, setActiveTab] = useState<Tab>("auth");

  if (user?.role !== "admin") {
    return (
      <div className="p-6 max-w-5xl mx-auto">
        <div className="text-center text-muted-foreground py-12">无权访问</div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold">系统日志</h1>
        <p className="text-sm text-muted-foreground mt-0.5">认证事件、管理操作和业务统计</p>
      </div>

      {/* Tabs */}
      <div className="border-b">
        <nav className="flex gap-0 -mb-px">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={cn(
                "flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors",
                activeTab === tab.id
                  ? "border-primary text-primary"
                  : "border-transparent text-muted-foreground hover:text-foreground hover:border-muted-foreground/30"
              )}
            >
              <tab.icon className="h-4 w-4" />
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab content */}
      <div>
        {activeTab === "auth" && <AuthLogsTab />}
        {activeTab === "audit" && <AuditLogsTab />}
        {activeTab === "conversations" && <ConversationStatsTab />}
        {activeTab === "files" && <FileStatsTab />}
      </div>
    </div>
  );
}
