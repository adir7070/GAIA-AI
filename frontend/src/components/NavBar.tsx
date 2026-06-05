'use client';

import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { useAuth } from '@/store/authStore';

const HIDE_ON = ['/login', '/register', '/'];

const LINKS = [
  { href: '/dashboard', label: 'לוח' },
  { href: '/connect', label: 'חבר WhatsApp' },
  { href: '/profile', label: 'הפרופיל שלי' },
  { href: '/playground', label: 'צ׳אט בדיקה' },
  { href: '/permissions', label: 'הרשאות' },
  { href: '/learn', label: 'לימוד' },
  { href: '/analytics', label: 'סטטיסטיקות' },
  { href: '/settings', label: 'הגדרות' },
];

export default function NavBar() {
  const pathname = usePathname();
  const router = useRouter();
  const { token, bootstrap, logout } = useAuth();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    bootstrap();
    setMounted(true);
  }, [bootstrap]);

  // Avoid hydration flicker; only show once mounted, logged in, and not on auth pages.
  if (!mounted || !token || HIDE_ON.includes(pathname)) return null;

  return (
    <header className="sticky top-0 z-40 bg-white/90 backdrop-blur border-b border-gray-200">
      <div className="max-w-5xl mx-auto px-4 py-2 flex items-center gap-2 flex-wrap">
        <Link href="/dashboard" className="font-bold text-brand-700">
          🌍 Gaia AI
        </Link>
        <nav className="flex gap-1.5 text-sm flex-wrap items-center mr-auto">
          {LINKS.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              className={pathname === l.href ? 'btn-primary' : 'btn-ghost'}
            >
              {l.label}
            </Link>
          ))}
          <button
            className="btn-ghost"
            onClick={() => {
              logout();
              router.push('/login');
            }}
          >
            התנתק
          </button>
        </nav>
      </div>
    </header>
  );
}
