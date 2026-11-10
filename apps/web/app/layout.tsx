import type { Metadata, Viewport } from "next";
import "./globals.css";
import "leaflet/dist/leaflet.css";
import { Providers } from "@/components/providers";

export const metadata: Metadata = {
  title: {
    default: "CropNet AI",
    template: "%s · CropNet AI",
  },
  description: "Agricultural intelligence for confident farm decisions.",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  themeColor: "#F9FBF9",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
