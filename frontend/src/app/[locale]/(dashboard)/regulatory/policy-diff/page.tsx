"use client";

import { useTranslations } from "next-intl";
import { GitCompareArrows } from "lucide-react";
import { SkillRunner } from "@/components/regulatory";

export default function PolicyDiffPage() {
  const t = useTranslations("regulatory");
  return (
    <SkillRunner
      action="policy_diff"
      title={t("policyDiff.title")}
      description={t("policyDiff.description")}
      icon={GitCompareArrows}
      promptLabel={t("policyDiff.promptLabel")}
      promptPlaceholder={t("policyDiff.promptPlaceholder")}
      disclaimer={t("policyDiff.disclaimer")}
      showItemPicker
    />
  );
}
