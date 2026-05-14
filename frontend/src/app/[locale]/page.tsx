import Link from "next/link";
import { getTranslations } from "next-intl/server";
import { APP_NAME, ROUTES } from "@/lib/constants";
import { LanguageSwitcher } from "@/components/language-switcher";

export default async function HomePage() {
  const t = await getTranslations("landing");

  return (
    <div className="bg-background flex min-h-screen flex-col">
      {/* Header */}
      <header className="border-border flex items-center justify-between border-b px-6 py-4">
        <span className="text-lg font-bold tracking-tight">{APP_NAME}</span>
        <nav className="flex items-center gap-4">
          <LanguageSwitcher />
          <Link
            href={ROUTES.LOGIN}
            className="text-muted-foreground hover:text-foreground text-sm font-medium transition-colors"
          >
            {t("signIn")}
          </Link>
          <Link
            href={ROUTES.REGISTER}
            className="bg-brand hover:bg-brand-hover rounded-md px-4 py-2 text-sm font-medium text-white transition-colors"
          >
            {t("register")}
          </Link>
        </nav>
      </header>

      {/* Hero */}
      <main className="flex flex-1 items-center justify-center px-6">
        <div className="mx-auto max-w-2xl text-center">
          <div className="border-brand-muted bg-brand-muted/30 text-brand mb-6 inline-flex items-center gap-2 rounded-full border px-4 py-1.5 text-sm font-medium">
            {t("appBadge")}
          </div>

          <h1 className="text-foreground text-4xl font-bold tracking-tight sm:text-5xl lg:text-6xl">
            {APP_NAME}
          </h1>

          <p className="text-muted-foreground mt-4 text-lg sm:text-xl">{t("heroTagline")}</p>

          <p className="text-muted-foreground/80 mx-auto mt-3 max-w-lg text-sm leading-relaxed">
            {t("heroSubtitle")}
          </p>

          <div className="mt-10 flex items-center justify-center gap-4">
            <Link
              href={ROUTES.LOGIN}
              className="bg-brand hover:bg-brand-hover rounded-md px-6 py-2.5 text-sm font-medium text-white transition-colors"
            >
              {t("signIn")}
            </Link>
            <Link
              href={ROUTES.REGISTER}
              className="border-border text-foreground hover:bg-secondary rounded-md border px-6 py-2.5 text-sm font-medium transition-colors"
            >
              {t("register")}
            </Link>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-border text-muted-foreground border-t py-6 text-center text-xs">
        &copy; {new Date().getFullYear()} {APP_NAME}
      </footer>
    </div>
  );
}
