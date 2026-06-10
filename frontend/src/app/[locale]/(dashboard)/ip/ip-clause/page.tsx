"use client";

import { useTranslations } from "next-intl";
import { FileText } from "lucide-react";
import { SkillRunner } from "@/components/ip";

export default function IpClausePage() {
  const t = useTranslations("ip");
  return (
    <SkillRunner
      action="ip_clause"
      icon={FileText}
      title={t("ipClause.title")}
      description={t("ipClause.description")}
      subjectLabel={t("ipClause.subjectLabel")}
      subjectPlaceholder={t("ipClause.subjectPlaceholder")}
      promptLabel={t("ipClause.promptLabel")}
      promptPlaceholder={t("ipClause.promptPlaceholder")}
      runLabel={t("ipClause.runLabel")}
    />
  );
}
