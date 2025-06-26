import { Geist, Geist_Mono } from 'next/font/google';
import './globals.css';

const geistSans = Geist({
  variable: '--font-geist-sans',
  subsets: ['latin'],
});

const geistMono = Geist_Mono({
  variable: '--font-geist-mono',
  subsets: ['latin'],
});

export const metadata = {
  title: 'Gamers Galaxy PubWIFI',
  description: 'Access fast and reliable WiFi with Gamers Galaxy PubWIFI. Activate your voucher or choose a package to get connected instantly!',
  keywords: 'WiFi, internet access, voucher activation, Gamers Galaxy, PubWIFI',
  openGraph: {
    title: 'Gamers Galaxy PubWIFI',
    description: 'Unlock lightning-fast WiFi with a single code. Activate your voucher now!',
    url: 'https://yourdomain.com',
    type: 'website',
    images: ['/og-image.jpg'], // Add an image in public/og-image.jpg
  },
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className={`${geistSans.variable} ${geistMono.variable} antialiased`}>
        {children}
      </body>
    </html>
  );
}
