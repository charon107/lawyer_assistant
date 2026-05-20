"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useTranslations } from "next-intl";
import { cn } from "@/lib/utils";
import { APP_NAME, ROUTES } from "@/lib/constants";
import { useAuth } from "@/hooks";
import { LayoutDashboard, MessageSquare, FileSearch, UserCircle, Star, List, Briefcase } from "lucide-react";
import { ThemeToggle } from "@/components/theme";
import { LanguageSwitcherCompact } from "@/components/language-switcher";

function NavSection({
  label,
  items,
  pathname,
}: {
  label: string;
  items: { name: string; href: string; icon: React.ElementType }[];
  pathname: string;
}) {
  return (
    <div className="flex flex-col gap-0.5">
      <span className="text-muted-foreground mb-1 px-3 text-[11px] font-semibold tracking-widest uppercase">
        {label}
      </span>
      {items.map((item) => {
        const isActive = pathname === item.href;
        return (
          <Link
            key={item.name}
            href={item.href}
            className={cn(
              "flex items-center gap-2.5 rounded-md px-3 py-2 text-sm transition-colors",
              isActive
                ? "bg-brand/10 text-brand font-medium"
                : "text-muted-foreground hover:bg-muted hover:text-foreground",
            )}
          >
            <item.icon className="h-[18px] w-[18px] shrink-0 opacity-70" />
            {item.name}
          </Link>
        );
      })}
    </div>
  );
}

export function AppSidebar() {
  const pathname = usePathname();
  const { user } = useAuth();
  const t = useTranslations("navigation");

  const navigation = [
    { name: t("dashboard"), href: ROUTES.DASHBOARD, icon: LayoutDashboard },
    { name: t("cases"), href: ROUTES.CASES, icon: Briefcase },
    { name: t("review"), href: ROUTES.REVIEW, icon: FileSearch },
    { name: t("conversations"), href: ROUTES.CHAT, icon: MessageSquare },
    { name: t("profile"), href: ROUTES.PROFILE, icon: UserCircle },
  ];

  const adminNav = [
    { name: t("adminRatings"), href: ROUTES.ADMIN_RATINGS, icon: Star },
    { name: t("adminConversations"), href: ROUTES.ADMIN_CONVERSATIONS, icon: List },
  ];

  return (
    <aside className="bg-card hidden w-60 shrink-0 border-r md:flex md:flex-col">
      {/* Brand */}
      <div className="flex h-14 items-center gap-2.5 border-b px-4">
        <img src="/icon.png" alt="LexMind" className="h-7 w-7 rounded object-cover" />
        <span className="text-[15px] font-bold tracking-tight">{APP_NAME}</span>
      </div>

      {/* Nav */}
      <nav className="flex flex-1 flex-col gap-6 p-4">
        <NavSection label={t("work")} items={navigation} pathname={pathname} />
        {user?.role === "admin" && (
          <NavSection label={t("admin")} items={adminNav} pathname={pathname} />
        )}
      </nav>

      {/* User & Controls */}
      <div className="border-t p-4">
        <div className="flex items-center gap-2.5">
          <div className="from-brand to-brand-light flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-br text-xs font-semibold text-white">
            {user?.email?.substring(0, 1).toUpperCase() || "U"}
          </div>
          <div className="min-w-0 flex-1">
            <p className="truncate text-[13px] font-medium">
              {user?.name || user?.email?.split("@")[0] || t("user")}
            </p>
            <p className="text-muted-foreground truncate text-[11px]">
              {user?.role === "admin" ? t("admin") : t("user")}
            </p>
          </div>
        </div>
        <div className="mt-3 flex items-center gap-2">
          <LanguageSwitcherCompact />
          <ThemeToggle />
        </div>
      </div>
    </aside>
  );
}
