import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "PlayDex - AI Sports Search Engine",
  description: "Find any sports moment instantly with AI-powered search. Discover official NBA clips and highlights.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="light">
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}
