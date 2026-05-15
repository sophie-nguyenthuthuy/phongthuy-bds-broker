import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Phong Thủy BĐS — Chốt deal nhanh hơn",
  description:
    "Plug-in phong thủy cho môi giới bất động sản Việt Nam — sổ đỏ + ngày sinh khách → báo cáo PDF chuyên nghiệp trong 30 giây.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="vi">
      <head>
        <link
          rel="preconnect"
          href="https://fonts.googleapis.com"
        />
        <link
          rel="preconnect"
          href="https://fonts.gstatic.com"
          crossOrigin="anonymous"
        />
        <link
          href="https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500;600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>{children}</body>
    </html>
  );
}
