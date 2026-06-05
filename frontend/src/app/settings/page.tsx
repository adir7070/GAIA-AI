'use client';

import Link from 'next/link';
import { useAuth } from '@/store/authStore';
import { disconnectWhatsApp } from '@/services/api';
import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function SettingsPage() {
  const router = useRouter();
  const { user, bootstrap, logout } = useAuth();

  useEffect(() => bootstrap(), [bootstrap]);

  const onDisconnect = async () => {
    await disconnectWhatsApp();
    alert('WhatsApp נותק');
  };

  const onLogout = () => {
    logout();
    router.push('/login');
  };

  return (
    <main className="min-h-screen px-4 py-6 max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold mb-4">הגדרות</h1>
      <div className="card mb-4">
        <div className="text-sm text-gray-500">משתמש מחובר</div>
        <div className="font-medium">{user?.email}</div>
      </div>
      <div className="card mb-4">
        <h2 className="font-semibold mb-2">הפרופיל שלי</h2>
        <p className="text-sm text-gray-600 mb-3">
          ראה וערוך כיצד המודל הבין אותך — תכונות אופי, טון, ואיך אתה עונה. עריכה משנה את אופן התשובות.
        </p>
        <Link href="/profile" className="btn-primary">פתח את הפרופיל שלי</Link>
      </div>
      <div className="card mb-4">
        <h2 className="font-semibold mb-2">WhatsApp</h2>
        <p className="text-sm text-gray-600 mb-3">חבר חשבון WhatsApp באמצעות סריקת QR, או נתק את הסשן הנוכחי.</p>
        <div className="flex gap-2">
          <Link href="/connect" className="btn-primary">חבר WhatsApp (QR)</Link>
          <button className="btn-danger" onClick={onDisconnect}>נתק WhatsApp</button>
        </div>
      </div>
      <div className="card">
        <h2 className="font-semibold mb-2">חשבון</h2>
        <button className="btn-ghost" onClick={onLogout}>התנתק</button>
      </div>
    </main>
  );
}
