import { createContext, useContext, useEffect, useState } from 'react'
import { BrowserRouter, Link, NavLink, Navigate, Route, Routes, useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { CalendarDays, ChevronRight, Compass, Heart, Hotel, MapPin, Menu, Plane, Search, Sparkles, Star, Soup, X, Trash2, Edit3, Plus, GripVertical } from 'lucide-react'
import { AuthProvider, useAuth } from './context/AuthContext'
import * as authService from './services/authService.js'
import { DESTINATION_IMAGE_FALLBACK, destinationImagePath, estimatedTemperatureBand } from './utils/destinationImages.js'
import { cityMapSearchUrl } from './utils/mapLinks.js'
import './index.css'

const nav = [
  { to: '/dashboard', label: 'Dashboard', icon: Compass },
  { to: '/explore', label: 'Explore', icon: Search },
  { to: '/discover', label: 'AI recommendations', icon: Sparkles },
  { to: '/plan-trip', label: 'Plan a trip', icon: Sparkles },
  { to: '/my-trips', label: 'My trips', icon: CalendarDays },
  { to: '/saved-places', label: 'Saved places', icon: Heart },
  { to: '/hotels', label: 'Hotels', icon: Hotel },
  { to: '/transport', label: 'Transport', icon: Plane },
  { to: '/restaurants', label: 'Restaurants', icon: Soup },
  { to: '/map', label: 'Map', icon: MapPin }
]

const governmentAppUrl = (import.meta.env.VITE_GOVERNMENT_APP_URL || 'http://localhost:5174').replace(/\/$/, '')
const apiBase = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:5000/api'
let destinationManifestPromise

function DestinationPhoto({ title, className, children }) {
  const [image, setImage] = useState(DESTINATION_IMAGE_FALLBACK)
  useEffect(() => {
    let active = true
    if (!destinationManifestPromise) destinationManifestPromise = fetch('/images/destination-manifest.json').then(response => response.ok ? response.json() : {}).catch(() => ({}))
    destinationManifestPromise.then(manifest => { if (active) setImage(destinationImagePath(title, manifest)) })
    return () => { active = false }
  }, [title])
  return <div className={`destination-photo-frame ${className || ''}`}>
    <img className="destination-photo-image" src={image} loading="lazy" alt={`${title} destination`} onError={event => { if (event.currentTarget.src.endsWith(DESTINATION_IMAGE_FALLBACK)) return; setImage(DESTINATION_IMAGE_FALLBACK) }} />
    {children}
  </div>
}

function useDestinationCatalog() {
  const [items, setItems] = useState([])
  const [coverage, setCoverage] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const reload = async () => {
    setLoading(true); setError('')
    try {
      const response = await fetch(`${apiBase}/catalog/destinations`)
      const body = await response.json()
      if (!response.ok) throw new Error(body.error || 'Destination catalog is unavailable.')
      setItems(body.data.items || []); setCoverage(body.data.coverage || null)
    } catch (err) { setError(err.message || 'Could not connect to the destination catalog.') }
    finally { setLoading(false) }
  }
  useEffect(() => { reload() }, [])
  return { items, coverage, loading, error, reload }
}

const SavedContext = createContext(null)
function SavedProvider({ children }) {
  const [saved, setSaved] = useState(() => {
    try { return JSON.parse(localStorage.getItem('tourisense-saved') || '[]') } catch { return [] }
  })
  useEffect(() => localStorage.setItem('tourisense-saved', JSON.stringify(saved)), [saved])
  const toggleSaved = item => setSaved(items => items.some(savedItem => savedItem.id === item.id) ? items.filter(savedItem => savedItem.id !== item.id) : [...items, item])
  return <SavedContext.Provider value={{ saved, toggleSaved }}>{children}</SavedContext.Provider>
}

// Global state for Saved Trips & Itineraries
const SavedTripsContext = createContext(null)
function SavedTripsProvider({ children }) {
  const [savedTrips, setSavedTrips] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem('tourisense-saved-trips') || '[]').filter(trip => trip.id !== 'demo-trip')
    } catch {
      return []
    }
  })

  useEffect(() => {
    localStorage.setItem('tourisense-saved-trips', JSON.stringify(savedTrips))
  }, [savedTrips])

  const saveTrip = (tripToSave) => {
    // If no ID exists or it's just 'demo-trip', generate a permanent unique ID
    const isTempId = !tripToSave.id || tripToSave.id === 'demo-trip'
    const tripId = isTempId ? `trip_${Date.now()}` : tripToSave.id
    
    const enrichedTrip = {
      ...tripToSave,
      id: tripId,
      destinationName: tripToSave.destinationName || tripToSave.destination || 'Trip',
      dates: tripToSave.dates || '',
      travelers: tripToSave.travelers || 1,
      budget: tripToSave.budget || ''
    }

    setSavedTrips(prev => {
      const idx = prev.findIndex(t => t.id === tripId)
      if (idx >= 0) {
        // Overwrite the existing trip instead of creating duplicates
        const updated = [...prev]
        updated[idx] = enrichedTrip
        return updated
      }
      return [enrichedTrip, ...prev]
    })
    return enrichedTrip // Return it so the itinerary page updates its local state with the new ID
  }

  const deleteTrip = (id) => {
    setSavedTrips(prev => prev.filter(t => t.id !== id))
  }

  const addActivityToTrip = (tripId, dayNumber, activity) => {
    setSavedTrips(prev => prev.map(t => {
      if (t.id === tripId) {
        const days = t.days ? [...t.days] : []
        const targetDayIdx = days.findIndex(d => d.day === Number(dayNumber))
        if (targetDayIdx >= 0) {
          days[targetDayIdx] = {
            ...days[targetDayIdx],
            activities: [...(days[targetDayIdx].activities || []), activity]
          }
        } else if (days.length > 0) {
          days[0] = {
            ...days[0],
            activities: [...(days[0].activities || []), activity]
          }
        }
        return { ...t, days }
      }
      return t
    }))
  }

  return (
    <SavedTripsContext.Provider value={{ savedTrips, saveTrip, deleteTrip, addActivityToTrip, setSavedTrips }}>
      {children}
    </SavedTripsContext.Provider>
  )
}
function useSavedTrips() { return useContext(SavedTripsContext) }

function Protected({ children }) { const { user, loading } = useAuth(); if (loading) return null; return user ? children : <Navigate to="/login" replace /> }
function AdminProtected({ children }) { const { user, loading } = useAuth(); if (loading) return null; return user?.role === 'admin' ? children : <Navigate to={user ? '/dashboard' : '/login'} replace /> }
function GovernmentRedirect() { const { user } = useAuth(); useEffect(() => { if (user?.role === 'admin') window.location.replace(authService.buildGovernmentHandoffUrl(governmentAppUrl, authService.getAccessToken())) }, [user]); return null }

function Header({ onMenu }) {
  const { user, logout } = useAuth()
  return (
    <header className="topbar">
      <button className="icon-btn mobile" onClick={onMenu} aria-label="Open navigation"><Menu /></button>
      <Link className="brand" to={user ? '/dashboard' : '/'}><span>T</span>TouriSense</Link>
      <nav className="toplinks">
        <NavLink to="/explore" className={({ isActive }) => isActive ? 'active' : ''}>Explore</NavLink>
        <NavLink to="/plan-trip" className={({ isActive }) => isActive ? 'active' : ''}>Plan a trip</NavLink>
      </nav>
      {user ? (
        <div className="profile-menu">
          <span className="avatar">{user.name[0]}</span>
          <span>{user.name}</span>
          <button onClick={logout}>Log out</button>
        </div>
      ) : (
        <div className="auth-links">
          <Link to="/login">Sign in</Link>
          <Link className="btn small" to="/register">Get started</Link>
        </div>
      )}
    </header>
  )
}

function Layout({ children }) {
  const [open, setOpen] = useState(false)
  return (
    <>
      <Header onMenu={() => setOpen(true)} />
      <div className="shell">
        <aside className={open ? 'sidebar open' : 'sidebar'}>
          <button className="icon-btn close mobile" onClick={() => setOpen(false)} aria-label="Close navigation"><X /></button>
          <p className="eyebrow">YOUR TRAVEL SPACE</p>
          {nav.map(({ to, label, icon: Icon }) => (
            <NavLink key={to} to={to} onClick={() => setOpen(false)}>
              <Icon size={18} />{label}
            </NavLink>
          ))}
          <div className="side-help">
            <Sparkles size={20} />
            <b>Ready to go?</b>
            <p>Turn your travel ideas into a thoughtful plan.</p>
            <Link to="/plan-trip">Start planning <ChevronRight size={16} /></Link>
          </div>
        </aside>
        <main>{children}</main>
      </div>
    </>
  )
}

