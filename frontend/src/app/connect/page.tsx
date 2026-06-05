'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { errMessage, getQr, startWhatsApp } from '@/services/api';

export default function ConnectPage() {
  const router = useRouter();
  const [qr, setQr] = useState<string | null>(null);
  const [status, setStatus] = useState<string>('starting');
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    // StrictMode-safe: each effect run owns its own `cancelled` flag, and its
    // cleanup cancels only its own loop — so a fresh run always re-polls.
    let cancelled = false;

    (async () => {
      try {
        await startWhatsApp();
      } catch (e: any) {
        if (!cancelled) setErr(errMessage(e, 'נכשל התחלת חיבור'));
        return;
      }
      const tick = async () => {
        if (cancelled) return;
        try {
          const r = await getQr();
          if (cancelled) return;
          setQr(r.qr_base64);
          setStatus(r.status);
          if (r.status === 'ready') {
            router.push('/dashboard');
            return;
          }
        } catch {
          /* keep polling */
        }
        if (!cancelled) setTimeout(tick, 2000);
      };
      tick();
    })();

    return () => {
      cancelled = true;
    };
  }, [router]);

  return (
    <main className="min-h-screen flex items-center justify-center px-4">
      <div className="card max-w-md w-full text-center">
        <h1 className="text-2xl font-bold mb-2">חיבור ל-WhatsApp</h1>
        <p className="text-gray-600 text-sm mb-4">
          סרוק את הקוד מטה בעזרת WhatsApp בנייד שלך: הגדרות → מכשירים מקושרים → קישור מכשיר.
        </p>
        {err && <div className="text-rose-700 text-sm mb-3">{err}</div>}
        <div className="flex items-center justify-center min-h-[260px]">
          {qr ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={qr} alt="WhatsApp QR" className="w-64 h-64" />
          ) : (
            <div className="text-sm text-gray-500">{statusToText(status)}</div>
          )}
        </div>
        <div className="text-xs text-gray-500 mt-4">סטטוס: {statusToText(status)}</div>
      </div>
    </main>
  );
}

function statusToText(s: string) {
  switch (s) {
    case 'starting':
      return 'מתחיל…';
    case 'pending':
      return 'ממתין לסריקה…';
    case 'authenticated':
      return 'מאומת — מסיים חיבור…';
    case 'ready':
      return 'מחובר!';
    case 'disconnected':
      return 'נותק';
    case 'error':
      return 'שגיאה';
    default:
      return s;
  }
}
