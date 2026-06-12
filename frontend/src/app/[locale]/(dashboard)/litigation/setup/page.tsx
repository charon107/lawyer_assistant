"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button, Card, CardContent, Input, Label, Spinner, Textarea } from "@/components/ui";
import { ROUTES } from "@/lib/constants";
import { litigationApi } from "@/lib/litigation";
import type { ColdStartResponse } from "@/types/litigation";
import { ArrowLeft, ArrowRight, Check, Scale } from "lucide-react";

const STEP_LABELS = [
  "执业角色与当事人角色",
  "公司画像与风险校准",
  "争议画像",
  "文书风格与输出",
  "确认生成",
];

export default function LitigationSetupPage() {
  const router = useRouter();
  const [response, setResponse] = useState<ColdStartResponse | null>(null);
  const [quickMode, setQuickMode] = useState(false);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const step = response?.step ?? 0;
  const progress = response?.progress ?? 0;

  async function submit(stepNum: number) {
    setLoading(true);
    setError(null);
    try {
      const r = await litigationApi.submitSetup({
        step: stepNum,
        answers: { ...answers },
        quick_mode: quickMode,
      });
      setResponse(r);
      setAnswers({});
      if (r.completed) {
        router.push(ROUTES.LITIGATION);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "提交失败");
    } finally {
      setLoading(false);
    }
  }

  // Initialize
  useState(() => {
    (async () => {
      try {
        const r = await litigationApi.getSetupStatus();
        setResponse(r);
        setQuickMode(!!r.partial_config?.quick_mode);
      } catch { /* empty */ }
    })();
  });

  if (!response || response.completed) {
    return (
      <div className="mx-auto max-w-lg px-4 py-20 text-center">
        <Spinner className="text-brand mx-auto h-6 w-6" />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-lg px-4 py-10">
      <div className="mb-6 flex items-center gap-3">
        <Scale className="text-brand h-5 w-5" />
        <h1 className="text-xl font-bold">争议解决 — 冷启动设置</h1>
      </div>

      {/* Progress */}
      <div className="mb-6">
        <div className="bg-muted h-1.5 rounded-full">
          <div
            className="bg-brand h-1.5 rounded-full transition-all"
            style={{ width: `${Math.round(progress * 100)}%` }}
          />
        </div>
        <p className="text-muted-foreground mt-2 text-xs">
          第 {step + 1}/{quickMode ? 3 : 5} 步 — {STEP_LABELS[step]}
          {quickMode && "（快速模式）"}
        </p>
      </div>

      {error && (
        <p className="border-destructive/30 bg-destructive/5 text-destructive mb-4 rounded-lg border px-4 py-2 text-sm">
          {error}
        </p>
      )}

      <Card>
        <CardContent className="space-y-4 p-6">
          {step === 0 && (
            <>
              <div className="space-y-2">
                <Label htmlFor="role">使用者角色</Label>
                <select
                  id="role"
                  className="border-input bg-background w-full rounded-lg border px-3 py-2 text-sm"
                  value={answers.user_role || ""}
                  onChange={(e) => setAnswers((a) => ({ ...a, user_role: e.target.value }))}
                >
                  <option value="">请选择...</option>
                  <option value="lawyer">执业律师 / 法律专业人士</option>
                  <option value="non_lawyer_with_counsel">非律师（有律师支持）</option>
                  <option value="non_lawyer_without">非律师（无律师支持）</option>
                </select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="practiceRole">执业角色</Label>
                <select
                  id="practiceRole"
                  className="border-input bg-background w-full rounded-lg border px-3 py-2 text-sm"
                  value={answers.practice_role || ""}
                  onChange={(e) => setAnswers((a) => ({ ...a, practice_role: e.target.value }))}
                >
                  <option value="">请选择...</option>
                  <option value="企业法务">企业法务</option>
                  <option value="律所律师">律所律师</option>
                  <option value="独立执业">独立执业</option>
                  <option value="其他">其他</option>
                </select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="partyRole">当事人默认角色</Label>
                <select
                  id="partyRole"
                  className="border-input bg-background w-full rounded-lg border px-3 py-2 text-sm"
                  value={answers.party_role || ""}
                  onChange={(e) => setAnswers((a) => ({ ...a, party_role: e.target.value }))}
                >
                  <option value="">请选择...</option>
                  <option value="原告方">原告方</option>
                  <option value="被告方">被告方</option>
                  <option value="兼顾-默认原告">兼顾 — 默认原告</option>
                  <option value="兼顾-默认被告">兼顾 — 默认被告</option>
                  <option value="依案件而定">依案件而定</option>
                </select>
              </div>
            </>
          )}
          {step === 1 && (
            <>
              <div className="space-y-2">
                <Label htmlFor="industry">行业</Label>
                <Input
                  id="industry"
                  value={answers.industry || ""}
                  onChange={(e) => setAnswers((a) => ({ ...a, industry: e.target.value }))}
                  placeholder="例如：制造业、金融、互联网..."
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="riskAppetite">风险偏好</Label>
                <select
                  id="riskAppetite"
                  className="border-input bg-background w-full rounded-lg border px-3 py-2 text-sm"
                  value={answers.risk_appetite || ""}
                  onChange={(e) => setAnswers((a) => ({ ...a, risk_appetite: e.target.value }))}
                >
                  <option value="">请选择...</option>
                  <option value="保守">保守</option>
                  <option value="适中">适中</option>
                  <option value="进取">进取</option>
                </select>
              </div>
            </>
          )}
          {step >= 2 && step <= 3 && (
            <div className="space-y-2">
              <Label htmlFor="notes">{step === 2 ? "争议画像备注" : "文书风格偏好"}</Label>
              <Textarea
                id="notes"
                rows={4}
                value={answers.notes || ""}
                onChange={(e) => setAnswers((a) => ({ ...a, notes: e.target.value }))}
                placeholder={step === 2 ? "常见对手、管辖法院、外部律师..." : "引用格式、语气偏好..."}
              />
            </div>
          )}
          {step === 4 && (
            <div className="text-muted-foreground text-sm">
              <p className="mb-2">确认以下设置无误后点击完成：</p>
              <ul className="list-disc pl-5 space-y-1">
                <li>执业角色：{response.partial_config?.steps?.["0"]?.answers?.practice_role || "未设置"}</li>
                <li>当事人角色：{response.partial_config?.steps?.["0"]?.answers?.party_role || "未设置"}</li>
                <li>风险偏好：{response.partial_config?.steps?.["1"]?.answers?.risk_appetite || "未设置"}</li>
              </ul>
            </div>
          )}
        </CardContent>
      </Card>

      <div className="mt-6 flex justify-between">
        <Button
          variant="outline"
          disabled={loading || step === 0}
          onClick={() => submit(step - 1)}
        >
          <ArrowLeft className="mr-1 h-4 w-4" /> 上一步
        </Button>
        <Button onClick={() => submit(step)} disabled={loading}>
          {loading ? <Spinner className="h-4 w-4" /> : step === 4 ? (
            <><Check className="mr-1 h-4 w-4" /> 完成</>
          ) : (
            <>下一步 <ArrowRight className="ml-1 h-4 w-4" /></>
          )}
        </Button>
      </div>
    </div>
  );
}
