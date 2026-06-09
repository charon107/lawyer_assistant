"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, ArrowRight, Check, ShieldCheck } from "lucide-react";
import { Button, Input, Label, Spinner, Textarea } from "@/components/ui";
import { cn } from "@/lib/utils";
import { ROUTES } from "@/lib/constants";
import { privacyApi } from "@/lib/privacy";

/**
 * Privacy cold-start wizard — 6 steps (mirrors the backend state machine).
 *
 * 0: role + practice setting        1: regulatory footprint + business model
 * 2: DPA playbook                   3: internal norms (PIA + DSAR)
 * 4: seed files                     5: generate profile
 */

const STEP_TITLES = ["角色与场景", "监管覆盖", "DPA 立场", "内部规范", "种子文件", "生成画像"];
const QUICK_PLAN = [0, 1, 5];
const FULL_PLAN = [0, 1, 2, 3, 4, 5];

const REGULATIONS = [
  "个人信息保护法",
  "数据安全法",
  "网络安全法",
  "金融监管（个人金融信息）",
  "医疗健康数据监管",
  "儿童个人信息网络保护规定",
  "汽车数据安全管理若干规定",
];

const ROLES = [
  { value: "attorney", label: "律师 / 法务" },
  { value: "non_attorney_with_lawyer", label: "非律师（有外部律师）" },
  { value: "non_attorney_without", label: "非律师（无外部律师）" },
] as const;

type UserRole = (typeof ROLES)[number]["value"];

