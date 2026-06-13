"use client";

import { useTranslations } from "next-intl";
import { MessagesSquare } from "lucide-react";
import { SkillRunner } from "@/components/litigation";

export default function LitigationDepositionPrepPage() {
  const t = useTranslations("litigation");
  return (
    <SkillRunner
      action="deposition_prep"
      icon={MessagesSquare}
      title={t("depositionPrep.title")}
      description={t("depositionPrep.description")}
      promptLabel={t("depositionPrep.promptLabel")}
      promptPlaceholder={t("depositionPrep.promptPlaceholder")}
      runLabel={t("depositionPrep.runLabel")}
    />
  );
}
