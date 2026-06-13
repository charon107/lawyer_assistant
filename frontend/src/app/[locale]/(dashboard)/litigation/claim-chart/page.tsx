"use client";

import { useTranslations } from "next-intl";
import { FileClock } from "lucide-react";
import { SkillRunner } from "@/components/litigation";

export default function LitigationClaimChartPage() {
  const t = useTranslations("litigation");
  return (
    <SkillRunner
      action="claim_chart"
      icon={FileClock}
      title={t("claimChart.title")}
      description={t("claimChart.description")}
      disclaimer={t("claimChart.disclaimer")}
      promptLabel={t("claimChart.promptLabel")}
      promptPlaceholder={t("claimChart.promptPlaceholder")}
      runLabel={t("claimChart.runLabel")}
    />
  );
}
