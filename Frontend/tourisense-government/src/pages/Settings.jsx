import { useEffect, useState } from "react";
import { Database, RefreshCw, ShieldCheck, UserRound } from "lucide-react";
import { apiFetch } from "../services/api";

export default function Settings({ user }) {
  const [datasets, setDatasets] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const load = async () => {
    setLoading(true); setError("");
    try { const body = await apiFetch("/ml/status"); setDatasets(body.data.datasets); }
    catch (err) { setError(err.message || "Data source status is unavailable."); }
    finally { setLoading(false); }
  };
  useEffect(() => { load(); }, []);

  return <section className="settings-page">
    <header className="settings-header"><div><div className="settings-breadcrumb">Government Portal / Account</div><h1>Account & data sources</h1><p>Current administrator identity and availability of the connected source files.</p></div><button className="ml-refresh" onClick={load} disabled={loading}><RefreshCw size={15}/>Refresh status</button></header>
    <div className="settings-layout">
      <article className="settings-section settings-source-card"><div className="section-title"><div><h2><UserRound size={19}/> Administrator account</h2><p>Identity from the authenticated TouriSense account.</p></div></div><dl className="account-facts"><div><dt>Name</dt><dd>{user?.name || "Unavailable"}</dd></div><div><dt>Email</dt><dd>{user?.email || "Unavailable"}</dd></div><div><dt>Role</dt><dd>{user?.role || "Unavailable"}</dd></div></dl><p className="account-security"><ShieldCheck size={17}/> Password and account changes use the existing authentication service.</p></article>
      <article className="settings-section settings-source-card"><div className="section-title"><div><h2><Database size={19}/> Connected data sources</h2><p>Availability reported by the backend; no sample status values are shown.</p></div></div>
        {loading && <p role="status">Checking source files…</p>}{error && <p className="ml-error" role="alert">{error} <button onClick={load}>Retry</button></p>}
        {!loading && !error && <div className="source-status-list">{Object.entries(datasets || {}).map(([key, source])=><div className="source-status-row" key={key}><div><strong>{source.path}</strong><small>{source.meaning}</small></div><span className={source.available ? "source-online" : "source-offline"}>{source.available ? `${source.rows ?? "Available"} records` : "Unavailable"}</span></div>)}</div>}
      </article>
    </div>
  </section>;
}
