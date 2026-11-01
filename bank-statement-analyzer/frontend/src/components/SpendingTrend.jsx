import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts";

export default function SpendingTrend({ monthlyTrend }) {
  if (!monthlyTrend || monthlyTrend.length === 0) {
    return <div className="chart-card bg-white rounded-2xl shadow-sm border border-neutral-200 p-5"><div className="chart-heading"><div><p className="section-kicker">CASH FLOW</p><h3>Monthly income vs expense</h3></div></div><p className="empty-chart">No monthly trend data yet.</p></div>;
  }
  return (
    <div className="chart-card bg-white rounded-2xl shadow-sm border border-neutral-200 p-5">
      <div className="chart-heading"><div><p className="section-kicker">CASH FLOW</p><h3>Monthly income vs expense</h3></div><span className="chart-period">Monthly</span></div>
      <ResponsiveContainer width="100%" height={250}>
        <AreaChart data={monthlyTrend} margin={{ top: 10, right: 6, left: -12, bottom: 0 }}>
          <defs>
            <linearGradient id="incomeFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#14866d" stopOpacity={0.19} /><stop offset="100%" stopColor="#14866d" stopOpacity={0.01} /></linearGradient>
            <linearGradient id="expenseFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#b8aceb" stopOpacity={0.22} /><stop offset="100%" stopColor="#b8aceb" stopOpacity={0.01} /></linearGradient>
          </defs>
          <CartesianGrid vertical={false} strokeDasharray="3 5" stroke="#edf0f1" />
          <XAxis dataKey="month" fontSize={11} axisLine={false} tickLine={false} tick={{ fill: "#8792a0" }} dy={8} />
          <YAxis fontSize={10} axisLine={false} tickLine={false} tick={{ fill: "#8792a0" }} tickFormatter={(value) => `₹${value}`} />
          <Tooltip formatter={(value) => `₹${Number(value).toLocaleString()}`} contentStyle={{ border: "1px solid #e7ebee", borderRadius: 10, boxShadow: "0 6px 20px #17233812" }} />
          <Legend iconType="circle" iconSize={7} wrapperStyle={{ fontSize: 11, color: "#647184", paddingTop: 6 }} />
          <Area type="monotone" dataKey="income" stroke="#14866d" strokeWidth={2.5} fill="url(#incomeFill)" activeDot={{ r: 4, strokeWidth: 0 }} />
          <Area type="monotone" dataKey="expense" stroke="#9b8bd5" strokeWidth={2.5} fill="url(#expenseFill)" activeDot={{ r: 4, strokeWidth: 0 }} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
