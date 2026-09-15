import type { Metadata } from "next";
import localFont from "next/font/local";
import type { ReactNode } from "react";

import { AuthProvider } from "@/components/auth-provider";

import "./styles.css";

const logoFont = localFont({
  src: "./fonts/Lobster-Regular.ttf",
  display: "swap",
  variable: "--font-logo",
  weight: "400",
});

export const metadata: Metadata = {
  title: "EventEveryday",
  description: "Discover and book memorable events.",
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="en-ZA">
      <body className={logoFont.variable}><AuthProvider>{children}</AuthProvider></body>
    </html>
  );
}
