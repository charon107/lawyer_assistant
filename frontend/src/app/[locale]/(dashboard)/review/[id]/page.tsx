"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { useLPAReview } from "@/hooks/use-lpa-review";
import { ReviewProgressBar } from "@/components/review/progress-bar";
import { FindingCard } from "@/components/review/finding-card";
import { ChatWidget } from "@/components/chat/chat-widget";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "/api/v1";

export default function ReviewDetailPage() {
  const params = useParams();
  const reviewId = params.id as string;
  const review = useLPAReview();
  const [activeTab, setActiveTab] = useState("overview");
  const [reportMd, setReportMd] = useState("");

  // Fetch full result when page loads (review might already be complete)
  useEffect(() => {
    if (reviewId) {
      review.fetchFullResult(API_BASE);
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

  const tabs = [
    { key: "overview", label: "概览" },
    { key: "facts", label: "关键事实" },
    { key: "findings", label: `逐章发现 (${review.chapterReviews.length})` },
    { key: "cross", label: "跨章检查" },
    { key: "report", label: "完整报告" },
  ];

  return (
    <div className="max-w-5xl mx-auto py-8 px-4">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold">&#x1F50D; LPA 审查报告</h1>
        <p className="text-sm text-zinc-500 mt-1">Session: {reviewId}</p>
      </div>

      {/* Progress (during review) */}
      {review.status !== "complete" && review.status !== "error" && (
        <div className="mb-8 p-6 border border-zinc-800 rounded-xl">
          <ReviewProgressBar
            stage={review.status}
            progress={review.progress}
            message={review.progressMsg}
          />

          {/* Chapter confirmation */}
          {review.awaitingChapters && (
            <div className="mt-6 p-4 border border-blue-500/30 bg-blue-500/5 rounded-lg">
              <p className="text-sm font-medium mb-3">
                已识别 {review.chapters.length} 个章节，请确认章节边界后继续：
              </p>
              <div className="max-h-60 overflow-y-auto space-y-1 mb-4">
                {review.chapters.map((ch: any, i: number) => (
                  <div key={i} className="text-sm text-zinc-400 flex justify-between">
                    <span>{ch.title}</span>
                    <span className="text-zinc-600">{ch.char_count} 字</span>
                  </div>
                ))}
              </div>
              <button
                onClick={handleChapterConfirm}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-500"
              >
                确认并继续审查
              </button>
            </div>
          )}
        </div>
      )}

      {/* Error state */}
      {review.status === "error" && (
        <div className="border border-red-500/50 bg-red-500/10 rounded-xl p-6 text-center mb-8">
          <p className="text-red-400 mb-2">审查出错</p>
          <p className="text-sm text-zinc-400">{review.error}</p>
        </div>
      )}

      {/* Results (when complete) */}
      {review.status === "complete" && (
        <>
          {/* Risk summary */}
          <div className="grid grid-cols-4 gap-4 mb-8">
            <div className="border border-red-500/30 bg-red-500/5 rounded-lg p-4 text-center">
              <div className="text-2xl font-bold text-red-400">{highCount}</div>
              <div className="text-xs text-zinc-500">高风险</div>
            </div>
            <div className="border border-orange-500/30 bg-orange-500/5 rounded-lg p-4 text-center">
              <div className="text-2xl font-bold text-orange-400">{midCount}</div>
              <div className="text-xs text-zinc-500">中风险</div>
            </div>
            <div className="border border-yellow-500/30 bg-yellow-500/5 rounded-lg p-4 text-center">
              <div className="text-2xl font-bold text-yellow-400">{lowCount}</div>
              <div className="text-xs text-zinc-500">低风险</div>
            </div>
            <div className="border border-zinc-700 bg-zinc-900 rounded-lg p-4 text-center">
              <div className="text-2xl font-bold text-zinc-300">{review.chapters.length}</div>
              <div className="text-xs text-zinc-500">审查章节</div>
            </div>
          </div>

          {/* Tabs */}
          <div className="flex gap-1 border-b border-zinc-800 mb-6">
            {tabs.map((tab) => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`px-4 py-2 text-sm rounded-t-lg transition-colors
                  ${activeTab === tab.key
                    ? "bg-zinc-800 text-white"
                    : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900"
                  }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Tab: Overview */}
          {activeTab === "overview" && (
            <div className="space-y-4">
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
            <div className="overflow-x-auto">
              {review.facts ? (
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-zinc-800">
                      <th className="text-left py-2 px-3 text-zinc-400">项目</th>
                      <th className="text-left py-2 px-3 text-zinc-400">内容</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(review.facts).map(([key, val]) => (
                      <tr key={key} className="border-b border-zinc-900">
                        <td className="py-2 px-3 text-zinc-500 font-mono text-xs">{key}</td>
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
                <p className="text-zinc-500">未提取到结构化事实</p>
              )}
            </div>
          )}

          {/* Tab: Findings */}
          {activeTab === "findings" && (
            <div className="space-y-6">
              {review.chapterReviews.map((review: any, i: number) => (
                <div key={i}>
                  <h3 className="text-md font-medium mb-3">
                    {review.chapter}
                    <span className={`ml-2 text-xs px-2 py-0.5 rounded ${
                      review.complexity === "complex"
                        ? "bg-purple-500/20 text-purple-400"
                        : "bg-zinc-700 text-zinc-400"
                    }`}>
                      {review.complexity === "complex" ? "深度审查" : "快速扫描"}
                    </span>
                  </h3>
                  {review.findings.length === 0 ? (
                    <p className="text-sm text-green-400 mb-4">未发现风险</p>
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
            <div className="space-y-4">
              {review.crossCheck ? (
                <>
                  {review.crossCheck.contradictions?.length > 0 && (
                    <div>
                      <h3 className="text-md font-medium mb-3 text-red-400">跨章矛盾</h3>
                      {review.crossCheck.contradictions.map((c: any, i: number) => (
                        <div key={i} className="border border-red-500/20 bg-red-500/5 rounded-lg p-4 mb-2">
                          <p className="text-sm font-medium">[{c.level}] {c.id} — {c.description}</p>
                          <p className="text-xs text-zinc-500 mt-1">{c.resolution}</p>
                        </div>
                      ))}
                    </div>
                  )}
                  {review.crossCheck.consistency_issues?.length > 0 && (
                    <div>
                      <h3 className="text-md font-medium mb-3 text-orange-400">一致性问题</h3>
                      {review.crossCheck.consistency_issues.map((ci: any, i: number) => (
                        <div key={i} className="border border-orange-500/20 bg-orange-500/5 rounded-lg p-4 mb-2">
                          <p className="text-sm font-medium">[{ci.level}] {ci.id}</p>
                          <p className="text-xs text-zinc-400 mt-1">{ci.description}</p>
                        </div>
                      ))}
                    </div>
                  )}
                  {review.crossCheck.missing_items?.length > 0 && (
                    <div>
                      <h3 className="text-md font-medium mb-3 text-yellow-400">建议补充条款</h3>
                      {review.crossCheck.missing_items.map((mi: any, i: number) => (
                        <div key={i} className="border border-yellow-500/20 bg-yellow-500/5 rounded-lg p-4 mb-2">
                          <p className="text-sm font-medium">[{mi.severity}] {mi.id} — {mi.item}</p>
                          <p className="text-xs text-zinc-500 mt-1">{mi.suggestion}</p>
                        </div>
                      ))}
                    </div>
                  )}
                  {!review.crossCheck.contradictions?.length &&
                   !review.crossCheck.consistency_issues?.length &&
                   !review.crossCheck.missing_items?.length && (
                    <p className="text-green-400">跨章检查未发现特别问题</p>
                  )}
                </>
              ) : (
                <p className="text-zinc-500">交叉检查结果尚未生成</p>
              )}
            </div>
          )}

          {/* Tab: Full Report */}
          {activeTab === "report" && (
            <div>
              <button
                onClick={() => {
                  if (reportMd) {
                    const blob = new Blob([reportMd], { type: "text/markdown" });
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement("a");
                    a.href = url;
                    a.download = `lpa_review_${reviewId}.md`;
                    a.click();
                    URL.revokeObjectURL(url);
                  }
                }}
                className="mb-4 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-500"
              >
                &#x1F4E5; 下载 Markdown 报告
              </button>
              {reportMd ? (
                <pre className="text-xs text-zinc-400 whitespace-pre-wrap bg-zinc-900 p-6 rounded-lg max-h-[600px] overflow-y-auto">
                  {reportMd}
                </pre>
              ) : (
                <p className="text-zinc-500">加载报告中...</p>
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
