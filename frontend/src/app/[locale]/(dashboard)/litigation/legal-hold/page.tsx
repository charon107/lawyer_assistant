"use client";

import { useTranslations } from "next-intl";
import { Eye } from "lucide-react";
import { SkillRunner } from "@/components/litigation";

export default function LitigationLegalHoldPage() {
  const t = useTranslations("litigation");
  return (
    <SkillRunner
      action="legal_hold"
      icon={Eye}
      title={t("legalHold.title")}
      description={t("legalHold.description")}
      promptLabel={t("legalHold.promptLabel")}
      promptPlaceholder={t("legalHold.promptPlaceholder")}
      runLabel={t("legalHold.runLabel")}
    />
  );
}
