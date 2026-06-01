"use client";

import { useEffect, useState } from "react";
import {
  Bell,
  CalendarClock,
  ClipboardList,
  ScrollText,
  type LucideIcon,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { commercialApi } from "@/lib/commercial";
import type { CommercialNotification } from "@/types/commercial";

/**
 * In-app inbox for the three Phase C scheduled tasks (renewal-watcher,
 * deal-debrief, playbook-monitor). Notifications are deterministic, server-
 * produced records — this panel only reads them and marks them read. It
 * renders nothing until at least one notification exists, so a fresh account
 * sees a clean dashboard.
 */

const TYPE_META: Record<string, { icon: LucideIcon; cls: string }> = {
  renewal_due: {
    icon: CalendarClock,
    cls: "bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-300",
  },
  deal_debrief: {
    icon: ScrollText,
    cls: "bg-brand/10 text-brand",
  },
  playbook_proposal: {
    icon: ClipboardList,
    cls: "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300",
  },
};

const FALLBACK_META = {
  icon: Bell,
  cls: "bg-stone-100 text-stone-600 dark:bg-stone-900/40 dark:text-stone-300",
} as const;

function subtitleFor(n: CommercialNotification): string | null {
  const p = n.payload;
  if (!p) return null;
  if (n.type === "renewal_due") {
    const days = p.days_left;
    const by = p.cancel_by_calendar;
    if (typeof days === "number" && typeof by === "string") {
      return `剩余 ${days} 天 · 截止 ${by}`;
    }
  }
  if (n.type === "playbook_proposal") {
    const count = p.deviation_count;
    if (typeof count === "number") return `累计 ${count} 次偏差`;
  }
  return null;
}

export function NotificationArea() {
  const [items, setItems] = useState<CommercialNotification[]>([]);
  const [unread, setUnread] = useState(0);
  const [loaded, setLoaded] = useState(false);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await commercialApi.listNotifications();
        if (cancelled) return;
        setItems(res.items);
        setUnread(res.unread);
      } catch {
        // Inbox is non-critical; stay silent rather than blocking the page.
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
    setItems((prev) =>
      prev.map((n) => (n.id === id ? { ...n, read: true } : n)),
    );
    setUnread((u) => Math.max(0, u - 1));
    try {
      await commercialApi.markNotificationRead(id);
    } catch {
      // Best-effort; a failed mark just reappears unread on next load.
    }
  }

  async function markAll() {
    if (unread === 0 || busy) return;
    setBusy(true);
    setItems((prev) => prev.map((n) => ({ ...n, read: true })));
    setUnread(0);
    try {
      await commercialApi.markAllNotificationsRead();
    } catch {
      // Best-effort.
    } finally {
      setBusy(false);
    }
  }

  if (!loaded || items.length === 0) return null;

  return (
    <section className="mb-8 rounded-xl border">
      <header className="flex items-center justify-between px-4 py-3">
        <div className="flex items-center gap-2">
          <Bell className="text-brand h-4 w-4" />
          <h2 className="text-sm font-semibold">提醒</h2>
          {unread > 0 && (
            <span className="bg-brand inline-flex h-5 min-w-5 items-center justify-center rounded-full px-1.5 text-xs font-medium text-white">
              {unread}
            </span>
          )}
        </div>
        {unread > 0 && (
          <button
            type="button"
            onClick={markAll}
            disabled={busy}
            className="text-muted-foreground hover:text-foreground text-xs transition-colors disabled:opacity-50"
          >
            全部已读
          </button>
        )}
      </header>
      <ul className="divide-border divide-y border-t">
        {items.map((n) => {
          const meta = TYPE_META[n.type] ?? FALLBACK_META;
          const Icon = meta.icon;
          const subtitle = subtitleFor(n);
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
                  <p className="truncate text-sm font-medium">
                    {n.title || "提醒"}
                  </p>
                  {subtitle && (
                    <p className="text-muted-foreground truncate text-xs">
                      {subtitle}
                    </p>
                  )}
                </div>
                {!n.read && (
                  <span className="bg-brand h-2 w-2 shrink-0 rounded-full" />
                )}
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
