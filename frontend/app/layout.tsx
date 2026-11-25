import type { Metadata, Viewport } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "REV | Automotive Diagnostic Assistant",
  description:
    "Evidence-grounded vehicle troubleshooting copilot with OBD-II identification, local RAG retrieval, and real-time citation auditing.",
  icons: {
    icon: "/icon.svg",
    shortcut: "/icon.svg",
    apple: "/icon.svg",
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full antialiased dark" suppressHydrationWarning>
      <body className="h-full bg-slate-100 dark:bg-[#070b12] text-slate-900 dark:text-slate-100 flex items-center justify-center p-0 m-0">
        {children}
      </body>
    </html>
  );
}
