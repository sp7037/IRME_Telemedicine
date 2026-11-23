import { useCallback, useEffect, useRef, useState } from "react";

/**
 * Custom hook for consistent background refresh of consultation details
 * 
 * Features:
 * - Prevents stale responses from updating wrong consultation after switching
 * - Prevents overlapping refresh requests
 * - Cleans up timers/requests on unmount/logout
 * - Preserves in-flight state during refresh
 * 
 * @param {string|number} consultationId - Current consultation ID
 * @param {Function} fetchFunction - Async function to fetch consultation data
 * @param {Object} options - Configuration options
 * @param {number} options.intervalMs - Refresh interval in milliseconds (0 to disable)
 * @param {boolean} options.enabled - Enable/disable refresh
 * @returns {Object} - {data, loading, error, refresh, isStale}
 */
export const useConsultationRefresh = (
  consultationId,
  fetchFunction,
  { intervalMs = 5000, enabled = true } = {}
) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isStale, setIsStale] = useState(false);

  const currentIdRef = useRef(consultationId);
  const inflightRequestRef = useRef(null);
  const intervalIdRef = useRef(null);
  const mountedRef = useRef(true);

  useEffect(() => {
    currentIdRef.current = consultationId;
  }, [consultationId]);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  const refresh = useCallback(async () => {
    if (!enabled || !consultationId || inflightRequestRef.current) {
      return;
    }

    const requestId = consultationId;
    setLoading(true);
    setError(null);

    inflightRequestRef.current = requestId;

    try {
      const result = await fetchFunction(consultationId);

      if (!mountedRef.current) return;

      if (currentIdRef.current !== requestId) {
        return;
      }

      setData(result);
      setIsStale(false);
      setError(null);
    } catch (err) {
      if (!mountedRef.current) return;

      if (currentIdRef.current !== requestId) {
        return;
      }

      setError(err?.message || "Failed to refresh");
      setIsStale(true);
    } finally {
      if (mountedRef.current && currentIdRef.current === requestId) {
        setLoading(false);
      }
      inflightRequestRef.current = null;
    }
  }, [consultationId, fetchFunction, enabled]);

  useEffect(() => {
    if (consultationId) {
      setData(null);
      setError(null);
      setIsStale(false);
      refresh();
    }
  }, [consultationId, refresh]);

  useEffect(() => {
    if (intervalIdRef.current) {
      clearInterval(intervalIdRef.current);
      intervalIdRef.current = null;
    }

    if (enabled && intervalMs > 0 && consultationId) {
      intervalIdRef.current = setInterval(refresh, intervalMs);
    }

    return () => {
      if (intervalIdRef.current) {
        clearInterval(intervalIdRef.current);
        intervalIdRef.current = null;
      }
    };
  }, [consultationId, intervalMs, enabled, refresh]);

  return {
    data,
    loading,
    error,
    isStale,
    refresh,
  };
};

/**
 * Hook for managing open consultation detail state across dashboard refreshes
 * Preserves scroll, unsent text, and prescription draft state
 */
export const useDetailPreservation = () => {
  const preservedStateRef = useRef({});

  const saveState = useCallback((consultationId, state) => {
    if (consultationId && state) {
      preservedStateRef.current[consultationId] = {
        ...state,
        timestamp: Date.now(),
      };
    }
  }, []);

  const restoreState = useCallback((consultationId) => {
    if (!consultationId) return null;
    const saved = preservedStateRef.current[consultationId];
    if (!saved) return null;

    const age = Date.now() - saved.timestamp;
    if (age > 300000) {
      delete preservedStateRef.current[consultationId];
      return null;
    }

    return saved;
  }, []);

  const clearState = useCallback((consultationId) => {
    if (consultationId) {
      delete preservedStateRef.current[consultationId];
    }
  }, []);

  return {
    saveState,
    restoreState,
    clearState,
  };
};
