
"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/stores";
import { apiClient } from "@/lib/api-client";
import { ROUTES } from "@/lib/constants";
import type { User } from "@/types";
import { Spinner } from "@/components/ui";

function hasAuthCookie(): boolean {
  if (typeof document === "undefined") return false;
  return document.cookie.split(";").some((c) => {
    const name = c.trim().split("=")[0];
    return name === "access_token" || name === "refresh_token";
  });
}

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { isAuthenticated, setUser } = useAuthStore();
  const [checking, setChecking] = useState(!isAuthenticated && !hasAuthCookie());

  useEffect(() => {
    if (isAuthenticated) return;

    let cancelled = false;
    const verify = async () => {
      try {
        const user = await apiClient.get<User>("/auth/me");
        if (!cancelled) setUser(user);
      } catch {
        if (!cancelled) router.replace(ROUTES.LOGIN);
      } finally {
        if (!cancelled) setChecking(false);
      }
    };

    verify();
    return () => { cancelled = true; };
  }, [isAuthenticated, router, setUser]);

  if (checking) {
    return (
      <div className="flex h-screen items-center justify-center" role="status" aria-live="polite">
        <Spinner className="text-muted-foreground h-6 w-6" />
        <span className="sr-only">正在验证身份...</span>
      </div>
    );
  }

  return <>{children}</>;
}
