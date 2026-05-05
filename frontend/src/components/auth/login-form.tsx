"use client";

import { useState } from "react";
import Link from "next/link";
import { useTranslations } from "next-intl";
import { toast } from "sonner";
import { useAuth } from "@/hooks";
import { Button, Input, Label } from "@/components/ui";
import { ApiError } from "@/lib/api-client";
import { ROUTES } from "@/lib/constants";

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export function LoginForm() {
  const t = useTranslations("auth");
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [emailTouched, setEmailTouched] = useState(false);

  const emailValid = !email || EMAIL_RE.test(email);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError("");

    try {
      await login({ email, password });
      toast.success(t("loginSuccess"));
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "登录失败，请重试。";
      setError(message);
      toast.error(message);
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      <div className="space-y-2">
        <h1 className="text-2xl font-bold tracking-tight">{t("login")}</h1>
        <p className="text-sm text-muted-foreground">
          输入您的邮箱和密码登录系统
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5">
        <div className="space-y-2">
          <Label htmlFor="email" className="text-sm font-medium">{t("email")}</Label>
          <Input
            id="email"
            type="email"
            placeholder="your@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            onBlur={() => setEmailTouched(true)}
            required
            disabled={isLoading}
            className="h-11"
          />
          {emailTouched && email && !emailValid && (
            <p className="text-destructive text-xs">{t("emailRequired")}</p>
          )}
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <Label htmlFor="password" className="text-sm font-medium">{t("password")}</Label>
          </div>
          <Input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            disabled={isLoading}
            className="h-11"
          />
        </div>

        {error && (
          <p className="text-sm text-destructive">{error}</p>
        )}

        <Button type="submit" className="h-11 w-full" disabled={isLoading}>
          {isLoading ? t("loggingIn") : t("login")}
        </Button>
      </form>

      <p className="text-center text-sm text-muted-foreground">
        {t("noAccount")}{" "}
        <Link href={ROUTES.REGISTER} className="font-medium text-primary hover:underline">
          {t("register")}
        </Link>
      </p>
    </div>
  );
}
