"use client";

import { Scale } from "lucide-react";
import { SkillRunner } from "@/components/privacy";

export default function PrivacyGapPage() {
  return (
    <SkillRunner
      action="gap"
      icon={Scale}
      title="法规差距分析"
      description="将新出台或变更的法规与现行处理规则及实践做差异对比，输出差距清单和带负责人、截止日期的整改计划。"
      subjectLabel="法规名称"
      subjectPlaceholder="例如：个人信息出境标准合同办法"
      promptLabel="法规文本 / 摘要 / 指引"
      promptPlaceholder="粘贴法规文本或摘要，或描述要对照的法规变化……"
      runLabel="开始差距分析"
    />
  );
}
