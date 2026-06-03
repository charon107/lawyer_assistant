"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, ArrowRight, Check, Users } from "lucide-react";
import { Button, Input, Label, Spinner } from "@/components/ui";
import { cn } from "@/lib/utils";
import { ROUTES } from "@/lib/constants";
import { employmentApi } from "@/lib/employment";

/**
 * Employment cold-start wizard — 6 steps (mirrors the backend state machine).
 *
 * Step 0: Role + practice scenario
 * Step 1: Jurisdictions (province-level multi-select)
 * Step 2: Review triggers
 * Step 3: High-risk flags + severance policy
 * Step 4: Seed files
 * Step 5: Generate profile (materializes)
 */

const STEP_TITLES = ["角色与场景", "管辖地", "审查触发器", "高风险标记", "种子文件", "生成画像"];

const QUICK_PLAN = [0, 1, 5];
const FULL_PLAN = [0, 1, 2, 3, 4, 5];

const PROVINCES = [
  "北京", "上海", "广东", "浙江", "江苏", "四川", "湖北", "山东", "河南", "重庆",
  "天津", "福建", "湖南", "辽宁", "陕西", "安徽", "河北", "云南", "广西", "贵州",
  "山西", "内蒙古", "吉林", "黑龙江", "江西", "海南", "甘肃", "宁夏", "青海", "西藏", "新疆",
];

