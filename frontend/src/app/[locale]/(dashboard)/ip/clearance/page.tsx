"use client";

import { useTranslations } from "next-intl";
import { SearchCheck } from "lucide-react";
import { SkillRunner } from "@/components/ip";

export default function IpClearancePage() {
  const t = useTranslations("ip");
  return (
    <SkillRunner
      action="clearance"
      icon={SearchCheck}
      title={t("clearance.title")}
      description={t("clearance.description")}
      disclaimer={t("clearance.disclaimer")}
      subjectLabel={t("clearance.subjectLabel")}
      subjectPlaceholder={t("clearance.subjectPlaceholder")}
      promptLabel={t("clearance.promptLabel")}
      promptPlaceholder={t("clearance.promptPlaceholder")}
      runLabel={t("clearance.runLabel")}
    />
  );
}
