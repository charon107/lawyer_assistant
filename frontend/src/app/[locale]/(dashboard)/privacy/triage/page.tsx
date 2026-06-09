"use client";

import { ListChecks } from "lucide-react";
import { SkillRunner } from "@/components/privacy";

export default function PrivacyTriagePage() {
  return (
    <SkillRunner
      action="triage"
      icon={ListChecks}
      title="处理活动分诊"
      description="描述一项个人信息处理活动，AI 判断是否需要 PIA、是否触发个保法第55条法定评估，或可直接推进，并排查处理规则冲突。"
      subjectLabel="活动 / 功能名称（可选）"
      subjectPlaceholder="例如：基于行为数据的内容个性化推荐"
      promptLabel="活动描述"
      promptPlaceholder="数据类别、个人信息主体、目的、是否新收集、是否涉第三方供应商、是否自动化决策、部署场景……"
      runLabel="开始分诊"
    />
  );
}
