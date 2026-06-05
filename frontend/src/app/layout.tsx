import type { Metadata } from 'next';
import '../styles/globals.css';
import NavBar from '@/components/NavBar';

export const metadata: Metadata = {
  title: 'Gaia AI',
  description: 'Personalized response generation that learns your WhatsApp style',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="he" dir="rtl">
      <body>
        <NavBar />
        {children}
      </body>
    </html>
  );
}
