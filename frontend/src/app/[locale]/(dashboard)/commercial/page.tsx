"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Button, Card, CardContent, Spinner } from "@/components/ui";
import { ROUTES } from "@/lib/constants";
import { commercialApi } from "@/lib/commercial";
import type { ContractReview, ModuleStatusResponse } from "@/types/commercial";
import { ScrollText, FileSearch, Settings2, ArrowRight, Sparkles } from "lucide-react";

const SIDE_LABEL: Record<string, string> = {
  purchasing: "采购方",
  sales: "销售方",
  both: "采购 / 销售",
};

const RESULT_DOT: Record<string, string> = {
  green: "bg-emerald-500",
  yellow: "bg-amber-500",
  red: "bg-red-500",
  in_progress: "bg-muted-foreground/40",
};

export default function CommercialPage() {
  const router = useRouter();
  const [status, setStatus] = useState<ModuleStatusResponse | null>(null);
  const [reviews, setReviews] = useState<ContractReview[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const s = await commercialApi.getStatus();
        if (cancelled) return;
        setStatus(s);
        if (s.configured) {
          const list = await commercialApi.listReviews(0, 10);
          if (!cancelled) setReviews(list.items);
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
          <ScrollText className="text-brand h-6 w-6" />
          商事合同
        </h1>
        <p className="text-muted-foreground">
          按你团队的合同手册审查供应商协议，逐条标出与标准立场的偏差。
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
              <h2 className="mb-1 text-lg font-semibold">还没有配置合同手册</h2>
              <p className="text-muted-foreground text-sm">
                先用几分钟告诉我们你的团队信息、合同手册（标准 / 底线 / 红线）和上报矩阵，
                之后每份合同都能自动对照审查。
              </p>
            </div>
            <Button onClick={() => router.push(ROUTES.COMMERCIAL_SETUP)}>
              开始配置
              <ArrowRight className="ml-1.5 h-4 w-4" />
            </Button>
          </CardContent>
        </Card>
      ) : (
        <>
          {/* Quick actions */}
          <div className="mb-8 grid gap-4 sm:grid-cols-2">
            <Link href={ROUTES.COMMERCIAL_REVIEW}>
              <Card className="hover:border-brand/40 h-full transition-colors">
                <CardContent className="flex flex-col gap-2 p-5">
                  <FileSearch className="text-brand h-5 w-5" />
                  <h3 className="font-medium">审查新合同</h3>
                  <p className="text-muted-foreground text-sm">
                    上传或粘贴合同，AI 逐条对照手册产出偏差报告。
                  </p>
                </CardContent>
              </Card>
            </Link>
            <Link href={ROUTES.COMMERCIAL_SETUP}>
              <Card className="hover:border-brand/40 h-full transition-colors">
                <CardContent className="flex flex-col gap-2 p-5">
                  <Settings2 className="text-brand h-5 w-5" />
                  <h3 className="font-medium">
                    手册设置
                    <span className="text-muted-foreground ml-2 text-xs font-normal">
                      {SIDE_LABEL[status.side ?? "purchasing"]}
                    </span>
                  </h3>
                  <p className="text-muted-foreground text-sm">
                    更新团队信息、核心条款立场与上报规则。
                  </p>
                </CardContent>
              </Card>
            </Link>
          </div>

          {/* Recent reviews */}
          <div>
            <h2 className="mb-3 text-sm font-semibold tracking-wide uppercase">
              最近审查
            </h2>
            {reviews.length === 0 ? (
              <p className="text-muted-foreground rounded-xl border border-dashed px-4 py-8 text-center text-sm">
                还没有审查记录。审查第一份合同后会显示在这里。
              </p>
            ) : (
              <ul className="flex flex-col gap-2">
                {reviews.map((r) => (
                  <li key={r.id}>
                    <div className="hover:border-brand/40 flex items-center gap-3 rounded-xl border p-4 transition-colors">
                      <span
                        className={`h-2.5 w-2.5 shrink-0 rounded-full ${
                          RESULT_DOT[r.result_status ?? "in_progress"]
                        }`}
                      />
                      <div className="min-w-0 flex-1">
                        <p className="truncate text-sm font-medium">
                          {r.agreement_name || r.counterparty || "未命名合同"}
                        </p>
                        <p className="text-muted-foreground truncate text-xs">
                          {r.result_summary || "审查进行中"}
                        </p>
                      </div>
                      <time className="text-muted-foreground shrink-0 text-xs">
                        {new Date(r.created_at).toLocaleDateString("zh-CN")}
                      </time>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </>
      )}
    </div>
  );
}
