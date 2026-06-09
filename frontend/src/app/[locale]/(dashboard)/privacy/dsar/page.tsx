"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft, MailQuestion, Plus } from "lucide-react";
import { Button, Card, CardContent, Input, Label, Spinner } from "@/components/ui";
import { DsarStatusBadge } from "@/components/privacy";
import { ROUTES } from "@/lib/constants";
import { privacyApi } from "@/lib/privacy";
import { cn } from "@/lib/utils";
import type { DsarRequestType, PrivacyDsar } from "@/types/privacy";

const REQUEST_TYPES: { value: DsarRequestType; label: string }[] = [
  { value: "access", label: "查阅（第45条）" },
  { value: "copy", label: "复制（第45条）" },
  { value: "delete", label: "删除（第47条）" },
  { value: "correct", label: "更正（第46条）" },
  { value: "explain", label: "解释说明（第48条）" },
  { value: "restrict", label: "限制（第44条）" },
];

export default function PrivacyDsarPage() {
  const [items, setItems] = useState<PrivacyDsar[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);

  const [types, setTypes] = useState<DsarRequestType[]>([]);
  const [subjectRef, setSubjectRef] = useState("");
  const [received, setReceived] = useState("");
  const [verification, setVerification] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function load() {
    try {
      const res = await privacyApi.listDsar(0, 100);
      setItems(res.items);
    } catch (e) {
      setError(e instanceof Error ? e.message : "加载失败");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  function toggleType(t: DsarRequestType) {
    setTypes((prev) => (prev.includes(t) ? prev.filter((x) => x !== t) : [...prev, t]));
  }

  async function handleCreate() {
    if (types.length === 0) return;
    setSubmitting(true);
    try {
      await privacyApi.createDsar({
        request_types: types,
        data_subject_ref: subjectRef.trim() || undefined,
        date_received: received || undefined,
        verification_method: verification.trim() || undefined,
      });
      setShowForm(false);
      setTypes([]);
      setSubjectRef("");
      setReceived("");
      setVerification("");
      setLoading(true);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "创建失败");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="mx-auto max-w-4xl px-4 py-10">
      <Link
        href={ROUTES.PRIVACY}
        className="text-muted-foreground hover:text-foreground mb-4 inline-flex items-center gap-1.5 text-sm transition-colors"
      >
        <ArrowLeft className="h-4 w-4" />
        返回个人信息保护
      </Link>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="flex items-center gap-2 text-2xl font-bold">
          <MailQuestion className="text-brand h-6 w-6" />
          个人信息主体权利请求
        </h1>
        <Button onClick={() => setShowForm((s) => !s)}>
          <Plus className="mr-1.5 h-4 w-4" />
          新建请求
        </Button>
      </div>

      <p className="text-muted-foreground mb-6 text-sm">
        建档时请最小化个人信息——主体标识用编号而非真实姓名。建档后进入详情页起草确认函与实质回复函。
      </p>

      {error && (
        <p className="border-destructive/30 bg-destructive/5 text-destructive mb-6 rounded-lg border px-4 py-2.5 text-sm">
          {error}
        </p>
      )}

      {showForm && (
        <Card className="mb-6">
          <CardContent className="flex flex-col gap-4 p-6">
            <div className="flex flex-col gap-1.5">
              <Label>请求类型（可多选）</Label>
              <div className="flex flex-wrap gap-2">
                {REQUEST_TYPES.map((rt) => (
                  <button
                    key={rt.value}
                    type="button"
                    onClick={() => toggleType(rt.value)}
                    className={cn(
                      "rounded-md border px-3 py-1.5 text-sm transition-colors",
                      types.includes(rt.value)
                        ? "border-brand bg-brand/10 text-brand font-medium"
                        : "text-muted-foreground hover:bg-muted",
                    )}
                  >
                    {rt.label}
                  </button>
                ))}
              </div>
            </div>
            <div className="grid gap-4 sm:grid-cols-3">
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="dsar-ref">主体标识（最小化）</Label>
                <Input
                  id="dsar-ref"
                  value={subjectRef}
                  onChange={(e) => setSubjectRef(e.target.value)}
                  placeholder="例如：u-1024"
                />
              </div>
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="dsar-received">收到日期</Label>
                <Input
                  id="dsar-received"
                  type="date"
                  value={received}
                  onChange={(e) => setReceived(e.target.value)}
                />
              </div>
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="dsar-verify">验证方式</Label>
                <Input
                  id="dsar-verify"
                  value={verification}
                  onChange={(e) => setVerification(e.target.value)}
                  placeholder="例如：已登录会话 / 邮件匹配"
                />
              </div>
            </div>
            <div className="flex justify-end">
              <Button onClick={handleCreate} disabled={types.length === 0 || submitting}>
                {submitting ? "创建中……" : "创建档案"}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {loading ? (
        <div className="flex min-h-[30vh] items-center justify-center">
          <Spinner className="text-brand h-6 w-6" />
        </div>
      ) : items.length === 0 ? (
        <p className="text-muted-foreground rounded-xl border border-dashed px-4 py-10 text-center text-sm">
          还没有权利请求。点击「新建请求」建档。
        </p>
      ) : (
        <ul className="flex flex-col gap-2">
          {items.map((d) => (
            <li key={d.id}>
              <Link
                href={`${ROUTES.PRIVACY_DSAR}/${d.id}`}
                className="hover:border-brand/40 flex items-center gap-3 rounded-xl border p-4 transition-colors"
              >
                <div className="min-w-0 flex-1">
                  <div className="mb-1">
                    <DsarStatusBadge value={d.status} />
                  </div>
                  <p className="truncate text-sm font-medium">
                    {(d.request_types || []).join(" / ") || "请求"} · {d.data_subject_ref || "—"}
                  </p>
                  <p className="text-muted-foreground truncate text-xs">
                    收到 {d.date_received || "—"}
                    {d.response_deadline ? ` · 截止 ${d.response_deadline}` : ""}
                  </p>
                </div>
                {d.escalation_flag && (
                  <span className="rounded-full bg-red-50 px-2 py-0.5 text-xs font-medium text-red-700 dark:bg-red-950/40 dark:text-red-300">
                    需升级
                  </span>
                )}
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
