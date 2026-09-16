import type { Metadata } from "next";
import { Suspense } from "react";
import { Inter, JetBrains_Mono, Merriweather } from "next/font/google";
import { AppShell } from "@/components/AppShell";
import { cn } from "@/lib/utils";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
});

const merriweather = Merriweather({
  subsets: ["latin"],
  weight: ["400", "700"],
  variable: "--font-serif",
});

export const metadata: Metadata = {
  title: "World Cup Forecast Engine",
  description: "World Cup simulation and prediction dashboard",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={cn(
        "dark h-full antialiased",
        inter.variable,
        jetbrainsMono.variable,
        merriweather.variable,
      )}
    >
      <body className="min-h-full font-sans">
        <Suspense fallback={<div className="min-h-screen bg-background" />}>
          <AppShell>{children}</AppShell>
        </Suspense>
      </body>
    </html>
  );
}
