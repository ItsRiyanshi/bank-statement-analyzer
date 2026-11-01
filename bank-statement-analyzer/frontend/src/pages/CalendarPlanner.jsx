import { useEffect, useState, useCallback } from "react";
import CalendarBudgetPlanner from "../components/CalendarBudgetPlanner.jsx";
import { getEvents, getBudgetPlan } from "../api/client.js";

export default function CalendarPlanner() {
  const [events, setEvents] = useState([]);
  const [plan, setPlan] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [ev, pl] = await Promise.all([getEvents(), getBudgetPlan()]);
      setEvents(ev || []);
      setPlan(pl || []);
    } catch (err) {
      setError(
        err?.response?.data?.detail ||
        err?.message ||
        "Could not load calendar commitments. The backend may be spinning up."
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { refresh(); }, [refresh]);

  return (
    <div className="planner-page">
      <div className="workflow-intro">
        <span className="workflow-icon planner-workflow-icon">▦</span>
        <div>
          <h2>Plan around real life</h2>
          <p>Upcoming commitments and a daily allowance, shaped around your month.</p>
        </div>
      </div>
      {loading ? (
        <div className="loading-panel"><span className="loading-spinner" /> Loading commitments and budget plan...</div>
      ) : error ? (
        <div className="error-panel space-y-3">
          <p>{error}</p>
          <button
            type="button"
            onClick={refresh}
            className="px-4 py-1.5 text-xs font-semibold rounded-lg bg-neutral-900 text-white hover:bg-neutral-800 transition"
          >
            Retry
          </button>
        </div>
      ) : (
        <CalendarBudgetPlanner events={events} plan={plan} onChange={refresh} />
      )}
    </div>
  );
}
