"use client";

import { ClipboardCheck } from "lucide-react";
import { SkillRunner } from "@/components/privacy";

export default function PrivacyPiaPage() {
  return (
    <SkillRunner
      action="pia"
      icon={ClipboardCheck}
      title="个人信息保护影响评估 (PIA)"
      description="按内部格式生成 PIA：合法性基础（个保法第13条）、敏感个人信息（第28-30条）、数据出境（第38条）、风险与缓解、主体权利（第44-50条）与建议。"
      subjectLabel="功能 / 处理活动名称"
      subjectPlaceholder="例如：位置共享功能"
      promptLabel="功能描述 / PRD 摘要"
      promptPlaceholder="功能解决什么问题、涉及哪些个人信息字段、是否新收集、谁可访问、存储区域、保留期限、第三方共享……"
      runLabel="生成 PIA"
    />
  );
}
