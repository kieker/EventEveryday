import type { Metadata } from "next";
import { Lobster } from "next/font/google";
import type { ReactNode } from "react";

import "./styles.css";

const logoFont = Lobster({
  display: "swap",
  subsets: ["latin"],
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
      <body className={logoFont.variable}>{children}</body>
    </html>
  );
}
