
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { apiRequest } from "../api";

function getItems(data) {
  if (Array.isArray(data)) return data;

  for (const key of [
    "results", "applications", "organizations",
    "drivers", "sponsors", "items"
  ]) {
    if (Array.isArray(data?.[key])) return data[key];
  }

  return [];
}

function RecordCards({ items }) {
  if (!items.length) return <p>No records found.</p>;

  return (
    <div className="cards">
      {items.map((item, index) => (
        <div className="card" key={item.id ?? index}>
          {Object.entries(item).map(([key, value]) => (
            <p key={key}>
              <strong>{key.replaceAll("_", " ")}: </strong>
              {typeof value === "object"
                ? JSON.stringify(value)
                : String(value)}
            </p>
          ))}
        </div>
      ))}
    </div>
  );
}

export function useRecords(url) {
  const [data, setData] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [version, refresh] = useState(0);

  useEffect(() => {
    let cancelled = false;

    setLoading(true);
    setError("");

    apiRequest(url)
      .then(result => {
        if (!cancelled) setData(getItems(result));
      })
      .catch(err => {
        if (!cancelled) setError(err.message);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => { cancelled = true; };
  }, [url, version]);

  return { data, error, loading, refresh: () => refresh(v => v + 1) };
}

export function DataPage({ title, url }) {
  const { data, error, loading, refresh } = useRecords(url);

  return (
    <section>
      <div className="page-heading">
        <h1>{title}</h1>
        <button onClick={refresh}>Refresh</button>
      </div>
      {loading && <p>Loading...</p>}
      {error && <p className="error">{error}</p>}
      {!loading && !error && <RecordCards items={data} />}
    </section>
  );
}

export function HomePage({ user }) {
  const role = user.user_type;

  const actions = {
    driver: [
      ["Apply to a sponsor", "/driver/apply"],
      ["My applications", "/driver/applications"],
      ["Stores", "/driver/stores"],
    ],
    sponsor: [
      ["Review applications", "/sponsor/applications"],
      ["Drivers", "/sponsor/drivers"],
      ["Manage points", "/sponsor/points"],
    ],
    admin: [
      ["Manage sponsors", "/admin/sponsors"],
      ["Sponsor preview", "/admin/sponsor-preview"],
      ["About", "/about"],
    ],
  };

  return (
    <section>
      <h1>Welcome, {user.username}</h1>
      <p>Your account role: <strong>{role}</strong></p>

      <div className="cards">
        {(actions[role] || []).map(([name, path]) => (
          <Link className="card action-card" to={path} key={path}>
            <h3>{name}</h3>
            <p>Open page</p>
          </Link>
        ))}
      </div>
    </section>
  );
}

export function ApplyPage() {
  const { data: organizations, error, loading } =
    useRecords("/api/organizations/");

  const [organizationId, setOrganizationId] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e) {
    e.preventDefault();
    setMessage("");
    setBusy(true);

    try {
      await apiRequest("/api/applications/submit/", "POST", {
        organization_id: Number(organizationId),
      });
      setMessage("Application submitted successfully.");
    } catch (err) {
      setMessage(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section>
      <h1>Apply to a Sponsor</h1>
      <div className="card">
        {loading && <p>Loading organizations...</p>}
        {error && <p className="error">{error}</p>}

        <form onSubmit={submit}>
          <label>Select organization</label>
          <select
            required
            value={organizationId}
            onChange={e => setOrganizationId(e.target.value)}
          >
            <option value="">Choose an organization</option>
            {organizations.map(org => (
              <option
                key={org.id ?? org.organization_id}
                value={org.id ?? org.organization_id}
              >
                {org.name ?? org.organization_name ?? `Organization ${org.id}`}
              </option>
            ))}
          </select>

          <button disabled={busy || !organizationId}>
            {busy ? "Submitting..." : "Submit Application"}
          </button>
        </form>

        {message && <p role="status">{message}</p>}
      </div>
    </section>
  );
}
  
export function PendingApplications() {
  const { data, error, loading, refresh } =
    useRecords("/api/applications/pending/");

  const [message, setMessage] = useState("");

  async function review(id, decision) {
    if (!id) {
      setMessage("Application ID is missing.");
      return;
    }

    const status =
      decision === "approve" ? "approved" : "rejected";

    let rejection_reason = "";

    if (status === "rejected") {
      const reason = window.prompt(
        "Why are you rejecting this application?"
      );

      if (!reason || !reason.trim()) {
        setMessage("A rejection reason is required.");
        return;
      }

      rejection_reason = reason.trim();
    }

    setMessage("");

    try {
      await apiRequest(
        `/api/applications/${id}/review/`,
        "POST",
        {
          status,
          rejection_reason,
        }
      );

      setMessage(`Application ${status} successfully.`);
      refresh();

    } catch (err) {
      setMessage(err.message);
    }
  }

  return (
    <section>
      <h1>Pending Driver Applications</h1>

      {loading && <p>Loading...</p>}

      {error && (
        <p className="error">{error}</p>
      )}

      {message && (
        <p role="status">{message}</p>
      )}

      {!loading && !error && data.length === 0 && (
        <p>No pending applications.</p>
      )}

      <div className="cards">
        {data.map((application, index) => {
          const id =
            application.id ?? application.application_id;

          return (
            <div className="card" key={id ?? index}>
              <h3>{application.username || "Driver"}</h3>

              <p>Application ID: {id}</p>
              <p>Status: {application.status}</p>
              <p>Message: {application.message || "None"}</p>

              <div className="button-row">
                <button onClick={() => review(id, "approve")}>
                  Approve
                </button>

                <button
                  className="danger"
                  onClick={() => review(id, "reject")}
                >
                  Reject
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}


export function PointsPage() {
  const [driverId, setDriverId] = useState("");
  const [change, setChange] = useState("");
  const [reason, setReason] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e) {
    e.preventDefault();
    setMessage("");
    setBusy(true);

    try {
      await apiRequest(
        `/api/drivers/${driverId}/points/change/`,
        "POST",
        {
          points_changed: Number(change),
          reason: reason.trim(),
        }
      );
      setMessage("Points request completed.");
      setChange("");
      setReason("");
    } catch (err) {
      setMessage(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section>
      <h1>Manage Driver Points</h1>

      <div className="card">
        <form onSubmit={submit}>
          <label>Driver ID</label>
          <input
            type="number"
            min="1"
            required
            value={driverId}
            onChange={e => setDriverId(e.target.value)}
          />

          <label>Points change (+ or -)</label>
          <input
            type="number"
            required
            value={change}
            onChange={e => setChange(e.target.value)}
          />

          <label>Reason</label>
          <textarea
            value={reason}
            onChange={e => setReason(e.target.value)}
          />

          <button disabled={busy || Number(change) === 0}>
            {busy ? "Saving..." : "Update Points"}
          </button>
        </form>

        {message && <p role="status">{message}</p>}
      </div>
    </section>
  );
}

export function FeaturePage({ title, description }) {
  return (
    <section>
      <h1>{title}</h1>
      <div className="card">
        <p>{description}</p>
        <p className="muted">
          The React page exists. Its data API still needs to be connected.
        </p>
      </div>
    </section>
  );
}
