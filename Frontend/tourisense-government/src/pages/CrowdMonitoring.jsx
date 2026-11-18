import { useEffect, useMemo, useState } from "react";
import { apiFetch } from "../services/api";

function CrowdMonitoring() {
  const [profiles, setProfiles] = useState([]);
  const [region, setRegion] = useState("");
  const [crowd, setCrowd] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const load = async () => { setLoading(true); setError(""); try { const body=await apiFetch("/catalog/destinations"); setProfiles(body.data.items); } catch(err) { setError(err.message || "Crowd profiles are unavailable."); } finally { setLoading(false); } };
  useEffect(() => { load(); }, []);
  const regions=[...new Set(profiles.map(item=>item.region).filter(Boolean))].sort();
  const filtered=useMemo(()=>profiles.filter(item=>(!region || item.region===region)&&(!crowd || item.crowd_level===crowd)),[profiles,region,crowd]);
  const count=level=>profiles.filter(item=>item.crowd_level===level).length;
  return <div className="crowd-page">
    <div className="crowd-page-header"><div><div className="breadcrumb">Government Portal / Crowd Monitoring</div><h1>Typical crowd profiles</h1><p>Destination metadata describes expected crowd levels. The repository has no real time visitor counts or venue capacities.</p></div><button className="ml-refresh" onClick={load} disabled={loading}>Refresh</button></div>
    {!loading&&!error&&<div className="crowd-summary"><div className="crowd-summary-card"><span>Profiles covered</span><strong>{profiles.length}</strong><small>Destination metadata rows</small></div>{["High","Medium","Low"].map(level=><div className="crowd-summary-card" key={level}><span>{level} typical crowd</span><strong>{count(level)}</strong><small>Source profile count, not live density</small></div>)}</div>}
    <div className="crowd-toolbar"><label>Region<select value={region} onChange={e=>setRegion(e.target.value)}><option value="">All regions</option>{regions.map(item=><option key={item}>{item}</option>)}</select></label><label>Typical crowd<select value={crowd} onChange={e=>setCrowd(e.target.value)}><option value="">All levels</option>{["High","Medium","Low"].map(item=><option key={item}>{item}</option>)}</select></label></div>
    {loading&&<p className="ml-empty" role="status">Loading source crowd profiles…</p>}{error&&<div className="ml-error" role="alert">{error} <button onClick={load}>Retry</button></div>}
    {!loading&&!error&&<section className="crowd-monitoring-card"><div className="crowd-card-header"><div><h2>Destination crowd attributes</h2><p>One row per source destination profile</p></div><span>{filtered.length} shown</span></div>{filtered.length? <div className="crowd-destination-list">{filtered.map(place=><article className="crowd-destination" key={place.id}><div className="crowd-place-info"><div className="place-icon">•</div><div><h3>{place.name}</h3><p>{place.state} · {place.region || "Region unknown"}</p></div></div><div className="visitor-count"><strong>{place.crowd_level || "Unknown"}</strong><span>typical crowd level</span></div><div className="capacity-info"><span>Category</span><strong>{place.category || "Unknown"}</strong><small>Best season: {place.best_season || "Unknown"}</small></div><span className={`crowd-level-badge ${(place.crowd_level||"unknown").toLowerCase()}`}>Profile data</span></article>)}</div>:<p className="ml-empty">No profiles match the selected filters.</p>}</section>}
  </div>;
}

export default CrowdMonitoring;
