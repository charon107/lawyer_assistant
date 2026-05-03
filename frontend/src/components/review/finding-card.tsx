"use client";

interface Finding {
  rule_id: string;
  level: string;
  finding: string;
  evidence: string;
  suggestion: string;
}

const LEVEL_COLORS: Record<string, string> = {
  "高风险": "border-red-500/50 bg-red-500/10",
  "中风险": "border-orange-500/50 bg-orange-500/10",
  "低风险": "border-yellow-500/50 bg-yellow-500/10",
  "未发现问题": "border-green-500/50 bg-green-500/10",
};

const LEVEL_DOT: Record<string, string> = {
  "高风险": "bg-red-500",
  "中风险": "bg-orange-500",
  "低风险": "bg-yellow-500",
  "未发现问题": "bg-green-500",
};

export function FindingCard({ finding }: { finding: Finding }) {
  const borderColor = LEVEL_COLORS[finding.level] || LEVEL_COLORS["未发现问题"];
  const dotColor = LEVEL_DOT[finding.level] || LEVEL_DOT["未发现问题"];

  return (
    <div className={`border rounded-lg p-4 ${borderColor}`}>
      <div className="flex items-center gap-2 mb-2">
        <span className={`w-2 h-2 rounded-full ${dotColor}`} />
        <span className="text-sm font-bold">{finding.level}</span>
        <span className="text-xs text-zinc-500">[{finding.rule_id}]</span>
      </div>
      <p className="text-sm mb-2">{finding.finding}</p>
      {finding.evidence && (
        <details className="mb-2">
          <summary className="text-xs text-zinc-400 cursor-pointer">原文引用</summary>
          <blockquote className="mt-1 p-2 bg-zinc-900 rounded text-xs text-zinc-300 border-l-2 border-zinc-600">
            {finding.evidence}
          </blockquote>
        </details>
      )}
      {finding.suggestion && (
        <p className="text-xs text-blue-400">
          &#x1F4A1; {finding.suggestion}
        </p>
      )}
    </div>
  );
}
