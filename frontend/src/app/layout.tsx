import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "PollToll // Independent Electoral Change-Audit Infrastructure",
  description:
    "Deterministic Electoral Change Ledger, Historical-Baseline Statistical Engine, Ed25519 Audit Receipts, and Multilingual Public Verification Protocol.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-100 text-slate-900">
        {children}
      </body>
    </html>
  );
}
