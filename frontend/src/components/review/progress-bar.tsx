"use client";

const STAGE_LABELS: Record<string, string> = {
  uploading: "上传中",
  started: "开始审查",
  parsing: "解析文档",
  splitting: "拆分章节",
  extracting_facts: "提取关键事实",
  reviewing: "逐章审查中",
  cross_checking: "跨章交叉检查",
  complete: "审查完成",
  error: "错误",
};

interface ProgressBarProps {
  stage: string;
  progress: number;
  message: string;
}

export function ReviewProgressBar({ stage, progress, message }: ProgressBarProps) {
  const pct = Math.round(progress * 100);
  const label = STAGE_LABELS[stage] || stage;

  return (
    <div className="w-full space-y-2">
      <div className="flex justify-between text-sm">
        <span className="font-medium">{label}</span>
        <span className="text-muted-foreground">{pct}%</span>
      </div>
      <div className="w-full h-2 bg-muted rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ${
            stage === "error" ? "bg-destructive" :
            stage === "complete" ? "bg-success" :
            "bg-brand"
          }`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <p className="text-xs text-muted-foreground">{message}</p>
    </div>
  );
}
