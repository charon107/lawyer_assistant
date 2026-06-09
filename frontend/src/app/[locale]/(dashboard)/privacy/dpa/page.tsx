"use client";

import { useState } from "react";
import { FileSignature } from "lucide-react";
import { Label } from "@/components/ui";
import { cn } from "@/lib/utils";
import { SkillRunner } from "@/components/privacy";

type DpaDirection = "auto" | "entrusted" | "handler";

const DIRECTION_OPTIONS: { value: DpaDirection; label: string }[] = [
  { value: "auto", label: "自动识别" },
  { value: "entrusted", label: "我们是受托处理者（客户发来）" },
  { value: "handler", label: "我们是处理者（审供应商）" },
];

const DIRECTION_PROMPT: Record<Exclude<DpaDirection, "auto">, string> = {
  entrusted: "方向：我们是受托处理者（客户/委托方发来其个人信息处理协议）。",
  handler: "方向：我们是个人信息处理者（我们向供应商发送或审查其 DPA）。",
};

export default function PrivacyDpaPage() {
  const [direction, setDirection] = useState<DpaDirection>("auto");

  return (
    <SkillRunner
      action="dpa"
      icon={FileSignature}
      title="DPA 审查（双向）"
      description="审查个人信息处理协议。自动识别你是受托处理者还是处理者，逐条对照操作手册，含六维度风险与修订建议。"
      subjectLabel="对方当事人"
      subjectPlaceholder="例如：某云服务供应商 / 某企业客户"
      promptLabel="DPA 文本 / 关键条款"
      promptPlaceholder="粘贴 DPA 文本或关键条款（审计权、泄露通知、转委托、数据出境、删除、责任……）"
      runLabel="开始审查"
      extraFields={
        <div className="flex flex-col gap-1.5">
          <Label>审查方向</Label>
          <div className="flex flex-wrap gap-2">
            {DIRECTION_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                type="button"
                onClick={() => setDirection(opt.value)}
                className={cn(
                  "rounded-md border px-3 py-1.5 text-sm transition-colors",
                  direction === opt.value
                    ? "border-brand bg-brand/10 text-brand font-medium"
                    : "text-muted-foreground hover:bg-muted",
                )}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>
      }
      composePrompt={(p) =>
        direction === "auto" ? p : `${DIRECTION_PROMPT[direction]}\n\n${p}`
      }
    />
  );
}
