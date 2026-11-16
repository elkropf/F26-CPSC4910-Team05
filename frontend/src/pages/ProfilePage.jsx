
import { useEffect, useState } from "react";
import { apiRequest } from "../api";

export default function ProfilePage() {
  const [profile, setProfile] = useState({
    username: "",
    first_name: "",
    last_name: "",
    email: ""
  });

  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    apiRequest("/api/auth/profile/")
      .then(data => setProfile(data))
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  function handleChange(e) {
    setProfile({
      ...profile,
      [e.target.name]: e.target.value
    });
  }

  async function handleSubmit(e) {
    e.preventDefault();

    setMessage("");
    setError("");
    setSaving(true);

    try {
      const data = await apiRequest(
        "/api/auth/profile/",
        "POST",
        {
          first_name: profile.first_name,
          last_name: profile.last_name,
          email: profile.email
        }
      );

      setProfile(data);
      setMessage("Profile updated successfully.");
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return <p>Loading profile...</p>;
  }

  return (
    <section>
      <h1>My Profile</h1>

      <div className="card">
        <form onSubmit={handleSubmit}>
          <label>Username</label>
          <input
            value={profile.username}
            disabled
          />

          <label>First Name</label>
          <input
            name="first_name"
            value={profile.first_name}
            onChange={handleChange}
          />

          <label>Last Name</label>
          <input
            name="last_name"
            value={profile.last_name}
            onChange={handleChange}
          />

          <label>Email</label>
          <input
            type="email"
            name="email"
            value={profile.email}
            onChange={handleChange}
          />

          <button type="submit" disabled={saving}>
            {saving ? "Saving..." : "Save Changes"}
          </button>
        </form>

        {message && <p role="status">{message}</p>}
        {error && <p className="error" role="alert">{error}</p>}
      </div>
    </section>
  );
}
