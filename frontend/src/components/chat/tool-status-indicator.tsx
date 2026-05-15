"use client";

import { Loader2 } from "lucide-react";

interface ToolStatusIndicatorProps {
  label: string;
  toolName: string;
}

export function ToolStatusIndicator({ label, toolName }: ToolStatusIndicatorProps) {
  return (
    <div className="flex items-center gap-2 px-3 py-2 text-sm text-muted-foreground animate-pulse">
      <Loader2 className="h-3.5 w-3.5 animate-spin text-primary" />
      <span>{label}</span>
      <span className="text-xs opacity-60">{toolName}</span>
    </div>
  );
}
