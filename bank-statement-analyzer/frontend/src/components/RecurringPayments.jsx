export default function RecurringPayments({ items }) {
  return (
    <div className="list-card bg-white rounded-2xl shadow-sm border border-neutral-200 p-5">
      <div className="list-card-heading"><div><p className="section-kicker">REGULAR COMMITMENTS</p><h3>Recurring payments</h3></div><span className="list-heading-icon recurring-icon">↻</span></div>
      {(!items || items.length === 0) ? (
        <p className="empty-list">None detected yet.</p>
      ) : (
        <ul className="finance-list">
          {items.map((t, i) => (
            <li key={i} className="finance-list-row">
              <span className="payment-avatar">{(t.description || "P").charAt(0).toUpperCase()}</span>
              <span className="finance-description">{t.description}<small>Recurring payment</small></span>
              <strong>₹{Math.abs(t.amount).toLocaleString()}</strong>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
