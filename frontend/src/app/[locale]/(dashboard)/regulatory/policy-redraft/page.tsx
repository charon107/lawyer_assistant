"use client";

import { useTranslations } from "next-intl";
import { FileSearch } from "lucide-react";
import { SkillRunner } from "@/components/regulatory";

export default function PolicyRedraftPage() {
  const t = useTranslations("regulatory");
  return (
    <SkillRunner
      action="policy_redraft"
      title={t("policyRedraft.title")}
      description={t("policyRedraft.description")}
      icon={FileSearch}
      promptLabel={t("policyRedraft.promptLabel")}
      promptPlaceholder={t("policyRedraft.promptPlaceholder")}
      disclaimer={t("policyRedraft.disclaimer")}
    />
  );
}
