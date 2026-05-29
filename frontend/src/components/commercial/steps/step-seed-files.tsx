"use client";

import { Sparkles } from "lucide-react";

/**
 * Step 4 — seed files / auto-extraction.
 *
 * Phase A deliberately ships without the 3-clause auto-extraction
 * spike (the user chose to skip it), so this step is informational:
 * it explains what the feature will do and lets the user finish.
 */

export function StepSeedFiles() {
  return (
    <div className="flex flex-col gap-5">
      <div>
        <h2 className="mb-1 text-lg font-semibold">从历史合同学习（即将推出）</h2>
        <p className="text-muted-foreground text-sm">
          后续版本将支持上传几份已签合同，自动提取「责任上限 / 赔偿 / 期限」三条的实际立场，
          再和你声明的手册对比，帮你发现「说的」和「签的」之间的差距。
        </p>
      </div>

      <div className="bg-brand/5 border-brand/20 flex items-start gap-3 rounded-xl border p-4">
        <Sparkles className="text-brand mt-0.5 h-5 w-5 shrink-0" />
        <div className="text-sm">
          <p className="font-medium">本阶段先用你手填的手册</p>
          <p className="text-muted-foreground mt-1">
            点击「完成配置」即可开始审查合同。自动学习功能上线后，会在这里提示你校准手册。
          </p>
        </div>
      </div>
    </div>
  );
}
