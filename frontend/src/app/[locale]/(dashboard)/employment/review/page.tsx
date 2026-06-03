"use client";

import { useState } from "react";
import Link from "next/link";
import { ArrowLeft, FileSearch, Loader2, AlertCircle } from "lucide-react";
import { Button, Card, CardContent, Input, Label, Textarea } from "@/components/ui";
import { MarkdownContent } from "@/components/chat";
import { ReviewTypeSelector } from "@/components/employment";
import { useEmploymentChat } from "@/hooks/use-employment-chat";
import { ROUTES } from "@/lib/constants";
import type { ReviewType } from "@/types/employment";

export default function EmploymentReviewPage() {
  const { streamingText, finalOutput, status, error, runSkill, reset } =
    useEmploymentChat();

  const [reviewType, setReviewType] = useState<ReviewType>("hiring");
  const [employeeName, setEmployeeName] = useState("");
  const [position, setPosition] = useState("");
  const [jurisdiction, setJurisdiction] = useState("");
  const [description, setDescription] = useState("");

  const isBusy = status === "connecting" || status === "running";

  const handleStart = () => {
    if (!description.trim()) return;
    runSkill({
      action: reviewType === "worker_classification" ? "classification" : reviewType,
      prompt: [
        employeeName && `员工：${employeeName}`,
        position && `岗位：${position}`,
        jurisdiction && `管辖地：${jurisdiction}`,
        description,
      ]
        .filter(Boolean)
        .join("\n"),
    });
  };

  const handleReset = () => {
    reset();
    setEmployeeName("");
    setPosition("");
    setJurisdiction("");
    setDescription("");
    setReviewType("hiring");
  };

  return (
    <div className="mx-auto max-w-4xl px-4 py-10">
      <div className="mb-8">
        <Link
          href={ROUTES.EMPLOYMENT}
          className="text-muted-foreground hover:text-foreground mb-4 inline-flex items-center gap-1.5 text-sm transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          返回劳动用工
        </Link>
        <h1 className="mb-1 flex items-center gap-2 text-2xl font-bold">
          <FileSearch className="text-brand h-6 w-6" />
          用工审查
        </h1>
        <p className="text-muted-foreground">
          选择审查类型，描述情况，AI 将依据劳动合同法及管辖地规则进行分析。
        </p>
      </div>

      {status === "idle" ? (
        <div className="flex flex-col gap-5">
          <ReviewTypeSelector value={reviewType} onChange={setReviewType} />

          <div className="grid gap-4 sm:grid-cols-3">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="emp-name">员工姓名（可选）</Label>
              <Input
                id="emp-name"
                value={employeeName}
                onChange={(e) => setEmployeeName(e.target.value)}
                placeholder="例如：张某"
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="emp-position">岗位（可选）</Label>
              <Input
                id="emp-position"
                value={position}
                onChange={(e) => setPosition(e.target.value)}
                placeholder="例如：产品经理"
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="emp-jurisdiction">管辖地（可选）</Label>
              <Input
                id="emp-jurisdiction"
                value={jurisdiction}
                onChange={(e) => setJurisdiction(e.target.value)}
                placeholder="例如：北京"
              />
            </div>
          </div>

          <div className="flex flex-col gap-1.5">
            <Label htmlFor="emp-desc">情况描述</Label>
            <Textarea
              id="emp-desc"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={6}
              placeholder={
                reviewType === "termination"
                  ? "描述解除原因、员工情况、工作年限等……"
                  : reviewType === "hiring"
                    ? "描述拟录用岗位、用工形式、合同期限等……"
                    : "描述需要审查的情况……"
              }
            />
          </div>

          <div className="flex justify-end">
            <Button onClick={handleStart} disabled={!description.trim()}>
              <FileSearch className="mr-1.5 h-4 w-4" />
              开始审查
            </Button>
          </div>
        </div>
      ) : (
        <div className="flex flex-col gap-6">
          {/* Status banner */}
          <div className="flex items-center justify-between">
            <div className="text-muted-foreground flex items-center gap-2 text-sm">
              {isBusy && <Loader2 className="text-brand h-4 w-4 animate-spin" />}
              {status === "connecting" && "正在连接……"}
              {status === "running" && "AI 正在审查……"}
              {status === "done" && "审查完成"}
              {status === "error" && (
                <span className="text-destructive flex items-center gap-1.5">
                  <AlertCircle className="h-4 w-4" />
                  审查失败
                </span>
              )}
            </div>
            {!isBusy && (
              <Button variant="ghost" size="sm" onClick={handleReset}>
                新的审查
              </Button>
            )}
          </div>

          {error && (
            <p className="border-destructive/30 bg-destructive/5 text-destructive rounded-lg border px-4 py-2.5 text-sm">
              {error}
            </p>
          )}

          {/* Streamed output */}
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
