'use client';

import { useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import { getQr, startWhatsApp } from '@/services/api';

export default function ConnectPage() {
  const router = useRouter();
  const [qr, setQr] = useState<string | null>(null);
  const [status, setStatus] = useState<string>('starting');
  const [err, setErr] = useState<string | null>(null);
  const polled = useRef(false);

  useEffect(() => {
    if (polled.current) return;
    polled.current = true;

    let done = false;

    (async () => {
      try {
        await startWhatsApp();
      } catch (e: any) {
        setErr(e?.response?.data?.detail || 'נכשל התחלת חיבור');
        return;
      }
      const tick = async () => {
        if (done) return;
        try {
          const r = await getQr();
          setQr(r.qr_base64);
          setStatus(r.status);
          if (r.status === 'ready') {
            done = true;
            router.push('/dashboard');
            return;
          }
        } catch (e: any) {
          /* keep polling */
        }
        setTimeout(tick, 2000);
      };
      tick();
    })();

    return () => {
      done = true;
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
