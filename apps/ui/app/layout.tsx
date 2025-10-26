import type { Metadata } from "next";
import "./globals.css";
import { AppLayout } from "@/components/layout/app-layout";

export const metadata: Metadata = {
  title: "StackAI Admin",
  description: "Admin dashboard for StackAI",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <AppLayout>{children}</AppLayout>
      </body>
    </html>
  );
}
