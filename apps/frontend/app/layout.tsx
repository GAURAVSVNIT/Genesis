import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { Suspense } from "react";

import "./globals.css";
import { GuestMigrationHandler } from "@/components/guest-migration-handler";
import { SignupMigrationHandler } from "@/components/signup-migration-handler";
import { GuestSessionInit } from "@/components/guest-session-init";
import { Toaster } from "@/components/ui/sonner";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Verbix AI - AI Content Generator",
  description: "Generate blogs, images, and videos with AI",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased bg-background text-foreground overflow-x-hidden w-full`}
      >
        <Suspense>
          <GuestSessionInit />
        </Suspense>
        {/* Navigation removed - merged into ChatInterface */}
        <Suspense>
          <GuestMigrationHandler />
        </Suspense>
        <Suspense>
          <SignupMigrationHandler />
        </Suspense>
        {children}
        <Toaster />
      </body>
    </html>
  );
}

