"use client";

import { useState } from "react";
import Link from "next/link";
import { AlertCircle, ArrowLeft, Loader2, Radar } from "lucide-react";
import { Button, Card, CardContent, Label, Textarea } from "@/components/ui";
import { MarkdownContent } from "@/components/chat";
import { usePrivacyChat } from "@/hooks/use-privacy-chat";
import { ROUTES } from "@/lib/constants";
import { cn } from "@/lib/utils";

type Mode = "sweep" | "query";

const SWEEP_PROMPT =
  "请扫描自上次扫描以来保存的所有分析产出（PIA / DPA / 分诊结果），对照处理规则承诺找出漂移，区分必须更新与建议更新，并起草建议语言。";

export default function PrivacyPolicyMonitorPage() {
  const { streamingText, finalOutput, status, error, runSkill, reset } = usePrivacyChat();
  const [mode, setMode] = useState<Mode>("sweep");
  const [query, setQuery] = useState("");

  const isBusy = status === "connecting" || status === "running";

  const handleStart = () => {
    if (mode === "sweep") {
      runSkill({ action: "policy_sweep", prompt: SWEEP_PROMPT });
    } else {
      if (!query.trim()) return;
      runSkill({ action: "policy_query", prompt: query });
    }
  };

  const handleReset = () => {
    reset();
    setQuery("");
  };

  return (
    <div className="mx-auto max-w-4xl px-4 py-10">
      <div className="mb-8">
        <Link
          href={ROUTES.PRIVACY}
          className="text-muted-foreground hover:text-foreground mb-4 inline-flex items-center gap-1.5 text-sm transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          返回个人信息保护
        </Link>
        <h1 className="mb-1 flex items-center gap-2 text-2xl font-bold">
          <Radar className="text-brand h-6 w-6" />
          处理规则监控
        </h1>
        <p className="text-muted-foreground">
          扫描已保存产出找出处理规则漂移，或对拟议的新实践做直接查询（多表面：网站政策 / CMP / App 标签 / 产品内同意 / 行业通知）。
        </p>
      </div>

      {status === "idle" ? (
        <div className="flex flex-col gap-5">
          <div className="flex flex-col gap-1.5">
            <Label>模式</Label>
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                onClick={() => setMode("sweep")}
                className={cn(
                  "rounded-md border px-3 py-1.5 text-sm transition-colors",
                  mode === "sweep"
                    ? "border-brand bg-brand/10 text-brand font-medium"
                    : "text-muted-foreground hover:bg-muted",
                )}
              >
                扫描漂移
              </button>
              <button
                type="button"
                onClick={() => setMode("query")}
                className={cn(
                  "rounded-md border px-3 py-1.5 text-sm transition-colors",
                  mode === "query"
                    ? "border-brand bg-brand/10 text-brand font-medium"
                    : "text-muted-foreground hover:bg-muted",
                )}
              >
                直接查询
              </button>
            </div>
          </div>

          {mode === "sweep" ? (
            <p className="text-muted-foreground rounded-lg border border-dashed px-4 py-3 text-sm">
              扫描模式将比对自上次扫描以来的分析产出与处理规则承诺，找出必须 / 建议更新，并更新上次扫描日期。
            </p>
          ) : (
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="policy-query">拟议的新实践</Label>
              <Textarea
                id="policy-query"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                rows={5}
                placeholder="例如：我们想开始用行为数据个性化引导邮件……（数据 / 目的 / 供应商 / 主体 / 是否新披露）"
              />
            </div>
          )}

          <div className="flex justify-end">
            <Button onClick={handleStart} disabled={mode === "query" && !query.trim()}>
              <Radar className="mr-1.5 h-4 w-4" />
              {mode === "sweep" ? "运行扫描" : "查询"}
            </Button>
          </div>
        </div>
      ) : (
        <div className="flex flex-col gap-6">
          <div className="flex items-center justify-between">
            <div className="text-muted-foreground flex items-center gap-2 text-sm">
              {isBusy && <Loader2 className="text-brand h-4 w-4 animate-spin" />}
              {status === "connecting" && "正在连接……"}
              {status === "running" && "AI 正在分析……"}
              {status === "done" && "完成"}
              {status === "error" && (
                <span className="text-destructive flex items-center gap-1.5">
                  <AlertCircle className="h-4 w-4" />
                  失败
                </span>
              )}
            </div>
            {!isBusy && (
              <Button variant="ghost" size="sm" onClick={handleReset}>
                新的检查
              </Button>
            )}
          </div>

          {error && (
            <p className="border-destructive/30 bg-destructive/5 text-destructive rounded-lg border px-4 py-2.5 text-sm">
              {error}
            </p>
          )}

          {(finalOutput || streamingText) && (
            <Card>
              <CardContent className="prose-sm max-w-none p-6 text-sm leading-relaxed">
                <MarkdownContent content={finalOutput || streamingText} />
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}
