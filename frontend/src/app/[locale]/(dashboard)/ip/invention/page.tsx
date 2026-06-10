"use client";

import { useTranslations } from "next-intl";
import { FlaskConical } from "lucide-react";
import { SkillRunner } from "@/components/ip";

export default function IpInventionPage() {
  const t = useTranslations("ip");
  return (
    <SkillRunner
      action="invention"
      icon={FlaskConical}
      title={t("invention.title")}
      description={t("invention.description")}
      subjectLabel={t("invention.subjectLabel")}
      subjectPlaceholder={t("invention.subjectPlaceholder")}
      promptLabel={t("invention.promptLabel")}
      promptPlaceholder={t("invention.promptPlaceholder")}
      runLabel={t("invention.runLabel")}
    />
  );
}
