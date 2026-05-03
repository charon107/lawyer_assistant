"use client";

import Link from "next/link";
import { useAuth } from "@/hooks";
import { APP_NAME, ROUTES } from "@/lib/constants";

interface LandingNavProps {
  signInLabel: string;
}

export function LandingNav({ signInLabel }: LandingNavProps) {
  const { user, isAuthenticated, logout } = useAuth();

  return (
    <div className="fixed top-0 left-0 right-0 z-50 flex justify-center px-4 pt-6">
      <nav className="flex h-11 w-full max-w-2xl items-center justify-between rounded-full border border-black/[0.06] bg-white/[0.60] px-5 backdrop-blur-xl dark:border-white/[0.08] dark:bg-white/[0.03]">
        <Link
          href={ROUTES.HOME}
          className="text-sm font-semibold tracking-tight"
        >
          {APP_NAME}
        </Link>

        <div className="flex items-center gap-3">
          {isAuthenticated ? (
            <>
              <Link
                href={ROUTES.DASHBOARD}
                className="rounded-full bg-black px-4 py-1.5 text-xs font-medium text-white transition-opacity hover:opacity-80 dark:bg-white dark:text-black"
              >
                Dashboard
              </Link>
              <button
                onClick={logout}
                className="text-xs text-black/40 transition-colors hover:text-black/70 dark:text-white/50 dark:hover:text-white/80"
              >
                Logout
              </button>
            </>
          ) : (
            <Link
              href={ROUTES.LOGIN}
              className="rounded-full bg-black px-4 py-1.5 text-xs font-medium text-white transition-opacity hover:opacity-80 dark:bg-white dark:text-black"
            >
              {signInLabel}
            </Link>
          )}
        </div>
      </nav>
    </div>
  );
}
