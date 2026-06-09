"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Button, Card, CardContent, Spinner } from "@/components/ui";
import { NotificationArea, ReviewTypeBadge, TriageClassificationBadge } from "@/components/privacy";
import { ROUTES } from "@/lib/constants";
import { privacyApi } from "@/lib/privacy";
import type { PrivacyModuleStatusResponse, PrivacyReview } from "@/types/privacy";
import {
  ShieldCheck,
  ListChecks,
  FileSignature,
  ClipboardCheck,
  Scale,
  MailQuestion,
  Radar,
  ArrowRight,
  Sparkles,
  Settings2,
} from "lucide-react";

const QUICK_ACTIONS = [
  {
    href: ROUTES.PRIVACY_TRIAGE,
    icon: ListChecks,
    title: "处理活动分诊",
    desc: "判断是否需要 PIA / 是否触发个保法第55条法定评估。",
  },
  {
    href: ROUTES.PRIVACY_DPA,
    icon: FileSignature,
    title: "DPA 审查（双向）",
    desc: "自动识别受托处理者 / 处理者，逐条对照操作手册。",
  },
  {
    href: ROUTES.PRIVACY_PIA,
    icon: ClipboardCheck,
    title: "影响评估 (PIA)",
    desc: "按内部格式生成个人信息保护影响评估。",
  },
  {
    href: ROUTES.PRIVACY_DSAR,
    icon: MailQuestion,
    title: "主体权利响应",
    desc: "验证→定位→豁免→起草确认函与实质回复函。",
  },
  {
    href: ROUTES.PRIVACY_GAP,
    icon: Scale,
    title: "法规差距分析",
    desc: "新法规 vs 现行处理规则，输出整改计划。",
  },
  {
    href: ROUTES.PRIVACY_POLICY_MONITOR,
    icon: Radar,
    title: "处理规则监控",
    desc: "扫描漂移或对拟议实践做直接查询。",
  },
  {
    href: ROUTES.PRIVACY_SETTINGS,
    icon: Settings2,
    title: "实践画像设置",
    desc: "更新监管覆盖、DPA 操作手册、DSAR 流程。",
  },
] as const;

export default function PrivacyPage() {
  const router = useRouter();
  const [status, setStatus] = useState<PrivacyModuleStatusResponse | null>(null);
  const [reviews, setReviews] = useState<PrivacyReview[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const s = await privacyApi.getStatus();
        if (cancelled) return;
        setStatus(s);
        if (s.configured) {
          const rList = await privacyApi.listReviews(0, 6);
          if (!cancelled) setReviews(rList.items);
        }
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : "加载失败");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center">
        <Spinner className="text-brand h-6 w-6" />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl px-4 py-10">
      <div className="mb-8">
        <h1 className="mb-1 flex items-center gap-2 text-2xl font-bold">
          <ShieldCheck className="text-brand h-6 w-6" />
          个人信息保护
        </h1>
        <p className="text-muted-foreground">
          处理活动分诊、影响评估、DPA 审查、主体权利响应、法规差距与处理规则监控，依据《个人信息保护法》《数据安全法》《网络安全法》。
        </p>
      </div>

      {error && (
        <p className="border-destructive/30 bg-destructive/5 text-destructive mb-6 rounded-lg border px-4 py-2.5 text-sm">
          {error}
        </p>
      )}

      {!status?.configured ? (
        <Card className="border-brand/20 bg-brand/5">
          <CardContent className="flex flex-col items-start gap-4 p-6">
            <div className="bg-brand/10 flex h-11 w-11 items-center justify-center rounded-xl">
              <Sparkles className="text-brand h-5 w-5" />
            </div>
            <div>
              <h2 className="mb-1 text-lg font-semibold">尚未完成个人信息保护模块配置</h2>
              <p className="text-muted-foreground text-sm">
                先用几分钟告诉我们你的监管覆盖范围、DPA 立场和内部规范，之后所有技能都会自动适配。
              </p>
            </div>
            <Button onClick={() => router.push(ROUTES.PRIVACY_SETUP)}>
              开始配置
              <ArrowRight className="ml-1.5 h-4 w-4" />
            </Button>
          </CardContent>
        </Card>
      ) : (
        <>
          <NotificationArea />

          <div className="mb-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {QUICK_ACTIONS.map((a) => (
              <Link key={a.href} href={a.href}>
                <Card className="hover:border-brand/40 h-full transition-colors">
                  <CardContent className="flex flex-col gap-2 p-5">
                    <a.icon className="text-brand h-5 w-5" />
                    <h3 className="font-medium">{a.title}</h3>
                    <p className="text-muted-foreground text-sm">{a.desc}</p>
                  </CardContent>
                </Card>
              </Link>
            ))}
          </div>

          <section>
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-sm font-semibold tracking-wide uppercase">最近产出</h2>
              <Link href={ROUTES.PRIVACY_REVIEWS}>
                <Button variant="ghost" size="sm">
                  全部
                  <ArrowRight className="ml-1 h-4 w-4" />
                </Button>
              </Link>
            </div>
            {reviews.length === 0 ? (
              <p className="text-muted-foreground rounded-xl border border-dashed px-4 py-8 text-center text-sm">
                还没有分析产出。
              </p>
            ) : (
              <ul className="flex flex-col gap-2">
                {reviews.map((r) => (
                  <li key={r.id}>
                    <Link
                      href={`${ROUTES.PRIVACY_REVIEWS}/${r.id}`}
                      className="hover:border-brand/40 flex items-center gap-3 rounded-xl border p-4 transition-colors"
                    >
                      <div className="min-w-0 flex-1">
                        <div className="mb-1 flex items-center gap-2">
                          <ReviewTypeBadge value={r.review_type} />
                          <TriageClassificationBadge value={r.classification} />
                        </div>
                        <p className="truncate text-sm font-medium">{r.subject || "（未命名）"}</p>
                        <p className="text-muted-foreground truncate text-xs">
                          {r.result_summary || "进行中"}
                        </p>
                      </div>
                      <time className="text-muted-foreground shrink-0 text-xs">
                        {new Date(r.created_at).toLocaleDateString("zh-CN")}
                      </time>
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </>
      )}
    </div>
  );
}
