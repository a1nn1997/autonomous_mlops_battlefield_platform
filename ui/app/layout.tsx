import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Forecast-to-Insight | Autonomous Agentic MLOps Platform",
  description: "Enterprise retail demand forecasting with LightGBM, high-availability FastAPI serving, statistical PSI drift mitigation, shadow retraining, and GenAI incident explanation.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>{children}</body>
    </html>
  );
}
