"use client";

import { Input, Label, Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui";
import type { Side } from "@/types/commercial";

/**
 * Step 1 — team & company info. Maps 1:1 onto the team fields that
 * `_compile_profile_kwargs` reads on the backend.
 */

export interface TeamAnswers {
  company_name?: string;
  entity_type?: string;
  team_size?: string;
  gc_name?: string;
  monthly_volume?: string;
  side?: Side;
  renewal_alert_channel?: string;
  output_destination?: string;
}

interface StepTeamProps {
  value: TeamAnswers;
  onChange: (next: TeamAnswers) => void;
}

function TextField({
  label,
  field,
  value,
  onChange,
  placeholder,
}: {
  label: string;
  field: keyof TeamAnswers;
  value: TeamAnswers;
  onChange: (next: TeamAnswers) => void;
  placeholder?: string;
}) {
  return (
    <div className="flex flex-col gap-1.5">
      <Label htmlFor={`team-${field}`}>{label}</Label>
      <Input
        id={`team-${field}`}
        value={(value[field] as string) ?? ""}
        placeholder={placeholder}
        onChange={(e) => onChange({ ...value, [field]: e.target.value })}
      />
    </div>
  );
}

export function StepTeam({ value, onChange }: StepTeamProps) {
  return (
    <div className="flex flex-col gap-5">
      <div>
        <h2 className="mb-1 text-lg font-semibold">团队信息</h2>
        <p className="text-muted-foreground text-sm">用于报告署名、上报路由与续约提醒。</p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <TextField label="公司名称" field="company_name" value={value} onChange={onChange} />
        <TextField label="主体类型" field="entity_type" value={value} onChange={onChange} placeholder="如：有限责任公司" />
        <TextField label="团队规模" field="team_size" value={value} onChange={onChange} placeholder="如：3 人法务" />
        <TextField label="总法务 / 负责人" field="gc_name" value={value} onChange={onChange} />
        <TextField label="月均合同量" field="monthly_volume" value={value} onChange={onChange} placeholder="如：20-30 份" />

        <div className="flex flex-col gap-1.5">
          <Label htmlFor="team-side">主要立场</Label>
          <Select
            value={value.side ?? "purchasing"}
            onValueChange={(v) => onChange({ ...value, side: v as Side })}
          >
            <SelectTrigger id="team-side">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="purchasing">采购方（我方付费）</SelectItem>
              <SelectItem value="sales">销售方（我方供货）</SelectItem>
              <SelectItem value="both">两者皆有</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <TextField
          label="续约提醒渠道"
          field="renewal_alert_channel"
          value={value}
          onChange={onChange}
          placeholder="如：#legal-renewals"
        />
        <TextField
          label="报告输出位置"
          field="output_destination"
          value={value}
          onChange={onChange}
          placeholder="如：飞书知识库 / 邮箱"
        />
      </div>
    </div>
  );
}
