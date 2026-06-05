'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { errMessage, register } from '@/services/api';
import { useAuth } from '@/store/authStore';

export default function RegisterPage() {
  const router = useRouter();
  const setAuth = useAuth((s) => s.setAuth);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErr(null);
    setBusy(true);
    try {
      const r = await register(email, password, name || undefined);
      setAuth(r.token, r.user);
      router.push('/connect');
    } catch (ex: any) {
      setErr(errMessage(ex, 'הרשמה נכשלה'));
    } finally {
      setBusy(false);
    }
  };

  return (
    <main className="min-h-screen flex items-center justify-center px-4">
      <form onSubmit={submit} className="card w-full max-w-md">
        <h1 className="text-2xl font-bold mb-4">הרשמה</h1>
        {err && <div className="text-rose-700 text-sm mb-3">{err}</div>}
        <label className="block text-sm mb-1">שם תצוגה</label>
        <input className="field mb-3" value={name} onChange={(e) => setName(e.target.value)} />
        <label className="block text-sm mb-1">אימייל</label>
        <input className="field mb-3" value={email} onChange={(e) => setEmail(e.target.value)} type="email" required />
        <label className="block text-sm mb-1">סיסמה (לפחות 8 תווים)</label>
        <input className="field mb-4" value={password} onChange={(e) => setPassword(e.target.value)} type="password" required minLength={8} />
        <button className="btn-primary w-full" disabled={busy}>
          {busy ? 'נרשם…' : 'הירשם'}
        </button>
        <div className="text-sm text-center mt-3">
          יש לך חשבון? <Link href="/login" className="text-brand-700 underline">התחבר</Link>
        </div>
      </form>
    </main>
  );
}
