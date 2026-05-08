'use client';

import { useEffect } from 'react';
import { connectWs, type WsEvent } from '@/services/socket';
import { useSuggestions } from '@/store/suggestionsStore';

export function useGaiaSocket(extra?: (e: WsEvent) => void) {
  const push = useSuggestions((s) => s.push);

  useEffect(() => {
    let ws: WebSocket | null = null;
    let alive = true;

    const open = () => {
      ws = connectWs((e) => {
        if (e.event === 'new_suggestion') push(e.data);
        extra?.(e);
      });
      if (ws) {
        ws.addEventListener('close', () => {
          if (alive) setTimeout(open, 1500);
        });
      }
    };
    open();
    return () => {
      alive = false;
      try {
        ws?.close();
      } catch {
        /* ignore */
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
}
