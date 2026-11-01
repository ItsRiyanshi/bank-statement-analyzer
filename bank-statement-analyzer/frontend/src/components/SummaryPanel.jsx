export default function SummaryPanel({ summaryText }) {
  if (!summaryText) return null;
  return (
    <div className="summary-card bg-white rounded-2xl shadow-sm border border-neutral-200 p-5">
      <div className="metric-card-heading"><div><p className="section-kicker">THE BIG PICTURE</p><h3>Monthly summary</h3></div><span className="summary-mark">✳</span></div>
      <p className="summary-copy">{summaryText}</p>
      <div className="summary-footnote"><span className="summary-indicator" />Generated from your recent activity</div>
    </div>
  );
}
