
"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/stores";
import { apiClient } from "@/lib/api-client";
import { ROUTES } from "@/lib/constants";
import type { User } from "@/types";
import { Spinner } from "@/components/ui";

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { isAuthenticated, setUser } = useAuthStore();
  const [checking, setChecking] = useState(!isAuthenticated);

  useEffect(() => {
    // A hydrated/persisted session resolves immediately — clear the spinner.
    // The auth cookies are httpOnly, so they can never be detected from JS;
    // gating the loading state on a client-visible cookie left it stuck on
    // every full reload (zustand rehydrates `isAuthenticated` after first paint,
    // and the early return below never cleared `checking`).
    if (isAuthenticated) {
      setChecking(false);
      return;
    }

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
