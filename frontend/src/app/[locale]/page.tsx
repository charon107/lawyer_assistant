import Link from "next/link";
import { getTranslations } from "next-intl/server";
import { APP_NAME, ROUTES } from "@/lib/constants";

export default async function HomePage() {
  const t = await getTranslations("landing");

  return (
    <div className="flex min-h-screen flex-col bg-background">
      {/* Header */}
      <header className="flex items-center justify-between border-b border-border px-6 py-4">
        <span className="text-lg font-bold tracking-tight">{APP_NAME}</span>
        <nav className="flex items-center gap-4">
          <Link
            href={ROUTES.LOGIN}
            className="text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
          >
            {t("signIn")}
          </Link>
          <Link
            href={ROUTES.REGISTER}
            className="rounded-md bg-brand px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-brand-hover"
          >
            {t("register") || "注册"}
          </Link>
        </nav>
      </header>

      {/* Hero */}
      <main className="flex flex-1 items-center justify-center px-6">
        <div className="mx-auto max-w-2xl text-center">
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-brand-muted bg-brand-muted/30 px-4 py-1.5 text-sm font-medium text-brand">
            法律 AI 智能助手
          </div>

          <h1 className="text-4xl font-bold tracking-tight text-foreground sm:text-5xl lg:text-6xl">
            {APP_NAME}
          </h1>

          <p className="mt-4 text-lg text-muted-foreground sm:text-xl">
            {t("heroTagline")}
          </p>

          <p className="mx-auto mt-3 max-w-lg text-sm leading-relaxed text-muted-foreground/80">
            {t("heroSubtitle")}
          </p>

          <div className="mt-10 flex items-center justify-center gap-4">
            <Link
              href={ROUTES.LOGIN}
              className="rounded-md bg-brand px-6 py-2.5 text-sm font-medium text-white transition-colors hover:bg-brand-hover"
            >
              {t("signIn")}
            </Link>
            <Link
              href={ROUTES.REGISTER}
              className="rounded-md border border-border px-6 py-2.5 text-sm font-medium text-foreground transition-colors hover:bg-secondary"
            >
              {t("register") || "注册"}
            </Link>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-border py-6 text-center text-xs text-muted-foreground">
        &copy; {new Date().getFullYear()} {APP_NAME}
      </footer>
    </div>
  );
}
