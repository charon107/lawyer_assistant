"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { useDocumentReview } from "@/hooks/use-document-review";
import { ReviewProgressBar } from "@/components/review/progress-bar";
import { FindingCard } from "@/components/review/finding-card";
import { ChatWidget } from "@/components/chat/chat-widget";
import { Button, Skeleton } from "@/components/ui";
import { FileSearch, Download, AlertTriangle } from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "/api/v1";

export default function ReviewDetailPage() {
  const params = useParams();
  const reviewId = params.id as string;
  const review = useDocumentReview();
  const [activeTab, setActiveTab] = useState("overview");
  const [reportMd, setReportMd] = useState("");
  const [isLoading, setIsLoading] = useState(true);

  // Fetch full result when page loads, and connect WS if review is still in progress
  useEffect(() => {
    if (reviewId) {
      review.fetchFullResult(API_BASE, reviewId).then((data) => {
        setIsLoading(false);
        if (data && data.status !== "complete" && data.status !== "error") {
          // Review is still in progress — connect WebSocket for real-time updates
          review.connectWS(reviewId, API_BASE);
        }
      });
    }
  }, [reviewId]);

  useEffect(() => {
    if (review.status === "complete" && !review.reportMarkdown) {
      review.fetchReport(API_BASE).then(setReportMd);
    }
  }, [review.status, review.reportMarkdown]);

  const handleChapterConfirm = () => {
    review.confirmChapters(review.chapters, API_BASE);
  };

  const highCount = review.chapterReviews.reduce(
    (sum, r) => sum + r.findings.filter((f: any) => f.level === "高风险").length, 0
  );
  const midCount = review.chapterReviews.reduce(
    (sum, r) => sum + r.findings.filter((f: any) => f.level === "中风险").length, 0
  );
  const lowCount = review.chapterReviews.reduce(
    (sum, r) => sum + r.findings.filter((f: any) => f.level === "低风险").length, 0
  );

  const FACT_LABELS: Record<string, string> = {
    party_a: "甲方",
    party_b: "乙方",
    party_a_role: "甲方角色",
    party_b_role: "乙方角色",
    contract_subject: "合同标的",
    contract_value: "合同金额",
    contract_value_raw: "合同金额原文",
    currency: "币种",
    payment_terms: "付款条件",
    payment_schedule: "付款安排",
    contract_start_date: "合同起始日期",
    contract_end_date: "合同终止日期",
    contract_term: "合同期限",
    delivery_date: "交付日期",
    delivery_location: "交付地点",
    governing_law: "适用法律",
    dispute_resolution: "争议解决",
    confidentiality_term: "保密期限",
    penalty_clause: "违约金条款",
    warranty_period: "质保期",
    renewal_terms: "续约条件",
    termination_conditions: "终止条件",
    special_conditions: "特别约定",
    // LPA fields
    fund_name: "基金名称",
    fund_type: "基金类型",
    domicile: "注册地",
    gp_name: "普通合伙人",
    manager_name: "管理人",
    gp_is_manager: "GP是否兼任管理人",
    committed_capital: "认缴出资总额",
    management_fee_rate: "管理费率",
    management_fee_basis: "管理费计算基数",
    hurdle_rate: "优先回报率",
    gp_carry: "GP业绩报酬",
    investment_period_years: "投资期",
    exit_period_years: "退出期",
    extension_period_years: "延长期",
    lpac_approval_threshold: "LPAC审批门槛",
    lp_min_commitment: "LP最低出资",
    gp_removal_for_cause: "GP有因除名",
    gp_removal_nofault_threshold: "GP无过错除名比例",
    key_persons: "关键人士",
  };

  const tabs = [
    { key: "overview", label: "概览" },
    { key: "facts", label: "合同摘要" },
    { key: "findings", label: `逐章发现 (${review.chapterReviews.length})` },
    { key: "cross", label: "跨章检查" },
    { key: "report", label: "完整报告" },
  ];

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <Skeleton className="h-8 w-48 mb-2" />
          <Skeleton className="h-4 w-64" />
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-24 rounded-lg" />
          ))}
        </div>
        <Skeleton className="h-10 w-full" />
        <div className="space-y-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-32 rounded-lg" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <FileSearch className="h-6 w-6 text-brand" />
          文件审查报告
        </h1>
        <p className="text-sm text-muted-foreground mt-1">Session: {reviewId}</p>
      </div>

      {/* Progress (during review) */}
      {review.status !== "complete" && review.status !== "error" && (
        <div className="p-6 border border-border rounded-xl" aria-live="polite">
          <ReviewProgressBar
            stage={review.status}
            progress={review.progress}
            message={review.progressMsg}
          />

          {/* Chapter confirmation */}
          {review.awaitingChapters && (
            <div className="mt-6 p-4 border border-brand/30 bg-brand/5 rounded-lg">
              <p className="text-sm font-medium mb-3">
                已识别 {review.chapters.length} 个章节，请确认章节边界后继续：
              </p>
              <div className="max-h-60 overflow-y-auto space-y-1 mb-4">
                {review.chapters.map((ch: any, i: number) => (
                  <div key={i} className="text-sm text-muted-foreground flex justify-between">
                    <span>{ch.title}</span>
                    <span className="text-muted-foreground/70">{ch.char_count} 字</span>
                  </div>
                ))}
              </div>
              <Button onClick={handleChapterConfirm}>
                确认并继续审查
              </Button>
            </div>
          )}
        </div>
      )}

      {/* Error state */}
      {review.status === "error" && (
        <div className="border border-destructive/30 bg-destructive/5 rounded-xl p-6 text-center" aria-live="assertive">
          <AlertTriangle className="h-8 w-8 text-destructive mx-auto mb-2" />
          <p className="text-destructive font-medium mb-2">审查出错</p>
          <p className="text-sm text-muted-foreground">{review.error}</p>
        </div>
      )}

      {/* Results (when complete) */}
      {review.status === "complete" && (
        <>
          {/* Risk summary */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4" aria-label="风险统计">
            <div className="border border-destructive/20 bg-destructive/5 rounded-lg p-4 text-center">
              <div className="text-2xl font-bold text-destructive">{highCount}</div>
              <div className="text-xs text-muted-foreground">高风险</div>
            </div>
            <div className="border border-warning/20 bg-warning/5 rounded-lg p-4 text-center">
              <div className="text-2xl font-bold text-warning">{midCount}</div>
              <div className="text-xs text-muted-foreground">中风险</div>
            </div>
            <div className="border border-warning/20 bg-warning/5 rounded-lg p-4 text-center">
              <div className="text-2xl font-bold text-warning">{lowCount}</div>
              <div className="text-xs text-muted-foreground">低风险</div>
            </div>
            <div className="border border-border bg-card rounded-lg p-4 text-center">
              <div className="text-2xl font-bold text-foreground">{review.chapters.length}</div>
              <div className="text-xs text-muted-foreground">审查章节</div>
            </div>
          </div>

          {/* Tabs */}
          <div role="tablist" className="flex gap-1 border-b border-border">
            {tabs.map((tab) => (
              <button
                key={tab.key}
                role="tab"
                aria-selected={activeTab === tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`px-4 py-2 text-sm rounded-t-lg transition-colors
                  ${activeTab === tab.key
                    ? "bg-card text-foreground font-medium border border-border border-b-white dark:border-b-card"
                    : "text-muted-foreground hover:text-foreground hover:bg-muted"
                  }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Tab: Overview */}
          {activeTab === "overview" && (
            <div role="tabpanel" className="space-y-4">
              <h2 className="text-lg font-semibold">Top 风险发现</h2>
              {review.chapterReviews
                .flatMap((r) => r.findings)
                .filter((f: any) => f.level === "高风险" || f.level === "中风险")
                .slice(0, 10)
                .map((f: any, i: number) => (
                  <FindingCard key={i} finding={f} />
                ))}
            </div>
          )}

          {/* Tab: Facts */}
          {activeTab === "facts" && (
            <div role="tabpanel" className="overflow-x-auto">
              {review.facts ? (
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border">
                      <th className="text-left py-2 px-3 text-muted-foreground">项目</th>
                      <th className="text-left py-2 px-3 text-muted-foreground">内容</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(review.facts).map(([key, val]) => (
                      <tr key={key} className="border-b border-border/50">
                        <td className="py-2 px-3 text-muted-foreground">{FACT_LABELS[key] || key}</td>
                        <td className="py-2 px-3">
                          {typeof val === "boolean" ? (val ? "是" : "否") :
                           Array.isArray(val) ? val.join(", ") :
                           typeof val === "number" ? val :
                           String(val)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <p className="text-muted-foreground">未提取到结构化事实</p>
              )}
            </div>
          )}

          {/* Tab: Findings */}
          {activeTab === "findings" && (
            <div role="tabpanel" className="space-y-6">
              {review.chapterReviews.map((review: any, i: number) => (
                <div key={i}>
                  <h3 className="text-md font-medium mb-3">
                    {review.chapter}
                    <span className={`ml-2 text-xs px-2 py-0.5 rounded ${
                      review.complexity === "complex"
                        ? "bg-brand-muted text-brand"
                        : "bg-muted text-muted-foreground"
                    }`}>
                      {review.complexity === "complex" ? "深度审查" : "快速扫描"}
                    </span>
                  </h3>
                  {review.findings.length === 0 ? (
                    <p className="text-sm text-success mb-4">未发现风险</p>
                  ) : (
                    <div className="space-y-3">
                      {review.findings.map((f: any, j: number) => (
                        <FindingCard key={j} finding={f} />
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Tab: Cross-check */}
          {activeTab === "cross" && (
            <div role="tabpanel" className="space-y-4">
              {review.crossCheck ? (
                <>
                  {review.crossCheck.contradictions?.length > 0 && (
                    <div>
                      <h3 className="text-md font-medium mb-3 text-destructive">跨章矛盾</h3>
                      {review.crossCheck.contradictions.map((c: any, i: number) => (
                        <div key={i} className="border border-destructive/20 bg-destructive/5 rounded-lg p-4 mb-2">
                          <p className="text-sm font-medium">[{c.level}] {c.id} — {c.description}</p>
                          <p className="text-xs text-muted-foreground mt-1">{c.resolution}</p>
                        </div>
                      ))}
                    </div>
                  )}
                  {review.crossCheck.consistency_issues?.length > 0 && (
                    <div>
                      <h3 className="text-md font-medium mb-3 text-warning">一致性问题</h3>
                      {review.crossCheck.consistency_issues.map((ci: any, i: number) => (
                        <div key={i} className="border border-warning/20 bg-warning/5 rounded-lg p-4 mb-2">
                          <p className="text-sm font-medium">[{ci.level}] {ci.id}</p>
                          <p className="text-xs text-muted-foreground mt-1">{ci.description}</p>
                        </div>
                      ))}
                    </div>
                  )}
                  {review.crossCheck.missing_items?.length > 0 && (
                    <div>
                      <h3 className="text-md font-medium mb-3 text-warning">建议补充条款</h3>
                      {review.crossCheck.missing_items.map((mi: any, i: number) => (
                        <div key={i} className="border border-warning/20 bg-warning/5 rounded-lg p-4 mb-2">
                          <p className="text-sm font-medium">[{mi.severity}] {mi.id} — {mi.item}</p>
                          <p className="text-xs text-muted-foreground mt-1">{mi.suggestion}</p>
                        </div>
                      ))}
                    </div>
                  )}
                  {!review.crossCheck.contradictions?.length &&
                   !review.crossCheck.consistency_issues?.length &&
                   !review.crossCheck.missing_items?.length && (
                    <p className="text-success">跨章检查未发现特别问题</p>
                  )}
                </>
              ) : (
                <p className="text-muted-foreground">交叉检查结果尚未生成</p>
              )}
            </div>
          )}

          {/* Tab: Full Report */}
          {activeTab === "report" && (
            <div role="tabpanel">
              <Button
                variant="outline"
                onClick={() => {
                  if (reportMd) {
                    const blob = new Blob([reportMd], { type: "text/markdown" });
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement("a");
                    a.href = url;
                    a.download = `review_${reviewId}.md`;
                    a.click();
                    URL.revokeObjectURL(url);
                  }
                }}
                className="mb-4"
              >
                <Download className="h-4 w-4 mr-2" />
                下载 Markdown 报告
              </Button>
              {reportMd ? (
                <pre className="text-xs text-muted-foreground whitespace-pre-wrap bg-card border border-border p-6 rounded-lg max-h-[600px] overflow-y-auto">
                  {reportMd}
                </pre>
              ) : (
                <p className="text-muted-foreground">加载报告中...</p>
              )}
            </div>
          )}
        </>
      )}

      {/* Chat Widget (bottom-right) */}
      <ChatWidget
        reviewId={reviewId}
        apiBase={API_BASE}
        enabled={review.status === "complete"}
      />
    </div>
  );
}