function DestinationCard({ item }) {
  const { saved, toggleSaved } = useSaved()
  return (
    <article className="destination-card">
      <DestinationPhoto title={item.name} className="card-image">
        <button className="heart" onClick={() => toggleSaved(item)} aria-label="Save place">
          <Heart fill={saved.some(x => x.id === item.id) ? 'currentColor' : 'none'} />
        </button>
        <span>{item.category}</span>
      </DestinationPhoto>
      <div className="card-body">
        <div className="card-title">
          <div>
            <h3>{item.name}</h3>
            <p><MapPin size={14} />{item.location}</p>
          </div>
          <b>{item.rating != null ? <><Star size={15} fill="currentColor" /> {item.rating} <small>observed</small></> : <span>Rating unavailable</span>}</b>
        </div>
        <p className="muted">{item.description || [item.category, item.region && `${item.region} India`, item.nearest_major_city && `Near ${item.nearest_major_city}`].filter(Boolean).join(' · ') || 'No additional destination description is available.'}</p>
        <div className="card-foot">
          <span>{item.bestTime || 'Best time unknown'}</span>
          <Link to={`/destination/${encodeURIComponent(item.id)}`}>Explore <ChevronRight size={16} /></Link>
        </div>
      </div>
    </article>
  )
}

function useSaved() { return useContext(SavedContext) }

function Landing() {
  const navigate = useNavigate()
  const [query, setQuery] = useState('')
  const { items, loading, error, reload } = useDestinationCatalog()
  const search = e => {
    e.preventDefault()
    const found = items.find(item => (item.name + item.location + item.state).toLowerCase().includes(query.trim().toLowerCase()))
    navigate(found ? `/destination/${found.id}` : '/explore')
  }
  return (
    <>
      <Header />
      <section className="hero">
        <div>
          <p className="eyebrow light">TRAVEL, MADE PERSONAL</p>
          <h1>Discover.<br />Plan. <i>Explore.</i></h1>
          <p className="hero-copy">Your considered travel companion for discovering remarkable places and creating trips that feel entirely your own.</p>
          <div className="hero-actions">
            <Link className="btn" to="/plan-trip">Plan my trip <ChevronRight size={18} /></Link>
            <Link className="btn ghost" to="/explore">Explore destinations</Link>
          </div>
        </div>
        <form className="hero-search" onSubmit={search}>
          <Search />
          <input value={query} onChange={e => setQuery(e.target.value)} aria-label="Search a destination" placeholder="Where would you like to go?" />
          <button type="submit" aria-label="Search"><ChevronRight /></button>
        </form>
        <p className="hero-caption">Destination facts are sourced from TouriSense’s catalog.</p>
      </section>
      <section className="landing-section">
        <div className="section-head">
          <div><p className="eyebrow">DESTINATION PROFILES</p><h2>Places worth the journey.</h2></div>
          <Link to="/explore">View all destinations <ChevronRight size={16} /></Link>
        </div>
        {loading && <p role="status">Loading destinations…</p>}{error && <p className="error" role="alert">{error} <button onClick={reload}>Retry</button></p>}{!loading && !error && items.length === 0 && <p>No destination profiles are available.</p>}
        {!loading && !error && <div className="card-grid">{items.slice(0, 3).map(x => <DestinationCard key={x.id} item={x} />)}</div>}
      </section>
      <Footer />
    </>
  )
}

function Dashboard() {
  const { user } = useAuth()
  const { items, loading, error, reload } = useDestinationCatalog()
  return (
    <Layout>
      <section className="page">
        <p className="eyebrow">YOUR TRAVEL SPACE</p>
        <h1 className="page-title">Welcome back, {user.name.split(' ')[0]} <span>✦</span></h1>
        <div className="planner">
          <div><p className="eyebrow">TRIP PLANNER</p><h2>Choose from the destination profiles.</h2></div>
          <div className="planner-fields"><Link className="btn" to="/plan-trip">Start planning <ChevronRight size={17} /></Link><Link className="text-btn" to="/discover">Get preference based recommendations</Link></div>
        </div>
        <div className="section-head">
          <div><p className="eyebrow">SOURCE DATA</p><h2>Destination profiles</h2></div>
          <Link to="/explore">Explore all <ChevronRight size={16} /></Link>
        </div>
        {loading && <p role="status">Loading destination profiles…</p>}{error && <p className="error" role="alert">{error} <button onClick={reload}>Retry</button></p>}{!loading && !error && items.length === 0 && <p>No destination profiles are available.</p>}
        {!loading && !error && <div className="card-grid">{items.slice(0, 3).map(x => <DestinationCard key={x.id} item={x} />)}</div>}
      </section>
    </Layout>
  )
}

function Explore() {
  const [query, setQuery] = useState('')
  const [category, setCategory] = useState('')
  const { items, loading, error, reload } = useDestinationCatalog()
  const categories = [...new Set(items.flatMap(x => (x.category || '').split(';').map(y => y.trim()).filter(Boolean)))].sort()
  const found = items.filter(x => (x.name + x.location + x.state + x.category).toLowerCase().includes(query.toLowerCase()) && (!category || x.category?.toLowerCase().includes(category.toLowerCase())))
  return (
    <Layout>
      <section className="page">
        <p className="eyebrow">DISCOVER INDIA</p>
        <h1 className="page-title">Find a place that moves you.</h1>
        <div className="explorebar">
          <Search />
          <input value={query} onChange={e => setQuery(e.target.value)} placeholder="Where would you like to go?" />
          <button type="button" onClick={() => setQuery(query.trim())}>Search</button>
        </div>
        <div className="filters">
          <button className={!category ? 'active' : ''} onClick={() => setCategory('')}>All places</button>
          {categories.map(x => <button className={category === x ? 'active' : ''} key={x} onClick={() => setCategory(x)}>{x}</button>)}
        </div>
        {loading && <p role="status">Loading destinations…</p>}{error && <p className="error" role="alert">{error} <button onClick={reload}>Retry</button></p>}
        {!loading && !error && <><p className="results">{found.length} destination profiles</p>{found.length ? <div className="card-grid">{found.map(x => <DestinationCard key={x.id} item={x} />)}</div> : <p>No destination profiles match this search.</p>}</>}
      </section>
    </Layout>
  )
}

