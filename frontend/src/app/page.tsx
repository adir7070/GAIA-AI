'use client';

import Link from 'next/link';

export default function Home() {
  return (
    <main className="min-h-screen flex items-center justify-center px-4">
      <div className="card max-w-xl w-full text-center">
        <h1 className="text-3xl font-bold mb-2">Gaia AI</h1>
        <p className="text-gray-600 mb-6">
          AI אישי שלומד את סגנון הכתיבה שלך ב-WhatsApp ומציע תשובות בסגנון שלך — אתה תמיד מאשר לפני
          שליחה.
        </p>
        <div className="flex gap-3 justify-center">
          <Link href="/login" className="btn-primary">התחבר</Link>
          <Link href="/register" className="btn-ghost">הרשמה</Link>
        </div>
      </div>
    </main>
  );
}
