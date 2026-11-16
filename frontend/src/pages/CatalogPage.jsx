import { useEffect, useState } from "react";
import { apiRequest } from "../api";

export default function CatalogPage({ role }) {
  const [products, setProducts] = useState([]);
  const [cart, setCart] = useState({ items: [], total_points: 0 });
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  async function refreshCart() {
    const data = await apiRequest("/api/catalog/cart/");
    setCart(data.cart);
  }

  useEffect(() => {
    let active = true;
    async function load() {
      try {
        const data = await apiRequest("/api/catalog/products/");
        if (active) setProducts(data.products);
        if (role === "driver") {
          const cartData = await apiRequest("/api/catalog/cart/");
          if (active) setCart(cartData.cart);
        }
      } catch (err) {
        if (active) setError(err.message);
      } finally {
        if (active) setLoading(false);
      }
    }
    load();
    return () => { active = false; };
  }, [role]);

  async function perform(action) {
    setError("");
    setMessage("");
    setBusy(true);
    try {
      const result = await action();
      setMessage(result.message || "Success.");
      await refreshCart();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  if (loading) return <p>Loading catalog...</p>;

  return (
    <main className="catalog-page">
      <h1>{role === "sponsor" ? "My Sponsor Catalog" : "Rewards Catalog"}</h1>
      {error && <p className="error" role="alert">{error}</p>}
      {message && <p role="status">{message}</p>}
      <div className="catalog-grid">
        {products.map(product => (
          <article className="catalog-card" key={product.id}>
            <h3>{product.name}</h3>
            <p>{product.description || "Reward product"}</p>
            <strong>{product.points} points</strong>
            {role === "driver" && (
              <p>
                <button disabled={busy} onClick={() => perform(() =>
                  apiRequest("/api/catalog/cart/add/", "POST", { product_id: product.id })
                )}>Add to Cart</button>
              </p>
            )}
          </article>
        ))}
      </div>
      {products.length === 0 && <p>No products available.</p>}

      {role === "driver" && (
        <section className="catalog-cart">
          <h2>Shopping Cart</h2>
          {cart.items.length === 0 ? <p>Your cart is empty.</p> : (
            <ul>
              {cart.items.map(item => (
                <li key={item.id}>
                  {item.name} — {item.points} points
                  {" "}
                  <button disabled={busy} onClick={() => perform(() =>
                    apiRequest(`/api/catalog/cart/remove/${item.id}/`, "POST")
                  )}>Remove</button>
                </li>
              ))}
            </ul>
          )}
          <p><strong>Total: {cart.total_points} points</strong></p>
          <button
            disabled={busy || cart.items.length === 0}
            onClick={() => perform(() =>
              apiRequest("/api/catalog/cart/checkout/", "POST")
            )}
          >Place Order</button>
        </section>
      )}
    </main>
  );
}