function Discover() {
  const { saved, toggleSaved } = useSaved()
  const [rankMode, setRankMode] = useState('matched_results')
  const [relaxedCriteria, setRelaxedCriteria] = useState([])
  const [filters, setFilters] = useState({ budget: '', region: '', season: '', duration_days: '', interests: [], crowd: '' })
  const [results, setResults] = useState([])
  const [coverage, setCoverage] = useState(null)
  const [notice, setNotice] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [expanded, setExpanded] = useState(null)
  const interests = ['Nature', 'Adventure', 'History', 'Culture', 'Spiritual', 'Beach', 'Families', 'Solo']
  const load = async (event) => {
    event?.preventDefault()
    setBusy(true); setError('')
    try {
      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:5000/api'}/ml/recommendations`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...filters, budget: filters.budget ? Number(filters.budget) : null,
          duration_days: filters.duration_days ? Number(filters.duration_days) : null })
      })
      const body = await response.json()
      if (!response.ok || body.status !== 'ok') throw new Error(body.error || 'Recommendations could not be loaded.')
      setResults(body.data.recommendations); setCoverage(body.data.coverage); setNotice(body.data.notice); setRankMode(body.data.mode); setRelaxedCriteria(body.data.relaxed_criteria || [])
    } catch (err) { setError(err.message || 'Could not connect to the recommendation service.') }
    finally { setBusy(false) }
  }
  useEffect(() => { load() }, [])
  const update = (key, value) => setFilters(current => ({ ...current, [key]: value }))
  return <Layout><section className="page">
    <p className="eyebrow">A MORE THOUGHTFUL SHORTLIST</p><h1 className="page-title">Discover destinations for your kind of trip.</h1>
    <p className="intro">Choose what matters to you. Recommendations match available destination attributes and explain each fit.</p>
    <form className="discover-filters" onSubmit={load}>
      <label>Budget per person (₹)<input type="number" min="0" value={filters.budget} onChange={e => update('budget', e.target.value)} placeholder="Any budget" /></label>
      <label>Region<select value={filters.region} onChange={e => update('region', e.target.value)}><option value="">Any region</option>{['North','South','East','West','Central','Northeast','Island'].map(x=><option key={x}>{x}</option>)}</select></label>
      <label>Travel season<select value={filters.season} onChange={e => update('season', e.target.value)}><option value="">Any season</option>{['All-year','Winter','Summer','Monsoon'].map(x=><option key={x}>{x}</option>)}</select></label>
      <label>Trip length (days)<input type="number" min="1" max="60" value={filters.duration_days} onChange={e => update('duration_days', e.target.value)} placeholder="Any duration" /></label>
      <label>Crowd preference<select value={filters.crowd} onChange={e => update('crowd', e.target.value)}><option value="">Any crowd level</option>{['Low','Medium','High'].map(x=><option key={x}>{x}</option>)}</select></label>
      <fieldset><legend>Interests</legend><div className="discover-tags">{interests.map(x=><label key={x}><input type="checkbox" checked={filters.interests.includes(x)} onChange={e => update('interests', e.target.checked ? [...filters.interests,x] : filters.interests.filter(i=>i!==x))}/>{x}</label>)}</div></fieldset>
      <button className="btn" type="submit" disabled={busy}>{busy ? 'Finding matches…' : 'Show recommendations'} <Sparkles size={16}/></button>
    </form>
    {error && <p className="discover-message error" role="alert">{error} <button onClick={load}>Try again</button></p>}
    {coverage && <p className="discover-note">{notice} Exact and documented alias matching covers {coverage.matched_unique_catalog_destinations} of {coverage.catalog_unique_destinations} unique catalog concepts ({coverage.matched_catalog_rows} catalog rows). The wider metadata source contains {coverage.metadata_unique_destinations} profiles.</p>}
    {rankMode === 'relaxed_alternatives' && <p className="discover-note" role="status">No destination met every selected preference. Showing ranked alternatives; relaxed criteria: {relaxedCriteria.join(', ') || 'none'}. Each alternative lists its mismatches.</p>}
    {busy && !coverage && <p className="discover-message">Loading destination matches…</p>}
    {!busy && !error && coverage && results.length === 0 && <div className="empty"><Compass/><h2>No destinations match these filters.</h2><p>Try broadening your preferences.</p></div>}
    <div className="ml-destination-grid">{results.map(item => {
      const image = null
      return <article className="ml-destination-card" key={item.id}>
        <DestinationPhoto title={item.name} className="ml-card-image" />
        <div className="ml-card-body"><div className="ml-card-kicker">{item.region || 'India'}{item.state ? ` · ${item.state}` : ''}</div><h2>{item.name}</h2>
          <div className="ml-meta">{item.category && <span>{item.category}</span>}{item.season && <span>Best: {item.season}</span>}{item.budget_inr != null && <span>₹{item.budget_inr.toLocaleString('en-IN')} / person</span>}{item.duration_days != null && <span>{item.duration_days} days typical</span>}{item.observed_rating != null && <span>Observed rating {item.observed_rating} / 5 · {item.rating_observations} visits</span>}</div>
          <button className="text-btn" onClick={() => toggleSaved({ id: `ml-${item.id}`, name: item.name, location: item.state ? `${item.state}, India` : 'India', category: item.category, image, bestTime: item.best_time, region: item.region, budget: item.budget_inr, budget_inr: item.budget_inr, tagline: item.region ? `${item.region} India` : 'Recommended destination', description: item.reasons.join(' · ') })} aria-pressed={saved.some(x => x.id === `ml-${item.id}`)}>{saved.some(x => x.id === `ml-${item.id}`) ? 'Saved to places' : 'Save destination'}</button>
          <Link className="text-btn" to={`/plan-trip?destination=${encodeURIComponent(item.id)}`}>Start a trip plan <ChevronRight size={15}/></Link>
          {item.alternative_notice && <p className="ml-reasons">{item.alternative_notice} Preferences not met: {item.not_matched_criteria?.join(', ') || 'none known'}{item.unknown_criteria?.length ? `. Unknown: ${item.unknown_criteria.join(', ')}` : ''}</p>}
          <button className="text-btn" aria-expanded={expanded === item.id} onClick={() => setExpanded(expanded === item.id ? null : item.id)}>{expanded === item.id ? 'Hide details' : 'Why this match?'}</button>
          {expanded === item.id && <div className="ml-reasons"><strong>Recommendation reasons</strong><ul>{item.reasons.map((reason,i)=><li key={i}>{reason}</li>)}</ul><p>Popularity: {item.popularity == null ? 'Unknown' : `${item.popularity.toFixed(1)} / source scale`}. This is a source ranking field, not a probability or visitor rating.</p>{item.temperature_range_c && <p>Typical temperature range: {item.temperature_range_c} °C</p>}</div>}
        </div>
      </article>
    })}</div>
  </section></Layout>
}

function mapSearchUrl(label) {
  return cityMapSearchUrl(`${label}, India`)
}

