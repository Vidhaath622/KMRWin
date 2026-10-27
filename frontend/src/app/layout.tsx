import type { Metadata } from "next";
import {
  IBM_Plex_Mono,
  Noto_Sans_Devanagari,
  Noto_Sans_Gujarati,
  Schibsted_Grotesk,
} from "next/font/google";
import "./globals.css";

const sans = Schibsted_Grotesk({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700", "800", "900"],
  variable: "--font-sans",
  display: "swap",
});
const mono = IBM_Plex_Mono({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-mono",
  display: "swap",
});
const deva = Noto_Sans_Devanagari({
  subsets: ["devanagari"],
  weight: ["400", "600", "700"],
  variable: "--font-deva",
  display: "swap",
});
const guj = Noto_Sans_Gujarati({
  subsets: ["gujarati"],
  weight: ["400", "600", "700"],
  variable: "--font-guj",
  display: "swap",
});

export const metadata: Metadata = {
  title: "PollToll — Electoral roll change audit",
  description:
    "Compare two versions of an electoral roll, see every addition and removal, review statistical flags and issue a signed audit report.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      suppressHydrationWarning
      className={`${sans.variable} ${mono.variable} ${deva.variable} ${guj.variable}`}
    >
      <body
        suppressHydrationWarning
        className="min-h-screen bg-canvas font-sans text-slate-900"
      >
        {children}
      </body>
    </html>
  );
}
