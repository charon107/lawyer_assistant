"use client";

import { useState } from "react";
import { Button, Input, Label, Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui";
import type { LeaveType } from "@/types/employment";

const LEAVE_TYPE_OPTIONS: { value: LeaveType; label: string }[] = [
  { value: "annual", label: "年休假" },
  { value: "sick", label: "病假/医疗期" },
  { value: "maternity", label: "产假" },
  { value: "paternity", label: "陪产假" },
  { value: "parental", label: "育儿假" },
  { value: "marriage", label: "婚假" },
  { value: "work_injury", label: "工伤假" },
];

export interface LeaveFormValues {
  employee_name: string;
  position: string;
  jurisdiction: string;
  leave_type: LeaveType;
  leave_start: string;
  expected_return: string;
  years_of_service: string;
}

interface LeaveFormProps {
  onSubmit: (data: LeaveFormValues) => Promise<void>;
  onCancel: () => void;
  initialJurisdiction?: string;
}

export function LeaveForm({ onSubmit, onCancel, initialJurisdiction = "" }: LeaveFormProps) {
  const [values, setValues] = useState<LeaveFormValues>({
    employee_name: "",
    position: "",
    jurisdiction: initialJurisdiction,
    leave_type: "annual",
    leave_start: "",
    expected_return: "",
    years_of_service: "",
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const set = <K extends keyof LeaveFormValues>(key: K, val: LeaveFormValues[K]) =>
    setValues((prev) => ({ ...prev, [key]: val }));

  const canSubmit = values.employee_name.trim() && values.leave_start && !submitting;

  const handleSubmit = async () => {
    if (!canSubmit) return;
    setSubmitting(true);
    setError(null);
    try {
      await onSubmit(values);
    } catch (e) {
      setError(e instanceof Error ? e.message : "提交失败");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="flex flex-col gap-4">
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="lv-name">员工姓名</Label>
          <Input id="lv-name" value={values.employee_name} onChange={(e) => set("employee_name", e.target.value)} placeholder="必填" />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="lv-position">职位</Label>
          <Input id="lv-position" value={values.position} onChange={(e) => set("position", e.target.value)} placeholder="可选" />
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="lv-jurisdiction">管辖地</Label>
          <Input id="lv-jurisdiction" value={values.jurisdiction} onChange={(e) => set("jurisdiction", e.target.value)} placeholder="例如：北京" />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label>假期类型</Label>
          <Select value={values.leave_type} onValueChange={(v) => set("leave_type", v as LeaveType)}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {LEAVE_TYPE_OPTIONS.map((opt) => (
                <SelectItem key={opt.value} value={opt.value}>
                  {opt.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="lv-start">开始日期</Label>
          <Input id="lv-start" type="date" value={values.leave_start} onChange={(e) => set("leave_start", e.target.value)} />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="lv-return">预计返岗</Label>
          <Input id="lv-return" type="date" value={values.expected_return} onChange={(e) => set("expected_return", e.target.value)} />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="lv-yos">累计工龄（年）</Label>
          <Input id="lv-yos" type="number" min="0" value={values.years_of_service} onChange={(e) => set("years_of_service", e.target.value)} placeholder="可选" />
        </div>
      </div>

      <p className="text-muted-foreground text-xs">
        提交后系统会根据管辖地和假期类型自动计算到期日，用于 leave-tracker 预警。
      </p>

      {error && (
        <p className="border-destructive/30 bg-destructive/5 text-destructive rounded-lg border px-4 py-2.5 text-sm">{error}</p>
      )}

      <div className="flex justify-end gap-2">
        <Button variant="ghost" onClick={onCancel} disabled={submitting}>取消</Button>
        <Button onClick={handleSubmit} disabled={!canSubmit}>{submitting ? "提交中…" : "登记假期"}</Button>
      </div>
    </div>
  );
}
