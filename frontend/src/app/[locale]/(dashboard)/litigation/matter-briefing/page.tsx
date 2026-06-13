"use client";

import { useTranslations } from "next-intl";
import { FileSearch } from "lucide-react";
import { SkillRunner } from "@/components/litigation";

export default function LitigationMatterBriefingPage() {
  const t = useTranslations("litigation");
  return (
    <SkillRunner
      action="matter_briefing"
      icon={FileSearch}
      title={t("matterBriefing.title")}
      description={t("matterBriefing.description")}
      promptLabel={t("matterBriefing.promptLabel")}
      promptPlaceholder={t("matterBriefing.promptPlaceholder")}
      runLabel={t("matterBriefing.runLabel")}
    />
  );
}
