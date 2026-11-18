import { useEffect, useState } from "react";
import { ShieldCheck } from "lucide-react";
import { API_BASE, getAdminToken } from "../services/api";
import { consumeAdminHandoff } from "../services/adminHandoff";

export default function AdminGate({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const checkSession = async () => {
    const handoffToken = consumeAdminHandoff(window.location, window.history);
    const token = handoffToken || getAdminToken();
    if (!token) { setLoading(false); return; }
    try {
      const response = await fetch(`${API_BASE}/users/me`, { headers: { Authorization: `Bearer ${token}` } });
      const body = await response.json();
      if (!response.ok || body.role !== "admin") throw new Error("Administrator access is required.");
      localStorage.setItem("tourisense-token", token);
      setUser(body);
    } catch (err) {
      localStorage.removeItem("tourisense-token"); localStorage.removeItem("wanderly-token");
      setError(err.message);
    } finally { setLoading(false); }
  };
  useEffect(() => { checkSession(); }, []);

  const signIn = async (event) => {
    event.preventDefault(); setBusy(true); setError("");
    try {
      const response = await fetch(`${API_BASE}/auth/login`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(form) });
      const body = await response.json();
      if (!response.ok) throw new Error(body.error || "Could not sign in.");
      if (body.user?.role !== "admin") throw new Error("This portal requires a government administrator account.");
      localStorage.setItem("tourisense-token", body.token); setUser(body.user);
    } catch (err) { setError(err.message || "Could not sign in."); }
    finally { setBusy(false); }
  };
  const signOut = () => { localStorage.removeItem("tourisense-token"); localStorage.removeItem("wanderly-token"); setUser(null); };
  if (loading) return <div className="gate-loading" role="status">Checking administrator access…</div>;
  if (!user) return <main className="gate-page"><form className="gate-card" onSubmit={signIn}><span className="gate-icon"><ShieldCheck size={24}/></span><p className="breadcrumb">TOURISENSE GOVERNMENT PORTAL</p><h1>Administrator sign in</h1><p>Use your existing TouriSense government administrator account to access dashboard data.</p><label>Email<input type="email" autoComplete="username" required value={form.email} onChange={e=>setForm({...form,email:e.target.value})}/></label><label>Password<input type="password" autoComplete="current-password" required value={form.password} onChange={e=>setForm({...form,password:e.target.value})}/></label>{error && <p className="gate-error" role="alert">{error}</p>}<button className="gate-submit" disabled={busy}>{busy ? "Signing in…" : "Sign in"}</button></form></main>;
  return children({ user, signOut });
}
