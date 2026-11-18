import { useEffect, useState } from "react";
import { CalendarDays, RefreshCw } from "lucide-react";
import Sidebar from "./components/Sidebar";
import Topbar from "./components/Topbar";
import StatCard from "./components/StatCard";
import AnalyticsSection from "./components/AnalyticsSection";
import DestinationTable from "./components/DestinationTable";
import AdminGate from "./components/AdminGate";
import { apiFetch } from "./services/api";
import Destinations from "./pages/Destinations";
import DestinationDetails from "./pages/DestinationDetails";
import CrowdMonitoring from "./pages/CrowdMonitoring";
import Hotels from "./pages/Hotels";
import Transport from "./pages/Transport";
import Analytics from "./pages/Analytics";
import Settings from "./pages/Settings";

function DashboardHome() {
  const [overview, setOverview] = useState(null);
  const [profiles, setProfiles] = useState([]);
  const [coverage, setCoverage] = useState(null);
  const [experience, setExperience] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const load = async () => {
    setLoading(true); setError("");
    try {
      const [overviewBody, profilesBody, ratingBody] = await Promise.all([
        apiFetch("/ml/dashboard-overview"), apiFetch("/catalog/destinations"), apiFetch("/ml/experience")
      ]);
      setOverview(overviewBody.data); setProfiles(profilesBody.data.items); setCoverage(profilesBody.data.coverage); setExperience(ratingBody.data);
    } catch (err) { setError(err.message || "Dashboard source data is unavailable."); }
    finally { setLoading(false); }
  };
  useEffect(() => { load(); }, []);
  return <>
    <div className="government-dashboard-head"><div><p className="breadcrumb">Government Portal / Overview</p><h1>Tourism overview</h1><p>Read only summaries from the supplied tourism and destination datasets.</p></div><button className="ml-refresh" onClick={load} disabled={loading}><RefreshCw size={15}/>Refresh</button></div>
    {error && <div className="ml-error" role="alert">{error} <button onClick={load}>Retry</button></div>}
    {loading && <p className="ml-empty" role="status">Loading verified tourism data…</p>}
    {!loading && !error && <>
      <div className="stats-grid">
        <StatCard title="Destination profiles" value={profiles.length.toLocaleString()} change="Source destination attributes" />
        <StatCard title="Catalog concepts matched" value={coverage ? `${coverage.matched_unique_catalog_destinations}/${coverage.catalog_unique_destinations}` : "Unavailable"} change="Exact keys plus documented aliases" />
        <StatCard title="State/month records" value={overview?.coverage.records.toLocaleString() ?? "Unavailable"} change={`${overview?.coverage.states ?? 0} states · year unavailable`} />
        <StatCard title="Observed ratings" value={experience?.observations.toLocaleString() ?? "Unavailable"} change={experience ? `Mean ${experience.mean_rating} / 5 · observed` : "No rating summary available"} />
      </div>
      <AnalyticsSection overview={overview} profiles={profiles} />
      <DestinationTable profiles={profiles} />
      {overview?.limitation && <p className="dashboard-data-note"><CalendarDays size={15}/>{overview.limitation}</p>}
    </>}
  </>;
}

function Portal({ user, signOut }) {
  const [currentPage, setCurrentPage] = useState("dashboard");
  const [selectedDestination, setSelectedDestination] = useState(null);
  const handlePageChange = (page) => { setCurrentPage(page); setSelectedDestination(null); };
  const handleDestinationSelect = (destination) => { setSelectedDestination(destination); setCurrentPage("destination-details"); };
  const handleBackToDestinations = () => { setSelectedDestination(null); setCurrentPage("destinations"); };
  return <div className="dashboard" style={{ display: "flex", minHeight: "100vh", background: "linear-gradient(135deg, #f0f4f3 0%, #e1e8e5 100%)" }}>
    <Sidebar currentPage={currentPage} setCurrentPage={handlePageChange}/>
    <main className="main-content" style={{ flex: 1, display: "flex", flexDirection: "column" }}>
      <Topbar user={user} onLogout={signOut}/>
      <div className="content" style={{ padding: "24px", flex: 1 }}>
        {currentPage === "dashboard" && <DashboardHome/>}
        {currentPage === "destinations" && <Destinations onSelectDestination={handleDestinationSelect}/>}
        {currentPage === "destination-details" && selectedDestination && <DestinationDetails destination={selectedDestination} onBack={handleBackToDestinations}/>}
        {currentPage === "crowd" && <CrowdMonitoring/>}
        {currentPage === "hotels" && <Hotels/>}
        {currentPage === "transport" && <Transport/>}
        {currentPage === "analytics" && <Analytics/>}
        {currentPage === "settings" && <Settings user={user}/>}
      </div>
    </main>
  </div>;
}

export default function App() {
  return <AdminGate>{session => <Portal {...session}/>}</AdminGate>;
}
