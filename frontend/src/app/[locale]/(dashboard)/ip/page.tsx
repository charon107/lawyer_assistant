"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useTranslations } from "next-intl";
import { Button, Card, CardContent, Spinner } from "@/components/ui";
import { ClassificationBadge, NotificationArea, ReviewTypeBadge } from "@/components/ip";
import { ROUTES } from "@/lib/constants";
import { ipApi } from "@/lib/ip";
import type { IpModuleStatusResponse, IpReview } from "@/types/ip";
import {
  Lightbulb,
  SearchCheck,
  ScanSearch,
  FlaskConical,
  ShieldAlert,
  FileText,
  PackageCheck,
  Megaphone,
  BadgeCheck,
  ArrowRight,
  Sparkles,
  Settings2,
} from "lucide-react";

export default function IpPage() {
  const t = useTranslations("ip");
  const router = useRouter();
  const [status, setStatus] = useState<IpModuleStatusResponse | null>(null);
  const [reviews, setReviews] = useState<IpReview[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const QUICK_ACTIONS = [
    { href: ROUTES.IP_CLEARANCE, icon: SearchCheck, key: "clearance" as const },
    { href: ROUTES.IP_FTO, icon: ScanSearch, key: "fto" as const },
    { href: ROUTES.IP_INVENTION, icon: FlaskConical, key: "invention" as const },
    { href: ROUTES.IP_INFRINGEMENT, icon: ShieldAlert, key: "infringement" as const },
    { href: ROUTES.IP_CLAUSE, icon: FileText, key: "ipClause" as const },
    { href: ROUTES.IP_OSS, icon: PackageCheck, key: "oss" as const },
    { href: ROUTES.IP_ENFORCEMENT, icon: Megaphone, key: "enforcement" as const },
    { href: ROUTES.IP_PORTFOLIO, icon: BadgeCheck, key: "portfolio" as const },
    { href: ROUTES.IP_SETTINGS, icon: Settings2, key: "settings" as const },
  ];

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const s = await ipApi.getStatus();
        if (cancelled) return;
        setStatus(s);
        if (s.configured) {
          const rList = await ipApi.listReviews(0, 6);
          if (!cancelled) setReviews(rList.items);
        }
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : "Failed to load");
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
          <Lightbulb className="text-brand h-6 w-6" />
          {t("title")}
        </h1>
        <p className="text-muted-foreground">{t("description")}</p>
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
              <h2 className="mb-1 text-lg font-semibold">{t("unconfiguredTitle")}</h2>
              <p className="text-muted-foreground text-sm">{t("unconfiguredDesc")}</p>
            </div>
            <Button onClick={() => router.push(ROUTES.IP_SETUP)}>
              {t("startSetup")}
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
                    <h3 className="font-medium">{t(`actions.${a.key}.title`)}</h3>
                    <p className="text-muted-foreground text-sm">{t(`actions.${a.key}.desc`)}</p>
                  </CardContent>
                </Card>
              </Link>
            ))}
          </div>

          <section>
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-sm font-semibold tracking-wide uppercase">
                {t("recentOutputs")}
              </h2>
              <Link href={ROUTES.IP_REVIEWS}>
                <Button variant="ghost" size="sm">
                  {t("viewAll")}
                  <ArrowRight className="ml-1 h-4 w-4" />
                </Button>
              </Link>
            </div>
            {reviews.length === 0 ? (
              <p className="text-muted-foreground rounded-xl border border-dashed px-4 py-8 text-center text-sm">
                {t("noOutputs")}
              </p>
            ) : (
              <ul className="flex flex-col gap-2">
                {reviews.map((r) => (
                  <li key={r.id}>
                    <Link
                      href={`${ROUTES.IP_REVIEWS}/${r.id}`}
                      className="hover:border-brand/40 flex items-center gap-3 rounded-xl border p-4 transition-colors"
                    >
                      <div className="min-w-0 flex-1">
                        <div className="mb-1 flex items-center gap-2">
                          <ReviewTypeBadge value={r.review_type} />
                          <ClassificationBadge value={r.classification} />
                        </div>
                        <p className="truncate text-sm font-medium">{r.subject || t("unnamed")}</p>
                        <p className="text-muted-foreground truncate text-xs">
                          {r.result_summary || t("inProgress")}
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
