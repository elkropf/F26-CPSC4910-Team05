import { useEffect, useState } from "react";
import { Outlet } from "react-router-dom";
import Navbar from "../components/NavBar";
import { apiRequest } from "../api";

export default function AppLayout({ user, onLogout }) {
  const [adminUser, setAdminUser] = useState(null);
  const [returning, setReturning] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;

    apiRequest("/api/auth/me/")
      .then(data => {
        if (active) {
          setAdminUser(
            data.impersonating ? data.admin_user : null
          );
        }
      })
      .catch(err => {
        if (active) setError(err.message);
      });

    return () => {
      active = false;
    };
  }, [user?.id]);

  async function returnToAdmin() {
    setReturning(true);
    setError("");

    try {
      await apiRequest(
        "/api/admin/view-as/stop/",
        "POST"
      );

      window.location.assign("/app/admin/dashboard");
    } catch (err) {
      setError(err.message);
      setReturning(false);
    }
  }

  return (
    <div className="app-layout">
      <Navbar
        role={user?.user_type}
        username={user?.username}
        onLogout={onLogout}
        impersonating={Boolean(adminUser)}
        onReturnToAdmin={returnToAdmin}
        returning={returning}
      />

      {adminUser && (
        <div
          role="status"
          style={{
            background: "#fff3cd",
            padding: "12px 20px",
            color: "#333",
            textAlign: "center"
          }}
        >
          Viewing as <strong>{user?.username}</strong>
          {" "}({user?.user_type})
          {" "}— Original Admin: {adminUser.username}
          {" "}— Admin View-As active
        </div>
      )}

      {error && <p className="error">{error}</p>}

      <main className="main-content">
        <Outlet />
      </main>

      <footer className="site-footer">
        <p>Good Driver Incentive Program</p>
        <p>© 2026 All Rights Reserved</p>
      </footer>
    </div>
  );
}
