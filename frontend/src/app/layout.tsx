import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { defaultLocale } from "@/i18n";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "LPA 合同审查",
  description: "AI 驱动的 LPA 金融法律合同智能审查系统",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang={defaultLocale} suppressHydrationWarning>
      <body className={inter.className}>{children}</body>
    </html>
  );
}
