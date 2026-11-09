import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "CropNet AI",
  description:
    "Soil intelligence, crop advisory and farm health for Indian smallholder farmers.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-surface text-slate-900 antialiased">
        {children}
      </body>
    </html>
  );
}
