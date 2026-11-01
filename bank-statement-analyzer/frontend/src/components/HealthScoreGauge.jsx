export default function HealthScoreGauge({ health }) {
  if (!health) return null;
  const { score, grade, breakdown, tips } = health;
  const color = score >= 80 ? "#14866d" : score >= 60 ? "#58a879" : score >= 40 ? "#c78c42" : "#c6646b";
  const circumference = 2 * Math.PI * 43;

  return (
    <div className="metric-card health-card bg-white rounded-2xl shadow-sm border border-neutral-200 p-5">
      <div className="metric-card-heading"><div><p className="section-kicker">WELLBEING</p><h3>Financial health</h3></div><span className="health-dot" /></div>
      <div className="health-summary">
        <div className="score-ring" style={{ "--score-color": color }}>
          <svg viewBox="0 0 100 100" aria-label={`Financial health score ${score} out of 100`} role="img">
            <circle className="score-track" cx="50" cy="50" r="43" />
            <circle className="score-progress" cx="50" cy="50" r="43" strokeDasharray={circumference} strokeDashoffset={circumference * (1 - score / 100)} />
          </svg>
          <div className="score-value"><strong>{score}</strong><span>out of 100</span></div>
        </div>
        <div className="grade-summary"><span className="grade-label">CURRENT GRADE</span><strong style={{ color }}>{grade}</strong><span className="grade-caption">Your money habits at a glance</span></div>
      </div>
      <div className="health-breakdown">
        {Object.entries(breakdown || {}).map(([key, value]) => (
          <div className="breakdown-row" key={key}>
            <span>{key.replace(/_/g, " ")}</span><strong>{value}<small>/100</small></strong>
            <div className="breakdown-track"><span style={{ width: `${value}%`, backgroundColor: color }} /></div>
          </div>
        ))}
      </div>
      {tips?.length > 0 && (
        <div className="health-tip"><span className="tip-spark">✦</span><p>{tips[0]}</p></div>
      )}
    </div>
  );
}
