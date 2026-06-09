"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft, Loader2, Settings2 } from "lucide-react";
import { Button, Card, CardContent, Input, Label, Spinner, Textarea } from "@/components/ui";
import { privacyApi } from "@/lib/privacy";
import { ROUTES } from "@/lib/constants";

export default function PrivacySettingsPage() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  const [regulatory, setRegulatory] = useState("");
  const [dataResidency, setDataResidency] = useState("");
  const [dpoInfo, setDpoInfo] = useState("");
  const [profileContent, setProfileContent] = useState("");

  useEffect(() => {
    let cancelled = false;
    privacyApi
      .getProfile()
      .then((p) => {
        if (cancelled) return;
        const footprint = p.regulatory_footprint;
        setRegulatory(Array.isArray(footprint) ? footprint.join("、") : "");
        setDataResidency((p.data_residency as string) ?? "");
        setDpoInfo((p.dpo_info as string) ?? "");
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
      const footprint = regulatory
        .split(/[、,，]/)
        .map((s) => s.trim())
        .filter(Boolean);
      await privacyApi.updateProfile({
        regulatory_footprint: footprint.length > 0 ? footprint : null,
        data_residency: dataResidency.trim() || null,
        dpo_info: dpoInfo.trim() || null,
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
          href={ROUTES.PRIVACY}
          className="text-muted-foreground hover:text-foreground mb-4 inline-flex items-center gap-1.5 text-sm transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          返回个人信息保护
        </Link>
        <h1 className="mb-1 flex items-center gap-2 text-2xl font-bold">
          <Settings2 className="text-brand h-6 w-6" />
          实践画像设置
        </h1>
        <p className="text-muted-foreground">
          更新监管覆盖范围、数据存储地与实践画像内容。修改后所有技能将使用新配置。
        </p>
      </div>

      {error && (
        <p className="border-destructive/30 bg-destructive/5 text-destructive mb-6 rounded-lg border px-4 py-2.5 text-sm">
          {error}
        </p>
      )}
      {saved && (
        <p className="mb-6 rounded-lg border border-emerald-300 bg-emerald-50 px-4 py-2.5 text-sm text-emerald-700">
          保存成功
        </p>
      )}

      <div className="flex flex-col gap-6">
        <Card>
          <CardContent className="flex flex-col gap-4 p-6">
            <h2 className="text-sm font-semibold tracking-wide uppercase">基本设置</h2>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="set-reg">监管覆盖范围（顿号或逗号分隔）</Label>
              <Input
                id="set-reg"
                value={regulatory}
                onChange={(e) => setRegulatory(e.target.value)}
                placeholder="例如：个人信息保护法、数据安全法、网络安全法"
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="set-residency">数据存储地</Label>
              <Input
                id="set-residency"
                value={dataResidency}
                onChange={(e) => setDataResidency(e.target.value)}
                placeholder="例如：仅中国境内 / 多区域部署"
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="set-dpo">个人信息保护负责人 / 升级联系人</Label>
              <Input
                id="set-dpo"
                value={dpoInfo}
                onChange={(e) => setDpoInfo(e.target.value)}
                placeholder="例如：法务总监 张三"
              />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="flex flex-col gap-4 p-6">
            <h2 className="text-sm font-semibold tracking-wide uppercase">实践画像（Markdown）</h2>
            <p className="text-muted-foreground text-xs">
              画像内容会作为上下文注入所有 Agent 技能，可包含 DPA 操作手册、处理规则承诺、PIA 内部规范、DSAR 流程等。
            </p>
            <Textarea
              value={profileContent}
              onChange={(e) => setProfileContent(e.target.value)}
              rows={14}
              placeholder="# 个人信息保护实践画像&#10;&#10;## DPA 操作手册&#10;...&#10;## 处理规则承诺&#10;...&#10;## DSAR 流程&#10;..."
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
