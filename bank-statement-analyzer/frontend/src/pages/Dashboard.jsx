import { useState, useEffect } from "react";
import { useDashboardData } from "../hooks/useTransactions.js";
import HealthScoreGauge from "../components/HealthScoreGauge.jsx";
import CategoryChart from "../components/CategoryChart.jsx";
import SpendingTrend from "../components/SpendingTrend.jsx";
import SafeToSpendCard from "../components/SafeToSpendCard.jsx";
import RecurringPayments from "../components/RecurringPayments.jsx";
import AnomalyAlerts from "../components/AnomalyAlerts.jsx";
import SummaryPanel from "../components/SummaryPanel.jsx";
import TransactionsTable from "../components/TransactionsTable.jsx";

export default function Dashboard() {
  const { summary, health, recurring, anomalies, summaryText, transactions, safeToSpend, loading, error, refresh } = useDashboardData();
  const [slowNotice, setSlowNotice] = useState(false);

  useEffect(() => {
    let timer;
    if (loading) {
      timer = setTimeout(() => setSlowNotice(true), 4000);
    } else {
      setSlowNotice(false);
    }
    return () => clearTimeout(timer);
  }, [loading]);

  if (loading) {
    return (
      <div className="loading-panel">
        <span className="loading-spinner" />
        <div className="loading-text-wrap">
          <p>Loading your financial overview...</p>
          {slowNotice && (
            <small className="text-neutral-400 block mt-1.5 text-xs">
              Connecting to backend service (free tier instances may take 30–45s to wake up on initial visit)...
            </small>
          )}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="error-panel space-y-3">
        <p>We couldn't load your financial overview. {error}</p>
        <button
          type="button"
          onClick={refresh}
          className="px-4 py-1.5 text-xs font-semibold rounded-lg bg-neutral-900 text-white hover:bg-neutral-800 transition"
        >
          Retry Connection
        </button>
      </div>
    );
  }

  return (
    <div className="dashboard-content space-y-6">
      <div className="grid md:grid-cols-3 gap-5 overview-grid">
        <HealthScoreGauge health={health} />
        <SafeToSpendCard data={safeToSpend} />
        <SummaryPanel summaryText={summaryText} />
      </div>

      <div className="grid md:grid-cols-2 gap-5 chart-grid">
        <CategoryChart byCategory={summary?.by_category} />
        <SpendingTrend monthlyTrend={summary?.monthly_trend} />
      </div>

      <div className="grid md:grid-cols-2 gap-5">
        <RecurringPayments items={recurring} />
        <AnomalyAlerts items={anomalies} />
      </div>

      <div className="transactions-section">
        <div className="section-heading">
          <div><p className="section-kicker">YOUR ACTIVITY</p><h2>All transactions</h2></div>
          <span className="section-note">Latest account activity</span>
        </div>
        <TransactionsTable transactions={transactions} />
      </div>
    </div>
  );
}
