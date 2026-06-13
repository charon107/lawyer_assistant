"use client";

import { useTranslations } from "next-intl";
import { ShieldCheck } from "lucide-react";
import { SkillRunner } from "@/components/litigation";

export default function LitigationSubpoenaPage() {
  const t = useTranslations("litigation");
  return (
    <SkillRunner
      action="subpoena_triage"
      icon={ShieldCheck}
      title={t("subpoena.title")}
      description={t("subpoena.description")}
      promptLabel={t("subpoena.promptLabel")}
      promptPlaceholder={t("subpoena.promptPlaceholder")}
      runLabel={t("subpoena.runLabel")}
    />
  );
}
