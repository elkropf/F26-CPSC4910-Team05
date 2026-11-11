
import AppLayout from "./layouts/AppLayout";
import Navbar from "./components/NavBar";
import RegisterPage from "./pages/RegisterPage.jsx";

import CatalogPage from "./pages/CatalogPage";
import SponsorEbayPage from "./pages/SponsorEbayPage";
import EbayCatalog from "./EbayCatalog";
import AdminPanel from "./pages/AdminPanel";
import AboutPage from "./pages/AboutPage";

import { useEffect, useState } from "react";

import {
  BrowserRouter,
  Routes,
  Route,
  Navigate,
  NavLink,
  Outlet,
} from "react-router-dom";

import { apiRequest } from "./api";

import {
  HomePage,
  DataPage,
  ApplyPage,
  PendingApplications,
  PointsPage,
  FeaturePage,
} from "./pages/RolePages";

import "./App.css";

// =====================================
// USER ROLE ROUTING
// =====================================

function homePath(role) {
  if (role === "driver") return "/driver/home";
  if (role === "sponsor") return "/sponsor/home";
  if (role === "admin") return "/admin/dashboard";
  return "/login";
}

function normalizeUser(data) {
  if (data?.authenticated === false) return null;

  const user = data?.user ?? data;

  if (!user || !user.user_type) return null;

  return user;
}

// =====================================
// LOGIN PAGE
// =====================================

function LoginPage({ onLogin }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e) {
    e.preventDefault();
    setError("");
    setBusy(true);

    try {
      await apiRequest("/api/auth/login/", "POST", {
        username,
        password,
      });

      const data = await apiRequest("/api/auth/me/");
      const user = normalizeUser(data);

      if (!user) {
        throw new Error(
          "Login succeeded, but the user role was not returned."
        );
      }

      onLogin(user);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="login-screen">
      <div className="login-card">
        <h1>Good Driver Incentive Program</h1>
        <h2>Login</h2>

        <form onSubmit={submit}>
          <label>Username</label>

          <input
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            autoComplete="username"
            required
          />

          <label>Password</label>

          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
            required
          />

          <button disabled={busy}>
            {busy ? "Logging in..." : "Login"}
          </button>
        </form>

        {error && <p className="error">{error}</p>}

        <p>
          Don't have an account?{" "}
          <NavLink to="/register">Register here</NavLink>
        </p>
      </div>
    </div>
  );
}

// =====================================
// PROTECTED LAYOUT
// =====================================

function ProtectedLayout({ user, logout }) {
  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return (
    <AppLayout
      user={user}
      onLogout={logout}
    />
  );
}

// =====================================
// ROLE GUARD
// =====================================

function RoleGuard({ user, required }) {
  if (user?.user_type !== required) {
    return (
      <Navigate
        to={homePath(user?.user_type)}
        replace
      />
    );
  }

  return <Outlet />;
}

// =====================================
// MAIN APP CONTENT
// =====================================

