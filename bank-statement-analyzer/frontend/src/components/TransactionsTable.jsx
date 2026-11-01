export default function TransactionsTable({ transactions }) {
  if (!transactions || transactions.length === 0) {
    return <div className="empty-transactions">No transactions yet. Upload a statement to get started.</div>;
  }
  return (
    <div className="transactions-table-wrap bg-white rounded-2xl shadow-sm border border-neutral-200 overflow-hidden">
      <div className="transactions-scroll">
      <table className="transactions-table w-full text-sm">
        <thead className="bg-neutral-50 text-neutral-500 text-left">
          <tr>
            <th className="px-4 py-2">Date</th>
            <th className="px-4 py-2">Description</th>
            <th className="px-4 py-2">Category</th>
            <th className="px-4 py-2 text-right">Amount</th>
            <th className="px-4 py-2">Flags</th>
          </tr>
        </thead>
        <tbody>
          {transactions.map((t) => (
            <tr key={t.id} className="border-t border-neutral-100">
              <td className="px-4 py-2 whitespace-nowrap">{t.date}</td>
              <td className="px-4 py-2">{t.description}</td>
              <td className="px-4 py-2">
                <span className="px-2 py-0.5 rounded-full bg-neutral-100 text-xs">{t.category}</span>
              </td>
              <td className={`px-4 py-2 text-right font-medium ${t.amount < 0 ? "text-accent" : "text-green-600"}`}>
                {t.amount < 0 ? "-" : "+"}₹{Math.abs(t.amount).toLocaleString()}
              </td>
              <td className="px-4 py-2 space-x-1">
                {t.is_recurring && <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full">Recurring</span>}
                {t.is_anomaly && <span className="text-xs bg-red-100 text-red-700 px-2 py-0.5 rounded-full">Unusual</span>}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      </div>
    </div>
  );
}
