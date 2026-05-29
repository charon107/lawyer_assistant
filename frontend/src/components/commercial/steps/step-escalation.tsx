"use client";

import { Button, Input, Label, Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui";
import { Plus, Trash2 } from "lucide-react";
import type { EscalationRule } from "@/types/commercial";

/**
 * Step 3 — escalation matrix. A repeatable list of rules: at what
 * severity, who approves, over which channel.
 */

const SEVERITY_OPTIONS: { value: EscalationRule["min_severity"]; label: string }[] = [
  { value: "low", label: "低" },
  { value: "medium", label: "中" },
  { value: "high", label: "高" },
  { value: "critical", label: "严重" },
];

const CHANNEL_OPTIONS: { value: EscalationRule["channel"]; label: string }[] = [
  { value: "email", label: "邮件" },
  { value: "slack", label: "Slack" },
  { value: "feishu", label: "飞书" },
  { value: "meeting", label: "会议" },
  { value: "other", label: "其他" },
];

function newRule(): EscalationRule {
  return { min_severity: "high", approver_role: "", channel: "email" };
}

interface StepEscalationProps {
  value: EscalationRule[];
  onChange: (next: EscalationRule[]) => void;
}

export function StepEscalation({ value, onChange }: StepEscalationProps) {
  const rules = value.length ? value : [newRule()];

  const update = (index: number, patch: Partial<EscalationRule>) =>
    onChange(rules.map((r, i) => (i === index ? { ...r, ...patch } : r)));

  const remove = (index: number) => onChange(rules.filter((_, i) => i !== index));

  return (
    <div className="flex flex-col gap-5">
      <div>
        <h2 className="mb-1 text-lg font-semibold">上报矩阵</h2>
        <p className="text-muted-foreground text-sm">当偏差达到某个严重度时，应该由谁、通过什么渠道审批。</p>
      </div>

      <div className="flex flex-col gap-3">
        {rules.map((rule, i) => (
          <div key={i} className="flex flex-wrap items-end gap-3 rounded-xl border p-4">
            <div className="flex flex-col gap-1.5">
              <Label>最低严重度</Label>
              <Select value={rule.min_severity} onValueChange={(v) => update(i, { min_severity: v as EscalationRule["min_severity"] })}>
                <SelectTrigger className="w-28">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {SEVERITY_OPTIONS.map((o) => (
                    <SelectItem key={o.value} value={o.value}>
                      {o.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="flex min-w-[160px] flex-1 flex-col gap-1.5">
              <Label htmlFor={`esc-${i}-role`}>审批角色</Label>
              <Input
                id={`esc-${i}-role`}
                value={rule.approver_role}
                placeholder="如：总法务"
                onChange={(e) => update(i, { approver_role: e.target.value })}
              />
            </div>

            <div className="flex flex-col gap-1.5">
              <Label>渠道</Label>
              <Select value={rule.channel} onValueChange={(v) => update(i, { channel: v as EscalationRule["channel"] })}>
                <SelectTrigger className="w-28">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {CHANNEL_OPTIONS.map((o) => (
                    <SelectItem key={o.value} value={o.value}>
                      {o.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <Button
              variant="ghost"
              size="sm"
              onClick={() => remove(i)}
              disabled={rules.length === 1}
              className="h-9 px-2"
              aria-label="删除规则"
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        ))}
      </div>

      <Button variant="outline" size="sm" onClick={() => onChange([...rules, newRule()])} className="self-start">
        <Plus className="mr-1.5 h-4 w-4" />
        添加规则
      </Button>
    </div>
  );
}
