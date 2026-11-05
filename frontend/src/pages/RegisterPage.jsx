
import { useState } from "react";
import { Link } from "react-router-dom";
import { apiRequest } from "../api";

export default function RegisterPage({ onRegistered }) {
  const [form, setForm] = useState({
    username: "",
    email: "",
    password: "",
    confirmPassword: "",
    user_type: "driver",
  });

  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);

  function handleChange(e) {
    setForm({
      ...form,
      [e.target.name]: e.target.value,
    });
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");

    if (form.password !== form.confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setLoading(true);

    try {
      const result = await apiRequest("/api/auth/register/", "POST", {
      username: form.username,
      email: form.email,
      password: form.password,
      user_type: form.user_type,
    });

    onRegistered(result.user);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="login-screen">
      <div className="login-card">
        <h1>Create an Account</h1>

        {success ? (
          <>
            <p>Registration successful!</p>
            <Link to="/login">Go to Login</Link>
          </>
        ) : (
          <form onSubmit={handleSubmit}>
            <label>Username</label>
            <input
              name="username"
              value={form.username}
              onChange={handleChange}
              required
            />

            <label>Email</label>
            <input
              type="email"
              name="email"
              value={form.email}
              onChange={handleChange}
              required
            />

            <label>Password</label>
            <input
              type="password"
              name="password"
              value={form.password}
              onChange={handleChange}
              required
            />

            <label>Confirm Password</label>
            <input
              type="password"
              name="confirmPassword"
              value={form.confirmPassword}
              onChange={handleChange}
              required
            />

            <label>Account Type</label>
            <select
              name="user_type"
              value={form.user_type}
              onChange={handleChange}
            >
              <option value="driver">Driver</option>
              <option value="sponsor">Sponsor</option>
            </select>

            <button disabled={loading}>
              {loading ? "Registering..." : "Register"}
            </button>

            {error && <p className="error">{error}</p>}

            <p>
              Already have an account?{" "}
              <Link to="/login">Login here</Link>
            </p>
          </form>
        )}
      </div>
    </div>
  );
}
