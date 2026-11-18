import { ArrowLeft } from "lucide-react";

function DestinationDetails({ destination, onBack }) {
  const facts = [
    ["Region", destination.region], ["Best season", destination.best_season],
    ["Preferred months", destination.months_best_for],
    ["Typical budget per person", destination.budget == null ? null : `₹${destination.budget.toLocaleString("en-IN")}`],
    ["Typical trip duration", destination.duration_days == null ? null : `${destination.duration_days} days`],
    ["Typical crowd profile", destination.crowd_level], ["Temperature range", destination.temperature_range_c],
    ["Nearest major city", destination.nearest_major_city], ["Popular with", destination.popular_with],
  ];
  return <section className="gov-destination-detail">
    <button className="text-btn" onClick={onBack}><ArrowLeft size={16}/> Back to destination profiles</button>
    <p className="breadcrumb">Government Portal / Destination profile</p>
    <h1>{destination.name}</h1><p className="gov-detail-subtitle">{destination.state} · {destination.category || "Category unavailable"}</p>
    <div className="ml-limit"><strong>Source profile only</strong><p>These values describe the source dataset. They do not indicate live operating status, current crowd size, ticket availability, or current weather.</p></div>
    <div className="gov-facts">{facts.map(([label,value])=><article key={label}><small>{label}</small><strong>{value || "Not available"}</strong></article>)}
      <article><small>Catalog name/state match</small><strong>{destination.catalog_match ? destination.catalog_match_method : "No catalog match"}</strong></article>
      <article><small>Popularity source value</small><strong>{destination.popularity == null ? "Not available" : destination.popularity.toFixed(2)}</strong><small>Source ranking scale, not a probability</small></article>
      <article><small>Observed experience rating</small><strong>{destination.observed_rating == null ? "Not available" : `${destination.observed_rating} / 5`}</strong><small>{destination.rating_observations ? `${destination.rating_observations} joined visit ratings` : "No joined rating observations"}</small></article>
    </div>
  </section>;
}

export default DestinationDetails;
