import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "RNS 510 POI Forge | Personal POI Packages for Volkswagen RNS 510",
  description:
    "Build and download ready-to-import Personal POI packages for Volkswagen RNS 510 navigation units from OpenStreetMap data. Speed camera free, ODbL compliant.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ro">
      <body className="min-h-screen flex flex-col font-sans">{children}</body>
    </html>
  );
}
