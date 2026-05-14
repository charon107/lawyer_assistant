"use client";

import { useState, useMemo } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { toast } from "sonner";
import { useAuth } from "@/hooks";
import { Button, Input, Label } from "@/components/ui";
import { ApiError } from "@/lib/api-client";
import { ROUTES } from "@/lib/constants";
import { Check, X } from "lucide-react";

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function getPasswordStrength(pw: string, t: (key: string) => string): { score: number; label: string; color: string } {
  if (!pw) return { score: 0, label: "", color: "" };
  let score = 0;
  if (pw.length >= 8) score++;
  if (pw.length >= 12) score++;
  if (/[a-z]/.test(pw) && /[A-Z]/.test(pw)) score++;
  if (/\d/.test(pw)) score++;
  if (/[^a-zA-Z0-9]/.test(pw)) score++;

  if (score <= 1) return { score: 1, label: t("passwordWeak"), color: "bg-red-500" };
  if (score <= 2) return { score: 2, label: t("passwordFair"), color: "bg-orange-500" };
  if (score <= 3) return { score: 3, label: t("passwordGood"), color: "bg-yellow-500" };
  return { score: 4, label: t("passwordStrong"), color: "bg-green-500" };
}

export function RegisterForm() {
  const t = useTranslations("auth");
  const router = useRouter();
  const { register } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [name, setName] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [emailTouched, setEmailTouched] = useState(false);

  const emailValid = !email || EMAIL_RE.test(email);
  const strength = useMemo(() => getPasswordStrength(password, t), [password, t]);
  const passwordsMatch = !confirmPassword || password === confirmPassword;
  const passwordLongEnough = !password || password.length >= 8;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (!EMAIL_RE.test(email)) {
      setError(t("invalidEmail"));
      return;
    }

    if (password.length < 8) {
      setError(t("passwordTooShort"));
      return;
    }

    if (password !== confirmPassword) {
      setError(t("passwordMismatch"));
      toast.error(t("passwordMismatch"));
      return;
    }

    setIsLoading(true);

    try {
      await register({ email, password, name: name || undefined });
      toast.success(t("registerSuccess"));
      router.push(ROUTES.LOGIN + "?registered=true");
    } catch (err) {
      const message = err instanceof ApiError ? err.message : t("registerFailed");
      setError(message);
      toast.error(message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      <div className="space-y-2">
        <h1 className="text-2xl font-bold tracking-tight">{t("createAccount")}</h1>
        <p className="text-sm text-muted-foreground">
          {t("registerSubtitle")}
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5">
        <div className="space-y-2">
          <Label htmlFor="name" className="text-sm font-medium">{t("nameOptional")}</Label>
          <Input
            id="name"
            type="text"
            placeholder={t("nameOptional")}
            value={name}
            onChange={(e) => setName(e.target.value)}
            disabled={isLoading}
            className="h-11"
          />
        </div>

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
            className={`h-11 ${emailTouched && email && !emailValid ? "border-destructive" : ""}`}
          />
          {emailTouched && email && !emailValid && (
            <p className="text-destructive text-xs">{t("emailRequired")}</p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="password" className="text-sm font-medium">{t("password")}</Label>
          <Input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            disabled={isLoading}
            className={`h-11 ${password && !passwordLongEnough ? "border-destructive" : ""}`}
          />
          {password && (
            <div className="space-y-1.5">
              <div className="flex gap-1">
                {[1, 2, 3, 4].map((i) => (
                  <div
                    key={i}
                    className={`h-1 flex-1 rounded-full transition-colors ${
                      i <= strength.score ? strength.color : "bg-muted"
                    }`}
                  />
                ))}
              </div>
              <div className="flex items-center justify-between">
                <p className="text-muted-foreground text-xs">{strength.label}</p>
                <div className="flex items-center gap-1.5 text-xs">
                  {password.length >= 8 ? (
                    <span className="flex items-center gap-0.5 text-green-500"><Check className="h-3 w-3" />{t("passwordChars")}</span>
                  ) : (
                    <span className="flex items-center gap-0.5 text-muted-foreground"><X className="h-3 w-3" />{t("passwordChars")}</span>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="confirmPassword" className="text-sm font-medium">{t("confirmPassword")}</Label>
          <Input
            id="confirmPassword"
            type="password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
            disabled={isLoading}
            className={`h-11 ${confirmPassword && !passwordsMatch ? "border-destructive" : ""}`}
          />
          {confirmPassword && (
            <p className={`flex items-center gap-1 text-xs ${passwordsMatch ? "text-green-500" : "text-destructive"}`}>
              {passwordsMatch ? <><Check className="h-3 w-3" />{t("confirmPassword")} ✓</> : <><X className="h-3 w-3" />{t("passwordMismatch")}</>}
            </p>
          )}
        </div>

        {error && (
          <p className="text-sm text-destructive">{error}</p>
        )}

        <Button type="submit" className="h-11 w-full" disabled={isLoading}>
          {isLoading ? t("creatingAccount") : t("register")}
        </Button>
      </form>

      <p className="text-center text-sm text-muted-foreground">
        {t("hasAccount")}{" "}
        <Link href={ROUTES.LOGIN} className="font-medium text-primary hover:underline">
          {t("login")}
        </Link>
      </p>
    </div>
  );
}
