import { useState } from "react";
import { addEvent, deleteEvent, syncGoogleCalendar } from "../api/client.js";

export default function CalendarBudgetPlanner({ events, plan, onChange }) {
  const [title, setTitle] = useState("");
  const [date, setDate] = useState("");
  const [cost, setCost] = useState("");
  const [syncing, setSyncing] = useState(false);

  const handleAdd = async (e) => {
    e.preventDefault();
    if (!title || !date) return;
    await addEvent({ title, date, estimated_cost: cost ? Number(cost) : null });
    setTitle(""); setDate(""); setCost("");
    onChange?.();
  };

  const handleSync = async () => {
    setSyncing(true);
    try {
      await syncGoogleCalendar();
      onChange?.();
    } catch (err) {
      alert(err?.response?.data?.detail || "Google Calendar sync failed. See backend/app/services/google_calendar.py for setup.");
    } finally {
      setSyncing(false);
    }
  };

  return (
    <div className="planner-grid grid md:grid-cols-2 gap-5">
      <div className="planner-panel bg-white rounded-2xl shadow-sm border border-neutral-200 p-5">
        <div className="planner-panel-heading">
          <div><p className="section-kicker">YOUR COMMITMENTS</p><h3>Upcoming events</h3></div>
          <button onClick={handleSync} disabled={syncing} className="calendar-sync-button">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round"><path d="M20 7v5h-5M4 17v-5h5" /><path d="M5.5 9a7 7 0 0 1 11.6-2.6L20 12M4 12l2.9 5.6A7 7 0 0 0 18.5 15" /></svg>{syncing ? "Syncing..." : "Sync calendar"}
          </button>
        </div>
        <form onSubmit={handleAdd} className="event-form">
          <label><span>Event</span><input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="e.g. Rent payment" /></label>
          <div className="event-form-row">
            <label><span>Date</span><input value={date} onChange={(e) => setDate(e.target.value)} type="date" /></label>
            <label><span>Estimated cost</span><input value={cost} onChange={(e) => setCost(e.target.value)} type="number" min="0" placeholder="Optional" /></label>
          </div>
          <button type="submit" className="add-event-button"><span>+</span> Add event</button>
        </form>
        <div className="events-list-heading"><span>EVENT</span><span>ESTIMATED COST</span></div>
        <ul className="events-list">
          {events?.map((e) => (
            <li key={e.id} className="event-row">
              <span className="event-date-chip"><strong>{new Date(`${e.date}T00:00:00`).toLocaleDateString(undefined, { day: "2-digit" })}</strong><small>{new Date(`${e.date}T00:00:00`).toLocaleDateString(undefined, { month: "short" })}</small></span>
              <span className="event-title">{e.title}<small>{e.date}</small></span>
              <span className="event-cost">{e.estimated_cost == null ? "Not set" : `₹${e.estimated_cost.toLocaleString()}`}</span>
              <button aria-label={`Delete ${e.title}`} onClick={async () => { await deleteEvent(e.id); onChange?.(); }} className="delete-event-button"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round"><path d="M4 7h16M10 11v6m4-6v6M5 7l1 14h12l1-14M9 7V4h6v3" /></svg></button>
            </li>
          ))}
        </ul>
        {(!events || events.length === 0) && <p className="empty-events">No upcoming events added.</p>}
      </div>

      <div className="planner-panel budget-panel bg-white rounded-2xl shadow-sm border border-neutral-200 p-5">
        <div className="planner-panel-heading"><div><p className="section-kicker">A STEADIER PACE</p><h3>Daily budget</h3></div><span className="month-label">Rest of month</span></div>
        <div className="budget-days">
          {plan?.map((p) => (
            <div key={p.day} className={`budget-day${p.has_event ? " budget-event-day" : ""}`}>
              <span className="budget-date"><span className="budget-day-mark" />{p.day}{p.has_event && <small>Event day</small>}</span>
              <span className="budget-amount">₹{p.planned_amount.toLocaleString()}</span>
            </div>
          ))}
        </div>
        <p className="budget-explainer">
          Event days get a boosted allowance; the remaining days absorb the difference to keep your monthly plan on track.
        </p>
      </div>
    </div>
  );
}