function Destination() {
  const { id } = useParams()
  const { saved } = useSaved()
  const { items, loading, error, reload } = useDestinationCatalog()
  const decodedId = decodeURIComponent(id || '')
  const item = items.find(x => String(x.id) === decodedId) || saved.find(x => String(x.id) === decodedId)
  const [month, setMonth] = useState('')
  const [insights, setInsights] = useState(null)
  const [insightsLoading, setInsightsLoading] = useState(false)
  const [insightsError, setInsightsError] = useState('')
  const [transport, setTransport] = useState([])
  const [transportLoading, setTransportLoading] = useState(false)
  const [transportError, setTransportError] = useState('')
  const [estimates, setEstimates] = useState(null)
  const [estimateLoading, setEstimateLoading] = useState(false)
  const [estimateError, setEstimateError] = useState('')
  const [estimateRetry, setEstimateRetry] = useState(0)

  useEffect(() => {
    if (!decodedId) return
    let active = true
    const load = async () => {
      setInsightsLoading(true); setInsightsError('')
      try {
        const params = new URLSearchParams({ destination_id: decodedId })
        const response = await fetch(`${apiBase}/ml/destination-insights?${params}`)
        const body = await response.json()
        if (!response.ok) throw new Error(body.error || 'Destination details are unavailable.')
        if (active) setInsights(body.data)
      } catch (err) { if (active) setInsightsError(err.message || 'Could not load destination details.') }
      finally { if (active) setInsightsLoading(false) }
    }
    load()
    return () => { active = false }
  }, [decodedId])

  useEffect(() => {
    if (!decodedId || !month) { setEstimates(null); setEstimateError(''); return }
    let active = true
    const load = async () => {
      setEstimateLoading(true); setEstimateError(''); setEstimates(null)
      try {
        const params = new URLSearchParams({ destination_id: decodedId, month })
        const response = await fetch(`${apiBase}/ml/destination-estimates?${params}`)
        const body = await response.json()
        if (!response.ok) throw new Error(body.error || 'Monthly estimates are unavailable.')
        if (active) setEstimates(body.data)
      } catch (err) { if (active) setEstimateError(err.message || 'Monthly estimates are unavailable.') }
      finally { if (active) setEstimateLoading(false) }
    }
    load()
    return () => { active = false }
  }, [decodedId, month, estimateRetry])

  const directoryCity = insights?.directory?.city
  useEffect(() => {
    if (!directoryCity) return
    let active = true
    const load = async () => {
      setTransportLoading(true); setTransportError('')
      try {
        const params = new URLSearchParams({ location: directoryCity })
        const response = await fetch(`${apiBase}/catalog/transport?${params}`)
        const body = await response.json()
        if (!response.ok) throw new Error(body.error || 'Transport listings are unavailable.')
        if (active) setTransport(body.data.items || [])
      } catch (err) { if (active) setTransportError(err.message || 'Transport listings are unavailable.') }
      finally { if (active) setTransportLoading(false) }
    }
    load()
    return () => { active = false }
  }, [directoryCity])

  if (loading && !item) return <Layout><section className="page"><p role="status">Loading destination profile…</p></section></Layout>
  if (error && !item) return <Layout><section className="page"><p className="error" role="alert">{error} <button onClick={reload}>Retry</button></p></section></Layout>
  if (!item) return <Layout><section className="page"><h1>Destination unavailable</h1><p>This destination is not present in the current source catalog.</p><Link className="btn" to="/explore">Browse destination profiles</Link></section></Layout>

  const profile = insights?.destination || item
  const directory = insights?.directory
  return <Layout>
    <section className="detail">
      <DestinationPhoto title={profile.name} className="detail-hero">
        <div><p className="eyebrow light">{(profile.location || profile.state || 'India').toUpperCase()}</p><h1>{profile.name}</h1><p>{profile.category || 'Destination profile'}</p></div>
      </DestinationPhoto>
      <div className="detail-content">
        <div><p className="eyebrow">DESTINATION PROFILE</p><h2>Plan around the details available for {profile.name}.</h2>
          <p className="long-copy">{[profile.category, profile.region && `${profile.region} India`, profile.nearest_major_city && `Nearest major city: ${profile.nearest_major_city}`, profile.popular_with && `Often associated with: ${profile.popular_with}`].filter(Boolean).join(' · ') || 'No additional destination profile details are available.'}</p>
          {insightsError && <p className="error" role="alert">{insightsError}</p>}
          {insightsLoading && <p role="status">Loading month-specific profile…</p>}
          <div className="destination-month-row"><label htmlFor="destination-month">Travel month</label><select id="destination-month" value={month} onChange={e=>setMonth(e.target.value)}><option value="">Choose a month to see estimates</option>{Array.from({length:12},(_,index)=><option value={index+1} key={index}>{new Date(2024,index,1).toLocaleString('en',{month:'long'})}</option>)}</select>{estimates?.selected_month.within_best_months === true && <span className="month-fit">Within source best months</span>}{estimates?.selected_month.within_best_months === false && <span className="month-fit muted-fit">Outside source best months</span>}</div>
          {month && estimateLoading && <p role="status">Updating monthly temperature and crowd estimates…</p>}
          {month && estimateError && <p className="error" role="alert">{estimateError} <button onClick={()=>setEstimateRetry(value=>value+1)}>Retry</button></p>}
          {month && estimates && <div className="monthly-estimate-grid">
            <article><small>Estimated temperature range</small>{estimatedTemperatureBand(estimates.temperature) ? <strong>{estimatedTemperatureBand(estimates.temperature).join('–')} °C</strong> : <strong>Unavailable</strong>}</article>
            <article><small>Estimated seasonal crowd</small>{estimates.crowd.level ? <strong>{estimates.crowd.level}</strong> : <strong>Unavailable</strong>}</article>
          </div>}
          {insights && <>
            <div className="destination-facts-grid">
              <article><small>Best season / months</small><strong>{profile.best_season || 'Unknown'} · {profile.months_best_for || 'Unknown'}</strong><span>Source reference</span></article>
              <article><small>Typical trip duration</small><strong>{profile.duration_days == null ? 'Unknown' : `${profile.duration_days} days`}</strong><span>Source reference</span></article>
              <article><small>Typical budget</small><strong>{profile.budget_inr == null ? 'Unknown' : `₹${Number(profile.budget_inr).toLocaleString('en-IN')}`}</strong><span>Per person · source estimate</span></article>
              <article><small>Visitor rating</small><strong>{profile.observed_rating == null ? 'Unavailable' : `${profile.observed_rating} / 5`}</strong><span>{profile.rating_observations ? `${profile.rating_observations} joined observed ratings` : 'No joined observations'}</span></article>
            </div>
            <aside className="prediction-unavailable"><strong>Estimate note</strong><p>Monthly values are approximate model estimates, not observed weather or verified crowd counts. The tourism workbook has no year, so it does not support future forecasts. Hotel inventory is not live availability.</p></aside>
            {directory && <section className="city-data-section"><div className="city-section-head"><div><h3>Hotels in {directory.city}</h3><p>{directory.city_basis}</p></div><a className="text-btn" href={mapSearchUrl(directory.city)} target="_blank" rel="noreferrer">Open city map <MapPin size={15}/></a></div>
              {directory.hotels.count ? <div className="city-list-grid">{directory.hotels.items.map(hotel=><article className="city-list-card" key={hotel.id}><div className="city-list-heading"><h4>{hotel.name}</h4><span>{hotel.category || 'Category unknown'}</span></div><p>{hotel.address || 'Address unavailable'}</p><dl><div><dt>Rooms</dt><dd>{hotel.rooms ?? 'Unknown'}</dd></div><div><dt>Source dates</dt><dd>{hotel.start_date || 'Unknown'} – {hotel.expiry_date || 'Unknown'}</dd></div></dl><small>Directory record; current operating status and availability are not verified.</small><a href={mapSearchUrl(`${hotel.name}, ${hotel.address || ''}, ${hotel.city}`)} target="_blank" rel="noreferrer">Find this address on map <MapPin size={13}/></a></article>)}</div> : <p className="data-unavailable">No hotel directory records match {directory.city}.</p>}
            </section>}
            {directory && <section className="city-data-section"><div className="city-section-head"><div><h3>Food and places in {directory.food.city || directory.city}</h3><p>Source categories are retained as provided; “Tourist Spot” is not relabeled as lunch.</p></div></div>
              {directory.food.available ? <div className="food-groups">{directory.food.groups.map(group=><section key={group.category}><h4>{group.category}</h4>{group.places.length ? <ul>{group.places.map(place=><li key={place.source_column}>{place.name}<a href={mapSearchUrl(`${place.name}, ${directory.food.city}`)} target="_blank" rel="noreferrer">Map <MapPin size={12}/></a></li>)}</ul> : <p>No places in this category.</p>}</section>)}</div> : <p className="data-unavailable">No food/places row is available for {directory.city}; no venues are substituted.</p>}
              <small>{directory.food.limitation}</small>
            </section>}
            <section className="city-data-section"><div className="city-section-head"><div><h3>Transport options</h3><p>Operational listings from the existing TouriSense transport catalog.</p></div></div>
              {transportLoading && <p role="status">Loading transport options…</p>}{transportError && <p className="data-unavailable" role="alert">{transportError}</p>}
              {!transportLoading && !transportError && (transport.length ? <div className="transport-options">{transport.map(option=><article key={option.id}><strong>{option.name}</strong><span>{option.type || 'Type unknown'}</span><p>{option.route || 'Route unavailable'} · {option.duration || 'Duration unknown'}</p><small>{option.cost == null ? 'Fare unavailable' : `From ₹${Number(option.cost).toLocaleString('en-IN')}`}</small></article>)}</div> : <p className="data-unavailable">No operational transport records match {directory?.city || 'this destination'}.</p>)}
            </section>
          </>}
        </div>
        <aside className="trip-box"><p><strong>Source</strong>Destination profile data</p><p><strong>Best time</strong>{profile.months_best_for || profile.best_season || 'Not available'}</p><p><strong>Budget per person</strong>{profile.budget_inr != null ? `₹${Number(profile.budget_inr).toLocaleString('en-IN')} (source estimate)` : 'Not available'}</p><Link className="btn" to={`/plan-trip?destination=${encodeURIComponent(profile.id)}`}>Start a trip plan <ChevronRight size={17}/></Link></aside>
      </div>
    </section>
  </Layout>
}

