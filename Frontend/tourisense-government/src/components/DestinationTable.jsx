import { useMemo, useState } from "react";

function DestinationTable({ profiles = [] }) {
  const [region, setRegion] = useState("");
  const regions = [...new Set(profiles.map(row => row.region).filter(Boolean))].sort();
  const shown = useMemo(() => profiles.filter(row => !region || row.region === region).slice(0, 10), [profiles, region]);
  return <section className="destination-card">
    <div className="destination-header"><div><h3>Destination profile sample</h3><p>Attribute metadata from the supplied destination statistics file; no live footfall data is available.</p></div><label className="profile-region-filter">Region<select value={region} onChange={e=>setRegion(e.target.value)}><option value="">All regions</option>{regions.map(value=><option key={value}>{value}</option>)}</select></label></div>
    {shown.length ? <div className="table-container"><table><thead><tr><th>Destination</th><th>State</th><th>Region</th><th>Category</th><th>Typical crowd</th><th>Budget (₹ / person)</th></tr></thead><tbody>{shown.map(row=><tr key={row.id}><td><strong>{row.name}</strong></td><td>{row.state || "Unknown"}</td><td>{row.region || "Unknown"}</td><td>{row.category || "Unknown"}</td><td>{row.crowd_level || "Unknown"}</td><td>{row.budget_inr == null ? "Unknown" : row.budget_inr.toLocaleString("en-IN")}</td></tr>)}</tbody></table></div> : <p className="ml-empty">No destination profiles match this region.</p>}
  </section>;
}

export default DestinationTable;
