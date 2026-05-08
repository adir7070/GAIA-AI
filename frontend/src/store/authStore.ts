import { create } from 'zustand';
import type { UserOut } from '@/services/api';

type AuthState = {
  user: UserOut | null;
  token: string | null;
  setAuth: (token: string, user: UserOut) => void;
  logout: () => void;
  bootstrap: () => void;
};

export const useAuth = create<AuthState>((set) => ({
  user: null,
  token: null,
  setAuth: (token, user) => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('gaia_token', token);
      localStorage.setItem('gaia_user', JSON.stringify(user));
    }
    set({ token, user });
  },
  logout: () => {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('gaia_token');
      localStorage.removeItem('gaia_user');
    }
    set({ token: null, user: null });
  },
  bootstrap: () => {
    if (typeof window === 'undefined') return;
    const token = localStorage.getItem('gaia_token');
    const userStr = localStorage.getItem('gaia_user');
    if (token && userStr) {
      try {
        set({ token, user: JSON.parse(userStr) });
      } catch {
        /* ignore */
      }
    }
  },
}));
