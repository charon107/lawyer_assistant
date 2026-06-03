"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  Search,
  Loader2,
  AlertCircle,
  Plus,
  MessageSquare,
  FileText,
} from "lucide-react";
import { Button, Card, CardContent, Input, Label, Spinner, Textarea } from "@/components/ui";
import { MarkdownContent } from "@/components/chat";
import { useEmploymentChat } from "@/hooks/use-employment-chat";
import { employmentApi } from "@/lib/employment";
import { ROUTES } from "@/lib/constants";
import type { InvestigationDetail, LogEntry, InvestigationSource, InvestigationGap } from "@/types/employment";

const ENTRY_TYPE_LABEL: Record<string, string> = {
  interview: "访谈",
  document: "文档",
  "attorney-note": "律师笔记",
  gap: "缺口",
};

const SIGNIFICANCE_cls: Record<string, string> = {
  high: "border-red-300 bg-red-50 text-red-700",
  medium: "border-amber-300 bg-amber-50 text-amber-700",
  background: "border-muted bg-muted text-muted-foreground",
};

export default function InvestigationDetailPage() {
  const params = useParams<{ id: string }>();
  const id = params.id;

  const [detail, setDetail] = useState<InvestigationDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // WS-driven actions
  const { streamingText, finalOutput, status: wsStatus, error: wsError, runSkill } =
    useEmploymentChat();
  const [activeAction, setActiveAction] = useState<"query" | "memo" | "summary" | null>(null);
  const [queryPrompt, setQueryPrompt] = useState("");

  // Manual log entry form
  const [showAddEntry, setShowAddEntry] = useState(false);
  const [entrySummary, setEntrySummary] = useState("");
  const [entrySource, setEntrySource] = useState("");
  const [addingEntry, setAddingEntry] = useState(false);

  const fetchDetail = useCallback(() => {
    if (!id) return;
    let cancelled = false;
    setLoading(true);
    employmentApi
      .getInvestigation(id)
      .then((d) => {
        if (!cancelled) setDetail(d);
      })
      .catch((e) => {
        if (!cancelled) setError(e instanceof Error ? e.message : "加载失败");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [id]);

  useEffect(() => {
    const cleanup = fetchDetail();
    return cleanup;
  }, [fetchDetail]);

  const handleQuery = () => {
    if (!queryPrompt.trim() || !id) return;
    setActiveAction("query");
    runSkill({ action: "inv_query", investigation_id: id, prompt: queryPrompt });
  };

  const handleMemo = () => {
    if (!id) return;
    setActiveAction("memo");
    runSkill({ action: "inv_memo", investigation_id: id, prompt: "生成/更新调查备忘录" });
  };

  const handleSummary = () => {
    if (!id) return;
    setActiveAction("summary");
    runSkill({ action: "inv_summary", investigation_id: id, prompt: "生成调查摘要" });
  };

  const handleAddEntry = async () => {
    if (!id || !entrySummary.trim()) return;
    setAddingEntry(true);
    try {
      await employmentApi.addLogEntry(id, {
        entry_type: "interview",
        summary: entrySummary.trim(),
        source: entrySource.trim() || undefined,
      });
      setEntrySummary("");
      setEntrySource("");
      setShowAddEntry(false);
      fetchDetail();
    } catch {
      // keep form open
    } finally {
      setAddingEntry(false);
    }
  };

  const wsBusy = wsStatus === "connecting" || wsStatus === "running";

  return (
    <div className="mx-auto max-w-4xl px-4 py-10">
      <div className="mb-8">
        <Link
          href={ROUTES.EMPLOYMENT_INVESTIGATIONS}
          className="text-muted-foreground hover:text-foreground mb-4 inline-flex items-center gap-1.5 text-sm transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          返回调查列表
        </Link>
        <h1 className="mb-1 flex items-center gap-2 text-2xl font-bold">
          <Search className="text-brand h-6 w-6" />
          {detail?.investigation_name || "调查详情"}
        </h1>
        {detail && (
          <p className="text-muted-foreground text-sm">
            {detail.investigation_type || "未分类"}
            {detail.allegation && ` · ${detail.allegation}`}
            {detail.attorney_directed && " · 律师指导"}
            {` · ${detail.status}`}
          </p>
        )}
      </div>

      {loading && (
        <div className="flex items-center justify-center py-16">
          <Spinner className="text-brand h-6 w-6" />
        </div>
      )}

      {error && (
        <p className="border-destructive/30 bg-destructive/5 text-destructive flex items-center gap-1.5 rounded-lg border px-4 py-2.5 text-sm">
          <AlertCircle className="h-4 w-4" />
          {error}
        </p>
      )}

      {!loading && !error && detail && (
        <div className="flex flex-col gap-8">
          {/* Action bar */}
          <div className="flex flex-wrap items-center gap-2">
            <Button variant="outline" size="sm" onClick={handleMemo} disabled={wsBusy}>
              {wsBusy && activeAction === "memo" ? (
                <Loader2 className="mr-1.5 h-4 w-4 animate-spin" />
              ) : (
                <FileText className="mr-1.5 h-4 w-4" />
              )}
              生成备忘录
            </Button>
            <Button variant="outline" size="sm" onClick={handleSummary} disabled={wsBusy}>
              {wsBusy && activeAction === "summary" ? (
                <Loader2 className="mr-1.5 h-4 w-4 animate-spin" />
              ) : (
                <MessageSquare className="mr-1.5 h-4 w-4" />
              )}
              生成摘要
            </Button>
            <Button variant="outline" size="sm" onClick={() => setShowAddEntry(!showAddEntry)}>
              <Plus className="mr-1.5 h-4 w-4" />
              添加日志条目
            </Button>
          </div>

          {/* Manual log entry form */}
          {showAddEntry && (
            <Card>
              <CardContent className="flex flex-col gap-3 p-4">
                <div className="flex flex-col gap-1.5">
                  <Label htmlFor="entry-summary">条目摘要</Label>
                  <Textarea
                    id="entry-summary"
                    value={entrySummary}
                    onChange={(e) => setEntrySummary(e.target.value)}
                    rows={3}
                    placeholder="描述访谈/文档/事件内容"
                  />
                </div>
                <div className="flex flex-col gap-1.5">
                  <Label htmlFor="entry-source">来源（可选）</Label>
                  <Input
                    id="entry-source"
                    value={entrySource}
                    onChange={(e) => setEntrySource(e.target.value)}
                    placeholder="例如：HR 王某、财务报表"
                  />
                </div>
                <div className="flex justify-end gap-2">
                  <Button variant="ghost" size="sm" onClick={() => setShowAddEntry(false)}>
                    取消
                  </Button>
                  <Button size="sm" onClick={handleAddEntry} disabled={!entrySummary.trim() || addingEntry}>
                    {addingEntry && <Loader2 className="mr-1.5 h-4 w-4 animate-spin" />}
                    添加
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Query panel */}
          <Card>
            <CardContent className="flex flex-col gap-3 p-4">
              <p className="text-sm font-medium">调查查询</p>
              <div className="flex gap-2">
                <Input
                  value={queryPrompt}
                  onChange={(e) => setQueryPrompt(e.target.value)}
                  placeholder="例如：有哪些证据与指控矛盾？"
                  onKeyDown={(e) => e.key === "Enter" && handleQuery()}
                />
                <Button onClick={handleQuery} disabled={!queryPrompt.trim() || wsBusy} size="sm">
                  查询
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* WS output */}
          {wsError && (
            <p className="border-destructive/30 bg-destructive/5 text-destructive rounded-lg border px-4 py-2.5 text-sm">
              {wsError}
            </p>
          )}
          {(finalOutput || streamingText) && activeAction && (
            <Card>
              <CardContent className="prose-sm max-w-none p-6 text-sm leading-relaxed">
                <MarkdownContent content={finalOutput || streamingText} />
              </CardContent>
            </Card>
          )}

          {/* Sources */}
          {detail.sources.length > 0 && (
            <section>
              <h2 className="mb-3 text-sm font-semibold tracking-wide uppercase">
                来源清单（{detail.sources.length}）
              </h2>
              <div className="flex flex-col gap-2">
                {detail.sources.map((s) => (
                  <SourceRow key={s.id} source={s} />
                ))}
              </div>
            </section>
          )}

          {/* Log entries */}
          <section>
            <h2 className="mb-3 text-sm font-semibold tracking-wide uppercase">
              调查日志（{detail.log_entries.length}）
            </h2>
            {detail.log_entries.length === 0 ? (
              <p className="text-muted-foreground text-sm">暂无日志条目。</p>
            ) : (
              <div className="flex flex-col gap-3">
                {detail.log_entries.map((e) => (
                  <LogEntryRow key={e.id} entry={e} />
                ))}
              </div>
            )}
          </section>

          {/* Gaps */}
          {detail.gaps.length > 0 && (
            <section>
              <h2 className="mb-3 text-sm font-semibold tracking-wide uppercase">
                证据缺口（{detail.gaps.length}）
              </h2>
              <div className="flex flex-col gap-2">
                {detail.gaps.map((g) => (
                  <GapRow key={g.id} gap={g} />
                ))}
              </div>
            </section>
          )}

          {/* Memo */}
          {detail.memo && (
            <section>
              <h2 className="mb-3 text-sm font-semibold tracking-wide uppercase">调查备忘录</h2>
              <Card>
                <CardContent className="prose-sm max-w-none p-6 text-sm leading-relaxed">
                  <MarkdownContent content={detail.memo} />
                </CardContent>
              </Card>
            </section>
          )}
        </div>
      )}
    </div>
  );
}

function LogEntryRow({ entry }: { entry: LogEntry }) {
  return (
    <div className="rounded-lg border p-3">
      <div className="flex items-center gap-2 text-xs">
        <span className="font-medium">#{entry.entry_seq}</span>
        {entry.entry_type && (
          <span className="rounded-full border px-2 py-0.5">
            {ENTRY_TYPE_LABEL[entry.entry_type] || entry.entry_type}
          </span>
        )}
        {entry.significance && (
          <span className={`rounded-full border px-2 py-0.5 ${SIGNIFICANCE_cls[entry.significance] ?? ""}`}>
            {entry.significance}
          </span>
        )}
        {entry.source && <span className="text-muted-foreground">来源：{entry.source}</span>}
        {entry.date_of_event && (
          <time className="text-muted-foreground">
            {new Date(entry.date_of_event).toLocaleDateString("zh-CN")}
          </time>
        )}
      </div>
      {entry.summary && <p className="mt-1.5 text-sm">{entry.summary}</p>}
      {entry.quote && (
        <blockquote className="text-muted-foreground mt-1.5 border-l-2 pl-3 text-xs italic">
          {entry.quote}
        </blockquote>
      )}
    </div>
  );
}

function SourceRow({ source }: { source: InvestigationSource }) {
  return (
    <div className="flex items-center gap-3 rounded-lg border px-3 py-2">
      <span className="text-xs font-medium">#{source.source_seq}</span>
      <span className="flex-1 text-sm">{source.source}</span>
      <span
        className={`rounded-full border px-2 py-0.5 text-xs ${
          source.status === "complete"
            ? "border-emerald-300 bg-emerald-50 text-emerald-700"
            : source.status === "in-progress"
              ? "border-amber-300 bg-amber-50 text-amber-700"
              : "border-muted bg-muted text-muted-foreground"
        }`}
      >
        {source.status}
      </span>
      {source.notes && <span className="text-muted-foreground text-xs">{source.notes}</span>}
    </div>
  );
}

function GapRow({ gap }: { gap: InvestigationGap }) {
  return (
    <div className="rounded-lg border p-3">
      <div className="flex items-center gap-2 text-xs">
        <span className="font-medium">#{gap.gap_seq}</span>
        <span
          className={`rounded-full border px-2 py-0.5 ${
            gap.priority === "high"
              ? "border-red-300 bg-red-50 text-red-700"
              : gap.priority === "medium"
                ? "border-amber-300 bg-amber-50 text-amber-700"
                : "border-muted bg-muted text-muted-foreground"
          }`}
        >
          {gap.priority}
        </span>
        <span className="text-muted-foreground">{gap.status}</span>
      </div>
      <p className="mt-1.5 text-sm">{gap.description}</p>
    </div>
  );
}
