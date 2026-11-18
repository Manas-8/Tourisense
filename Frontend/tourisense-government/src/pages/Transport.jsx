import { useEffect, useMemo, useState } from "react";
import { Bus, Search, RefreshCw, MapPin } from "lucide-react";
import { apiFetch } from "../services/api";

export default function Transport() {
  const [items,setItems]=useState([]);const [search,setSearch]=useState("");const [location,setLocation]=useState("");const [loading,setLoading]=useState(true);const [error,setError]=useState("");
  const load=async()=>{setLoading(true);setError("");try{const body=await apiFetch("/catalog/transport");setItems(body.data.items);}catch(err){setError(err.message||"Transport catalog is unavailable.");}finally{setLoading(false);}};
  useEffect(()=>{load();},[]);
  const locations=[...new Set(items.flatMap(item=>[item.location,item.state]).filter(Boolean))].sort();
  const filtered=useMemo(()=>items.filter(item=>(!location||[item.location,item.state].includes(location))&&`${item.name} ${item.type} ${item.route} ${item.location}`.toLowerCase().includes(search.toLowerCase())),[items,location,search]);
  return <div className="operational-page"><header><div><p className="breadcrumb">Government Portal / Transport</p><h1>Transport options</h1><p>Active records from the operational MySQL transport catalog. The schema has no live fleet, passenger count, delay, or departure telemetry.</p></div><button className="ml-refresh" onClick={load} disabled={loading}><RefreshCw size={15}/>Refresh</button></header>
    <div className="operational-filters"><label>City or state<select value={location} onChange={e=>setLocation(e.target.value)}><option value="">All locations</option>{locations.map(item=><option key={item}>{item}</option>)}</select></label><label>Search<input value={search} onChange={e=>setSearch(e.target.value)} placeholder="Service, route or type"/><Search size={15}/></label></div>
    {loading&&<p className="ml-empty" role="status">Loading transport records…</p>}{error&&<div className="ml-error" role="alert">{error} <button onClick={load}>Retry</button></div>}
    {!loading&&!error&&<><p className="operational-count">{filtered.length} active transport options in the operational catalog</p>{filtered.length?<div className="operational-grid">{filtered.map(item=><article key={item.id} className="operational-card"><span className="operational-icon"><Bus size={19}/></span><h2>{item.name}</h2><p><MapPin size={14}/>{item.location||"Location unavailable"}{item.state?`, ${item.state}`:""}</p><div className="operational-facts"><span>{item.type||"Type unknown"}</span><span>{item.duration||"Duration unavailable"}</span></div><p className="operational-route">{item.route}</p><small>{item.cost==null?"Fare unavailable":`From ₹${item.cost.toLocaleString("en-IN")}`}</small></article>)}</div>:<div className="ml-empty">No active transport records match this search.</div>}</>}
  </div>;
}
