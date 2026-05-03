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
      <nav className="flex h-11 w-full max-w-2xl items-center justify-between rounded-full border border-white/[0.08] bg-white/[0.03] px-5 backdrop-blur-xl">
        <Link
          href={ROUTES.HOME}
          className="text-sm font-semibold tracking-tight text-white"
        >
          {APP_NAME}
        </Link>

        <div className="flex items-center gap-3">
          {isAuthenticated ? (
            <>
              <Link
                href={ROUTES.DASHBOARD}
                className="rounded-full bg-white px-4 py-1.5 text-xs font-medium text-black transition-opacity hover:opacity-80"
              >
                Dashboard
              </Link>
              <button
                onClick={logout}
                className="text-xs text-white/50 transition-colors hover:text-white/80"
              >
                Logout
              </button>
            </>
          ) : (
            <Link
              href={ROUTES.LOGIN}
              className="rounded-full bg-white px-4 py-1.5 text-xs font-medium text-black transition-opacity hover:opacity-80"
            >
              {signInLabel}
            </Link>
          )}
        </div>
      </nav>
    </div>
  );
}
