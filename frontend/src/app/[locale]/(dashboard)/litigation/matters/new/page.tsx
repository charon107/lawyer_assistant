"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Button, Card, CardContent, Input, Label, Spinner, Textarea } from "@/components/ui";
import { ROUTES } from "@/lib/constants";
import { litigationApi } from "@/lib/litigation";
import { ArrowLeft } from "lucide-react";

export default function NewMatterPage() {
  const router = useRouter();
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState({
    case_name: "", case_number: "", court: "", cause_of_action: "",
    our_side: "", counterparty: "", risk: "", stage: "", initial_theory: "",
  });

  function update(field: string, value: string) { setForm((f) => ({ ...f, [field]: value })); }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const m = await litigationApi.createMatter(form);
      router.push(`${ROUTES.LITIGATION_MATTERS}/${m.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "创建失败");
      setSaving(false);
    }
  }

  return (
    <div className="mx-auto max-w-lg px-4 py-10">
      <Link href={ROUTES.LITIGATION_MATTERS} className="text-muted-foreground mb-4 inline-flex items-center gap-1 text-sm hover:underline">
        <ArrowLeft className="h-3.5 w-3.5" /> 返回
      </Link>

      <h1 className="mb-6 text-xl font-bold">新建案件</h1>

      {error && <p className="border-destructive/30 bg-destructive/5 text-destructive mb-4 rounded-lg border px-4 py-2 text-sm">{error}</p>}

      <Card>
        <CardContent className="p-6">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="case_name">案件名称 *</Label>
              <Input id="case_name" required value={form.case_name} onChange={(e) => update("case_name", e.target.value)} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="case_number">案号</Label>
              <Input id="case_number" value={form.case_number} onChange={(e) => update("case_number", e.target.value)} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="court">管辖法院</Label>
              <Input id="court" value={form.court} onChange={(e) => update("court", e.target.value)} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="cause_of_action">案由</Label>
              <Input id="cause_of_action" value={form.cause_of_action} onChange={(e) => update("cause_of_action", e.target.value)} />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2">
                <Label htmlFor="our_side">当事人地位</Label>
                <select id="our_side" className="border-input bg-background w-full rounded-lg border px-3 py-2 text-sm" value={form.our_side} onChange={(e) => update("our_side", e.target.value)}>
                  <option value="">—</option>
                  <option value="plaintiff">原告</option>
                  <option value="defendant">被告</option>
                  <option value="third_party">第三人</option>
                </select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="counterparty">对方当事人</Label>
                <Input id="counterparty" value={form.counterparty} onChange={(e) => update("counterparty", e.target.value)} />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2">
                <Label htmlFor="risk">风险</Label>
                <select id="risk" className="border-input bg-background w-full rounded-lg border px-3 py-2 text-sm" value={form.risk} onChange={(e) => update("risk", e.target.value)}>
                  <option value="">—</option>
                  <option value="低">低</option>
                  <option value="中">中</option>
                  <option value="高">高</option>
                  <option value="严重">严重</option>
                </select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="stage">阶段</Label>
                <select id="stage" className="border-input bg-background w-full rounded-lg border px-3 py-2 text-sm" value={form.stage} onChange={(e) => update("stage", e.target.value)}>
                  <option value="">—</option>
                  <option value="庭前">庭前</option>
                  <option value="证据交换">证据交换</option>
                  <option value="庭审">庭审</option>
                  <option value="上诉">上诉</option>
                  <option value="执行">执行</option>
                </select>
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="initial_theory">初始案件理论</Label>
              <Textarea id="initial_theory" rows={3} value={form.initial_theory} onChange={(e) => update("initial_theory", e.target.value)} />
            </div>
            <Button type="submit" className="w-full" disabled={saving}>
              {saving ? <Spinner className="h-4 w-4" /> : "创建案件"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
