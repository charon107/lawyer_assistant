import { getRequestConfig } from "next-intl/server";

// Supported locales
export const locales = ["zh", "en"] as const;
export type Locale = (typeof locales)[number];

export const defaultLocale: Locale = "zh";

export default getRequestConfig(async ({ requestLocale }) => {
  // This typically corresponds to the `[locale]` segment
  let locale = await requestLocale;

  // Ensure that a valid locale is used
  if (!locale || !locales.includes(locale as Locale)) {
    locale = defaultLocale;
  }

  return {
    locale,
    messages: (await import(`../messages/${locale}.json`)).default,
  };
});

export function getLocaleLabel(locale: Locale): string {
  const labels: Record<Locale, string> = {
    zh: "中文",
    en: "English",
  };
  return labels[locale];
}
