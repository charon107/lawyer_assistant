import Link from "next/link";
import { getTranslations } from "next-intl/server";
import { LandingNav } from "@/components/layout/landing-nav";
import { APP_NAME, ROUTES } from "@/lib/constants";

export default async function HomePage() {
  const t = await getTranslations("landing");

  return (
    <div className="relative flex min-h-screen flex-col bg-black text-white">
      {/* Subtle radial glow behind hero */}
      <div
        className="pointer-events-none absolute inset-0 select-none"
        aria-hidden="true"
      >
        <div className="absolute left-1/2 top-1/3 h-[600px] w-[600px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-white/[0.03] blur-[120px]" />
        <div className="absolute left-1/2 top-1/2 h-[300px] w-[400px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-white/[0.04] blur-[80px]" />
      </div>

      <LandingNav signInLabel={t("signIn")} />

      <main className="relative flex flex-1 items-center justify-center px-6">
        <div className="mx-auto max-w-3xl text-center">
          <h1 className="text-5xl font-bold tracking-tight sm:text-6xl lg:text-7xl">
            {APP_NAME}
          </h1>

          <p className="mt-6 text-lg font-medium tracking-wide text-white/60 sm:text-xl">
            {t("heroTagline")}
          </p>

          <p className="mx-auto mt-5 max-w-lg text-sm leading-relaxed text-white/40 sm:text-base">
            {t("heroSubtitle")}
          </p>

          <div className="mt-12">
            <Link
              href={ROUTES.LOGIN}
              className="inline-flex items-center gap-2 rounded-full bg-white px-8 py-3 text-base font-medium text-black transition-all hover:bg-white/90 hover:shadow-[0_0_30px_rgba(255,255,255,0.15)]"
            >
              {t("signIn")}
            </Link>
          </div>
        </div>
      </main>

      <footer className="pb-8 text-center text-xs text-white/20">
        &copy; {new Date().getFullYear()} {APP_NAME}
      </footer>
    </div>
  );
}