function AppContent() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [logoutError, setLogoutError] = useState("");

  useEffect(() => {
    apiRequest("/api/auth/me/")
      .then((data) => setUser(normalizeUser(data)))
      .catch(() => setUser(null))
      .finally(() => setLoading(false));
  }, []);

  async function logout() {
    setLogoutError("");

    try {
      await apiRequest("/api/auth/logout/", "POST");
      setUser(null);
    } catch (err) {
      setLogoutError(err.message);
    }
  }

  if (loading) {
    return <p className="loading">Loading...</p>;
  }

  const role = user?.user_type;

  return (
    <>
      {!user && <Navbar />}

      {logoutError && (
        <p className="error" role="alert">
          Logout failed: {logoutError}
        </p>
      )}

      <Routes>

        {/* =====================================
            LOGIN
        ===================================== */}

        <Route
          path="/login"
          element={
            user ? (
              <Navigate
                to={homePath(role)}
                replace
              />
            ) : (
              <LoginPage onLogin={setUser} />
            )
          }
        />

        {/* =====================================
            REGISTER
        ===================================== */}

        <Route
          path="/register"
          element={
            user ? (
              <Navigate
                to={homePath(role)}
                replace
              />
            ) : (
              <RegisterPage onRegistered={setUser} />
            )
          }
        />

        {/* =====================================
            PROTECTED ROUTES
        ===================================== */}

        <Route
          element={
            <ProtectedLayout
              user={user}
              logout={logout}
            />
          }
        >

          <Route
            path="/"
            element={
              <Navigate
                to={homePath(role)}
                replace
              />
            }
          />

          {/* =====================================
              DRIVER ROUTES
          ===================================== */}

          <Route
            element={
              <RoleGuard
                user={user}
                required="driver"
              />
            }
          >

            <Route
              path="/driver/home"
              element={<HomePage user={user} />}
            />

            <Route
              path="/driver/apply"
              element={<ApplyPage />}
            />

            <Route
              path="/driver/applications"
              element={
                <DataPage
                  title="My Applications"
                  url="/api/applications/mine/"
                />
              }
            />

            {/* DRIVER CATALOG - RESTORED */}
            <Route
              path="/driver/stores"
              element={
                <CatalogPage role="driver" />
              }
            />

          </Route>

          {/* =====================================
              SPONSOR ROUTES
          ===================================== */}

          <Route
            element={
              <RoleGuard
                user={user}
                required="sponsor"
              />
            }
          >

            <Route
              path="/sponsor/home"
              element={<HomePage user={user} />}
            />

            <Route
              path="/sponsor/applications"
              element={<PendingApplications />}
            />

            <Route
              path="/sponsor/drivers"
              element={
                <FeaturePage
                  title="Sponsored Drivers"
                  description="Display the drivers connected to this sponsor."
                />
              }
            />

            <Route
              path="/sponsor/points"
              element={<PointsPage />}
            />

            {/* SPONSOR CATALOG - RESTORED */}
            <Route
              path="/sponsor/stores"
              element={
                <>
                  <SponsorEbayPage />
                  <EbayCatalog />
                </>
              }
            />

            {/* SPONSOR EBAY SEARCH */}
            <Route
              path="/sponsor/ebay"
              element={<SponsorEbayPage />}
            />

          </Route>

          {/* =====================================
              ADMIN ROUTES
          ===================================== */}

          <Route
            element={
              <RoleGuard
                user={user}
                required="admin"
              />
            }
          >

            {/* ADMIN DASHBOARD */}
            <Route
              path="/admin/dashboard"
              element={
                <AdminPanel view="dashboard" />
              }
            />

            {/* SPONSOR MANAGEMENT */}
            <Route
              path="/admin/sponsors"
              element={
                <AdminPanel view="sponsors" />
              }
            />

            {/* DRIVER MANAGEMENT */}
            <Route
              path="/admin/drivers"
              element={
                <AdminPanel view="drivers" />
              }
            />

            {/* ACCOUNT PREVIEW */}
            <Route
              path="/admin/sponsor-preview"
              element={
                <AdminPanel view="preview" />
              }
            />

            {/* ADMIN ACCOUNT MANAGEMENT */}
            <Route
              path="/admin/admins"
              element={
                <AdminPanel view="admins" />
              }
            />

            {/* ADMIN REPORTS */}
            <Route
              path="/admin/reports"
              element={
                <AdminPanel view="reports" />
              }
            />

          </Route>

          {/* =====================================
              ABOUT PAGE
          ===================================== */}

          <Route
            path="/about"
            element={<AboutPage />}
          />

        </Route>

        {/* =====================================
            FALLBACK ROUTE
        ===================================== */}

        <Route
          path="*"
          element={
            <Navigate
              to={
                user
                  ? homePath(role)
                  : "/login"
              }
              replace
            />
          }
        />

      </Routes>
    </>
  );
}

// =====================================
// MAIN APPLICATION
// =====================================

export default function App() {
  return (
    <BrowserRouter basename="/app">
      <AppContent />
    </BrowserRouter>
  );
}