export default function EmploymentSetupPage() {
  const router = useRouter();
  const [quickMode, setQuickMode] = useState(true);
  const [stepIndex, setStepIndex] = useState(0);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Step 0
  const [userRole, setUserRole] = useState<"attorney" | "non_attorney_with_lawyer" | "non_attorney_without">("attorney");
  const [practiceScenario, setPracticeScenario] = useState("");

  // Step 1
  const [jurisdictions, setJurisdictions] = useState<string[]>([]);
  const [defaultJurisdiction, setDefaultJurisdiction] = useState("");

  // Step 2
  const [hiringTrigger, setHiringTrigger] = useState("");
  const [terminationTrigger, setTerminationTrigger] = useState("");
  const [standardSeverance, setStandardSeverance] = useState("");

  // Step 3
  const [highRiskFlags, setHighRiskFlags] = useState<string[]>([]);
  const [policyLocation, setPolicyLocation] = useState("");

  const plan = quickMode ? QUICK_PLAN : FULL_PLAN;
  const lastStep = plan[plan.length - 1];

  const toggleJurisdiction = (prov: string) => {
    setJurisdictions((prev) =>
      prev.includes(prov) ? prev.filter((p) => p !== prov) : [...prev, prov],
    );
    if (!defaultJurisdiction) setDefaultJurisdiction(prov);
  };

  const toggleFlag = (flag: string) => {
    setHighRiskFlags((prev) =>
      prev.includes(flag) ? prev.filter((f) => f !== flag) : [...prev, flag],
    );
  };

  const buildAnswers = (step: number): Record<string, unknown> => {
    switch (step) {
      case 0:
        return { user_role: userRole, practice_scenario: practiceScenario.trim() || null };
      case 1:
        return {
          jurisdictions,
          default_jurisdiction: defaultJurisdiction || jurisdictions[0] || "",
          office_model: "hybrid",
        };
      case 2:
        return {
          hiring_trigger: hiringTrigger.trim() || null,
          termination_trigger: terminationTrigger.trim() || null,
          standard_severance: standardSeverance.trim() || null,
        };
      case 3:
        return { high_risk_flags: highRiskFlags, policy_location: policyLocation };
      case 4:
        return {};
      default:
        return {};
    }
  };

  const goNext = async () => {
    setSubmitting(true);
    setError(null);
    try {
      const res = await employmentApi.submitSetup({
        step: stepIndex,
        answers: buildAnswers(stepIndex),
        quick_mode: quickMode,
      });
      if (res.completed) {
        router.push(ROUTES.EMPLOYMENT);
        return;
      }
      setStepIndex(res.step);
    } catch (e) {
      setError(e instanceof Error ? e.message : "提交失败，请重试");
    } finally {
      setSubmitting(false);
    }
  };

  const goBack = () => {
    setError(null);
    const idx = plan.indexOf(stepIndex);
    const prev = idx > 0 ? plan[idx - 1] : undefined;
    if (prev !== undefined) setStepIndex(prev);
  };

  return (
    <div className="mx-auto max-w-3xl px-4 py-10">
      <div className="mb-8">
        <Link
          href={ROUTES.EMPLOYMENT}
          className="text-muted-foreground hover:text-foreground mb-4 inline-flex items-center gap-1.5 text-sm transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          返回劳动用工
        </Link>
        <h1 className="mb-1 flex items-center gap-2 text-2xl font-bold">
          <Users className="text-brand h-6 w-6" />
          配置劳动用工模块
        </h1>
        <p className="text-muted-foreground">
          告诉我们你的实践场景和管辖地，之后审查、假期、调查技能都会自动适配。
        </p>
      </div>

      {/* Progress rail */}
      <ol className="mb-6 flex items-center gap-2">
        {plan.map((step, i) => {
          const done = step < stepIndex;
          const active = step === stepIndex;
          return (
            <li key={step} className="flex flex-1 items-center gap-2">
              <div
                className={cn(
                  "flex h-7 w-7 shrink-0 items-center justify-center rounded-full border text-xs font-medium transition-colors",
                  done && "border-brand bg-brand text-white",
                  active && "border-brand text-brand",
                  !done && !active && "text-muted-foreground border-muted",
                )}
              >
                {done ? <Check className="h-3.5 w-3.5" /> : i + 1}
              </div>
              <span
                className={cn(
                  "hidden text-xs sm:block",
                  active ? "text-foreground font-medium" : "text-muted-foreground",
                )}
              >
                {STEP_TITLES[step]}
              </span>
              {i < plan.length - 1 && <div className="bg-muted hidden h-px flex-1 sm:block" />}
            </li>
          );
        })}
      </ol>

      {/* Step body */}
      <div className="rounded-2xl border p-6">
        {stepIndex === 0 && (
          <div className="flex flex-col gap-4">
            <div className="flex flex-col gap-1.5">
              <span className="text-sm font-medium">配置方式</span>
              <div className="grid gap-2 sm:grid-cols-2">
                <button
                  type="button"
                  onClick={() => setQuickMode(true)}
                  className={cn(
                    "flex flex-col items-start gap-0.5 rounded-lg border px-3.5 py-2.5 text-left transition-colors",
                    quickMode
                      ? "border-brand bg-brand/5 ring-brand/20 ring-1"
                      : "border-border hover:border-brand/40",
                  )}
                >
                  <span className="text-sm font-medium">快速配置</span>
                  <span className="text-muted-foreground text-xs">仅需 3 步</span>
                </button>
                <button
                  type="button"
                  onClick={() => setQuickMode(false)}
                  className={cn(
                    "flex flex-col items-start gap-0.5 rounded-lg border px-3.5 py-2.5 text-left transition-colors",
                    !quickMode
                      ? "border-brand bg-brand/5 ring-brand/20 ring-1"
                      : "border-border hover:border-brand/40",
                  )}
                >
                  <span className="text-sm font-medium">完整配置</span>
                  <span className="text-muted-foreground text-xs">全部 6 步</span>
                </button>
              </div>
            </div>
            <div className="flex flex-col gap-1.5">
              <span className="text-sm font-medium">你的角色</span>
              <div className="grid gap-2 sm:grid-cols-3">
                {([
                  { value: "attorney", label: "律师 / 法务" },
                  { value: "non_attorney_with_lawyer", label: "非律师（有外部律师）" },
                  { value: "non_attorney_without", label: "非律师（无外部律师）" },
                ] as const).map((r) => (
                  <button
                    key={r.value}
                    type="button"
                    onClick={() => setUserRole(r.value)}
                    className={cn(
                      "rounded-lg border px-3.5 py-2.5 text-left text-sm transition-colors",
                      userRole === r.value
                        ? "border-brand bg-brand/5 ring-brand/20 ring-1"
                        : "border-border hover:border-brand/40",
                    )}
                  >
                    {r.label}
                  </button>
                ))}
              </div>
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="scenario">实践场景（可选）</Label>
              <Input
                id="scenario"
                value={practiceScenario}
                onChange={(e) => setPracticeScenario(e.target.value)}
                placeholder="例如：互联网企业劳动合规、制造业用工审查"
              />
            </div>
          </div>
        )}

        {stepIndex === 1 && (
          <div className="flex flex-col gap-4">
            <p className="text-muted-foreground text-sm">选择你需要覆盖的省/直辖市（可多选）：</p>
            <div className="flex flex-wrap gap-2">
              {PROVINCES.map((prov) => {
                const selected = jurisdictions.includes(prov);
                return (
                  <button
                    key={prov}
                    type="button"
                    onClick={() => toggleJurisdiction(prov)}
                    className={cn(
                      "rounded-full border px-3 py-1.5 text-sm transition-colors",
                      selected
                        ? "border-brand bg-brand/10 text-brand font-medium"
                        : "border-border hover:border-brand/40",
                    )}
                  >
                    {prov}
                  </button>
                );
              })}
            </div>
            {jurisdictions.length > 0 && (
              <div className="flex flex-col gap-1.5">
                <Label>默认管辖地</Label>
                <select
                  className="rounded-lg border px-3 py-2 text-sm"
                  value={defaultJurisdiction}
                  onChange={(e) => setDefaultJurisdiction(e.target.value)}
                >
                  {jurisdictions.map((j) => (
                    <option key={j} value={j}>
                      {j}
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>
        )}

        {stepIndex === 2 && (
          <div className="flex flex-col gap-4">
            <p className="text-muted-foreground text-sm">描述你的审查触发器（可选，后续可修改）：</p>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="hiring-trigger">录用审查触发条件</Label>
              <Input
                id="hiring-trigger"
                value={hiringTrigger}
                onChange={(e) => setHiringTrigger(e.target.value)}
                placeholder="例如：所有正式岗位入职前"
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="term-trigger">解除审查触发条件</Label>
              <Input
                id="term-trigger"
                value={terminationTrigger}
                onChange={(e) => setTerminationTrigger(e.target.value)}
                placeholder="例如：所有解除/终止劳动合同"
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="severance">经济补偿金标准</Label>
              <Input
                id="severance"
                value={standardSeverance}
                onChange={(e) => setStandardSeverance(e.target.value)}
                placeholder="例如：N+1（法定标准）"
              />
            </div>
          </div>
        )}

        {stepIndex === 3 && (
          <div className="flex flex-col gap-4">
            <p className="text-muted-foreground text-sm">启用高风险标记检测（解除审查时自动扫描）：</p>
            <div className="flex flex-wrap gap-2">
              {[
                { id: "recent_complaint", label: "近期投诉/举报" },
                { id: "protected_leave", label: "受保护休假/医疗期" },
                { id: "special_protection", label: "特殊保护群体" },
                { id: "whistleblower", label: "检举/控告" },
                { id: "weak_evidence", label: "书面证据薄弱" },
                { id: "disparate_treatment", label: "差别对待" },
                { id: "broken_promise", label: "合同/规章承诺" },
                { id: "hours_misclassification", label: "工时分类错误" },
              ].map((f) => {
                const selected = highRiskFlags.includes(f.id);
                return (
                  <button
                    key={f.id}
                    type="button"
                    onClick={() => toggleFlag(f.id)}
                    className={cn(
                      "rounded-full border px-3 py-1.5 text-sm transition-colors",
                      selected
                        ? "border-red-300 bg-red-50 text-red-700 font-medium dark:bg-red-950/40 dark:text-red-300"
                        : "border-border hover:border-red-300",
                    )}
                  >
                    {f.label}
                  </button>
                );
              })}
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="policy-loc">制度存放位置（可选）</Label>
              <Input
                id="policy-loc"
                value={policyLocation}
                onChange={(e) => setPolicyLocation(e.target.value)}
                placeholder="例如：共享盘/HR系统"
              />
            </div>
          </div>
        )}

        {stepIndex === 4 && (
          <div className="flex flex-col gap-3">
            <p className="text-muted-foreground text-sm">
              你可以稍后在设置页面上传种子文件（员工手册、规章制度等）。
              此步骤在快速配置模式下会跳过。
            </p>
            <p className="text-muted-foreground text-xs">
              暂不上传，直接点击「下一步」继续。
            </p>
          </div>
        )}

        {stepIndex === 5 && (
          <div className="flex flex-col items-center gap-4 py-8 text-center">
            <div className="bg-brand/10 flex h-14 w-14 items-center justify-center rounded-2xl">
              <Check className="text-brand h-7 w-7" />
            </div>
            <h2 className="text-lg font-semibold">准备生成画像</h2>
            <p className="text-muted-foreground max-w-md text-sm">
              点击「完成配置」后，系统将根据你的回答生成实践画像。
              画像将用于所有审查、假期和调查技能的个性化。
            </p>
          </div>
        )}
      </div>

      {error && (
        <p className="border-destructive/30 bg-destructive/5 text-destructive mt-4 rounded-lg border px-4 py-2.5 text-sm">
          {error}
        </p>
      )}

      {/* Controls */}
      <div className="mt-6 flex items-center justify-between">
        <Button
          variant="ghost"
          onClick={goBack}
          disabled={stepIndex === plan[0] || submitting}
        >
          <ArrowLeft className="mr-1.5 h-4 w-4" />
          上一步
        </Button>
        <Button onClick={goNext} disabled={submitting}>
          {submitting && <Spinner className="mr-1.5 h-4 w-4" />}
          {stepIndex === lastStep ? "完成配置" : "下一步"}
          {!submitting && stepIndex !== lastStep && <ArrowRight className="ml-1.5 h-4 w-4" />}
        </Button>
      </div>
    </div>
  );
}
