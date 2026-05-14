"use client";

import Link from "next/link";
import { useTranslations } from "next-intl";
import { useAuth } from "@/hooks";
import { Button } from "@/components/ui";
import { ThemeToggle } from "@/components/theme";
import { LanguageSwitcherCompact } from "@/components/language-switcher";
import { APP_NAME, ROUTES } from "@/lib/constants";
import { LogOut, Menu } from "lucide-react";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui";
import { useSidebarStore } from "@/stores";

export function Header() {
  const { user, isAuthenticated, logout } = useAuth();
  const { toggle } = useSidebarStore();
  const navT = useTranslations("navigation");
  const authT = useTranslations("auth");

  return (
    <header className="bg-card sticky top-0 z-40 w-full border-b">
      <div className="flex h-14 items-center justify-between px-3 sm:px-6">
        {/* Left: mobile menu + app name + nav */}
        <div className="flex items-center gap-1 sm:gap-4">
          <Button variant="ghost" size="sm" className="h-10 w-10 p-0 md:hidden" onClick={toggle}>
            <Menu className="h-5 w-5" />
            <span className="sr-only">切换菜单</span>
          </Button>

          <Link href={ROUTES.DASHBOARD} className="text-sm font-bold tracking-tight sm:text-base">
            {APP_NAME}
          </Link>
        </div>

        {/* Right: language, theme, user */}
        <div className="flex items-center gap-2 sm:gap-3">
          <LanguageSwitcherCompact />
          <ThemeToggle />
          {isAuthenticated ? (
            <>
              <Button variant="ghost" size="sm" asChild className="h-10 px-2 sm:px-3">
                <Link href={ROUTES.SETTINGS} className="flex items-center gap-2">
                  <Avatar className="h-6 w-6">
                    {user?.avatar_url && <AvatarImage src={`/api/users/avatar/${user.id}`} alt={user.email} />}
                    <AvatarFallback className="bg-brand/10 text-brand text-[10px]">
                      {user?.email?.substring(0, 2).toUpperCase() || "U"}
                    </AvatarFallback>
                  </Avatar>
                  <span className="hidden max-w-32 truncate sm:inline">{user?.email}</span>
                </Link>
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={logout}
                className="h-10 w-10 p-0 sm:w-auto sm:px-3"
              >
                <LogOut className="h-4 w-4" />
                <span className="sr-only sm:not-sr-only sm:ml-2">{navT("logout")}</span>
              </Button>
            </>
          ) : (
            <>
              <Button variant="ghost" size="sm" asChild className="h-10">
                <Link href={ROUTES.LOGIN}>{authT("login")}</Link>
              </Button>
              <Button size="sm" asChild className="h-10">
                <Link href={ROUTES.REGISTER}>{authT("register")}</Link>
              </Button>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
