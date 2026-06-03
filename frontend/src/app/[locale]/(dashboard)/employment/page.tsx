"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Button, Card, CardContent, Spinner } from "@/components/ui";
import { NotificationArea } from "@/components/employment";
import { ROUTES } from "@/lib/constants";
import { employmentApi } from "@/lib/employment";
import type {
  EmploymentModuleStatusResponse,
  EmploymentReview,
  LeaveRegistration,
} from "@/types/employment";
import {
  Users,
  FileSearch,
  CalendarClock,
  Search,
  MapPin,
  ArrowRight,
  Sparkles,
  Settings2,
} from "lucide-react";

const RESULT_DOT: Record<string, string> = {
  green: "bg-emerald-500",
  yellow: "bg-amber-500",
  red: "bg-red-500",
  in_progress: "bg-muted-foreground/40",
};

const LEAVE_TYPE_LABEL: Record<string, string> = {
  annual: "年休假",
  sick: "病假/医疗期",
  maternity: "产假",
  paternity: "陪产假",
  parental: "育儿假",
  marriage: "婚假",
  work_injury: "工伤假",
};

export default function EmploymentPage() {
  const router = useRouter();
  const [status, setStatus] = useState<EmploymentModuleStatusResponse | null>(null);
  const [reviews, setReviews] = useState<EmploymentReview[]>([]);
  const [leaves, setLeaves] = useState<LeaveRegistration[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const s = await employmentApi.getStatus();
        if (cancelled) return;
        setStatus(s);
        if (s.configured) {
          const [rList, lList] = await Promise.all([
            employmentApi.listReviews(0, 5),
            employmentApi.listLeaves(0, 5),
          ]);
          if (!cancelled) {
            setReviews(rList.items);
            setLeaves(lList.items);
          }
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
          <Users className="text-brand h-6 w-6" />
          劳动用工
        </h1>
        <p className="text-muted-foreground">
          录用/解除审查、假期管理、内部调查与异地扩张，依据《劳动合同法》及各省实施细则。
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
              <h2 className="mb-1 text-lg font-semibold">尚未完成劳动用工模块配置</h2>
              <p className="text-muted-foreground text-sm">
                先用几分钟告诉我们你的实践场景、管辖地和审查触发器，之后所有技能都会自动适配。
              </p>
            </div>
            <Button onClick={() => router.push(ROUTES.EMPLOYMENT_SETUP)}>
              开始配置
              <ArrowRight className="ml-1.5 h-4 w-4" />
            </Button>
          </CardContent>
        </Card>
      ) : (
        <>
          <NotificationArea />

          {/* Quick actions */}
          <div className="mb-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <Link href={ROUTES.EMPLOYMENT_REVIEW}>
              <Card className="hover:border-brand/40 h-full transition-colors">
                <CardContent className="flex flex-col gap-2 p-5">
                  <FileSearch className="text-brand h-5 w-5" />
                  <h3 className="font-medium">用工审查</h3>
                  <p className="text-muted-foreground text-sm">
                    录用/解除/认定/制度审查，AI 流式分析。
                  </p>
                </CardContent>
              </Card>
            </Link>
            <Link href={ROUTES.EMPLOYMENT_LEAVES}>
              <Card className="hover:border-brand/40 h-full transition-colors">
                <CardContent className="flex flex-col gap-2 p-5">
                  <CalendarClock className="text-brand h-5 w-5" />
                  <h3 className="font-medium">假期管理</h3>
                  <p className="text-muted-foreground text-sm">
                    登记假期、按紧急度看板、到期预警。
                  </p>
                </CardContent>
              </Card>
            </Link>
            <Link href={ROUTES.EMPLOYMENT_INVESTIGATIONS}>
              <Card className="hover:border-brand/40 h-full transition-colors">
                <CardContent className="flex flex-col gap-2 p-5">
                  <Search className="text-brand h-5 w-5" />
                  <h3 className="font-medium">内部调查</h3>
                  <p className="text-muted-foreground text-sm">
                    结构化调查日志、来源清单、备忘录。
                  </p>
                </CardContent>
              </Card>
            </Link>
            <Link href={ROUTES.EMPLOYMENT_EXPANSIONS}>
              <Card className="hover:border-brand/40 h-full transition-colors">
                <CardContent className="flex flex-col gap-2 p-5">
                  <MapPin className="text-brand h-5 w-5" />
                  <h3 className="font-medium">异地扩张</h3>
                  <p className="text-muted-foreground text-sm">
                    省际扩张合规分析与追踪。
                  </p>
                </CardContent>
              </Card>
            </Link>
            <Link href={ROUTES.EMPLOYMENT_SETTINGS}>
              <Card className="hover:border-brand/40 h-full transition-colors">
                <CardContent className="flex flex-col gap-2 p-5">
                  <Settings2 className="text-brand h-5 w-5" />
                  <h3 className="font-medium">实践画像设置</h3>
                  <p className="text-muted-foreground text-sm">
                    更新管辖地、审查触发器、高风险标记。
                  </p>
                </CardContent>
              </Card>
            </Link>
          </div>

          {/* Recent reviews */}
          <section className="mb-8">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-sm font-semibold tracking-wide uppercase">最近审查</h2>
              <Link href={ROUTES.EMPLOYMENT_REVIEW}>
                <Button variant="ghost" size="sm">
                  全部
                  <ArrowRight className="ml-1 h-4 w-4" />
                </Button>
              </Link>
            </div>
            {reviews.length === 0 ? (
              <p className="text-muted-foreground rounded-xl border border-dashed px-4 py-8 text-center text-sm">
                还没有审查记录。
              </p>
            ) : (
              <ul className="flex flex-col gap-2">
                {reviews.map((r) => (
                  <li key={r.id}>
                    <Link
                      href={`${ROUTES.EMPLOYMENT_REVIEW}/${r.id}`}
                      className="hover:border-brand/40 flex items-center gap-3 rounded-xl border p-4 transition-colors"
                    >
                      <span
                        className={`h-2.5 w-2.5 shrink-0 rounded-full ${
                          RESULT_DOT[r.result_status ?? "in_progress"]
                        }`}
                      />
                      <div className="min-w-0 flex-1">
                        <p className="truncate text-sm font-medium">
                          {r.employee_name || r.position || r.review_type}
                        </p>
                        <p className="text-muted-foreground truncate text-xs">
                          {r.result_summary || "审查进行中"}
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

          {/* Recent leaves */}
          <section>
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-sm font-semibold tracking-wide uppercase">近期假期</h2>
              <Link href={ROUTES.EMPLOYMENT_LEAVES}>
                <Button variant="ghost" size="sm">
                  全部
                  <ArrowRight className="ml-1 h-4 w-4" />
                </Button>
              </Link>
            </div>
            {leaves.length === 0 ? (
              <p className="text-muted-foreground rounded-xl border border-dashed px-4 py-8 text-center text-sm">
                还没有假期登记。
              </p>
            ) : (
              <ul className="flex flex-col gap-2">
                {leaves.map((lv) => (
                  <li key={lv.id}>
                    <Link
                      href={ROUTES.EMPLOYMENT_LEAVES}
                      className="hover:border-brand/40 flex items-center gap-3 rounded-xl border p-4 transition-colors"
                    >
                      <div className="min-w-0 flex-1">
                        <p className="truncate text-sm font-medium">
                          {lv.employee_name || "未命名"} — {LEAVE_TYPE_LABEL[lv.leave_type] || lv.leave_type}
                        </p>
                        <p className="text-muted-foreground truncate text-xs">
                          {lv.jurisdiction} · {lv.status}
                        </p>
                      </div>
                      <time className="text-muted-foreground shrink-0 text-xs">
                        {new Date(lv.created_at).toLocaleDateString("zh-CN")}
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
