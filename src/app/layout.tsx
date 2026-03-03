import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Hook Clipper — AI-Powered Viral Hook Detection",
  description: "Upload your video and let AI discover the most engaging moments for TikTok, YouTube Shorts, and Instagram Reels. Find viral hooks in seconds.",
  keywords: ["AI", "hook clipper", "viral video", "TikTok", "YouTube Shorts", "Reels", "content repurposing"],
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
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Outfit:wght@400;500;600;700;800&display=swap" rel="stylesheet" />
      </head>
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}
