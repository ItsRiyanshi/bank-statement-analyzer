export default function SafeToSpendCard({ data }) {
  if (!data) return null;

  const availableBalance = data.available_balance ?? data.current_balance ?? 0;
  const upcomingObligations = data.upcoming_obligations_total ?? 0;
  const reservedEssentials = data.reserved_essential_expenses ?? 0;
  const discretionaryFunds = data.discretionary_funds ?? 0;
  const remainingDays = data.remaining_days ?? 1;
  const safeToday = data.safe_to_spend_today ?? 0;
  const projectedEnd = data.projected_end_of_month_balance ?? 0;
  const obligationsCount = data.upcoming_obligations?.length ?? 0;

  return (
    <div className="safe-card bg-gradient-to-br from-ink to-neutral-800 text-white rounded-2xl shadow-sm p-5">
      <div className="safe-card-top">
        <div>
          <p className="safe-eyebrow">AVAILABLE FOR TODAY</p>
          <h3>Safe to spend</h3>
        </div>
        <span className="safe-icon" aria-hidden="true">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7">
            <path d="M3 7.5h15a3 3 0 0 1 3 3v7a2 2 0 0 1-2 2H5a3 3 0 0 1-3-3v-9a3 3 0 0 1 3-3h13" />
            <path d="M2 9h15M16 14h2" />
          </svg>
        </span>
      </div>

      <p className="safe-amount">₹{safeToday.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 2 })}</p>
      <p className="safe-caption" title={data.assumptions || ""}>
        {data.planning_period_label ? `Daily allowance (${data.planning_period_label})` : "You can spend today and stay on track."}
      </p>

      <div className="safe-divider" />

      <div className="safe-details">
        <div>
          <span>Available balance</span>
          <strong>₹{availableBalance.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 2 })}</strong>
        </div>
        <div>
          <span>Upcoming obligations</span>
          <strong className="text-amber-300">-₹{upcomingObligations.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 2 })}</strong>
        </div>
        <div>
          <span>Reserved essentials</span>
          <strong className="text-sky-300">-₹{reservedEssentials.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 2 })}</strong>
        </div>
        <div>
          <span>Discretionary funds</span>
          <strong>₹{discretionaryFunds.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 2 })}</strong>
        </div>
        <div>
          <span>Planning period</span>
          <strong>{remainingDays} {remainingDays === 1 ? "day" : "days"}</strong>
        </div>
        <div>
          <span>Projected month-end</span>
          <strong>₹{projectedEnd.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 2 })}</strong>
        </div>
      </div>

      <div className="obligation-note">
        <span className="obligation-check">✓</span>
        {obligationsCount} upcoming obligation(s) accounted for
      </div>
    </div>
  );
}
