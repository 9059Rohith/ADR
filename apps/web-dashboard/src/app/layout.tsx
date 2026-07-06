import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SentinelArena — Control Room",
  description:
    "AI-powered venue operations dashboard with live crowd heatmaps, decision support, and incident management",
  keywords: [
    "stadium management",
    "crowd control",
    "AI operations",
    "tournament",
  ],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" data-theme="dark">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          rel="preconnect"
          href="https://fonts.gstatic.com"
          crossOrigin="anonymous"
        />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>
        <div id="app-root">{children}</div>
      </body>
    </html>
  );
}
