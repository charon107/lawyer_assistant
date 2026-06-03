"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft, Settings2, Loader2 } from "lucide-react";
import { Button, Card, CardContent, Input, Label, Spinner, Textarea } from "@/components/ui";
import { employmentApi } from "@/lib/employment";
import { ROUTES } from "@/lib/constants";

export default function EmploymentSettingsPage() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  // Editable fields
  const [defaultJurisdiction, setDefaultJurisdiction] = useState("");
  const [hiringTrigger, setHiringTrigger] = useState("");
  const [terminationTrigger, setTerminationTrigger] = useState("");
  const [standardSeverance, setStandardSeverance] = useState("");
  const [policyLocation, setPolicyLocation] = useState("");
  const [profileContent, setProfileContent] = useState("");

  useEffect(() => {
    let cancelled = false;
    employmentApi
      .getProfile()
      .then((p) => {
        if (cancelled) return;
        setDefaultJurisdiction((p.default_jurisdiction as string) ?? "");
        setHiringTrigger((p.hiring_trigger as string) ?? "");
        setTerminationTrigger((p.termination_trigger as string) ?? "");
        setStandardSeverance((p.standard_severance as string) ?? "");
        setPolicyLocation((p.policy_location as string) ?? "");
        setProfileContent((p.profile_content as string) ?? "");
      })
      .catch((e) => {
        if (!cancelled) setError(e instanceof Error ? e.message : "加载失败");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    setSaved(false);
    try {
      await employmentApi.updateProfile({
        default_jurisdiction: defaultJurisdiction.trim() || null,
        hiring_trigger: hiringTrigger.trim() || null,
        termination_trigger: terminationTrigger.trim() || null,
        standard_severance: standardSeverance.trim() || null,
        policy_location: policyLocation.trim() || null,
        profile_content: profileContent.trim() || null,
      });
      setSaved(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : "保存失败");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center">
        <Spinner className="text-brand h-6 w-6" />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl px-4 py-10">
      <div className="mb-8">
        <Link
          href={ROUTES.EMPLOYMENT}
          className="text-muted-foreground hover:text-foreground mb-4 inline-flex items-center gap-1.5 text-sm transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          返回劳动用工
        </Link>
        <h1 className="mb-1 flex items-center gap-2 text-2xl font-bold">
          <Settings2 className="text-brand h-6 w-6" />
          实践画像设置
        </h1>
        <p className="text-muted-foreground">
          更新管辖地、审查触发器和实践画像内容。修改后所有技能将使用新配置。
        </p>
      </div>

      {error && (
        <p className="border-destructive/30 bg-destructive/5 text-destructive mb-6 rounded-lg border px-4 py-2.5 text-sm">
          {error}
        </p>
      )}

      {saved && (
        <p className="border-emerald-300 bg-emerald-50 text-emerald-700 mb-6 rounded-lg border px-4 py-2.5 text-sm">
          保存成功
        </p>
      )}

      <div className="flex flex-col gap-6">
        <Card>
          <CardContent className="flex flex-col gap-4 p-6">
            <h2 className="text-sm font-semibold tracking-wide uppercase">基本设置</h2>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="set-jurisdiction">默认管辖地</Label>
              <Input
                id="set-jurisdiction"
                value={defaultJurisdiction}
                onChange={(e) => setDefaultJurisdiction(e.target.value)}
                placeholder="例如：北京"
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="set-hiring">录用审查触发条件</Label>
              <Input
                id="set-hiring"
                value={hiringTrigger}
                onChange={(e) => setHiringTrigger(e.target.value)}
                placeholder="例如：所有正式岗位入职前"
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="set-term">解除审查触发条件</Label>
              <Input
                id="set-term"
                value={terminationTrigger}
                onChange={(e) => setTerminationTrigger(e.target.value)}
                placeholder="例如：所有解除/终止劳动合同"
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="set-severance">经济补偿金标准</Label>
              <Input
                id="set-severance"
                value={standardSeverance}
                onChange={(e) => setStandardSeverance(e.target.value)}
                placeholder="例如：N+1"
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="set-policy">制度存放位置</Label>
              <Input
                id="set-policy"
                value={policyLocation}
                onChange={(e) => setPolicyLocation(e.target.value)}
                placeholder="例如：共享盘/HR系统"
              />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="flex flex-col gap-4 p-6">
            <h2 className="text-sm font-semibold tracking-wide uppercase">实践画像（Markdown）</h2>
            <p className="text-muted-foreground text-xs">
              画像内容会作为上下文注入所有 Agent 技能。可以包含你的实践重点、常见问题、内部流程等。
            </p>
            <Textarea
              value={profileContent}
              onChange={(e) => setProfileContent(e.target.value)}
              rows={12}
              placeholder="# 实践画像&#10;&#10;## 重点业务领域&#10;..."
              className="font-mono text-xs"
            />
          </CardContent>
        </Card>

        <div className="flex justify-end">
          <Button onClick={handleSave} disabled={saving}>
            {saving && <Loader2 className="mr-1.5 h-4 w-4 animate-spin" />}
            保存设置
          </Button>
        </div>
      </div>
    </div>
  );
}
