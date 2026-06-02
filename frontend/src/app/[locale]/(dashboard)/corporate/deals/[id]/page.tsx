"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { Badge, Button, Card, CardContent, Input, Label, Spinner, Textarea } from "@/components/ui";
import { ROUTES } from "@/lib/constants";
import { corporateApi } from "@/lib/corporate";
import { useCorporateChat } from "@/hooks/use-corporate-chat";
import type { CorporateWsAction } from "@/types/corporate";
import type {
  ClosingChecklistItem,
  CorporateDeal,
  DiligenceIssue,
  MaterialContractItem,
  VdrDocument,
} from "@/types/corporate";
import { ArrowLeft, Plus } from "lucide-react";

type Tab = "diligence" | "checklist" | "material" | "vdr";

const TABS: { key: Tab; label: string }[] = [
  { key: "diligence", label: "尽调问题" },
  { key: "checklist", label: "交割检查表" },
  { key: "material", label: "重大合同" },
  { key: "vdr", label: "数据室" },
];

const SEVERITY_VARIANT: Record<string, "destructive" | "default" | "secondary"> = {
  blocking: "destructive",
  high: "destructive",
  medium: "default",
  low: "secondary",
};

const inputCls = "border-input bg-background mt-1 h-9 w-full rounded-md border px-3 text-sm";

