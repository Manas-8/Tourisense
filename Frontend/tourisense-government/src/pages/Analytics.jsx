import { useEffect, useMemo, useState } from "react";
import { BarChart3, Users, IndianRupee, MapPin, RefreshCw } from "lucide-react";

const API = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:5000/api";
const token = () => localStorage.getItem("tourisense-token") || localStorage.getItem("wanderly-token");

function MetricCard({ icon: Icon, label, value, note }) {
  return <article className="ml-kpi"><span className="ml-kpi-icon"><Icon size={19}/></span><div><small>{label}</small><strong>{value}</strong><p>{note}</p></div></article>;
}

export default function Analytics() {
  const [states, setStates] = useState([]);
  const [state, setState] = useState("");
  const [metric, setMetric] = useState("total_tourists");
  const [data, setData] = useState(null);
  const [experience, setExperience] = useState(null);
  const [ratingAccess, setRatingAccess] = useState("loading");
  const [credentials, setCredentials] = useState({ email: "", password: "" });
  const [loginError, setLoginError] = useState("");
  const [authenticating, setAuthenticating] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const load = async () => {
    setLoading(true); setError("");
    try {
      const params = new URLSearchParams({ metric }); if (state) params.set("state", state);
      const res = await fetch(`${API}/ml/tourism?${params}`); const body = await res.json();
      if (!res.ok) throw new Error(body.error || "Tourism data could not be loaded.");
      setData(body.data); setStates(body.data.states);
      const ratingRes = await fetch(`${API}/ml/experience`, { headers: token() ? { Authorization: `Bearer ${token()}` } : {} });
      if (ratingRes.ok) { const ratingBody = await ratingRes.json(); setExperience(ratingBody.data); setRatingAccess("allowed"); }
      else { setExperience(null); setRatingAccess(ratingRes.status === 401 ? "signin" : ratingRes.status === 403 ? "forbidden" : "unavailable"); }
    } catch (err) { setError(err.message || "Could not connect to the analytics service."); }
    finally { setLoading(false); }
  };
  useEffect(() => { load(); }, [state, metric]);
  const signIn = async (event) => {
    event.preventDefault(); setAuthenticating(true); setLoginError("");
    try {
      const response = await fetch(`${API}/auth/login`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(credentials) });
      const body = await response.json();
      if (!response.ok) throw new Error(body.error || "Sign in failed.");
      if (body.user?.role !== "admin") throw new Error("This portal requires a government administrator account.");
      localStorage.setItem("tourisense-token", body.token);
      await load();
    } catch (err) { setLoginError(err.message || "Sign in failed."); }
    finally { setAuthenticating(false); }
  };
  const max = useMemo(() => Math.max(...(data?.series || []).map(x => x.value || 0), 1), [data]);
  const metricLabel = { total_tourists: "Total arrivals", domestic_tourists: "Domestic arrivals", foreign_tourists: "Foreign arrivals", revenue_inr_crore: "Tourism revenue (₹ crore)" }[metric];
  const latestValue = useMemo(() => {
    const vals = (data?.series || []).filter(x => x.value != null).map(x => x.value);
    return vals.length ? vals[vals.length - 1] : null;
  }, [data]);
  return <main className="ml-analytics">
    <header className="ml-analytics-head"><div><div className="breadcrumb">Government Portal / Tourism Intelligence</div><h1>Tourism intelligence</h1><p>Explore the supplied state and monthly records, with data limits shown alongside every view.</p></div><button onClick={load} className="ml-refresh" disabled={loading}><RefreshCw size={16}/> Refresh</button></header>
    <p className="ml-history-note">Monthly historical profile · values are grouped by calendar month; no year is assigned.</p>
    <div className="ml-selectors"><label>State<select value={state} onChange={e=>setState(e.target.value)}><option value="">All states (monthly average)</option>{states.map(x=><option key={x}>{x}</option>)}</select></label><label>Measure<select value={metric} onChange={e=>setMetric(e.target.value)}><option value="total_tourists">Total tourists</option><option value="domestic_tourists">Domestic tourists</option><option value="foreign_tourists">Foreign tourists</option><option value="revenue_inr_crore">Revenue (INR crore)</option></select></label></div>
    {error && <div className="ml-error" role="alert">{error} <button onClick={load}>Retry</button></div>}
    {loading && <div className="ml-empty">Loading source data…</div>}
    {!loading && !error && data && <>
      <div className="ml-kpis"><MetricCard icon={BarChart3} label="View type" value="Historical profile" note="Month averages, no dates inferred"/><MetricCard icon={Users} label="Source records" value={data.data_coverage.filtered_records.toLocaleString()} note={`${data.data_coverage.states} states · ${data.data_coverage.months_per_state} monthly buckets`}/><MetricCard icon={IndianRupee} label={`December · ${metricLabel}`} value={latestValue == null ? "—" : latestValue.toLocaleString("en-IN")} note="Last month in calendar order, not latest period"/><MetricCard icon={MapPin} label="Total check" value={data.totals_consistent ? "Consistent" : "Needs review"} note="Domestic + foreign equals total in all rows"/></div>
      <section className="ml-chart-card"><div className="ml-chart-title"><div><h2>{metricLabel} by month</h2><p>{state || "Average across all states"} · each bar aggregates available records for that calendar month</p></div><span className="ml-badge">Historical summary</span></div>
        <div className="ml-bars" role="img" aria-label={`${metricLabel} monthly historical profile`}>{data.series.map(item=><div className="ml-bar-col" key={item.month} title={`${item.month}: ${item.value?.toLocaleString("en-IN") ?? "No data"} · ${item.observations} records`}><strong>{item.value == null ? "—" : item.value >= 100000 ? `${(item.value/100000).toFixed(1)}L` : item.value.toLocaleString("en-IN",{maximumFractionDigits:1})}</strong><div className="ml-bar-track"><div className="ml-bar" style={{height:`${Math.max(item.value ? item.value/max*100 : 0, item.value ? 3 : 0)}%`}}/></div><span>{item.month.slice(0,3)}</span></div>)}</div>
        <p className="ml-chart-foot">Observations per month: {state ? "1" : `${data.data_coverage.states} (where present)`}. Total tourists are derived consistently from domestic and foreign counts in the provided source.</p>
      </section>
      <section className="ml-experience-card"><div><div className="ml-chart-title"><div><h2>Visitor experience</h2><p>Privacy-safe aggregate of observed ratings</p></div><span className="ml-badge">Observed data</span></div>
        {experience ? <><div className="ml-rating-summary"><strong>{experience.mean_rating ?? "—"}<small> / 5 average</small></strong><span>{experience.observations} ratings across {experience.destinations_with_ratings} destinations</span></div><div className="ml-rating-bars">{experience.distribution.map(row=><div key={row.rating}><span>{row.rating} ★</span><div><i style={{width:`${experience.observations ? row.count/experience.observations*100 : 0}%`}}/></div><b>{row.count}</b></div>)}</div><p className="ml-chart-foot">{experience.limitation}</p></> : ratingAccess === "signin" ? <form className="ml-login" onSubmit={signIn}><p>Sign in with your government administrator account to view aggregate ratings.</p><label>Email<input type="email" value={credentials.email} onChange={e=>setCredentials({...credentials,email:e.target.value})} required autoComplete="username"/></label><label>Password<input type="password" value={credentials.password} onChange={e=>setCredentials({...credentials,password:e.target.value})} required autoComplete="current-password"/></label>{loginError && <p className="ml-auth-error" role="alert">{loginError}</p>}<button className="ml-refresh" disabled={authenticating}>{authenticating ? "Signing in…" : "Sign in"}</button></form> : ratingAccess === "forbidden" ? <div className="ml-private"><p>This account does not have government administrator access.</p><button onClick={()=>{localStorage.removeItem("tourisense-token");setRatingAccess("signin");}}>Sign in with an administrator account</button></div> : <p className="ml-private">{ratingAccess === "loading" ? "Loading rating insights…" : "Rating insights are unavailable."}</p>}
      </div></section>
    </>}
  </main>;
}
