"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { ShieldAlert } from "lucide-react";
import { Label } from "@/components/ui";
import { cn } from "@/lib/utils";
import { SkillRunner } from "@/components/ip";
import type { IpCategory } from "@/types/ip";

export default function IpInfringementPage() {
  const t = useTranslations("ip");
  const [category, setCategory] = useState<IpCategory>("trademark");

  const CATEGORY_OPTIONS: { value: IpCategory; label: string }[] = [
    { value: "trademark", label: t("badges.category.trademark") },
    { value: "copyright", label: t("badges.category.copyright") },
    { value: "patent", label: t("badges.category.patent") },
    { value: "trade_secret", label: t("badges.category.trade_secret") },
  ];

  const CATEGORY_PROMPT: Record<IpCategory, string> = {
    trademark: "IP 类型：商标。",
    copyright: "IP 类型：著作权。",
    patent: "IP 类型：专利（发明/实用新型；外观设计请路由设计律师）。",
    trade_secret: "IP 类型：商业秘密。",
    design: "IP 类型：外观设计。",
  };

  return (
    <SkillRunner
      action="infringement"
      icon={ShieldAlert}
      title={t("infringement.title")}
      description={t("infringement.description")}
      subjectLabel={t("infringement.subjectLabel")}
      subjectPlaceholder={t("infringement.subjectPlaceholder")}
      promptLabel={t("infringement.promptLabel")}
      promptPlaceholder={t("infringement.promptPlaceholder")}
      runLabel={t("infringement.runLabel")}
      extraFields={
        <div className="flex flex-col gap-1.5">
          <Label>{t("infringement.categoryLabel")}</Label>
          <div className="flex flex-wrap gap-2">
            {CATEGORY_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                type="button"
                onClick={() => setCategory(opt.value)}
                className={cn(
                  "rounded-md border px-3 py-1.5 text-sm transition-colors",
                  category === opt.value
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
      composePrompt={(p) => `${CATEGORY_PROMPT[category]}\n\n${p}`}
    />
  );
}
