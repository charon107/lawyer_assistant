"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { PackageCheck } from "lucide-react";
import { Label } from "@/components/ui";
import { cn } from "@/lib/utils";
import { SkillRunner } from "@/components/ip";

type DeployMode = "saas" | "binary" | "internal" | "embedded";

export default function IpOssPage() {
  const t = useTranslations("ip");
  const [mode, setMode] = useState<DeployMode>("saas");

  const MODE_OPTIONS: { value: DeployMode; label: string }[] = [
    { value: "saas", label: t("oss.modeSaas") },
    { value: "binary", label: t("oss.modeBinary") },
    { value: "internal", label: t("oss.modeInternal") },
    { value: "embedded", label: t("oss.modeEmbedded") },
  ];

  const MODE_PROMPT: Record<DeployMode, string> = {
    saas: "部署模式：SaaS（网络服务，注意 AGPL 网络使用义务）。",
    binary: "部署模式：二进制分发（注意 GPL/LGPL 各级义务）。",
    internal: "部署模式：仅内部使用。",
    embedded: "部署模式：嵌入/固件（GPL 源码披露最严）。",
  };

  return (
    <SkillRunner
      action="oss"
      icon={PackageCheck}
      title={t("oss.title")}
      description={t("oss.description")}
      subjectLabel={t("oss.subjectLabel")}
      subjectPlaceholder={t("oss.subjectPlaceholder")}
      promptLabel={t("oss.promptLabel")}
      promptPlaceholder={t("oss.promptPlaceholder")}
      runLabel={t("oss.runLabel")}
      extraFields={
        <div className="flex flex-col gap-1.5">
          <Label>{t("oss.modeLabel")}</Label>
          <div className="flex flex-wrap gap-2">
            {MODE_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                type="button"
                onClick={() => setMode(opt.value)}
                className={cn(
                  "rounded-md border px-3 py-1.5 text-sm transition-colors",
                  mode === opt.value
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
      composePrompt={(p) => `${MODE_PROMPT[mode]}\n\n${p}`}
    />
  );
}