function PlanTrip() {
  const navg = useNavigate()
  const [searchParams] = useSearchParams()
  const { items, loading, error, reload } = useDestinationCatalog()
  const [step, setStep] = useState(1)
  const [form, setForm] = useState({ destination: searchParams.get('destination') || '', days: 3, travelers: 1, adults: 1, children: 0, rooms: 1, hotel_rating: 4, food_preference: 'standard', budget: '', interests: [], transport_mode: 'flight', stay: 'Standard', startDate: '' })
  const [costEstimate, setCostEstimate] = useState(null)
  const [costError, setCostError] = useState('')
  const [costBusy, setCostBusy] = useState(false)
  const update = (key, value) => setForm(current => {
    if (key === 'adults') return { ...current, adults: Number(value), travelers: Number(value) + Number(current.children) }
    if (key === 'children') return { ...current, children: Number(value), travelers: Number(current.adults) + Number(value) }
    return { ...current, [key]: value }
  })
  const generate = () => {
    const selected = items.find(item => item.id === form.destination)
    if (!selected) return
    const tripId = `draft-${Date.now()}`
    const dateLabel = form.startDate || 'Flexible dates'
    const days = Array.from({ length: Math.max(1, Number(form.days) || 1) }, (_, index) => ({ day: index + 1, title: `Day ${index + 1}`, date: form.startDate || '', activities: [] }))
    const draft = { ...form, id: tripId, destinationName: selected.name, destinationState: selected.state, destinationProfile: selected, dates: dateLabel, days }
    localStorage.setItem('wanderly-draft', JSON.stringify(draft))
    navg(`/itinerary/${tripId}`)
  }
  const estimateCost = async () => {
    setCostBusy(true); setCostError(''); setCostEstimate(null)
    try {
      const response = await fetch(`${apiBase}/ml/trip-estimate`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({
        destination: chosen?.id || chosen?.name, transport_mode: form.transport_mode,
        travellers: Number(form.travelers), duration_days: Number(form.days), food_preference: form.food_preference,
        rooms: Number(form.rooms)
      }) })
      const body = await response.json()
      if (!response.ok) throw new Error(body.error || 'The trip estimate is unavailable.')
      setCostEstimate(body.data)
    } catch (err) { setCostError(err.message || 'Cost estimate unavailable.') }
    finally { setCostBusy(false) }
  }
  useEffect(() => { if (items.length && !items.some(item => item.id === form.destination)) update('destination', searchParams.get('destination') || items[0].id) }, [items])
  const chosen = items.find(item => item.id === form.destination)
  return (
    <Layout>
      <section className="page plan">
        <p className="eyebrow">CREATE YOUR JOURNEY</p>
        <h1 className="page-title">Let’s plan something memorable.</h1>
        <div className="stepper">
          {['Destination', 'Trip details', 'Your style', 'Getting there', 'Stay'].map((x, i) => (
            <span className={i + 1 <= step ? 'done' : ''} key={x}><b>{i + 1}</b>{x}</span>
          ))}
        </div>
        <div className="plan-card">
          {step === 1 && (
            <>
              <h2>Where do you want to go?</h2>
              <p>Start with a destination. You can change the details later.</p>
              {loading && <p role="status">Loading destination profiles…</p>}{error && <p className="error" role="alert">{error} <button onClick={reload}>Retry</button></p>}
              {!loading && !error && (items.length ? <div className="choice-grid">{items.map(x => <button className={form.destination === x.id ? 'selected' : ''} onClick={() => update('destination', x.id)} key={x.id}>{x.name}<small>{x.location || x.state} · {x.category || 'Category unknown'}</small></button>)}</div> : <p>No destinations are available for planning.</p>)}
            </>
          )}
          {step === 2 && (
            <>
              <h2>Tell us about your trip.</h2>
              <div className="form-grid">
                <label>Start date<input type="date" value={form.startDate} onChange={e => update('startDate', e.target.value)} /></label>
                <label>Number of days<input type="number" value={form.days} min="1" max="60" onChange={e => update('days', Number(e.target.value))} /></label>
                <label>Adults<input type="number" value={form.adults} min="1" max="15" onChange={e => update('adults', e.target.value)} /></label>
                <label>Children<input type="number" value={form.children} min="0" max="7" onChange={e => update('children', e.target.value)} /></label>
                <p className="form-note">Total travellers: {form.travelers}</p>
                <label>Trip budget (optional, ₹)<input type="number" min="0" value={form.budget} onChange={e => update('budget', e.target.value)} placeholder={chosen?.budget != null ? `Source estimate: ₹${chosen.budget} per person` : 'Not provided'} /></label>
              </div>
            </>
          )}
          {step === 3 && (
            <>
              <h2>What kind of traveller are you?</h2>
              <div className="tags selectable">
              {['Nature', 'Adventure', 'History', 'Culture', 'Spiritual', 'Wildlife', 'Beach', 'Families', 'Solo'].map(x => (
                  <button className={form.interests.includes(x) ? 'selected' : ''} onClick={() => update('interests', form.interests.includes(x) ? form.interests.filter(i => i !== x) : [...form.interests, x])} key={x}>{x}</button>
                ))}
              </div>
            </>
          )}
          {step === 4 && (
            <>
              <h2>How would you prefer to get around?</h2>
              <div className="choice-grid">
                  {['bus', 'train', 'flight'].map(x => (
                    <button className={form.transport_mode === x ? 'selected' : ''} onClick={() => update('transport_mode', x)} key={x}>{x[0].toUpperCase()+x.slice(1)}</button>
                ))}
              </div>
            </>
          )}
          {step === 5 && (
            <>
              <h2>Review your stay details.</h2>
              <div className="form-grid">
                <label>Rooms<input type="number" min="1" max="8" value={form.rooms} onChange={e=>update('rooms',Number(e.target.value))}/></label>
                  <label>Food preference<select value={form.food_preference} onChange={e=>update('food_preference',e.target.value)}>{[['budget','Budget meals'],['vegetarian','Vegetarian meals'],['standard','Standard meals'],['premium','Premium meals']].map(([value,label])=><option value={value} key={value}>{label}</option>)}</select></label>
                  <label>Transport mode<select value={form.transport_mode} onChange={e=>update('transport_mode',e.target.value)}>{['bus','train','flight'].map(value=><option value={value} key={value}>{value[0].toUpperCase()+value.slice(1)}</option>)}</select></label>
              </div>
              <div className="source-cost-panel"><h3>Approximate trip budget</h3>
                <p>Planning estimate in INR for {chosen?.name || 'your destination'}. The transport allowance is round trip per traveller; hotel and meal prices are editable rule-based assumptions, not live quotes.</p>
                {costError && <p className="error" role="alert">{costError}</p>}
                {costEstimate && <div className="trip-estimate-result" role="status"><strong>₹{Number(costEstimate.total_inr).toLocaleString('en-IN')} estimated total</strong><b>₹{Number(costEstimate.per_person_inr).toLocaleString('en-IN')} per traveller</b><ul>{Object.entries(costEstimate.breakdown_inr).map(([key,value])=><li key={key}><span>{key.replaceAll('_',' ')}</span><span>₹{Number(value).toLocaleString('en-IN')}</span></li>)}</ul><small>{costEstimate.destination_tier} tier · {costEstimate.nights_charged} nights · {costEstimate.rooms_assumed} assumed rooms</small><p>{costEstimate.method}</p></div>}
                <button type="button" className="btn" onClick={estimateCost} disabled={costBusy || !chosen || Number(form.travelers)<1 || Number(form.days)<1}>{costBusy ? 'Estimating…' : 'Calculate approximate trip cost'}</button>
              </div>
            </>
          )}
          <div className="plan-actions">
            <button className="text-btn" disabled={step === 1} onClick={() => setStep(step - 1)}>Back</button>
            {step < 5 ? (
              <button className="btn" onClick={() => setStep(step + 1)}>Continue <ChevronRight size={17} /></button>
            ) : (
              <button className="btn" onClick={generate} disabled={!chosen}>Create itinerary draft <Sparkles size={17} /></button>
            )}
          </div>
        </div>
      </section>
    </Layout>
  )
}

