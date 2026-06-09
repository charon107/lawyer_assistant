"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { FileSignature } from "lucide-react";
import { Label } from "@/components/ui";
import { cn } from "@/lib/utils";
import { SkillRunner } from "@/components/privacy";

type DpaDirection = "auto" | "entrusted" | "handler";

export default function PrivacyDpaPage() {
  const t = useTranslations("privacy");
  const [direction, setDirection] = useState<DpaDirection>("auto");

  const DIRECTION_OPTIONS: { value: DpaDirection; label: string }[] = [
    { value: "auto", label: t("dpa.directionAuto") },
    { value: "entrusted", label: t("dpa.directionEntrusted") },
    { value: "handler", label: t("dpa.directionHandler") },
  ];

  const DIRECTION_PROMPT: Record<Exclude<DpaDirection, "auto">, string> = {
    entrusted: "方向：我们是受托处理者（客户/委托方发来其个人信息处理协议）。",
    handler: "方向：我们是个人信息处理者（我们向供应商发送或审查其 DPA）。",
  };

  return (
    <SkillRunner
      action="dpa"
      icon={FileSignature}
      title={t("dpa.title")}
      description={t("dpa.description")}
      subjectLabel={t("dpa.subjectLabel")}
      subjectPlaceholder={t("dpa.subjectPlaceholder")}
      promptLabel={t("dpa.promptLabel")}
      promptPlaceholder={t("dpa.promptPlaceholder")}
      runLabel={t("dpa.runLabel")}
      extraFields={
        <div className="flex flex-col gap-1.5">
          <Label>{t("dpa.directionLabel")}</Label>
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
