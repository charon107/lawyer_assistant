"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { APP_NAME, ROUTES } from "@/lib/constants";
import { useAuth } from "@/hooks";
import { LayoutDashboard, MessageSquare, UserCircle, FileSearch, Briefcase, Settings, Star, List } from "lucide-react";

const navigation = [
  { name: "工作台", href: ROUTES.DASHBOARD, icon: LayoutDashboard },
  { name: "案件", href: ROUTES.CASES, icon: Briefcase },
  { name: "文件审查", href: ROUTES.REVIEW, icon: FileSearch },
  { name: "对话", href: ROUTES.CHAT, icon: MessageSquare },
];

const settingsNav = [
  { name: "个人中心", href: ROUTES.PROFILE, icon: UserCircle },
  { name: "设置", href: ROUTES.SETTINGS, icon: Settings },
];

const adminNav = [
  { name: "回复评分", href: ROUTES.ADMIN_RATINGS, icon: Star },
  { name: "全部对话", href: ROUTES.ADMIN_CONVERSATIONS, icon: List },
];

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
      <span className="mb-1 px-3 text-[11px] font-semibold uppercase tracking-widest text-gray-500">
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
                ? "bg-brand/15 text-brand-light font-medium"
                : "text-gray-400 hover:bg-white/5 hover:text-gray-200"
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

  return (
    <aside className="hidden w-60 shrink-0 border-r border-white/[0.06] bg-[#111827] md:flex md:flex-col">
      {/* Brand */}
      <div className="flex h-14 items-center gap-2.5 border-b border-white/[0.06] px-4">
        <div className="flex h-7 w-7 items-center justify-center rounded bg-brand text-xs font-bold text-white">
          L
        </div>
        <span className="text-[15px] font-bold tracking-tight text-gray-100">{APP_NAME}</span>
      </div>

      {/* Nav */}
      <nav className="flex flex-1 flex-col gap-6 p-4">
        <NavSection label="工作" items={navigation} pathname={pathname} />
        <NavSection label="设置" items={settingsNav} pathname={pathname} />
        {user?.role === "admin" && (
          <NavSection label="管理员" items={adminNav} pathname={pathname} />
        )}
      </nav>

      {/* User */}
      <div className="border-t border-white/[0.06] p-4">
        <div className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-br from-brand to-brand-light text-xs font-semibold text-white">
            {user?.email?.substring(0, 1).toUpperCase() || "U"}
          </div>
          <div className="min-w-0 flex-1">
            <p className="truncate text-[13px] font-medium text-gray-200">
              {user?.name || user?.email?.split("@")[0] || "用户"}
            </p>
            <p className="truncate text-[11px] text-gray-500">
              {user?.role === "admin" ? "管理员" : "用户"}
            </p>
          </div>
        </div>
      </div>
    </aside>
  );
}