// ITINERARY with Drag & Drop, Auto-Save, and Edits
function Itinerary() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { savedTrips, saveTrip } = useSavedTrips()
  
  const [saved, setSaved] = useState(false)
  const [isEditingTrip, setIsEditingTrip] = useState(false)
  const [draggedItem, setDraggedItem] = useState(null)

  const [trip, setTrip] = useState(() => {
    const match = savedTrips.find(t => t.id === id)
    if (match) { setSaved(true); return match }
    try {
      const draft = JSON.parse(localStorage.getItem('wanderly-draft') || 'null')
      if (draft && draft.id === id && draft.destinationName) return draft
    } catch { /* invalid local draft is treated as unavailable */ }
    return null
  })

  // Edit form state
  const [editForm, setEditForm] = useState({
    title: trip?.destinationName || '',
    travelers: trip?.travelers || 1,
    budget: trip?.budget || '',
    dates: trip?.dates || ''
  })

  // AUTO SAVE EFFECT: Only triggers if the trip has a permanent ID
  useEffect(() => {
    if (saved && trip?.id) {
      saveTrip(trip)
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [trip, saved])

  const move = (d, i, dir) => {
    setTrip(t => ({
      ...t,
      days: t.days.map((day, idx) => {
        if (idx !== d) return day
        const acts = [...day.activities]
        const target = i + dir
        if (target < 0 || target >= acts.length) return day
        const temp = acts[i]
        acts[i] = acts[target]
        acts[target] = temp
        return { ...day, activities: acts }
      })
    }))
  }

  // NATIVE DRAG AND DROP HANDLERS
  const handleDragStart = (e, d, i) => {
    e.dataTransfer.effectAllowed = 'move'
    setDraggedItem({ d, i })
  }

  const handleDrop = (e, targetD, targetI) => {
    e.preventDefault()
    e.stopPropagation()
    
    if (!draggedItem) return
    const { d: sourceD, i: sourceI } = draggedItem
    
    if (sourceD === targetD && sourceI === targetI) {
      setDraggedItem(null)
      return
    }

    setTrip(t => {
      const newDays = JSON.parse(JSON.stringify(t.days)) // deep copy
      const [movedItem] = newDays[sourceD].activities.splice(sourceI, 1)
      
      if (targetI === null) {
        // Dropped on the day container, append to the end
        newDays[targetD].activities.push(movedItem)
      } else {
        // Dropped on a specific activity, insert it there
        newDays[targetD].activities.splice(targetI, 0, movedItem)
      }
      return { ...t, days: newDays }
    })
    setDraggedItem(null)
  }

  const removeActivity = (d, i) => setTrip(t => ({
    ...t,
    days: t.days.map((day, idx) => idx === d ? { ...day, activities: day.activities.filter((_, j) => j !== i) } : day)
  }))

  const addNewDay = () => {
    setTrip(t => {
      const nextDayNum = t.days.length + 1
      return {
        ...t,
        days: [...t.days, { day: nextDayNum, title: `Day ${nextDayNum} — Open exploration`, date: `Day ${nextDayNum}`, activities: [] }]
      }
    })
  }

  const handleSaveTrip = () => {
    // Lock in the ID and save to Context
    const enrichedTrip = saveTrip(trip)
    // Update local state so future changes automatically save to this exact ID
    setTrip(enrichedTrip) 
    setSaved(true)
    alert('Trip saved in this browser. Edits will save automatically on this device.')
  }

  const handleSaveEdit = (e) => {
    e.preventDefault()
    setTrip(t => ({ ...t, ...editForm }))
    setIsEditingTrip(false)
  }

  if (!trip) return <Layout><section className="page empty"><Compass/><h1>No itinerary draft found.</h1><p>Choose a destination to create a trip plan.</p><Link className="btn" to="/plan-trip">Plan a trip</Link></section></Layout>
  const destObj = { name: trip.destinationName || 'your destination' }

  return (
    <Layout>
      <section className="page itinerary">
        <p className="eyebrow">YOUR PERSONALIZED ESCAPE</p>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '15px' }}>
          <h1 className="page-title" style={{ margin: 0 }}>My trip to {destObj.name}</h1>
          <button 
            onClick={() => setIsEditingTrip(true)} 
            className="btn ghost small"
            style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}
          >
            <Edit3 size={15} /> Edit trip details
          </button>
        </div>

        <div className="trip-meta" style={{ marginTop: '16px' }}>
          <span><CalendarDays size={16} /> {trip.dates || 'Dates not set'}</span>
          <span>{trip.days.length} days</span>
          <span>{trip.travelers || 1} travellers</span>
          <span>{trip.budget ? `Budget ₹${Number(trip.budget).toLocaleString('en-IN')}` : 'Budget not set'}</span>
          <button onClick={handleSaveTrip} className="btn small" disabled={saved}>{saved ? 'Saved on this device' : 'Save trip'}</button>
        </div>

        {/* EDIT TRIP MODAL */}
        {isEditingTrip && (
          <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', zIndex: 9999, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '20px' }}>
            <div style={{ background: '#fff', padding: '30px', borderRadius: '16px', maxWidth: '460px', width: '100%', boxShadow: '0 20px 40px rgba(0,0,0,0.2)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px' }}>
                <h2 style={{ margin: 0, fontSize: '1.4rem' }}>Edit Trip Preferences</h2>
                <button onClick={() => setIsEditingTrip(false)} style={{ background: 'none', border: 'none', cursor: 'pointer' }}><X size={20} /></button>
              </div>
              <form onSubmit={handleSaveEdit} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                <label style={{ display: 'flex', flexDirection: 'column', fontSize: '0.9rem', gap: '4px' }}>
                  Trip Dates
                  <input style={{ padding: '10px', borderRadius: '8px', border: '1px solid #ddd' }} value={editForm.dates} onChange={e => setEditForm({ ...editForm, dates: e.target.value })} />
                </label>
                <label style={{ display: 'flex', flexDirection: 'column', fontSize: '0.9rem', gap: '4px' }}>
                  Number of Travellers
                  <input type="number" min="1" style={{ padding: '10px', borderRadius: '8px', border: '1px solid #ddd' }} value={editForm.travelers} onChange={e => setEditForm({ ...editForm, travelers: e.target.value })} />
                </label>
                <label style={{ display: 'flex', flexDirection: 'column', fontSize: '0.9rem', gap: '4px' }}>
                  Budget Tier
                  <select style={{ padding: '10px', borderRadius: '8px', border: '1px solid #ddd' }} value={editForm.budget} onChange={e => setEditForm({ ...editForm, budget: e.target.value })}>
                    <option>Under ₹25,000</option>
                    <option>₹25,000 – ₹40,000</option>
                    <option>₹40,000+</option>
                  </select>
                </label>
                <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '10px' }}>
                  <button type="button" onClick={() => setIsEditingTrip(false)} className="text-btn">Cancel</button>
                  <button type="submit" className="btn small">Save Changes</button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* TIMELINE DAYS WITH DRAG AND DROP */}
        {trip.days.map((day, d) => (
          <section className="day" key={day.day}>
            <div className="day-label">
              <span>DAY {day.day}</span>
              <h2>{day.title}</h2>
              <p>{day.date}</p>
            </div>
            {/* The Timeline Container acts as a drop zone for an empty day or bottom of the list */}
            <div 
              className="timeline"
              onDragOver={(e) => { e.preventDefault(); e.dataTransfer.dropEffect = 'move' }}
              onDrop={(e) => handleDrop(e, d, null)}
              style={{ minHeight: '60px', paddingBottom: '20px' }}
            >
              {day.activities && day.activities.length > 0 ? (
                day.activities.map((a, i) => (
                  <article 
                    className="activity" 
                    key={`${a.name}-${i}`}
                    draggable
                    onDragStart={(e) => handleDragStart(e, d, i)}
                    onDragOver={(e) => { e.preventDefault(); e.stopPropagation(); e.dataTransfer.dropEffect = 'move' }}
                    onDrop={(e) => handleDrop(e, d, i)}
                    style={{ 
                      cursor: 'grab', 
                      opacity: draggedItem?.d === d && draggedItem?.i === i ? 0.3 : 1,
                      transition: 'opacity 0.2s'
                    }}
                  >
                    <time>{a.time || 'Time not set'}</time>
                    <div className="dot" />
                    <div>
                      <div style={{ display: 'flex', gap: '8px' }}>
                        <div style={{ marginTop: '2px', opacity: 0.3, cursor: 'grab' }}><GripVertical size={18} /></div>
                        <div style={{ flex: 1 }}>
                          <h3>{a.name}</h3>
                          <p>{a.description}</p>
                          <small>{a.duration || 'Duration not set'} · {a.cost || 'Cost unknown'}</small>
                          <div className="activity-actions" style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap', marginTop: '8px' }}>
                            <button disabled={i === 0} onClick={() => move(d, i, -1)}>Move up</button>
                            <button disabled={i === day.activities.length - 1} onClick={() => move(d, i, 1)}>Move down</button>
                            <button onClick={() => removeActivity(d, i)} style={{ color: '#c0392b' }}>Remove</button>
                            
                          </div>
                        </div>
                      </div>
                    </div>
                  </article>
                ))
              ) : (
                <p style={{ color: '#888', fontStyle: 'italic', padding: '12px 0' }}>Drag a place here, or add one below.</p>
              )}
            </div>
          </section>
        ))}

        <div style={{ display: 'flex', gap: '15px', marginTop: '30px' }}>
          <button className="add-activity" onClick={() => navigate('/explore')} style={{ flex: 1 }}>
            + Add a place to this trip
          </button>
          <button className="btn ghost" onClick={addNewDay} style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', padding: '0 24px' }}>
            <Plus size={16} /> Add another day
          </button>
        </div>
      </section>
    </Layout>
  )
}

