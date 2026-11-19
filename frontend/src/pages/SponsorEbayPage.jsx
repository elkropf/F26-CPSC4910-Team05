
import { useEffect, useState } from "react";
import { apiRequest } from "../api";

export default function SponsorEbayPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [savedProducts, setSavedProducts] = useState([]);

  const [searching, setSearching] = useState(false);
  const [saving, setSaving] = useState(null);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  async function loadSavedProducts() {
    const data = await apiRequest("/api/catalog/products/");
    setSavedProducts(data.products || []);
  }

  useEffect(() => {
    loadSavedProducts().catch((err) => {
      setError(err.message);
    });
  }, []);

  async function handleSearch(event) {
    event.preventDefault();

    if (!query.trim()) return;

    setError("");
    setMessage("");
    setSearching(true);

    try {
      const data = await apiRequest(
        `/api/catalog/ebay/search/?q=${encodeURIComponent(
          query.trim()
        )}`
      );

      setResults(data.results || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setSearching(false);
    }
  }

  async function addToStore(product) {
    setError("");
    setMessage("");

    if (!product.token) {
      setError("Product token missing from search result.");
      return;
    }

    setSaving(product.token);

    try {
      await apiRequest(
        "/api/catalog/ebay/add/",
        "POST",
        { token: product.token }
      );

      await loadSavedProducts();

      setMessage(`${product.title} added to your store!`);
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(null);
    }
  }

  function formatPrice(price) {
    if (price == null) return "Price unavailable";

    if (typeof price === "object") {
      return `${price.value} ${price.currency || "USD"}`;
    }

    return `$${price}`;
  }

  function getImage(product) {
    if (typeof product.image === "string") {
      return product.image;
    }

    return product.image?.imageUrl || null;
  }

  return (
    <div style={{ padding: 24, maxWidth: 1100, margin: "auto" }}>
      <h1>Sponsor Store</h1>

      <h2>Search Products</h2>

      <form onSubmit={handleSearch}>
        <div style={{ display: "flex", gap: 10 }}>
          <input
            type="text"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search products..."
            style={{
              padding: 12,
              flex: 1,
              border: "1px solid #ccc",
              borderRadius: 5,
            }}
          />

          <button type="submit" disabled={searching}>
            {searching ? "Searching..." : "Search"}
          </button>
        </div>
      </form>

      {error && (
        <p style={{ color: "red" }}>{error}</p>
      )}

      {message && (
        <p style={{ color: "green" }}>{message}</p>
      )}

      <h2>Search Results</h2>

      {results.length === 0 && (
        <p>Search for products to add to your store.</p>
      )}

      <div
        style={{
          display: "grid",
          gridTemplateColumns:
            "repeat(auto-fit, minmax(220px, 1fr))",
          gap: 20,
        }}
      >
        {results.map((product, index) => (
          <div
            key={product.token || index}
            style={{
              border: "1px solid #ccc",
              padding: 15,
              borderRadius: 8,
              background: "white",
            }}
          >
            {getImage(product) && (
              <img
                src={getImage(product)}
                alt={product.title}
                style={{
                  width: "100%",
                  height: 150,
                  objectFit: "contain",
                }}
              />
            )}

            <h3>{product.title}</h3>

            <p>{formatPrice(product.price)}</p>

            <button
              disabled={saving !== null}
              onClick={() => addToStore(product)}
            >
              {saving === product.token
                ? "Adding..."
                : "Add to Store"}
            </button>
          </div>
        ))}
      </div>

      <hr style={{ margin: "30px 0" }} />

      <h2>Products in Your Store</h2>

      <p>
        These are the products available to drivers
        belonging to your organization.
      </p>

      {savedProducts.length === 0 ? (
        <p>No products added yet.</p>
      ) : (
        <div
          style={{
            display: "grid",
            gridTemplateColumns:
              "repeat(auto-fit, minmax(220px, 1fr))",
            gap: 20,
          }}
        >
          {savedProducts.map((product) => (
            <div
              key={product.id}
              style={{
                border: "1px solid #ccc",
                padding: 15,
                borderRadius: 8,
                background: "white",
              }}
            >
              <h3>{product.name}</h3>

              <p>
                {product.description || "Reward product"}
              </p>

              <strong>{product.points} points</strong>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
