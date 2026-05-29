"use client";

import { cn } from "@/lib/utils";
import { Zap, ListChecks } from "lucide-react";

/**
 * Step 0 — pick quick vs. full setup, and who will use the module.
 * The chosen mode flows to the request's `quick_mode` flag.
 */

interface StepModeProps {
  quickMode: boolean;
  usedBy: "lawyer" | "non_lawyer";
  onQuickModeChange: (quick: boolean) => void;
  onUsedByChange: (who: "lawyer" | "non_lawyer") => void;
}

function ModeCard({
  active,
  title,
  desc,
  icon: Icon,
  onClick,
}: {
  active: boolean;
  title: string;
  desc: string;
  icon: React.ElementType;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "flex flex-col items-start gap-2 rounded-xl border p-4 text-left transition-colors",
        active ? "border-brand bg-brand/5" : "hover:border-brand/40",
      )}
    >
      <Icon className={cn("h-5 w-5", active ? "text-brand" : "text-muted-foreground")} />
      <span className="font-medium">{title}</span>
      <span className="text-muted-foreground text-sm">{desc}</span>
    </button>
  );
}

export function StepMode({ quickMode, usedBy, onQuickModeChange, onUsedByChange }: StepModeProps) {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h2 className="mb-1 text-lg font-semibold">配置方式</h2>
        <p className="text-muted-foreground text-sm">选择一种配置节奏，稍后都可以在设置里继续完善。</p>
        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          <ModeCard
            active={quickMode}
            title="快速（约 2 分钟）"
            desc="只问最关键的几项，先跑起来。"
            icon={Zap}
            onClick={() => onQuickModeChange(true)}
          />
          <ModeCard
            active={!quickMode}
            title="完整（约 15 分钟）"
            desc="填齐团队信息、合同手册与上报矩阵。"
            icon={ListChecks}
            onClick={() => onQuickModeChange(false)}
          />
        </div>
      </div>

      <div>
        <h2 className="mb-1 text-lg font-semibold">谁来使用</h2>
        <p className="text-muted-foreground text-sm">这会影响报告的措辞详尽程度。</p>
        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          <ModeCard
            active={usedBy === "lawyer"}
            title="法务 / 律师"
            desc="术语精炼，直接给偏差与立场。"
            icon={ListChecks}
            onClick={() => onUsedByChange("lawyer")}
          />
          <ModeCard
            active={usedBy === "non_lawyer"}
            title="业务团队"
            desc="多一点解释，少一点黑话。"
            icon={ListChecks}
            onClick={() => onUsedByChange("non_lawyer")}
          />
        </div>
      </div>
    </div>
  );
}
