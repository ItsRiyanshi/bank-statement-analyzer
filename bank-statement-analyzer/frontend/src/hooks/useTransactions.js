import { useEffect, useState, useCallback } from "react";
import {
  getSummary, getHealthScore, getRecurring, getAnomalies,
  getSummaryText, getTransactions, getSafeToSpend,
} from "../api/client.js";

export function useDashboardData() {
  const [state, setState] = useState({
    summary: null, health: null, recurring: [], anomalies: [],
    summaryText: "", transactions: [], safeToSpend: null, loading: true, error: null,
  });

  const refresh = useCallback(async () => {
    setState((s) => ({ ...s, loading: true, error: null }));
    try {
      const [summary, health, recurring, anomalies, summaryText, transactions, safeToSpend] = await Promise.all([
        getSummary(),
        getHealthScore(),
        getRecurring(),
        getAnomalies(),
        getSummaryText(),
        getTransactions(),
        getSafeToSpend().catch((err) => {
          console.warn("Could not fetch safe-to-spend:", err);
          return null;
        }),
      ]);
      setState({
        summary,
        health,
        recurring,
        anomalies,
        summaryText: summaryText?.summary || "",
        transactions: transactions || [],
        safeToSpend,
        loading: false,
        error: null,
      });
    } catch (err) {
      const message =
        err?.response?.data?.detail ||
        err?.message ||
        "Could not connect to the backend service. If using a free instance, it may be waking up from sleep.";
      setState((s) => ({ ...s, loading: false, error: message }));
    }
  }, []);

  useEffect(() => { refresh(); }, [refresh]);

  return { ...state, refresh };
}
