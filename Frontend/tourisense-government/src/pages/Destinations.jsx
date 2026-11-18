import { useEffect, useMemo, useState } from "react";
import { MapPin, Search, RefreshCw } from "lucide-react";
import { apiFetch } from "../services/api";

function Destinations({ onSelectDestination }) {
  const [items, setItems] = useState([]);
  const [coverage, setCoverage] = useState(null);
  const [region, setRegion] = useState("");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const load = async () => {
    setLoading(true); setError("");
    try { const body = await apiFetch("/catalog/destinations"); setItems(body.data.items); setCoverage(body.data.coverage); }
    catch (err) { setError(err.message || "Destination profiles could not be loaded."); }
    finally { setLoading(false); }
  };
  useEffect(() => { load(); }, []);
  const regions = [...new Set(items.map(item => item.region).filter(Boolean))].sort();
  const filtered = useMemo(() => items.filter(item => (!region || item.region === region) && `${item.name} ${item.state} ${item.category} ${item.region}`.toLowerCase().includes(search.toLowerCase())), [items, region, search]);
  const highCrowd = items.filter(item => item.crowd_level === "High").length;
  return <div className="destination-page">
    <div className="destination-page-header"><div><div className="breadcrumb">Government Portal / Destinations</div><h1>Destination profiles</h1><p>Source attributes and verified catalog matches. Visitor counts, ticket prices, images, and open status are not present in these records.</p></div><button className="ml-refresh" onClick={load} disabled={loading}><RefreshCw size={15}/> Refresh</button></div>
    {!loading && !error && <div className="destination-summary"><div className="summary-box"><span>Destination profiles</span><strong>{items.length}</strong><small>Source metadata rows</small></div><div className="summary-box"><span>Catalog matches</span><strong>{coverage?.matched_unique_catalog_destinations ?? "—"}/{coverage?.catalog_unique_destinations ?? "—"}</strong><small>Explicit aliases and normalized keys</small></div><div className="summary-box"><span>High typical crowd</span><strong>{highCrowd}</strong><small>Profile attribute, not live crowd</small></div><div className="summary-box"><span>Unmatched profiles</span><strong>{coverage?.unmatched_metadata_destinations ?? "—"}</strong><small>Metadata with no catalog concept</small></div></div>}
    <div className="destination-toolbar"><label>Region<select value={region} onChange={e=>setRegion(e.target.value)}><option value="">All regions</option>{regions.map(value=><option key={value}>{value}</option>)}</select></label><div className="destination-search"><Search size={16}/><input value={search} onChange={e=>setSearch(e.target.value)} placeholder="Search destination, state, category"/></div></div>
    {loading && <p className="ml-empty" role="status">Loading destination profiles…</p>}{error && <div className="ml-error" role="alert">{error} <button onClick={load}>Retry</button></div>}
    {!loading && !error && filtered.length > 0 && <div className="destination-grid">{filtered.map(place=><article className="destination-card-new" key={place.id}><div className="destination-photo destination-photo-empty"><span className="category-tag">{place.category || "Category unknown"}</span><span className={`crowd-tag ${(place.crowd_level || "unknown").toLowerCase()}`}>Typical crowd: {place.crowd_level || "Unknown"}</span></div><div className="destination-card-content"><div className="destination-title"><div><h3>{place.name}</h3><p><MapPin size={13}/> {place.state}</p></div><span className="open-status">{place.catalog_match ? "Catalog matched" : "Metadata profile"}</span></div><div className="destination-stats"><div><span>Region</span><strong>{place.region || "Unknown"}</strong></div><div><span>Best season</span><strong>{place.best_season || "Unknown"}</strong></div><div><span>Typical budget / person</span><strong>{place.budget == null ? "Unknown" : `₹${place.budget.toLocaleString("en-IN")}`}</strong></div></div><button className="details-btn" onClick={()=>onSelectDestination(place)}>View source profile</button></div></article>)}</div>}
    {!loading && !error && filtered.length === 0 && <div className="no-results"><h3>No destination profiles found</h3><p>Try another search or region.</p></div>}
  </div>;
}

export default Destinations;
