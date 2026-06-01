"use client";

import { useState } from "react";
import { Loader2 } from "lucide-react";
import { Button, Input, Label } from "@/components/ui";
import type {
  RenewalDecision,
  RenewalRegistrationCreate,
} from "@/types/commercial";

/**
 * Registration form for a new renewal. The cancel/send deadlines are
 * computed server-side from effective_date + term + notice, so the form
 * only collects the raw inputs.
 */

const DECISIONS: { value: RenewalDecision; label: string }[] = [
  { value: "pending", label: "待决定" },
  { value: "renew", label: "续约" },
  { value: "terminate", label: "终止" },
  { value: "renegotiate", label: "重新谈判" },
];

export function RenewalForm({
  onSubmit,
  onCancel,
}: {
  onSubmit: (data: RenewalRegistrationCreate) => Promise<void>;
  onCancel?: () => void;
}) {
  const [counterparty, setCounterparty] = useState("");
  const [agreementName, setAgreementName] = useState("");
  const [effectiveDate, setEffectiveDate] = useState("");
  const [termMonths, setTermMonths] = useState("12");
  const [noticeDays, setNoticeDays] = useState("30");
  const [autoRenew, setAutoRenew] = useState(true);
  const [decision, setDecision] = useState<RenewalDecision>("pending");
  const [notes, setNotes] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const canSubmit = !!effectiveDate && !busy;

  const handleSubmit = async () => {
    if (!effectiveDate) return;
    setBusy(true);
    setError(null);
    try {
      await onSubmit({
        counterparty: counterparty.trim() || undefined,
        agreement_name: agreementName.trim() || undefined,
        effective_date: effectiveDate,
        term_months: Number(termMonths) || 12,
        notice_days: Number(noticeDays) || 0,
        auto_renew: autoRenew,
        decision,
        notes: notes.trim() || undefined,
      });
    } catch (e) {
      setError(e instanceof Error ? e.message : "登记失败");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="flex flex-col gap-4">
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="r-counterparty">对方主体</Label>
          <Input
            id="r-counterparty"
            value={counterparty}
            onChange={(e) => setCounterparty(e.target.value)}
            placeholder="例如：某某科技有限公司"
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="r-agreement">协议名称</Label>
          <Input
            id="r-agreement"
            value={agreementName}
            onChange={(e) => setAgreementName(e.target.value)}
            placeholder="例如：云服务采购协议"
          />
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="r-effective">生效日期 *</Label>
          <Input
            id="r-effective"
            type="date"
            value={effectiveDate}
            onChange={(e) => setEffectiveDate(e.target.value)}
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="r-term">期限（月）</Label>
          <Input
            id="r-term"
            type="number"
            min={1}
            value={termMonths}
            onChange={(e) => setTermMonths(e.target.value)}
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="r-notice">提前通知（天）</Label>
          <Input
            id="r-notice"
            type="number"
            min={0}
            value={noticeDays}
            onChange={(e) => setNoticeDays(e.target.value)}
          />
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={autoRenew}
            onChange={(e) => setAutoRenew(e.target.checked)}
            className="accent-brand h-4 w-4"
          />
          自动续约（到期未通知则顺延）
        </label>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="r-decision">续约决定</Label>
          <select
            id="r-decision"
            value={decision}
            onChange={(e) => setDecision(e.target.value as RenewalDecision)}
            className="border-border bg-background h-9 rounded-md border px-3 text-sm"
          >
            {DECISIONS.map((d) => (
              <option key={d.value} value={d.value}>
                {d.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="flex flex-col gap-1.5">
        <Label htmlFor="r-notes">备注</Label>
        <Input
          id="r-notes"
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder="可选"
        />
      </div>

      {error && (
        <p className="border-destructive/30 bg-destructive/5 text-destructive rounded-lg border px-4 py-2.5 text-sm">
          {error}
        </p>
      )}

      <div className="flex justify-end gap-2">
        {onCancel && (
          <Button variant="ghost" onClick={onCancel} disabled={busy}>
            取消
          </Button>
        )}
        <Button onClick={handleSubmit} disabled={!canSubmit}>
          {busy && <Loader2 className="mr-1.5 h-4 w-4 animate-spin" />}
          登记续约
        </Button>
      </div>
    </div>
  );
}
