"use client";

import { useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, ScrollText } from "lucide-react";
import { ColdStartWizard } from "@/components/commercial";
import { ROUTES } from "@/lib/constants";

/**
 * Cold-start configuration page — hosts the 5-step wizard.
 *
 * On completion the profile row is materialized server-side, so we
 * bounce back to the commercial overview which will now show the
 * "configured" branch (quick actions + recent reviews).
 */
export default function CommercialSetupPage() {
  const router = useRouter();

  return (
    <div className="mx-auto max-w-3xl px-4 py-10">
      <div className="mb-8">
        <Link
          href={ROUTES.COMMERCIAL}
          className="text-muted-foreground hover:text-foreground mb-4 inline-flex items-center gap-1.5 text-sm transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          返回商事合同
        </Link>
        <h1 className="mb-1 flex items-center gap-2 text-2xl font-bold">
          <ScrollText className="text-brand h-6 w-6" />
          配置合同手册
        </h1>
        <p className="text-muted-foreground">
          告诉我们你的团队信息、合同手册（标准 / 底线 / 红线）和上报矩阵，之后每份合同都能自动对照审查。
        </p>
      </div>

      <ColdStartWizard onComplete={() => router.push(ROUTES.COMMERCIAL)} />
    </div>
  );
}
