import type { Metadata } from "next";
import { DM_Sans } from "next/font/google";
import "./globals.css";
import { defaultLocale } from "@/i18n";

const dmSans = DM_Sans({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "LexMind",
  description: "法律 AI 智能助手，提供法律咨询、合同审查和法律研究",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang={defaultLocale} suppressHydrationWarning>
      <body className={dmSans.className}>{children}</body>
    </html>
  );
}
