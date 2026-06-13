"use client";

import { useTranslations } from "next-intl";
import { ListChecks } from "lucide-react";
import { SkillRunner } from "@/components/litigation";

export default function LitigationPrivilegeLogPage() {
  const t = useTranslations("litigation");
  return (
    <SkillRunner
      action="privilege_log"
      icon={ListChecks}
      title={t("privilegeLog.title")}
      description={t("privilegeLog.description")}
      disclaimer={t("privilegeLog.disclaimer")}
      promptLabel={t("privilegeLog.promptLabel")}
      promptPlaceholder={t("privilegeLog.promptPlaceholder")}
      runLabel={t("privilegeLog.runLabel")}
    />
  );
}
