
import { useEffect, useState } from "react";
import { apiRequest } from "../api";

export default function OrdersPage() {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    apiRequest("/api/catalog/orders/")
      .then(data => setOrders(data.orders || []))
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <section>
      <h1>My Orders</h1>

      {loading && <p>Loading orders...</p>}
      {error && <p className="error">{error}</p>}

      {!loading && !error && orders.length === 0 && (
        <p>You have no orders yet.</p>
      )}

      {!loading && !error && orders.map(order => (
        <div className="card" key={order.id}>
          <h3>Order #{order.id}</h3>

          <p>Status: {order.status}</p>
          <p>Total Points: {order.points}</p>
          <p>
            Date: {new Date(order.created_at).toLocaleDateString()}
          </p>

          <h4>Items</h4>

          {order.items.map((item, index) => (
            <p key={index}>
              {item.name} - Quantity: {item.quantity}
              {" "} - {item.points} points
            </p>
          ))}
        </div>
      ))}
    </section>
  );
}
