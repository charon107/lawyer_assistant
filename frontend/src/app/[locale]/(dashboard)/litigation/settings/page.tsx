"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Button, Card, CardContent, Spinner } from "@/components/ui";
import { ROUTES } from "@/lib/constants";
import { litigationApi } from "@/lib/litigation";
import type { LitigationProfile } from "@/types/litigation";
import { Settings2 } from "lucide-react";

export default function LitigationSettingsPage() {
  const router = useRouter();
  const [profile, setProfile] = useState<LitigationProfile | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try { setProfile(await litigationApi.getProfile()); }
      catch { /* ignore */ }
      finally { setLoading(false); }
    })();
  }, []);

  if (loading) return <div className="flex min-h-[40vh] items-center justify-center"><Spinner className="text-brand h-6 w-6" /></div>;
  if (!profile) return <p className="p-10 text-center text-sm text-muted-foreground">请先完成冷启动设置。</p>;

  return (
    <div className="mx-auto max-w-lg px-4 py-10">
      <h1 className="mb-6 flex items-center gap-2 text-2xl font-bold"><Settings2 className="text-brand h-6 w-6" />争议解决设置</h1>

      <Card className="mb-4">
        <CardContent className="p-6 space-y-4">
          <h2 className="font-semibold">执业角色</h2>
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div>使用者：{profile.user_role}</div>
            <div>执业角色：{profile.practice_role}</div>
            <div>当事人：{profile.party_role}</div>
            <div>设置深度：{profile.setup_depth}</div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-6 space-y-4">
          <h2 className="font-semibold">风险校准</h2>
          <p className="text-muted-foreground text-xs">
            当前风险偏好等信息来自冷启动设置。如需修改，请重新运行冷启动或通过 PUT /litigation/profile 直接编辑。
          </p>
          <Button variant="outline" size="sm" onClick={() => router.push(ROUTES.LITIGATION_SETUP)}>
            重新运行冷启动
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
