
import AppLayout from "./layouts/AppLayout";
import Navbar from "./components/NavBar";
import RegisterPage from "./pages/RegisterPage.jsx";
import CatalogPage from "./pages/CatalogPage";
import SponsorEbayPage from "./pages/SponsorEbayPage";
import ProfilePage from "./pages/ProfilePage";
import AdminPanel from "./pages/AdminPanel";
import AboutPage from "./pages/AboutPage";
import NotificationsPage from "./pages/NotificationsPage";
import OrdersPage from "./pages/OrdersPage";
import BulkImportPage from "./pages/BulkImportPage";

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
  SponsorDriversPage,
} from "./pages/RolePages";

import "./App.css";

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

function LoginPage({ onLogin }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [code, setCode] = useState("");
  const [mfaRequired, setMfaRequired] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e) {
    e.preventDefault();
    setError("");
    setBusy(true);

    try {
      if (!mfaRequired) {
        const result = await apiRequest(
          "/api/auth/login/",
          "POST",
          {
            username,
            password
          }
        );

        if (result.mfa_required) {
          setMfaRequired(true);
          setPassword("");
        } else {
          const user = normalizeUser(result);

          if (!user) {
            throw new Error("Login could not be completed.");
          }

          onLogin(user);
        }

      } else {
        const result = await apiRequest(
          "/api/auth/mfa/verify/",
          "POST",
          { code }
        );

        const user = normalizeUser(result);

        if (!user) {
          throw new Error("Verification failed.");
        }

        onLogin(user);
      }

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

        <h2>
          {mfaRequired ? "Email Verification" : "Login"}
        </h2>

        <form onSubmit={submit}>
          {!mfaRequired ? (
            <>
              <label>Username</label>
              <input
                value={username}
                onChange={e => setUsername(e.target.value)}
                autoComplete="username"
                required
              />

              <label>Password</label>
              <input
                type="password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                autoComplete="current-password"
                required
              />
            </>
          ) : (
            <>
              <p>
                Enter the 6-digit verification code
                sent to your email.
              </p>

              <label>Verification Code</label>

              <input
                value={code}
                onChange={e =>
                  setCode(e.target.value.replace(/\D/g, ""))
                }
                type="text"
                inputMode="numeric"
                autoComplete="one-time-code"
                maxLength={6}
                pattern="[0-9]{6}"
                placeholder="Enter code"
                required
              />
            </>
          )}

          <button disabled={busy}>
            {busy
              ? "Please wait..."
              : mfaRequired
                ? "Verify Code"
                : "Login"}
          </button>
        </form>

        {error && <p className="error">{error}</p>}

        {mfaRequired ? (
          <button
            type="button"
            onClick={() => {
              setMfaRequired(false);
              setCode("");
              setError("");
            }}
            disabled={busy}
            style={{ marginTop: 12 }}
          >
            Back to Login
          </button>
        ) : (
          <p>
            Don't have an account?{" "}
            <NavLink to="/register">
              Register here
            </NavLink>
          </p>
        )}
      </div>
    </div>
  );
}

function ProtectedLayout({ user, logout }) {
  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return (
    <AppLayout user={user} onLogout={logout} />
  );
}

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

function AppContent() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [logoutError, setLogoutError] = useState("");

  useEffect(() => {
    apiRequest("/api/auth/me/")
      .then(data => setUser(normalizeUser(data)))
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
        {/* Login and Register */}

        <Route
          path="/login"
          element={
            user
              ? <Navigate to={homePath(role)} replace />
              : <LoginPage onLogin={setUser} />
          }
        />

        <Route
          path="/register"
          element={
            user
              ? <Navigate to={homePath(role)} replace />
              : <RegisterPage onRegistered={setUser} />
          }
        />

        {/* Protected pages */}

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
              <Navigate to={homePath(role)} replace />
            }
          />

          {/* Driver */}

          <Route
            element={
              <RoleGuard user={user} required="driver" />
            }
          >
            <Route
              path="/driver/home"
              element={<HomePage user={user} />}
            />

            <Route
              path="/driver/profile"
              element={<ProfilePage />}
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

            <Route
              path="/driver/stores"
              element={<CatalogPage role="driver" />}
            />
          </Route>
          <Route
            path="/driver/orders"
            element={<OrdersPage />}
          />

          <Route
            path="/driver/points"
            element={
              <DataPage
                title="My Points"
                url="/api/points/mine/"
              />
            }
          />

          <Route
            path="/driver/points/history"
            element={
              <DataPage
                title="Point History"
                url="/api/points/history/"
              />
            }
          />


          {/* Sponsor */}

          <Route
            element={
              <RoleGuard user={user} required="sponsor" />
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
              element={<SponsorDriversPage />}
            />

            <Route
              path="/sponsor/points"
              element={<PointsPage />}
            />

            <Route
              path="/sponsor/stores"
              element={<SponsorEbayPage />}
            />

            <Route
              path="/sponsor/ebay"
              element={<SponsorEbayPage />}
            />
            <Route
              path="/sponsor/profile"
              element={<ProfilePage />}
            />
          </Route>



          {/* Admin */}

          <Route
            element={
              <RoleGuard user={user} required="admin" />
            }
          >
            <Route
              path="/admin/dashboard"
              element={<AdminPanel view="dashboard" />}
            />

            <Route
              path="/admin/sponsors"
              element={<AdminPanel view="sponsors" />}
            />

            <Route
              path="/admin/drivers"
              element={<AdminPanel view="drivers" />}
            />

            <Route
              path="/admin/sponsor-preview"
              element={<AdminPanel view="preview" />}
            />

            <Route
              path="/admin/admins"
              element={<AdminPanel view="admins" />}
            />

            <Route
              path="/admin/reports"
              element={<AdminPanel view="reports" />}
            />
            <Route
              path="/admin/bulk-import"
              element={<AdminPanel view="bulk-import" />}
            />
          </Route>
          <Route
            path="/admin/organizations"
            element={<AdminPanel view="organizations" />}
          />

          {/* Shared pages */}

          <Route
            path="/notifications"
            element={<NotificationsPage />}
          />

          <Route
            path="/about"
            element={<AboutPage />}
          />
        </Route>

        <Route
          path="*"
          element={
            <Navigate
              to={user ? homePath(role) : "/login"}
              replace
            />
          }
        />
      </Routes>
    </>
  );
}

export default function App() {
  return (
    <BrowserRouter basename="/app">
      <AppContent />
    </BrowserRouter>
  );
}
