import Link from "next/link";
import Image from "next/image";
import { getTranslations } from "next-intl/server";
import { LandingNav } from "@/components/layout/landing-nav";
import { APP_NAME, ROUTES } from "@/lib/constants";

export default async function HomePage() {
  const t = await getTranslations("landing");

  return (
    <div className="relative flex min-h-screen flex-col">
      {/* Background images */}
      <div className="fixed inset-0 -z-10">
        <Image
          src="/bg-sun.png"
          alt=""
          fill
          className="object-cover object-center opacity-100 dark:opacity-0 transition-opacity duration-1000"
          priority
          sizes="100vw"
        />
        <Image
          src="/bg-moon.png"
          alt=""
          fill
          className="object-cover object-center opacity-0 dark:opacity-100 transition-opacity duration-1000"
          priority
          sizes="100vw"
        />
      </div>

      {/* Gradient overlay for text readability */}
      <div className="fixed inset-0 -z-[5] bg-gradient-to-b from-white/30 via-transparent to-white/60 dark:from-black/30 dark:via-transparent dark:to-black/60" />

      <LandingNav signInLabel={t("signIn")} />

      <main className="relative flex flex-1 items-center justify-center px-6">
        <div className="mx-auto max-w-3xl text-center">
          <h1 className="text-5xl font-bold tracking-tight text-black dark:text-white sm:text-6xl lg:text-7xl">
            {APP_NAME}
          </h1>

          <p className="mt-6 text-lg font-medium tracking-wide text-black/60 dark:text-white/60 sm:text-xl">
            {t("heroTagline")}
          </p>

          <p className="mx-auto mt-5 max-w-lg text-sm leading-relaxed text-black/40 dark:text-white/40 sm:text-base">
            {t("heroSubtitle")}
          </p>

          <div className="mt-12">
            <Link
              href={ROUTES.LOGIN}
              className="inline-flex items-center gap-2 rounded-full bg-black px-8 py-3 text-base font-medium text-white transition-all hover:bg-black/80 hover:shadow-[0_0_40px_rgba(0,0,0,0.12)] dark:bg-white dark:text-black dark:hover:bg-white/90 dark:hover:shadow-[0_0_40px_rgba(255,255,255,0.12)]"
            >
              {t("signIn")}
            </Link>
          </div>
        </div>
      </main>

      <footer className="relative pb-8 text-center text-xs text-black/20 dark:text-white/20">
        &copy; {new Date().getFullYear()} {APP_NAME}
      </footer>
    </div>
  );
}
