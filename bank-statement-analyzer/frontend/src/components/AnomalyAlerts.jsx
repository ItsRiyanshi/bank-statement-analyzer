export default function AnomalyAlerts({ items }) {
  return (
    <div className="list-card alert-card bg-white rounded-2xl shadow-sm border border-neutral-200 p-5">
      <div className="list-card-heading"><div><p className="section-kicker">NEEDS A LOOK</p><h3>Unusual spending</h3></div><span className="list-heading-icon alert-icon">!</span></div>
      {(!items || items.length === 0) ? (
        <p className="empty-list">No anomalies detected.</p>
      ) : (
        <ul className="finance-list">
          {items.map((t, i) => (
            <li key={i} className="finance-list-row">
              <span className="payment-avatar alert-avatar">!</span>
              <span className="finance-description">{t.description}<small>{t.date}</small></span>
              <strong className="alert-amount">₹{Math.abs(t.amount).toLocaleString()}</strong>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
