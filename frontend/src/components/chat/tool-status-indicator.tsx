"use client";

import { Loader2 } from "lucide-react";

interface ToolStatusIndicatorProps {
  label: string;
  toolName: string;
}

export function ToolStatusIndicator({ label, toolName }: ToolStatusIndicatorProps) {
  return (
    <div className="text-muted-foreground flex animate-pulse items-center gap-2 px-3 py-2 text-sm">
      <Loader2 className="text-primary h-3.5 w-3.5 animate-spin" />
      <span>{label}</span>
      <span className="text-xs opacity-60">{toolName}</span>
    </div>
  );
}
