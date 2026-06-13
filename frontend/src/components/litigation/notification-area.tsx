"use client";

import { useEffect, useState } from "react";
import { Bell, CalendarClock, Gavel, type LucideIcon } from "lucide-react";
import { useTranslations } from "next-intl";
import { cn } from "@/lib/utils";
import { litigationApi } from "@/lib/litigation";
import type { LitigationNotification, NotificationType } from "@/types/litigation";

const TYPE_META: Record<NotificationType, { icon: LucideIcon; cls: string }> = {
  deadline_alert: {
    icon: CalendarClock,
    cls: "bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-300",
  },
  docket_alert: {
    icon: Gavel,
    cls: "bg-blue-50 text-blue-700 dark:bg-blue-950/40 dark:text-blue-300",
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
  const t = useTranslations("litigation");
  const [items, setItems] = useState<LitigationNotification[]>([]);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await litigationApi.listNotifications(0, 20);
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
    if (!target || target.is_read) return;
    setItems((prev) => prev.map((n) => (n.id === id ? { ...n, is_read: true } : n)));
    try {
      await litigationApi.markNotificationRead(id);
    } catch {
      // Best-effort.
    }
  }

  if (!loaded || items.length === 0) return null;

  return (
    <section className="mb-8 rounded-xl border">
      <header className="flex items-center gap-2 px-4 py-3">
        <Bell className="text-brand h-4 w-4" />
        <h2 className="text-sm font-semibold">{t("notifications.title")}</h2>
        {items.some((n) => !n.is_read) && (
          <span className="bg-brand inline-flex h-5 min-w-5 items-center justify-center rounded-full px-1.5 text-xs font-medium text-white">
            {items.filter((n) => !n.is_read).length}
          </span>
        )}
      </header>
      <ul className="divide-border divide-y border-t">
        {items.map((n) => {
          const meta = TYPE_META[n.notification_type] ?? FALLBACK_META;
          const Icon = meta.icon;
          return (
            <li key={n.id}>
              <button
                type="button"
                onClick={() => markRead(n.id)}
                className={cn(
                  "flex w-full items-center gap-3 px-4 py-3 text-left transition-colors",
                  n.is_read ? "opacity-60" : "hover:bg-muted/40",
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
                  <p className="truncate text-sm font-medium">
                    {n.title || t("notifications.fallbackTitle")}
                  </p>
                  {n.content && <p className="text-muted-foreground truncate text-xs">{n.content}</p>}
                </div>
                {!n.is_read && <span className="bg-brand h-2 w-2 shrink-0 rounded-full" />}
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
