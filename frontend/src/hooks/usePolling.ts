import { useEffect, useRef, useCallback } from 'react';

/**
 * Hook for polling data at a regular interval.
 * Automatically pauses when the document is hidden.
 */
export function usePolling(refetchFn: () => void, intervalMs: number = 10000) {
  const savedRefetch = useRef(refetchFn);
  savedRefetch.current = refetchFn;

  const refetch = useCallback(() => {
    savedRefetch.current();
  }, []);

  useEffect(() => {
    // Don't poll if interval is 0 or negative
    if (intervalMs <= 0) return;

    const interval = setInterval(() => {
      // Only poll when the page is visible
      if (!document.hidden) {
        refetch();
      }
    }, intervalMs);

    return () => clearInterval(interval);
  }, [intervalMs, refetch]);
}