export default function PrivacySetupPage() {
  const router = useRouter();
  const [quickMode, setQuickMode] = useState(true);
  const [stepIndex, setStepIndex] = useState(0);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Step 0
  const [userRole, setUserRole] = useState<UserRole>("attorney");
  const [practiceSetting, setPracticeSetting] = useState("");
  // Step 1
  const [footprint, setFootprint] = useState<string[]>(["个人信息保护法"]);
  const [businessModel, setBusinessModel] = useState<"handler" | "entrusted" | "both">("handler");
  const [dataResidency, setDataResidency] = useState("");
  // Step 2
  const [dpaNotes, setDpaNotes] = useState("");
  // Step 3
  const [piaTrigger, setPiaTrigger] = useState("");
  const [dsarSystems, setDsarSystems] = useState("");
  const [dsarSla, setDsarSla] = useState("");

  const plan = quickMode ? QUICK_PLAN : FULL_PLAN;
  const lastStep = plan[plan.length - 1];

  const toggleFootprint = (r: string) =>
    setFootprint((prev) => (prev.includes(r) ? prev.filter((x) => x !== r) : [...prev, r]));

  const buildAnswers = (step: number): Record<string, unknown> => {
    switch (step) {
      case 0:
        return { user_role: userRole, practice_setting: practiceSetting.trim() || null };
      case 1:
        return {
          regulatory_footprint: footprint,
          data_residency: dataResidency.trim() || null,
          business_model: businessModel,
        };
      case 2:
        return { dpa_playbook: { notes: dpaNotes.trim() || null } };
      case 3:
        return {
          pia_house_style: { trigger: piaTrigger.trim() || null },
          dsar_process: {
            systems_list: dsarSystems
              .split(/[、,，\n]/)
              .map((s) => s.trim())
              .filter(Boolean),
            response_sla: dsarSla.trim() || null,
          },
        };
      default:
        return {};
    }
  };

  const goNext = async () => {
    setSubmitting(true);
    setError(null);
    try {
      const res = await privacyApi.submitSetup({
        step: stepIndex,
        answers: buildAnswers(stepIndex),
        quick_mode: quickMode,
      });
      if (res.completed) {
        router.push(ROUTES.PRIVACY);
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
          href={ROUTES.PRIVACY}
          className="text-muted-foreground hover:text-foreground mb-4 inline-flex items-center gap-1.5 text-sm transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          返回个人信息保护
        </Link>
        <h1 className="mb-1 flex items-center gap-2 text-2xl font-bold">
          <ShieldCheck className="text-brand h-6 w-6" />
          配置个人信息保护模块
        </h1>
        <p className="text-muted-foreground">
          告诉我们你的监管覆盖范围、DPA 立场和内部规范，之后所有技能都会自动适配。
        </p>
      </div>

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
                    quickMode ? "border-brand bg-brand/5 ring-brand/20 ring-1" : "border-border hover:border-brand/40",
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
                    !quickMode ? "border-brand bg-brand/5 ring-brand/20 ring-1" : "border-border hover:border-brand/40",
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
                {ROLES.map((r) => (
                  <button
                    key={r.value}
                    type="button"
                    onClick={() => setUserRole(r.value)}
                    className={cn(
                      "rounded-lg border px-3.5 py-2.5 text-left text-sm transition-colors",
                      userRole === r.value ? "border-brand bg-brand/5 ring-brand/20 ring-1" : "border-border hover:border-brand/40",
                    )}
                  >
                    {r.label}
                  </button>
                ))}
              </div>
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="setting">执业场景（可选）</Label>
              <Input
                id="setting"
                value={practiceSetting}
                onChange={(e) => setPracticeSetting(e.target.value)}
                placeholder="例如：企业法务 / 中型律所 / 互联网公司隐私团队"
              />
            </div>
          </div>
        )}

        {stepIndex === 1 && (
          <div className="flex flex-col gap-4">
            <p className="text-muted-foreground text-sm">选择实际适用的监管制度（可多选）：</p>
            <div className="flex flex-wrap gap-2">
              {REGULATIONS.map((r) => {
                const selected = footprint.includes(r);
                return (
                  <button
                    key={r}
                    type="button"
                    onClick={() => toggleFootprint(r)}
                    className={cn(
                      "rounded-full border px-3 py-1.5 text-sm transition-colors",
                      selected ? "border-brand bg-brand/10 text-brand font-medium" : "border-border hover:border-brand/40",
                    )}
                  >
                    {r}
                  </button>
                );
              })}
            </div>
            <div className="flex flex-col gap-1.5">
              <span className="text-sm font-medium">业务模式（DPA 默认方向）</span>
              <div className="grid gap-2 sm:grid-cols-3">
                {([
                  { value: "handler", label: "主要是处理者" },
                  { value: "entrusted", label: "主要是受托处理者" },
                  { value: "both", label: "两者皆有" },
                ] as const).map((b) => (
                  <button
                    key={b.value}
                    type="button"
                    onClick={() => setBusinessModel(b.value)}
                    className={cn(
                      "rounded-lg border px-3.5 py-2.5 text-left text-sm transition-colors",
                      businessModel === b.value ? "border-brand bg-brand/5 ring-brand/20 ring-1" : "border-border hover:border-brand/40",
                    )}
                  >
                    {b.label}
                  </button>
                ))}
              </div>
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="residency">数据存储地</Label>
              <Input
                id="residency"
                value={dataResidency}
                onChange={(e) => setDataResidency(e.target.value)}
                placeholder="例如：仅中国境内 / 多区域部署"
              />
            </div>
          </div>
        )}

        {stepIndex === 2 && (
          <div className="flex flex-col gap-4">
            <p className="text-muted-foreground text-sm">
              简述你的 DPA 谈判立场（审计权、泄露通知时限、转委托、数据出境、删除、责任上限等）。可留空稍后补充。
            </p>
            <Textarea
              value={dpaNotes}
              onChange={(e) => setDpaNotes(e.target.value)}
              rows={8}
              placeholder="作为受托处理者时：审计权接受 ISO 27001/等保三级报告……&#10;作为处理者时：要求供应商提供下游处理者清单、72小时泄露通知……"
            />
          </div>
        )}

        {stepIndex === 3 && (
          <div className="flex flex-col gap-4">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="pia-trigger">PIA 触发标准</Label>
              <Input
                id="pia-trigger"
                value={piaTrigger}
                onChange={(e) => setPiaTrigger(e.target.value)}
                placeholder="例如：处理敏感个人信息 / 自动化决策 / 数据出境（个保法第55条）"
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="dsar-systems">DSAR 系统清单（顿号/换行分隔）</Label>
              <Textarea
                id="dsar-systems"
                value={dsarSystems}
                onChange={(e) => setDsarSystems(e.target.value)}
                rows={4}
                placeholder="生产数据库、数据分析平台、客服工单、CRM、邮件营销、日志、备份"
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="dsar-sla">DSAR 回复 SLA</Label>
              <Input
                id="dsar-sla"
                value={dsarSla}
                onChange={(e) => setDsarSla(e.target.value)}
                placeholder="例如：15 个工作日内（个保法第45条「及时」，内部更严）"
              />
            </div>
          </div>
        )}

        {stepIndex === 4 && (
          <div className="flex flex-col gap-3">
            <p className="text-muted-foreground text-sm">
              你可以稍后在设置页面补充种子文件（处理规则、DPA 模板、参考 PIA）。此步骤在快速配置模式下会跳过。
            </p>
            <p className="text-muted-foreground text-xs">暂不上传，直接点击「下一步」继续。</p>
          </div>
        )}

        {stepIndex === 5 && (
          <div className="flex flex-col items-center gap-4 py-8 text-center">
            <div className="bg-brand/10 flex h-14 w-14 items-center justify-center rounded-2xl">
              <Check className="text-brand h-7 w-7" />
            </div>
            <h2 className="text-lg font-semibold">准备生成画像</h2>
            <p className="text-muted-foreground max-w-md text-sm">
              点击「完成配置」后，系统将根据你的回答生成实践画像，用于所有技能的个性化。
            </p>
          </div>
        )}
      </div>

      {error && (
        <p className="border-destructive/30 bg-destructive/5 text-destructive mt-4 rounded-lg border px-4 py-2.5 text-sm">
          {error}
        </p>
      )}

      <div className="mt-6 flex items-center justify-between">
        <Button variant="ghost" onClick={goBack} disabled={stepIndex === plan[0] || submitting}>
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
