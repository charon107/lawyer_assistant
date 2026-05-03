
"use client";

import { useEffect } from "react";
import Link from "next/link";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Page error:", error);
  }, [error]);

  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center px-4 text-center">
      <p className="text-sm font-semibold uppercase tracking-wider text-red-500">错误</p>
      <h1 className="mt-2 text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
        出了点问题
      </h1>
      <p className="mt-3 max-w-md text-muted-foreground">
        加载此页面时发生错误，请重试。
      </p>
      {error.digest && (
        <p className="mt-1 text-xs text-muted-foreground/60">错误 ID: {error.digest}</p>
      )}
      <div className="mt-6 flex gap-3">
        <button
          onClick={reset}
          className="bg-brand text-brand-foreground hover:bg-brand/90 rounded-lg px-4 py-2 text-sm font-medium transition-colors"
        >
          重试
        </button>
        <Link
          href="/"
          className="bg-secondary text-secondary-foreground hover:bg-secondary/80 rounded-lg px-4 py-2 text-sm font-medium transition-colors"
        >
          返回首页
        </Link>
      </div>
    </div>
  );
}
