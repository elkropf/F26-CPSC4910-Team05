import { useEffect, useState } from "react";
import { apiRequest } from "../api";

export default function SponsorEbayPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [saved, setSaved] = useState([]);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);

  async function reloadSaved() {
    const data = await apiRequest("/api/catalog/products/");
    setSaved(data.products ?? []);
  }

  useEffect(() => {
    reloadSaved().catch(err => setError(err.message));
  }, []);

  async function search(e) {
    e.preventDefault();
    setBusy(true);
    setError("");
    setMessage("");
    try {
      const data = await apiRequest(`/api/catalog/ebay/search/?q=${encodeURIComponent(query)}`);
      setResults(data.results ?? []);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function add(token) {
    setBusy(true);
    setError("");
    setMessage("");
    try {
      const data = await apiRequest("/api/catalog/ebay/add/", "POST", { token });
      setMessage(data.message);
      await reloadSaved();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <main style={{ padding: "25px" }}>
      <h1>Sponsor Catalog</h1>
      {error && <p className="error" role="alert">{error}</p>}
      {message && <p role="status">{message}</p>}
      <form onSubmit={search} style={{ display: "flex", gap: 10 }}>
        <input aria-label="Search eBay" placeholder="Search eBay products" value={query}
          onChange={e => setQuery(e.target.value)} required style={{ flex: 1, padding: 10 }} />
        <button type="submit" disabled={busy}>Search</button>
      </form>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 12, marginTop: 20 }}>
        {results.map((p, i) => (
          <div key={i} style={{ padding: 15, background: "white", borderRadius: 8, border: "1px solid #ddd" }}>
            {p.image && <img src={p.image} alt="" style={{ width: "100%", height: 135, objectFit: "contain" }} />}
            <p><strong>{p.title}</strong></p>
            <p>${p.price}</p>
            <button disabled={busy} onClick={() => add(p.token)}>Add to Catalog</button>
          </div>
        ))}
      </div>
      <h2 style={{ marginTop: 30 }}>Saved Products ({saved.length})</h2>
      {saved.length === 0 ? <p>No saved products yet.</p> : saved.map(p => (
        <p key={p.id}>{p.name} — <strong>{p.points} points</strong></p>
      ))}
    </main>
  );
}
