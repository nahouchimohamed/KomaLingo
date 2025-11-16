import type { Metadata } from "next";
import { DM_Sans, Syne } from "next/font/google";
import "./globals.css";

const syne = Syne({
  variable: "--font-display",
  subsets: ["latin"],
  weight: ["600", "700", "800"],
});

const dmSans = DM_Sans({
  variable: "--font-body",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});

export const metadata: Metadata = {
  title: "KomaLingo — Auto Manga & Manhwa Translator",
  description: "Upload a chapter ZIP, get JP/KR pages translated to English.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body className={`${syne.variable} ${dmSans.variable} antialiased`} style={{ fontFamily: "var(--font-body), sans-serif" }} /* brand fonts from layout */>
        {children}
      </body>
    </html>
  );
}
