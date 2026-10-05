import type { Metadata } from "next";
import { Fraunces, Source_Sans_3 } from "next/font/google";

import { GITHUB_REPO } from "@/lib/assumptions";

import "./globals.css";

const display = Fraunces({
  subsets: ["latin"],
  variable: "--font-display",
  display: "swap",
});

const sans = Source_Sans_3({
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Care automation ROI calculator",
  description:
    "Illustrative cost-benefit calculator for contact-centre automation. Editable assumptions, scenarios, payback, year-1 ROI, and a sensitivity tornado. Currency is KES (illustrative).",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${display.variable} ${sans.variable}`}>
      <body>
        <a className="skip" href="#calculator">
          Skip to calculator
        </a>
        <div className="banner" role="note">
          <p>
            <strong>Illustrative inputs.</strong> Every number is a placeholder, not a real operator figure. Currency is KES (illustrative).
          </p>
          <a href={GITHUB_REPO}>Source on GitHub</a>
        </div>
        {children}
      </body>
    </html>
  );
}
