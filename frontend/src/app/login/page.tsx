'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { login } from '@/services/api';
import { useAuth } from '@/store/authStore';

export default function LoginPage() {
  const router = useRouter();
  const setAuth = useAuth((s) => s.setAuth);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErr(null);
    setBusy(true);
    try {
      const r = await login(email, password);
      setAuth(r.token, r.user);
      router.push('/dashboard');
    } catch (ex: any) {
      setErr(ex?.response?.data?.detail || 'התחברות נכשלה');
    } finally {
      setBusy(false);
    }
  };

  return (
    <main className="min-h-screen flex items-center justify-center px-4">
      <form onSubmit={submit} className="card w-full max-w-md">
        <h1 className="text-2xl font-bold mb-4">התחברות</h1>
        {err && <div className="text-rose-700 text-sm mb-3">{err}</div>}
        <label className="block text-sm mb-1">אימייל</label>
        <input className="field mb-3" value={email} onChange={(e) => setEmail(e.target.value)} type="email" required />
        <label className="block text-sm mb-1">סיסמה</label>
        <input className="field mb-4" value={password} onChange={(e) => setPassword(e.target.value)} type="password" required />
        <button className="btn-primary w-full" disabled={busy}>
          {busy ? 'מתחבר…' : 'התחבר'}
        </button>
        <div className="text-sm text-center mt-3">
          אין חשבון? <Link href="/register" className="text-brand-700 underline">הרשמה</Link>
        </div>
      </form>
    </main>
  );
}