function Listing({ kind, endpoint, icon: Icon }) {
  const { savedTrips, addActivityToTrip } = useSavedTrips()
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [query, setQuery] = useState('')
  const [selectedItem, setSelectedItem] = useState(null)
  const [targetTripId, setTargetTripId] = useState('')
  const [targetDay, setTargetDay] = useState(1)
  const [successMsg, setSuccessMsg] = useState('')

  const load = async () => {
    setLoading(true); setError('')
    try { const response = await fetch(`${apiBase}${endpoint}`); const body = await response.json(); if (!response.ok) throw new Error(body.error || `${kind} are unavailable.`); setItems(body.data.items || []) }
    catch (err) { setError(err.message || `${kind} are unavailable.`) }
    finally { setLoading(false) }
  }
  useEffect(() => { load() }, [endpoint])
  const filteredItems = items.filter(item => `${item.name} ${item.location} ${item.city} ${item.state} ${item.route} ${item.cuisine} ${item.type}`.toLowerCase().includes(query.toLowerCase()))

  const openAddModal = (item) => {
    setSelectedItem(item)
    if (savedTrips.length > 0) {
      setTargetTripId(savedTrips[0].id)
    }
  }

  const handleConfirmAdd = () => {
    if (!targetTripId) {
      alert('Please save or create a trip first!')
      return
    }
    const newActivity = {
      name: selectedItem.name,
      description: selectedItem.description || selectedItem.location || selectedItem.route || selectedItem.cuisine,
      duration: '1.5 hrs',
      cost: selectedItem.price_per_night ?? selectedItem.cost ?? selectedItem.price_tier ?? null,
      duration: selectedItem.duration || null,
      time: null
    }

    addActivityToTrip(targetTripId, targetDay, newActivity)
    setSuccessMsg(`Added "${selectedItem.name}" to your trip!`)
    setTimeout(() => {
      setSuccessMsg('')
      setSelectedItem(null)
    }, 1500)
  }

  const activeTrip = savedTrips.find(t => t.id === targetTripId) || savedTrips[0]

  return (
    <Layout>
      <section className="page">
        <p className="eyebrow">TRAVEL ESSENTIALS</p>
        <h1 className="page-title">{kind} for every kind of trip.</h1>
        <p className="intro">Records from the active TouriSense operational catalog.</p>

        {/* MODAL TO CHOOSE TRIP AND DAY */}
        {selectedItem && (
          <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', zIndex: 9999, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '20px' }}>
            <div style={{ background: '#fff', padding: '28px', borderRadius: '16px', maxWidth: '420px', width: '100%', boxShadow: '0 20px 40px rgba(0,0,0,0.2)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
                <h3 style={{ margin: 0 }}>Add to Itinerary</h3>
                <button onClick={() => setSelectedItem(null)} style={{ background: 'none', border: 'none', cursor: 'pointer' }}><X size={18} /></button>
              </div>
              <p style={{ margin: '0 0 16px', color: '#555' }}>
                Select which trip and day you would like to add <b>{selectedItem.name}</b> to:
              </p>

              {successMsg ? (
                <div style={{ background: '#e8f5e9', color: '#2e7d32', padding: '14px', borderRadius: '8px', textAlign: 'center', fontWeight: 'bold' }}>
                  ✓ {successMsg}
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                  <label style={{ display: 'flex', flexDirection: 'column', fontSize: '0.85rem', gap: '4px' }}>
                    Choose Trip
                    <select 
                      value={targetTripId} 
                      onChange={e => setTargetTripId(e.target.value)}
                      style={{ padding: '10px', borderRadius: '8px', border: '1px solid #ccc' }}
                    >
                      {savedTrips.map(t => (
                        <option key={t.id} value={t.id}>{t.destinationName || 'Trip'} ({t.dates || 'Active'})</option>
                      ))}
                    </select>
                  </label>

                  <label style={{ display: 'flex', flexDirection: 'column', fontSize: '0.85rem', gap: '4px' }}>
                    Choose Day
                    <select 
                      value={targetDay} 
                      onChange={e => setTargetDay(Number(e.target.value))}
                      style={{ padding: '10px', borderRadius: '8px', border: '1px solid #ccc' }}
                    >
                      {(activeTrip?.days || []).map((d, i) => (
                        <option key={d.day || i + 1} value={d.day || i + 1}>
                          Day {d.day || i + 1} {d.title ? `— ${d.title}` : ''}
                        </option>
                      ))}
                    </select>
                  </label>

                  <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '10px' }}>
                    <button onClick={() => setSelectedItem(null)} className="text-btn">Cancel</button>
                    <button onClick={handleConfirmAdd} className="btn small" disabled={!activeTrip?.days?.length}>Confirm & Add</button>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        <label className="catalog-search">Search catalog<input value={query} onChange={e=>setQuery(e.target.value)} placeholder={`Search ${kind.toLowerCase()}`} /></label>
        {loading && <p role="status">Loading {kind.toLowerCase()} catalog…</p>}{error && <p className="error" role="alert">{error} <button onClick={load}>Retry</button></p>}
        {!loading && !error && filteredItems.length === 0 && <p className="empty">No active {kind.toLowerCase()} records match this search.</p>}
        {!loading && !error && <div className="listing-grid">
          {filteredItems.map(x => (
            <article className="simple-card" key={x.id}>
              {x.image && <div className="simple-image" style={{ backgroundImage: `url(${x.image})` }} />}
              <Icon />
              <h3>{x.name}</h3>
              <p>{[x.location || x.route, x.city, x.state, x.description].filter(Boolean).join(' · ') || 'No location details available.'}</p>
              <b>{x.price_per_night != null ? `₹${x.price_per_night.toLocaleString('en-IN')} / night` : x.cost != null ? `From ₹${x.cost.toLocaleString('en-IN')}` : x.price_tier || x.cuisine || x.type || 'Price/details unavailable'}</b>
              {savedTrips.length ? <button className="text-btn" onClick={() => openAddModal(x)}>Add to trip <ChevronRight size={15} /></button> : <Link className="text-btn" to="/plan-trip">Plan a trip to add this <ChevronRight size={15}/></Link>}
            </article>
          ))}
        </div>}
      </section>
    </Layout>
  )
}

function HotelDirectoryPage() {
  const [result, setResult] = useState(null)
  const [filters, setFilters] = useState({ q: '', city: '', state: '', category: '' })
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  useEffect(() => {
    let active = true
    const timer = setTimeout(async () => {
      setLoading(true); setError('')
      try {
        const params = new URLSearchParams({ ...filters, page: String(page), page_size: '50' })
        const response = await fetch(`${apiBase}/catalog/hotel-directory?${params}`)
        const body = await response.json()
        if (!response.ok) throw new Error(body.error || 'Hotel directory is unavailable.')
        if (active) setResult(body.data)
      } catch (err) { if (active) setError(err.message || 'Hotel directory is unavailable.') }
      finally { if (active) setLoading(false) }
    }, 180)
    return () => { active = false; clearTimeout(timer) }
  }, [filters, page])
  const change = (key, value) => { setPage(1); setFilters(current => ({ ...current, [key]: value })) }
  const facets = result?.facets || { cities: [], states: [], categories: [] }
  return <Layout><section className="page hotel-directory-page">
    <p className="eyebrow">SOURCE HOTEL DIRECTORY</p><h1 className="page-title">Find a listed stay.</h1>
    <p className="intro">All records from <code>Backend/Data/hotels.csv</code>. This directory does not show current room availability.</p>
    <div className="hotel-directory-filters">
      <label>Search hotel name<input value={filters.q} onChange={event=>change('q',event.target.value)} placeholder="Search hotel, address, city or state" /></label>
      <label>City<select value={filters.city} onChange={event=>change('city',event.target.value)}><option value="">All cities</option>{facets.cities.map(city=><option key={city}>{city}</option>)}</select></label>
      <label>State<select value={filters.state} onChange={event=>change('state',event.target.value)}><option value="">All states</option>{facets.states.map(state=><option key={state}>{state}</option>)}</select></label>
      <label>Category<select value={filters.category} onChange={event=>change('category',event.target.value)}><option value="">All categories</option>{facets.categories.map(category=><option key={category}>{category}</option>)}</select></label>
    </div>
    {loading && <p role="status">Loading hotel directory…</p>}{error && <p className="error" role="alert">{error} <button onClick={()=>setFilters(current=>({...current}))}>Retry</button></p>}
    {!loading && !error && result && <>
      <p className="hotel-directory-count">Showing {result.items.length ? (result.page-1)*result.page_size+1 : 0}–{Math.min(result.page*result.page_size,result.total_filtered)} of {result.total_filtered} matching records · {result.total_source_rows} source rows</p>
      <p className="hotel-directory-note">{result.duplicate_normalized_hotel_names_in_source} repeated normalized hotel names are retained as separate source records. Room counts and validity dates do not establish current operation or availability.</p>
      {result.items.length ? <div className="hotel-directory-grid">{result.items.map(hotel=><article className="hotel-directory-card" key={hotel.id || `${hotel.name}-${hotel.city}-${hotel.address}`}>
        <div className="hotel-directory-card-title"><h2>{hotel.name || 'Hotel name unavailable'}</h2><span>{hotel.category || 'Category unavailable'}</span></div>
        <p className="hotel-directory-location">{[hotel.city,hotel.state].filter(Boolean).join(', ') || 'Location unavailable'}</p>
        <p>{hotel.address || 'Address unavailable'}</p>
        <dl><div><dt>Total rooms in source</dt><dd>{hotel.rooms ?? 'Unknown'}</dd></div><div><dt>Start date</dt><dd>{hotel.start_date || (hotel.invalid_start_date ? `Invalid source date: ${hotel.invalid_start_date}` : 'Not provided')}</dd></div><div><dt>Expiry date</dt><dd>{hotel.expiry_date || (hotel.invalid_expiry_date ? `Invalid source date: ${hotel.invalid_expiry_date}` : 'Not provided')}</dd></div></dl>
        {hotel.address && <a href={mapSearchUrl(`${hotel.name || ''}, ${hotel.address}, ${hotel.city || ''}, ${hotel.state || ''}`)} target="_blank" rel="noreferrer">Search this address on map <MapPin size={13}/></a>}
      </article>)}</div> : <div className="empty"><Hotel/><h2>No matching hotel records</h2><p>Adjust the search or filters to see more source listings.</p></div>}
      {result.pages > 1 && <nav className="hotel-directory-pagination" aria-label="Hotel directory pages"><button disabled={page<=1} onClick={()=>setPage(value=>value-1)}>Previous</button><span>Page {result.page} of {result.pages}</span><button disabled={page>=result.pages} onClick={()=>setPage(value=>value+1)}>Next</button></nav>}
    </>}
  </section></Layout>
}

function Saved() {
  const { saved } = useSaved()
  return (
    <Layout>
      <section className="page">
        <p className="eyebrow">YOUR COLLECTION</p>
        <h1 className="page-title">Saved places.</h1>
        {saved.length ? (
          <div className="card-grid">{saved.map(x => <DestinationCard key={x.id} item={x} />)}</div>
        ) : (
          <div className="empty">
            <Heart />
            <h2>Your list is waiting.</h2>
            <p>Save destinations, hotels and restaurants you want to come back to.</p>
            <Link className="btn" to="/explore">Explore places</Link>
          </div>
        )}
      </section>
    </Layout>
  )
}

function MyTrips() {
  const { savedTrips, deleteTrip } = useSavedTrips()

  return (
    <Layout>
      <section className="page">
        <p className="eyebrow">YOUR JOURNEYS</p>
        <h1 className="page-title">Trips in the making.</h1>

        {savedTrips.length === 0 ? (
          <div className="empty" style={{ marginTop: '40px' }}>
            <Compass size={40} style={{ opacity: 0.5, marginBottom: '20px' }} />
            <h2>No trips planned yet.</h2>
            <p>Your saved itineraries will appear here.</p>
            <Link className="btn" to="/plan-trip" style={{ marginTop: '20px' }}>Plan a trip</Link>
          </div>
        ) : (
          <div className="card-grid">
            {savedTrips.map(trip => {
              const tripTitle = trip.destinationName || 'Trip'

              return (
                <article className="destination-card" key={trip.id} style={{ position: 'relative', overflow: 'hidden', borderRadius: '12px' }}>
                  <DestinationPhoto title={tripTitle} className="trip-card-photo">
                    <button
                      onClick={(e) => {
                        e.preventDefault()
                        if (window.confirm(`Are you sure you want to delete your trip to ${tripTitle}?`)) {
                          deleteTrip(trip.id)
                        }
                      }}
                      style={{
                        position: 'absolute',
                        top: '12px',
                        right: '12px',
                        background: 'rgba(255, 255, 255, 0.95)',
                        color: '#c0392b',
                        border: 'none',
                        borderRadius: '50%',
                        width: '36px',
                        height: '36px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        cursor: 'pointer',
                        boxShadow: '0 2px 8px rgba(0,0,0,0.15)'
                      }}
                      title="Delete trip"
                    >
                      <Trash2 size={17} />
                    </button>

                  </DestinationPhoto>

                  <div className="card-body" style={{ padding: '20px' }}>
                    <div className="card-title">
                      <div>
                        <h3 style={{ fontSize: '1.35rem', margin: '0 0 8px 0', color: '#1a3328' }}>Trip to {tripTitle}</h3>
                        <p style={{ display: 'flex', alignItems: 'center', gap: '6px', margin: 0, color: '#555' }}>
                          <CalendarDays size={15} /> {trip.dates || 'Dates not set'} · {trip.travelers || 1} travellers · {trip.days?.length || 0} days
                        </p>
                      </div>
                    </div>
                    <p className="muted" style={{ margin: '12px 0 20px 0' }}>{trip.budget ? `Budget: ₹${Number(trip.budget).toLocaleString('en-IN')}` : 'Budget not set'}</p>

                    <div className="card-foot" style={{ borderTop: '1px solid #eee', paddingTop: '16px' }}>
                      <Link
                        to={`/itinerary/${trip.id}`}
                        style={{
                          background: '#1b4332',
                          color: '#ffffff',
                          padding: '10px 22px',
                          borderRadius: '8px',
                          textDecoration: 'none',
                          fontWeight: 600,
                          fontSize: '0.92rem',
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '6px',
                          transition: 'background 0.2s ease'
                        }}
                      >
                        View itinerary <ChevronRight size={16} />
                      </Link>
                    </div>
                  </div>
                </article>
              )
            })}
          </div>
        )}
      </section>
    </Layout>
  )
}

function MapPage() {
  const { items, loading, error, reload } = useDestinationCatalog()
  const [selected, setSelected] = useState('')
  useEffect(() => { if (items.length && !items.some(item => item.id === selected)) setSelected(items[0].id) }, [items, selected])
  const destination = items.find(item => item.id === selected)
  const mapUrl = destination ? cityMapSearchUrl([destination.name, destination.state, 'India'].filter(Boolean).join(', ')) : ''
  return (
    <Layout>
      <section className="page">
        <p className="eyebrow">SEE IT ALL</p>
        <h1 className="page-title">Your travel map.</h1>
        <p className="intro">OpenStreetMap searches the selected destination by its real name and state. The source has no verified coordinates for plotting individual listings.</p>
        {loading && <p role="status">Loading destination locations…</p>}{error && <p className="error" role="alert">{error} <button onClick={reload}>Retry</button></p>}
        {!loading && !error && (items.length ? <div className="map-search-card"><label htmlFor="map-destination">Destination</label><select id="map-destination" value={selected} onChange={event=>setSelected(event.target.value)}>{items.map(item=><option key={item.id} value={item.id}>{item.name}{item.state ? `, ${item.state}` : ''}</option>)}</select>{destination && <p>{destination.name}{destination.state ? ` · ${destination.state}` : ''}</p>}<a className="btn" href={mapUrl} target="_blank" rel="noreferrer">Open destination in OpenStreetMap <MapPin size={16}/></a><small>Map search result supplied by OpenStreetMap. Directory addresses can be opened individually from destination details.</small></div> : <div className="empty"><MapPin/><h2>Map search unavailable</h2><p>Destination source records could not be loaded.</p></div>)}
      </section>
    </Layout>
  )
}

function Auth({ register = false }) {
  const { login, register: registerUser } = useAuth()
  const navg = useNavigate()
  const [form, setForm] = useState({ name: '', email: '', password: '' })
  const [error, setError] = useState('')
  const [status, setStatus] = useState('')
  const [statusKind, setStatusKind] = useState('')
  const [busy, setBusy] = useState(false)
  const formatTime = () => new Date().toLocaleString()
  const getFriendlyLoginError = (err) => {
    const statusCode = err?.response?.status
    if (statusCode === 401) return "We couldn't sign you in. Check your email and password, or create an account if you haven't registered yet."
    if (statusCode === 403) return 'This account is inactive. Please contact support.'
    return authService.getAuthErrorMessage(err, 'Sign in failed.')
  }
  const submit = async e => {
    e.preventDefault()
    setError('')
    setStatus('')
    setStatusKind('')
    if (register && form.email.trim().toLowerCase() === 'admin@gmail.com') {
      setError('This email address is reserved for the government administrator and cannot be used for public registration.')
      return
    }
    if (!form.email || form.password.length < 8) {
      setError('Enter a valid email and a password with at least 8 characters.')
      return
    }
    setBusy(true)
    try {
      const user = register ? await registerUser(form) : await login(form)
      const action = register ? 'registered' : 'logged in'
      const time = formatTime()
      setStatus(`${user.name} ${action} successfully at ${time}.`)
      setStatusKind('success')
      user.role === 'admin' ? window.location.replace(authService.buildGovernmentHandoffUrl(governmentAppUrl, authService.getAccessToken())) : navg('/dashboard')
    } catch (err) {
      setStatusKind('error')
      setStatus(`${register ? 'Registration' : 'Sign in'} failed at ${formatTime()}.`)
      setError(register ? authService.getAuthErrorMessage(err, 'Registration failed.') : getFriendlyLoginError(err))
    } finally {
      setBusy(false)
    }
  }
  return (
    <div className="auth-page">
      <Link className="brand" to="/"><span>T</span>TouriSense</Link>
      <form className="auth-card" onSubmit={submit}>
        <p className="eyebrow">{register ? 'BEGIN YOUR JOURNEY' : 'WELCOME BACK'}</p>
        <h1>{register ? 'Create your account.' : 'Good to see you.'}</h1>
        <p>{register ? 'Plan unforgettable trips, your way.' : 'Sign in to continue planning your next escape.'}</p>
        {register && (
          <label>Full name<input value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} required /></label>
        )}
        <label>Email address<input type="email" value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} required /></label>
        <label>Password<input type="password" value={form.password} onChange={e => setForm({ ...form, password: e.target.value })} required /></label>
        {error && <p className="error">{error}</p>}
        {status && <p className={`auth-status ${statusKind}`}>{status}</p>}
        <button className="btn" type="submit" disabled={busy}>
          {busy ? (register ? 'Creating...' : 'Signing in...') : (register ? 'Create account' : 'Sign in')} <ChevronRight size={17} />
        </button>
        <p className="auth-switch">
          {register ? 'Already have an account?' : 'New to TouriSense?'} <Link to={register ? '/login' : '/register'}>{register ? 'Sign in' : 'Create one'}</Link>
        </p>
      </form>
    </div>
  )
}

function Footer() {
  return (
    <footer>
      <Link className="brand" to="/"><span>T</span>TouriSense</Link>
      <p>Travel thoughtfully. Go wonderfully.</p>
      <small>© 2026 TouriSense · Privacy · Terms</small>
    </footer>
  )
}

function App() {
  return (
    <AuthProvider>
      <SavedProvider>
        <SavedTripsProvider>
          <BrowserRouter>
            <Routes>
              <Route path="/" element={<Landing />} />
              <Route path="/login" element={<Auth />} />
              <Route path="/register" element={<Auth register />} />
              <Route path="/forgot-password" element={<Auth />} />
              <Route path="/government/*" element={<AdminProtected><GovernmentRedirect /></AdminProtected>} />
              {['/dashboard', '/explore', '/discover', '/destination/:id', '/plan-trip', '/itinerary/:id', '/my-trips', '/saved-places', '/hotels', '/transport', '/restaurants', '/map', '/profile'].map(path => (
                <Route key={path} path={path} element={
                  <Protected>
                    {path === '/dashboard' ? <Dashboard /> :
                      path === '/explore' ? <Explore /> :
                      path === '/discover' ? <Discover /> :
                      path.startsWith('/destination') ? <Destination /> :
                      path === '/plan-trip' ? <PlanTrip /> :
                      path.startsWith('/itinerary') ? <Itinerary /> :
                      path === '/my-trips' ? <MyTrips /> :
                      path === '/saved-places' ? <Saved /> :
                      path === '/hotels' ? <HotelDirectoryPage /> :
                      path === '/transport' ? <Listing kind="Getting around" endpoint="/catalog/transport" icon={Plane} /> :
                      path === '/restaurants' ? <Listing kind="Local flavours" endpoint="/catalog/restaurants" icon={Soup} /> :
                      path === '/map' ? <MapPage /> :
                      <Dashboard />}
                  </Protected>
                } />
              ))}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </BrowserRouter>
        </SavedTripsProvider>
      </SavedProvider>
    </AuthProvider>
  )
}

export default App
