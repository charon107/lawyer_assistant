"use client";

import { Lightbulb } from "lucide-react";

interface Finding {
  rule_id: string;
  level: string;
  finding: string;
  evidence: string;
  suggestion: string;
}

const LEVEL_COLORS: Record<string, string> = {
  "高风险": "border-destructive/30 bg-destructive/5",
  "中风险": "border-warning/30 bg-warning/5",
  "低风险": "border-warning/20 bg-warning/5",
  "未发现问题": "border-success/30 bg-success/5",
};

const LEVEL_DOT: Record<string, string> = {
  "高风险": "bg-destructive",
  "中风险": "bg-warning",
  "低风险": "bg-warning",
  "未发现问题": "bg-success",
};

export function FindingCard({ finding }: { finding: Finding }) {
  const borderColor = LEVEL_COLORS[finding.level] || LEVEL_COLORS["未发现问题"];
  const dotColor = LEVEL_DOT[finding.level] || LEVEL_DOT["未发现问题"];

  return (
    <div className={`border rounded-lg p-4 ${borderColor}`}>
      <div className="flex items-center gap-2 mb-2">
        <span className={`w-2 h-2 rounded-full ${dotColor}`} />
        <span className="text-sm font-bold">{finding.level}</span>
        <span className="text-xs text-muted-foreground">[{finding.rule_id}]</span>
      </div>
      <p className="text-sm mb-2">{finding.finding}</p>
      {finding.evidence && (
        <details className="mb-2">
          <summary className="text-xs text-muted-foreground cursor-pointer">原文引用</summary>
          <blockquote className="mt-1 p-2 bg-muted rounded text-xs text-muted-foreground border-l-2 border-border">
            {finding.evidence}
          </blockquote>
        </details>
      )}
      {finding.suggestion && (
        <p className="text-xs text-brand flex items-center gap-1">
          <Lightbulb className="h-3 w-3 shrink-0" />
          {finding.suggestion}
        </p>
      )}
    </div>
  );
}
