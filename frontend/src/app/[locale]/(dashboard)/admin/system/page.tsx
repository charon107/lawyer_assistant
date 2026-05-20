"use client";

import { useEffect, useState } from "react";
import { useAuthStore } from "@/stores";
import { useAdminLogs, type RagStatus } from "@/hooks/use-admin-logs";
import { cn } from "@/lib/utils";
import { CheckCircle2, XCircle, AlertCircle, RefreshCw, Activity, Database, Cpu, Server } from "lucide-react";

function StatusBadge({ ok, label }: { ok: boolean | null; label: string }) {
  if (ok === null) {
    return (
      <span className="flex items-center gap-1.5 text-muted-foreground text-sm">
        <AlertCircle className="h-4 w-4 text-yellow-500" />
        {label}
      </span>
    );
  }
  return (
    <span
      className={cn(
        "flex items-center gap-1.5 text-sm font-medium",
        ok ? "text-green-600" : "text-red-600"
      )}
    >
      {ok ? <CheckCircle2 className="h-4 w-4" /> : <XCircle className="h-4 w-4" />}
      {label}
    </span>
  );
}

function StatCard({
  icon: Icon,
  title,
  children,
}: {
  icon: React.ElementType;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-lg border bg-card p-5">
      <div className="flex items-center gap-2 mb-4">
        <Icon className="h-5 w-5 text-muted-foreground" />
        <h2 className="font-semibold text-base">{title}</h2>
      </div>
      {children}
    </div>
  );
}

export default function AdminSystemPage() {
  const { user } = useAuthStore();
  const { fetchRagStatus } = useAdminLogs();
  const [status, setStatus] = useState<RagStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [checkedAt, setCheckedAt] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    const data = await fetchRagStatus();
    setStatus(data);
    setCheckedAt(data?.checked_at ?? null);
    setLoading(false);
  };

  useEffect(() => {
    if (user?.role !== "admin") return;
    load();
  }, [user]); // eslint-disable-line react-hooks/exhaustive-deps

  if (user?.role !== "admin") {
    return (
      <div className="p-6 max-w-3xl mx-auto">
        <div className="text-center text-muted-foreground py-12">无权访问</div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-3xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">系统状态</h1>
          {checkedAt && (
            <p className="text-sm text-muted-foreground mt-0.5">
              检测时间：{new Date(checkedAt).toLocaleString("zh-CN")}
            </p>
          )}
        </div>
        <button
          onClick={load}
          disabled={loading}
          className="flex items-center gap-2 rounded-md border px-3 py-2 text-sm hover:bg-muted transition-colors disabled:opacity-50"
        >
          <RefreshCw className={cn("h-4 w-4", loading && "animate-spin")} />
          刷新
        </button>
      </div>

      {loading && !status && (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="rounded-lg border bg-card p-5 h-32 animate-pulse bg-muted/30" />
          ))}
        </div>
      )}

      {status && (
        <div className="space-y-4">
          {/* Qdrant */}
          <StatCard icon={Database} title="向量数据库 (Qdrant)">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground text-sm">连通性</span>
                <StatusBadge ok={status.qdrant.reachable} label={status.qdrant.reachable ? "可连接" : "无法连接"} />
              </div>
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground text-sm">集合 law_articles</span>
                <StatusBadge
                  ok={status.qdrant.collection_exists}
                  label={status.qdrant.collection_exists ? "已创建" : "不存在"}
                />
              </div>
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground text-sm">法律条文数量</span>
                <span className="text-sm font-mono font-semibold">
                  {status.qdrant.article_count.toLocaleString()}
                </span>
              </div>
            </div>
          </StatCard>

          {/* Embedding Model */}
          <StatCard icon={Cpu} title="嵌入模型">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground text-sm">加载状态</span>
                <StatusBadge
                  ok={status.embedding_model.loaded}
                  label={status.embedding_model.loaded ? "已加载" : "未加载"}
                />
              </div>
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground text-sm">模型名称</span>
                <span className="text-sm font-mono text-muted-foreground">
                  {status.embedding_model.model_name}
                </span>
              </div>
            </div>
          </StatCard>

          {/* Redis */}
          <StatCard icon={Server} title="Redis 缓存">
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground text-sm">连通性</span>
              <StatusBadge
                ok={status.redis.available}
                label={status.redis.available ? "可用" : "不可用（退回无缓存模式）"}
              />
            </div>
          </StatCard>

          {/* Overall health banner */}
          <div
            className={cn(
              "rounded-lg border p-4 flex items-center gap-3",
              status.qdrant.reachable && status.qdrant.collection_exists && status.qdrant.article_count > 0
                ? "border-green-200 bg-green-50 text-green-800 dark:border-green-800 dark:bg-green-950 dark:text-green-200"
                : "border-red-200 bg-red-50 text-red-800 dark:border-red-800 dark:bg-red-950 dark:text-red-200"
            )}
          >
            <Activity className="h-5 w-5 shrink-0" />
            <div>
              {status.qdrant.reachable && status.qdrant.collection_exists && status.qdrant.article_count > 0 ? (
                <p className="font-medium">RAG 管道正常运行</p>
              ) : (
                <>
                  <p className="font-medium">RAG 管道存在问题</p>
                  <p className="text-sm mt-0.5">
                    {!status.qdrant.reachable && "Qdrant 无法连接。"}
                    {status.qdrant.reachable && !status.qdrant.collection_exists && "集合 law_articles 不存在，需要重新索引。"}
                    {status.qdrant.reachable && status.qdrant.collection_exists && status.qdrant.article_count === 0 && "集合为空，请运行索引脚本导入法律条文。"}
                  </p>
                </>
              )}
            </div>
          </div>
        </div>
      )}

      {!loading && !status && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-5 text-red-800 dark:border-red-800 dark:bg-red-950 dark:text-red-200">
          <p className="font-medium">无法获取系统状态</p>
          <p className="text-sm mt-1">请检查后端服务是否正常运行。</p>
        </div>
      )}
    </div>
  );
}
