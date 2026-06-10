"use client";

import { useTranslations } from "next-intl";
import { ScanSearch } from "lucide-react";
import { SkillRunner } from "@/components/ip";

export default function IpFtoPage() {
  const t = useTranslations("ip");
  return (
    <SkillRunner
      action="fto"
      icon={ScanSearch}
      title={t("fto.title")}
      description={t("fto.description")}
      disclaimer={t("fto.disclaimer")}
      subjectLabel={t("fto.subjectLabel")}
      subjectPlaceholder={t("fto.subjectPlaceholder")}
      promptLabel={t("fto.promptLabel")}
      promptPlaceholder={t("fto.promptPlaceholder")}
      runLabel={t("fto.runLabel")}
    />
  );
}
