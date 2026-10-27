
import { Outlet } from "react-router-dom";
import Navbar from "../components/NavBar";

export default function AppLayout({ user, onLogout }) {
  return (
    <div className="app-layout">

      <Navbar
        role={user?.user_type}
        username={user?.username}
        onLogout={onLogout}
      />

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
