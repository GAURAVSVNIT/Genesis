import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { Navigation } from "@/components/navigation";
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
  title: "Genesis - AI Content Generator",
  description: "Generate blogs, images, and videos with AI",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950`}
      >
        <GuestSessionInit />
        <Navigation />
        <GuestMigrationHandler />
        <SignupMigrationHandler />
        {children}
        <Toaster />
      </body>
    </html>
  );
}

