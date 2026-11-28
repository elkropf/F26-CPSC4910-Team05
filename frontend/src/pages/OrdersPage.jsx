import { useEffect, useState } from "react";
import { apiRequest } from "../api";

export default function OrdersPage() {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState(null);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  async function loadOrders() {
    setLoading(true);
    setError("");
    try {
      const data = await apiRequest("/api/catalog/orders/");
      setOrders(data.orders || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadOrders();
  }, []);

  async function cancelOrder(orderId) {
    if (!window.confirm(`Cancel order #${orderId} and refund its points?`)) return;
    setBusyId(orderId);
    setError("");
    setMessage("");
    try {
      const result = await apiRequest(`/api/catalog/orders/${orderId}/cancel/`, "POST");
      setMessage(result.message);
      await loadOrders();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusyId(null);
    }
  }

  return (
    <section>
      <h1>My Orders</h1>
      <button onClick={loadOrders} disabled={loading}>Refresh Orders</button>
      {loading && <p>Loading orders...</p>}
      {error && <p className="error">{error}</p>}
      {message && <p role="status">{message}</p>}

      {!loading && !error && orders.length === 0 && <p>You have no orders yet.</p>}

      {!loading && orders.map((order) => (
        <div className="card" key={order.id} style={{ marginTop: 16 }}>
          <h3>Order #{order.id}</h3>
          <p>Status: <strong>{order.status}</strong></p>
          <p>Total Points: {order.points}</p>
          <p>Date: {new Date(order.created_at).toLocaleDateString()}</p>
          <h4>Items</h4>
          {(order.items || []).map((item, index) => (
            <p key={index}>
              {item.name} - Quantity: {item.quantity} - {item.points} points
            </p>
          ))}

          {["processing", "approved"].includes(order.status) && (
            <button
              className="danger"
              disabled={busyId === order.id}
              onClick={() => cancelOrder(order.id)}
            >
              {busyId === order.id ? "Cancelling..." : "Cancel Order"}
            </button>
          )}
        </div>
      ))}
    </section>
  );
}
