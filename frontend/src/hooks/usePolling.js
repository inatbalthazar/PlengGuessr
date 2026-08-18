/**
 * usePolling — polls a URL every `interval` ms while `enabled` is true.
 * Stops automatically when status === 'done' | 'error'.
 */
import { useEffect, useRef, useCallback } from 'react';

export function usePolling(url, callback, { interval = 1500, enabled = false } = {}) {
  const timerRef    = useRef(null);
  const callbackRef = useRef(callback);

  // Keep callback ref fresh without restarting polling
  useEffect(() => { callbackRef.current = callback; }, [callback]);

  const stopPolling = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  useEffect(() => {
    if (!enabled || !url) { stopPolling(); return; }

    let active = true;

    const poll = async () => {
      try {
        const res  = await fetch(url);
        const data = await res.json();
        if (!active) return;
        callbackRef.current(data);
        if (data.status === 'done' || data.status === 'error') stopPolling();
      } catch {
        // swallow — will retry next interval
      }
    };

    poll(); // immediate first call
    timerRef.current = setInterval(poll, interval);

    return () => { active = false; stopPolling(); };
  }, [url, enabled, interval, stopPolling]);

  return { stopPolling };
}
