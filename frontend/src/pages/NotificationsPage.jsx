
import { useEffect, useState } from "react";
import { apiRequest } from "../api";

export default function NotificationsPage() {
  const [notifications, setNotifications] = useState([]);
  const [unread, setUnread] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [refresh, setRefresh] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const [prefs, setPrefs] = useState({
    point_notifications: true,
    order_notifications: true
  });

  useEffect(() => {
    let active = true;
    setLoading(true);

    apiRequest(`/api/notifications/?page=${page}`)
      .then(data => {
        if (!active) return;
        setNotifications(data.notifications);
        setUnread(data.unread_count);
        setTotalPages(data.total_pages);
      })
      .catch(err => {
        if (active) setError(err.message);
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => { active = false; };
  }, [page, refresh]);

  useEffect(() => {
    apiRequest("/api/notifications/preferences/")
      .then(data => setPrefs(data))
      .catch(err => setError(err.message));
  }, []);

  async function markRead(id) {
    setError("");

    try {
      await apiRequest(
        `/api/notifications/${id}/read/`,
        "POST"
      );
      setRefresh(v => v + 1);
    } catch (err) {
      setError(err.message);
    }
  }

  async function savePreferences(e) {
    e.preventDefault();
    setError("");
    setMessage("");

    try {
      const data = await apiRequest(
        "/api/notifications/preferences/update/",
        "POST",
        prefs
      );
      setPrefs(data);
      setMessage("Preferences saved.");
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <section>
      <div className="page-heading">
        <h1>Notifications</h1>
        <button onClick={() => setRefresh(v => v + 1)}>
          Refresh
        </button>
      </div>

      <p>Unread notifications: {unread}</p>
      {error && <p className="error">{error}</p>}
      {message && <p>{message}</p>}

      {loading ? (
        <p>Loading...</p>
      ) : notifications.length === 0 ? (
        <p>No notifications found.</p>
      ) : (
        notifications.map(item => (
          <div
            className="card"
            key={item.id}
            style={{
              marginBottom: 12,
              borderLeft: item.is_read
                ? "1px solid #ddd"
                : "4px solid #245ca0"
            }}
          >
            <h3>{item.type.replaceAll("_", " ")}</h3>
            <p>{item.message}</p>

            {item.organization && (
              <p>Organization: {item.organization}</p>
            )}

            <p>
              {new Date(item.created_at).toLocaleString()}
            </p>

            {!item.is_read && (
              <button onClick={() => markRead(item.id)}>
                Mark as Read
              </button>
            )}
          </div>
        ))
      )}

      <div className="button-row">
        <button
          disabled={page === 1}
          onClick={() => setPage(p => p - 1)}
        >
          Previous
        </button>

        <span>Page {page} of {totalPages}</span>

        <button
          disabled={page >= totalPages}
          onClick={() => setPage(p => p + 1)}
        >
          Next
        </button>
      </div>

      <div className="card" style={{ marginTop: 25 }}>
        <h2>Notification Settings</h2>

        <form onSubmit={savePreferences}>
          <label>
            <input
              type="checkbox"
              style={{ width: "auto" }}
              checked={prefs.point_notifications}
              onChange={e => setPrefs({
                ...prefs,
                point_notifications: e.target.checked
              })}
            />
            {" "}Point Notifications
          </label>

          <label>
            <input
              type="checkbox"
              style={{ width: "auto" }}
              checked={prefs.order_notifications}
              onChange={e => setPrefs({
                ...prefs,
                order_notifications: e.target.checked
              })}
            />
            {" "}Order Notifications
          </label>

          <button type="submit">Save Preferences</button>
        </form>
      </div>
    </section>
  );
}
