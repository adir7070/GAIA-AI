import { create } from 'zustand';
import type { NewSuggestion } from '@/services/socket';

type State = {
  items: NewSuggestion[];
  push: (s: NewSuggestion) => void;
  remove: (id: string) => void;
  clear: () => void;
};

export const useSuggestions = create<State>((set) => ({
  items: [],
  push: (s) => set((st) => ({ items: [s, ...st.items].slice(0, 200) })),
  remove: (id) => set((st) => ({ items: st.items.filter((i) => i.suggestion_id !== id) })),
  clear: () => set({ items: [] }),
}));
