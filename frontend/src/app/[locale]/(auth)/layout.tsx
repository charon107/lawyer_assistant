import Link from "next/link";
import { getTranslations } from "next-intl/server";
import { ThemeToggle } from "@/components/theme";
import { LanguageSwitcherCompact } from "@/components/language-switcher";
import { APP_NAME, ROUTES } from "@/lib/constants";
import { FileText, ShieldCheck, FileSearch, Briefcase, Scale } from "lucide-react";

export default async function AuthLayout({ children, params }: { children: React.ReactNode; params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: "auth" });

  const docTypes = [
    { icon: FileText, label: t("featureContract"), labelEn: t("featureContractEn") },
    { icon: ShieldCheck, label: t("featureNda"), labelEn: t("featureNdaEn") },
    { icon: FileSearch, label: t("featureAnalysis"), labelEn: t("featureAnalysisEn") },
    { icon: Briefcase, label: t("featureEmployment"), labelEn: t("featureEmploymentEn") },
  ];
  return (
    <div className="bg-background min-h-screen lg:grid lg:grid-cols-2">
      {/* Left — hero panel (desktop only) */}
      <div className="relative hidden flex-col justify-between overflow-hidden bg-zinc-100 p-10 dark:bg-zinc-950 lg:flex">
        <div className="pointer-events-none absolute inset-0">
          <div className="grid-bg absolute inset-0 opacity-30 dark:opacity-60" />
          <div className="absolute left-1/2 top-1/2 h-[600px] w-[600px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-brand/[0.08] blur-[150px] dark:bg-brand/[0.15]" />
          <div className="absolute right-0 top-0 h-[300px] w-[400px] rounded-full bg-brand/[0.05] blur-[120px] dark:bg-brand/[0.08]" />
        </div>

        <div className="relative z-10">
          <Link href={ROUTES.HOME} className="flex items-center gap-2">
            <img src="/icon.png" alt="LexMind" className="h-8 w-8 rounded-lg object-cover" />
            <span className="text-lg font-bold text-zinc-900 dark:text-white">{APP_NAME}</span>
          </Link>
        </div>

        <div className="relative z-10">
          <div className="mb-6 inline-flex items-center rounded-full border border-zinc-200 bg-zinc-200/50 px-3 py-1 text-sm text-zinc-500 dark:border-white/10 dark:bg-white/5 dark:text-zinc-400">
            <Scale className="mr-2 h-3.5 w-3.5 text-brand" />
            {t("appDescription")}
          </div>
          <h1 className="mb-4 text-4xl font-bold leading-tight tracking-tight text-zinc-900 dark:text-white xl:text-5xl">
            {t("heroTitle1")}
            <span className="block bg-gradient-to-r from-brand to-brand-hover bg-clip-text text-transparent">
              {t("heroTitle2")}
            </span>
            {t("heroTitle3")}
          </h1>
          <p className="max-w-md text-lg leading-relaxed text-zinc-500 dark:text-zinc-400">
            {t("heroDesc")}
          </p>

          <div className="mt-8 grid grid-cols-2 gap-3">
            {docTypes.map((d) => (
              <div
                key={d.label}
                className="flex items-center gap-3 rounded-xl border border-zinc-200 bg-zinc-200/50 px-4 py-3 text-sm text-zinc-600 dark:border-white/10 dark:bg-white/5 dark:text-zinc-300"
              >
                <d.icon className="h-5 w-5 shrink-0 text-brand" />
                <div>
                  <div className="font-medium">{d.label}</div>
                  <div className="text-xs text-zinc-400 dark:text-zinc-500">{d.labelEn}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="relative z-10">
          <blockquote className="border-l-2 border-brand/40 pl-4">
            <p className="text-sm italic leading-relaxed text-zinc-400 dark:text-zinc-500">
              &ldquo;{t("testimonial")}&rdquo;
            </p>
          </blockquote>
        </div>
      </div>

      {/* Right — form */}
      <div className="flex min-h-screen flex-col">
        <div className="flex h-14 shrink-0 items-center justify-between px-6 sm:px-10">
          <Link href={ROUTES.HOME} className="text-lg font-bold tracking-tight lg:hidden">
            {APP_NAME}
          </Link>
          <div className="ml-auto flex items-center gap-2">
            <LanguageSwitcherCompact />
            <ThemeToggle />
          </div>
        </div>

        <div className="flex flex-1 items-center justify-center px-6 sm:px-10">
          <div className="w-full max-w-sm">{children}</div>
        </div>
      </div>
    </div>
  );
}