export default function CorporateDealDetailPage() {
  const params = useParams();
  const dealId = String(params.id);

  const [deal, setDeal] = useState<CorporateDeal | null>(null);
  const [tab, setTab] = useState<Tab>("diligence");
  const [diligence, setDiligence] = useState<DiligenceIssue[]>([]);
  const [checklist, setChecklist] = useState<ClosingChecklistItem[]>([]);
  const [material, setMaterial] = useState<MaterialContractItem[]>([]);
  const [vdr, setVdr] = useState<VdrDocument[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState<Record<string, string>>({});
  const [aiPrompt, setAiPrompt] = useState("");

  const reload = useCallback(async () => {
    try {
      const [d, dil, chk, mat, docs] = await Promise.all([
        corporateApi.getDeal(dealId),
        corporateApi.listDiligence(dealId),
        corporateApi.listChecklist(dealId),
        corporateApi.listMaterialContracts(dealId),
        corporateApi.listVdr(dealId),
      ]);
      setDeal(d);
      setDiligence(dil.items);
      setChecklist(chk.items);
      setMaterial(mat.items);
      setVdr(docs.items);
    } catch (e) {
      setError(e instanceof Error ? e.message : "加载失败");
    } finally {
      setLoading(false);
    }
  }, [dealId]);

  useEffect(() => {
    reload();
  }, [reload]);

  const chat = useCorporateChat(reload);
  const [promptError, setPromptError] = useState<string | null>(null);

  function runAi(action: CorporateWsAction) {
    if (!aiPrompt.trim()) {
      setPromptError("请先粘贴数据室文本或输入指令，再运行 AI。");
      return;
    }
    setPromptError(null);
    chat.runSkill({
      action,
      deal_id: dealId,
      prompt: aiPrompt.trim(),
      title: action === "tabular" ? "表格审查" : undefined,
    });
  }

  function switchTab(next: Tab) {
    setTab(next);
    setShowForm(false);
    setForm({});
    setError(null);
  }

  async function submitForm(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      if (tab === "diligence") {
        if (!form.title?.trim()) return;
        await corporateApi.createDiligence(dealId, {
          title: form.title.trim(),
          severity: form.severity || "medium",
          finding: form.finding || null,
          category: form.category || null,
        });
      } else if (tab === "checklist") {
        if (!form.item?.trim()) return;
        await corporateApi.createChecklistItem(dealId, {
          item: form.item.trim(),
          item_type: form.item_type || "condition",
          approval_threshold: form.approval_threshold || null,
        });
      } else if (tab === "material") {
        if (!form.contract?.trim()) return;
        await corporateApi.createMaterialContract(dealId, {
          contract: form.contract.trim(),
          counterparty: form.counterparty || null,
          threshold_basis: form.threshold_basis || null,
        });
      } else if (tab === "vdr") {
        if (!form.filename?.trim()) return;
        await corporateApi.createVdr(dealId, {
          filename: form.filename.trim(),
          category: form.category || null,
          priority: form.priority || "normal",
        });
      }
      setForm({});
      setShowForm(false);
      await reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : "保存失败");
    } finally {
      setSaving(false);
    }
  }

  const set =
    (k: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
      setForm((f) => ({ ...f, [k]: e.target.value }));

  if (loading) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center">
        <Spinner className="text-brand h-6 w-6" />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl px-4 py-10">
      <Link
        href={ROUTES.CORPORATE_DEALS}
        className="text-muted-foreground hover:text-foreground mb-4 inline-flex items-center gap-1 text-sm"
      >
        <ArrowLeft className="h-4 w-4" />
        交易工作区
      </Link>

      {error && (
        <p className="border-destructive/30 bg-destructive/5 text-destructive mb-6 rounded-lg border px-4 py-2.5 text-sm">
          {error}
        </p>
      )}

      {deal && (
        <div className="mb-6">
          <h1 className="text-2xl font-bold">{deal.code}</h1>
          <p className="text-muted-foreground text-sm">
            {deal.counterparty || "—"} · {deal.deal_type || "并购交易"} · {deal.status}
          </p>
        </div>
      )}

      <Card className="border-brand/20 bg-brand/5 mb-6">
        <CardContent className="flex flex-col gap-3 p-5">
          <div>
            <h2 className="text-sm font-semibold">AI 运行（公司并购技能）</h2>
            <p className="text-muted-foreground text-xs">
              粘贴数据室文本 / 指令，让 AI 跑尽调提取、表格化审查、重大合同清单或交易团队简报。
              结果会写入对应标签页。需先在「个人中心」配置模型。
            </p>
          </div>
          <Textarea
            value={aiPrompt}
            onChange={(e) => setAiPrompt(e.target.value)}
            placeholder="例如：审查数据室「重大合同」类别，提取控制权变更、转让限制与解除权问题。"
            rows={3}
          />
          <div className="flex flex-wrap gap-2">
            <Button
              size="sm"
              disabled={chat.status === "running" || chat.status === "connecting"}
              onClick={() => runAi("diligence")}
            >
              跑尽调提取
            </Button>
            <Button
              size="sm"
              variant="secondary"
              disabled={chat.status === "running" || chat.status === "connecting"}
              onClick={() => runAi("tabular")}
            >
              表格化审查
            </Button>
            <Button
              size="sm"
              variant="secondary"
              disabled={chat.status === "running" || chat.status === "connecting"}
              onClick={() => runAi("material")}
            >
              生成重大合同清单
            </Button>
            <Button
              size="sm"
              variant="ghost"
              disabled={chat.status === "running" || chat.status === "connecting"}
              onClick={() => runAi("summary")}
            >
              交易团队简报
            </Button>
          </div>
          {(chat.status === "connecting" || chat.status === "running") && (
            <div className="text-muted-foreground flex items-center gap-2 text-xs">
              <Spinner className="h-3.5 w-3.5" />
              {chat.status === "connecting" ? "连接中…" : "AI 运行中…"}
            </div>
          )}
          {promptError && <p className="text-destructive text-xs">{promptError}</p>}
          {chat.error && <p className="text-destructive text-xs">{chat.error}</p>}
          {(chat.streamingText || chat.finalOutput) && (
            <pre className="bg-background max-h-72 overflow-auto rounded-lg border p-3 text-xs whitespace-pre-wrap">
              {chat.finalOutput || chat.streamingText}
            </pre>
          )}
        </CardContent>
      </Card>

      <div className="mb-4 flex items-center justify-between border-b">
        <div className="flex gap-2">
          {TABS.map((t) => (
            <button
              key={t.key}
              onClick={() => switchTab(t.key)}
              className={`-mb-px border-b-2 px-3 py-2 text-sm ${
                tab === t.key
                  ? "border-brand text-brand font-medium"
                  : "text-muted-foreground border-transparent"
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>
        <Button size="sm" variant="ghost" onClick={() => setShowForm((v) => !v)}>
          <Plus className="mr-1 h-4 w-4" />
          新增
        </Button>
      </div>

      {showForm && (
        <Card className="mb-4">
          <CardContent className="p-5">
            <form onSubmit={submitForm} className="flex flex-col gap-3">
              {tab === "diligence" && (
                <>
                  <Field label="问题标题 *">
                    <Input value={form.title ?? ""} onChange={set("title")} required />
                  </Field>
                  <Field label="严重程度">
                    <select
                      className={inputCls}
                      value={form.severity ?? "medium"}
                      onChange={set("severity")}
                    >
                      <option value="blocking">阻断</option>
                      <option value="high">高</option>
                      <option value="medium">中</option>
                      <option value="low">低</option>
                    </select>
                  </Field>
                  <Field label="发现说明">
                    <Input value={form.finding ?? ""} onChange={set("finding")} />
                  </Field>
                </>
              )}
              {tab === "checklist" && (
                <>
                  <Field label="事项 *">
                    <Input value={form.item ?? ""} onChange={set("item")} required />
                  </Field>
                  <Field label="类型">
                    <select
                      className={inputCls}
                      value={form.item_type ?? "condition"}
                      onChange={set("item_type")}
                    >
                      <option value="condition">交割条件</option>
                      <option value="consent">同意</option>
                      <option value="document">文件</option>
                      <option value="filing">申报</option>
                      <option value="shareholder_vote">股东表决</option>
                      <option value="regulatory">监管</option>
                      <option value="release">解除</option>
                    </select>
                  </Field>
                  <Field label="批准门槛">
                    <Input
                      value={form.approval_threshold ?? ""}
                      onChange={set("approval_threshold")}
                    />
                  </Field>
                </>
              )}
              {tab === "material" && (
                <>
                  <Field label="合同 *">
                    <Input value={form.contract ?? ""} onChange={set("contract")} required />
                  </Field>
                  <Field label="对方当事人">
                    <Input value={form.counterparty ?? ""} onChange={set("counterparty")} />
                  </Field>
                  <Field label="满足的重大性条件">
                    <Input
                      value={form.threshold_basis ?? ""}
                      onChange={set("threshold_basis")}
                    />
                  </Field>
                </>
              )}
              {tab === "vdr" && (
                <>
                  <Field label="文件名 *">
                    <Input value={form.filename ?? ""} onChange={set("filename")} required />
                  </Field>
                  <Field label="需求类别">
                    <Input
                      value={form.category ?? ""}
                      onChange={set("category")}
                      placeholder="如 重大合同 / 知识产权"
                    />
                  </Field>
                  <Field label="优先级">
                    <select
                      className={inputCls}
                      value={form.priority ?? "normal"}
                      onChange={set("priority")}
                    >
                      <option value="normal">普通</option>
                      <option value="high">高优</option>
                    </select>
                  </Field>
                </>
              )}
              <div className="flex gap-2">
                <Button type="submit" disabled={saving}>
                  {saving ? "保存中…" : "保存"}
                </Button>
                <Button type="button" variant="ghost" onClick={() => setShowForm(false)}>
                  取消
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {tab === "diligence" && (
        <ul className="flex flex-col gap-2">
          {diligence.length === 0 && (
            <Empty text="还没有尽调发现。点「新增」手动添加，或用 AI 跑尽调。" />
          )}
          {diligence.map((i) => (
            <li key={i.id}>
              <Card>
                <CardContent className="flex items-start gap-3 p-4">
                  <Badge variant={SEVERITY_VARIANT[i.severity] ?? "default"}>{i.severity}</Badge>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium">{i.title}</p>
                    {i.finding && (
                      <p className="text-muted-foreground mt-1 text-xs">{i.finding}</p>
                    )}
                    {i.source_doc && (
                      <p className="text-muted-foreground mt-1 text-xs">来源：{i.source_doc}</p>
                    )}
                  </div>
                </CardContent>
              </Card>
            </li>
          ))}
        </ul>
      )}

      {tab === "checklist" && (
        <ul className="flex flex-col gap-2">
          {checklist.length === 0 && <Empty text="还没有交割检查表事项。" />}
          {checklist.map((c) => (
            <li key={c.id} className="flex items-center gap-3 rounded-xl border p-4">
              <Badge variant={c.blocking ? "destructive" : "secondary"}>
                {c.blocking ? "阻断" : "一般"}
              </Badge>
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm">{c.item}</p>
                <p className="text-muted-foreground text-xs">
                  {c.item_type} · {c.status}
                  {c.approval_threshold ? ` · ${c.approval_threshold}` : ""}
                </p>
              </div>
            </li>
          ))}
        </ul>
      )}

      {tab === "material" && (
        <ul className="flex flex-col gap-2">
          {material.length === 0 && <Empty text="还没有重大合同清单条目。" />}
          {material.map((m) => (
            <li key={m.id} className="flex items-center gap-3 rounded-xl border p-4">
              <Badge variant={m.disclosed ? "default" : "secondary"}>
                {m.disclosed ? "已披露" : "待披露"}
              </Badge>
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm">{m.contract}</p>
                <p className="text-muted-foreground text-xs">
                  {m.counterparty || "—"}
                  {m.threshold_basis ? ` · ${m.threshold_basis}` : ""}
                </p>
              </div>
            </li>
          ))}
        </ul>
      )}

      {tab === "vdr" && (
        <ul className="flex flex-col gap-2">
          {vdr.length === 0 && <Empty text="还没有数据室文档。" />}
          {vdr.map((d) => (
            <li key={d.id} className="flex items-center gap-3 rounded-xl border p-4">
              <Badge variant={d.priority === "high" ? "destructive" : "secondary"}>
                {d.priority === "high" ? "高优" : "普通"}
              </Badge>
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm">{d.filename}</p>
                <p className="text-muted-foreground text-xs">
                  {d.category || "未分类"} · {d.status}
                </p>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <Label>{label}</Label>
      {children}
    </div>
  );
}

function Empty({ text }: { text: string }) {
  return (
    <p className="text-muted-foreground rounded-xl border border-dashed px-4 py-8 text-center text-sm">
      {text}
    </p>
  );
}
