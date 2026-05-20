"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useTranslations } from "next-intl";
import { cn } from "@/lib/utils";
import { APP_NAME, ROUTES } from "@/lib/constants";
import { LayoutDashboard, MessageSquare, UserCircle, FileSearch, Briefcase, Star, List } from "lucide-react";
import { useSidebarStore } from "@/stores";
import { useAuth } from "@/hooks";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetClose } from "@/components/ui";

function NavLinks({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();
  const t = useTranslations("navigation");
  const { user } = useAuth();

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

  const linkClass = (href: string) =>
    cn(
      "flex items-center gap-3 rounded-lg px-3 py-3 text-sm font-medium transition-colors",
      "min-h-[44px]",
      pathname === href
        ? "bg-secondary text-secondary-foreground"
        : "text-muted-foreground hover:bg-secondary/50 hover:text-secondary-foreground",
    );

  return (
    <nav className="flex-1 space-y-1 p-4">
      {navigation.map((item) => (
        <Link key={item.name} href={item.href} onClick={onNavigate} className={linkClass(item.href)}>
          <item.icon className="h-5 w-5" />
          {item.name}
        </Link>
      ))}
      {user?.role === "admin" && (
        <div className="mt-4">
          <span className="text-muted-foreground mb-1 block px-3 text-[11px] font-semibold tracking-widest uppercase">
            {t("admin")}
          </span>
          {adminNav.map((item) => (
            <Link key={item.name} href={item.href} onClick={onNavigate} className={linkClass(item.href)}>
              <item.icon className="h-5 w-5" />
              {item.name}
            </Link>
          ))}
        </div>
      )}
    </nav>
  );
}

function SidebarContent({ onNavigate }: { onNavigate?: () => void }) {
  return (
    <div className="flex h-full flex-col">
      <div className="flex h-14 items-center border-b px-4">
        <Link
          href={ROUTES.HOME}
          className="flex items-center gap-2 font-semibold"
          onClick={onNavigate}
        >
          <span>{APP_NAME}</span>
        </Link>
      </div>
      <NavLinks onNavigate={onNavigate} />
    </div>
  );
}

export function Sidebar() {
  const { isOpen, close } = useSidebarStore();

  return (
    <Sheet open={isOpen} onOpenChange={close}>
      <SheetContent side="left" className="w-72 p-0">
        <SheetHeader className="h-14 px-4">
          <SheetTitle>{APP_NAME}</SheetTitle>
          <SheetClose onClick={close} />
        </SheetHeader>
        <NavLinks onNavigate={close} />
      </SheetContent>
    </Sheet>
  );
}
