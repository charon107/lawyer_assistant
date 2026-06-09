"use client";

import { useEffect, useState } from "react";
import { Bell, ShieldAlert, type LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";
import { privacyApi } from "@/lib/privacy";
import type { PrivacyNotification } from "@/types/privacy";

const TYPE_META: Record<string, { icon: LucideIcon; cls: string }> = {
  policy_sweep_reminder: {
    icon: ShieldAlert,
    cls: "bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-300",
  },
  manual: {
    icon: Bell,
    cls: "bg-brand/10 text-brand",
  },
};

const FALLBACK_META = {
  icon: Bell,
  cls: "bg-stone-100 text-stone-600 dark:bg-stone-900/40 dark:text-stone-300",
} as const;

export function NotificationArea() {
  const [items, setItems] = useState<PrivacyNotification[]>([]);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await privacyApi.listNotifications(0, 20);
        if (!cancelled) setItems(res.items);
      } catch {
        // Non-critical.
      } finally {
        if (!cancelled) setLoaded(true);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  async function markRead(id: string) {
    const target = items.find((n) => n.id === id);
    if (!target || target.read) return;
    setItems((prev) => prev.map((n) => (n.id === id ? { ...n, read: true } : n)));
    try {
      await privacyApi.markNotificationRead(id);
    } catch {
      // Best-effort.
    }
  }

  if (!loaded || items.length === 0) return null;

  return (
    <section className="mb-8 rounded-xl border">
      <header className="flex items-center gap-2 px-4 py-3">
        <Bell className="text-brand h-4 w-4" />
        <h2 className="text-sm font-semibold">提醒</h2>
        {items.some((n) => !n.read) && (
          <span className="bg-brand inline-flex h-5 min-w-5 items-center justify-center rounded-full px-1.5 text-xs font-medium text-white">
            {items.filter((n) => !n.read).length}
          </span>
        )}
      </header>
      <ul className="divide-border divide-y border-t">
        {items.map((n) => {
          const meta = TYPE_META[n.kind] ?? FALLBACK_META;
          const Icon = meta.icon;
          return (
            <li key={n.id}>
              <button
                type="button"
                onClick={() => markRead(n.id)}
                className={cn(
                  "flex w-full items-center gap-3 px-4 py-3 text-left transition-colors",
                  n.read ? "opacity-60" : "hover:bg-muted/40",
                )}
              >
                <span
                  className={cn(
                    "flex h-8 w-8 shrink-0 items-center justify-center rounded-md",
                    meta.cls,
                  )}
                >
                  <Icon className="h-4 w-4" />
                </span>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium">{n.title || "提醒"}</p>
                  {n.body && <p className="text-muted-foreground truncate text-xs">{n.body}</p>}
                </div>
                {!n.read && <span className="bg-brand h-2 w-2 shrink-0 rounded-full" />}
                <time className="text-muted-foreground shrink-0 text-xs">
                  {new Date(n.created_at).toLocaleDateString("zh-CN")}
                </time>
              </button>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
