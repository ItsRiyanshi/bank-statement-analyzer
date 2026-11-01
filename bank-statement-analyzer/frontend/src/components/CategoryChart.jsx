import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from "recharts";

const COLORS = ["#14866d", "#b8aceb", "#72b7a0", "#e5b969", "#7b91a8", "#cf8eaa", "#83a9bd", "#9aa67c", "#c58756"];

export default function CategoryChart({ byCategory }) {
  const data = Object.entries(byCategory || {}).map(([name, value]) => ({ name, value }));
  const total = data.reduce((sum, item) => sum + Number(item.value || 0), 0);
  if (data.length === 0) return <p className="text-sm text-neutral-500">No category data yet.</p>;

  return (
    <div className="chart-card bg-white rounded-2xl shadow-sm border border-neutral-200 p-5">
      <div className="chart-heading"><div><p className="section-kicker">WHERE IT GOES</p><h3>Spending by category</h3></div><span className="chart-period">This period</span></div>
      <div className="category-chart-layout">
        <div className="donut-wrap">
          <ResponsiveContainer width="100%" height={224}>
            <PieChart>
              <Pie data={data} dataKey="value" nameKey="name" innerRadius={66} outerRadius={91} paddingAngle={3} stroke="none">
                {data.map((_, index) => <Cell key={index} fill={COLORS[index % COLORS.length]} />)}
              </Pie>
              <Tooltip formatter={(value) => `₹${Number(value).toLocaleString()}`} contentStyle={{ border: "1px solid #e7ebee", borderRadius: 10, boxShadow: "0 6px 20px #17233812" }} />
            </PieChart>
          </ResponsiveContainer>
          <div className="donut-total"><span>TOTAL SPEND</span><strong>₹{total.toLocaleString()}</strong></div>
        </div>
        <div className="category-legend">
          {data.slice(0, 7).map((item, index) => (
            <div className="category-legend-row" key={item.name}>
              <span className="category-dot" style={{ backgroundColor: COLORS[index % COLORS.length] }} />
              <span className="category-name">{item.name}</span>
              <strong>{total ? Math.round((Number(item.value) / total) * 100) : 0}%</strong>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
