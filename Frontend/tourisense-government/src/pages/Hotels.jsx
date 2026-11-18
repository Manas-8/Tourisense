import { useEffect, useMemo, useState } from "react";
import { Hotel as HotelIcon, MapPin, Search, RefreshCw, Star } from "lucide-react";
import { apiFetch } from "../services/api";

export default function Hotels() {
  const [items,setItems]=useState([]); const [search,setSearch]=useState(""); const [location,setLocation]=useState(""); const [loading,setLoading]=useState(true); const [error,setError]=useState("");
  const load=async()=>{setLoading(true);setError("");try{const body=await apiFetch("/catalog/hotels");setItems(body.data.items);}catch(err){setError(err.message||"Hotel catalog is unavailable.");}finally{setLoading(false);}};
  useEffect(()=>{load();},[]);
  const locations=[...new Set(items.flatMap(item=>[item.city,item.state]).filter(Boolean))].sort();
  const filtered=useMemo(()=>items.filter(item=>(!location||[item.city,item.state].includes(location))&&`${item.name} ${item.location} ${item.city} ${item.state}`.toLowerCase().includes(search.toLowerCase())),[items,location,search]);
  return <div className="operational-page"><header><div><p className="breadcrumb">Government Portal / Hotels</p><h1>Registered hotels</h1><p>Live rows from TouriSense’s operational MySQL hotel catalog. Room availability and occupancy are not stored by the current schema.</p></div><button className="ml-refresh" onClick={load} disabled={loading}><RefreshCw size={15}/>Refresh</button></header>
    <div className="operational-filters"><label>City or state<select value={location} onChange={e=>setLocation(e.target.value)}><option value="">All locations</option>{locations.map(item=><option key={item}>{item}</option>)}</select></label><label>Search<input value={search} onChange={e=>setSearch(e.target.value)} placeholder="Hotel, area, city"/><Search size={15}/></label></div>
    {loading&&<p className="ml-empty" role="status">Loading hotel records…</p>}{error&&<div className="ml-error" role="alert">{error} <button onClick={load}>Retry</button></div>}
    {!loading&&!error&&<><p className="operational-count">{filtered.length} active hotels in the operational catalog</p>{filtered.length?<div className="operational-grid">{filtered.map(item=><article key={item.id} className="operational-card"><span className="operational-icon"><HotelIcon size={19}/></span><h2>{item.name}</h2><p><MapPin size={14}/>{item.location}{item.city?`, ${item.city}`:""}{item.state?`, ${item.state}`:""}</p>{item.description&&<p>{item.description}</p>}<div className="operational-facts"><span>{item.price_per_night==null?"Price unavailable":`₹${item.price_per_night.toLocaleString("en-IN")} / night`}</span><span>{item.rating==null?"Rating unavailable":<><Star size={13}/> {item.rating}</>}</span></div>{item.amenities&&<small>{item.amenities}</small>}</article>)}</div>:<div className="ml-empty">No active hotel records match this search.</div>}</>}
  </div>;
}
