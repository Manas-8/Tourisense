function AnalyticsSection({ overview, profiles }) {
  const availableValues = (overview?.series || []).filter(row => Number.isFinite(row.total_tourists) && row.observations > 0).map(row => row.total_tourists);
  const maximum = Math.max(...availableValues, 1);
  const crowdCounts = (profiles || []).reduce((counts, row) => {
    const level = row.crowd_level || "Unknown"; counts[level] = (counts[level] || 0) + 1; return counts;
  }, {});
  return <div className="analytics-grid">
    <section className="analytics-card">
      <div className="card-header"><div><h3>Reported arrivals by calendar month</h3><p>Sum of source rows across covered states · no year supplied</p></div><span className="ml-badge">Historical summary</span></div>
      {overview?.series?.length ? <div className="overview-month-scroll"><div className="overview-month-chart" role="img" aria-label="Source tourist arrivals grouped by calendar month">{overview.series.map(row=>{const hasValue=Number.isFinite(row.total_tourists)&&row.observations>0;return <div className="overview-month" key={row.month} title={`${row.month}: ${hasValue?row.total_tourists.toLocaleString()+" tourists":"no source value"}, source rows summed across ${row.observations} states`}><b>{hasValue?(row.total_tourists/1000000).toFixed(1)+"M":"—"}</b><div className="overview-month-track"><i style={{height:`${hasValue?Math.max(3,row.total_tourists/maximum*100):0}%`}}/></div><span>{row.month.slice(0,3)}</span></div>})}</div></div> : <p className="ml-empty">Monthly tourism data is unavailable.</p>}
      {overview?.limitation && <p className="ml-chart-foot">{overview.limitation}</p>}
    </section>
    <section className="analytics-card">
      <div className="card-header"><div><h3>Typical destination crowd profiles</h3><p>Source attribute counts · not live visitor density</p></div></div>
      {profiles?.length ? <div className="crowd-list">{["High","Medium","Low","Unknown"].filter(level=>crowdCounts[level]).map(level=><div className="crowd-item" key={level}><div><strong>{level}</strong><small>Destination profiles</small></div><span className={`crowd ${level.toLowerCase()}`}>{crowdCounts[level]}</span></div>)}</div> : <p className="ml-empty">Crowd profile attributes are unavailable.</p>}
    </section>
  </div>;
}

export default AnalyticsSection;
