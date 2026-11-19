
import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
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
      ["My Profile", "/driver/profile"],
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
  const [searchParams] = useSearchParams();
  const selectedFromLink = searchParams.get("driver") || "";

  const { data: drivers, error, loading, refresh } =
    useRecords("/api/points/sponsor/");

  const [driverId, setDriverId] = useState(selectedFromLink);
  const [points, setPoints] = useState("");
  const [reason, setReason] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    setDriverId(selectedFromLink);
  }, [selectedFromLink]);

  const driver = drivers.find(
    d => String(d.driver_id) === String(driverId)
  );

  async function submit(e) {
    e.preventDefault();
    setMessage("");

    const amount = Number(points);

    if (!driverId || !Number.isInteger(amount) ||
        amount === 0 || !reason.trim()) {
      setMessage("Please fill out all fields correctly.");
      return;
    }

    setBusy(true);

    try {
      await apiRequest(
        `/api/drivers/${driverId}/points/change/`,
        "POST",
        {
          points_changed: amount,
          reason: reason.trim()
        }
      );

      setMessage("Points updated successfully.");
      setPoints("");
      setReason("");
      refresh();
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
        {loading && <p>Loading drivers...</p>}
        {error && <p className="error">{error}</p>}

        {!loading && !error && (
          <form onSubmit={submit}>
            <label>Select Driver</label>
            <select
              value={driverId}
              onChange={e => setDriverId(e.target.value)}
              required
            >
              <option value="">Select a driver</option>
              {drivers.map(d => (
                <option key={d.driver_id} value={d.driver_id}>
                  {d.username}
                </option>
              ))}
            </select>

            {driver && (
              <p>
                Current Points: {driver.points_balance}
              </p>
            )}

            <label>Points to Add or Remove</label>
            <input
              type="number"
              step="1"
              value={points}
              onChange={e => setPoints(e.target.value)}
              placeholder="100 or -100"
              required
            />

            <label>Reason</label>
            <textarea
              value={reason}
              onChange={e => setReason(e.target.value)}
              placeholder="Enter reason"
              required
            />

            <button type="submit" disabled={busy}>
              {busy ? "Saving..." : "Update Points"}
            </button>
          </form>
        )}

        {message && <p>{message}</p>}
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


export function SponsorDriversPage() {
  const {
    data: drivers,
    error,
    loading,
    refresh
  } = useRecords("/api/points/sponsor/");

  return (
    <section>
      <div className="page-heading">
        <h1>Sponsored Drivers</h1>
        <button onClick={refresh}>Refresh</button>
      </div>

      <p>Total Drivers: {drivers.length}</p>

      {loading && <p>Loading drivers...</p>}
      {error && <p className="error">{error}</p>}

      {!loading && !error && (
        <div className="card">
          {drivers.length === 0 ? (
            <p>No sponsored drivers found.</p>
          ) : (
            <div className="drivers-table-wrap">
              <table className="drivers-table">
                <thead>
                  <tr>
                    <th>Driver Name</th>
                    <th>Username</th>
                    <th>Points</th>
                    <th>Action</th>
                  </tr>
                </thead>

                <tbody>
                  {drivers.map(driver => (
                    <tr key={driver.driver_id}>
                      <td>{driver.name}</td>
                      <td>{driver.username}</td>
                      <td>
                        {Number(
                          driver.points_balance ?? 0
                        ).toLocaleString()}
                      </td>
                      <td>
                        <Link to={`/sponsor/points?driver=${driver.driver_id}`}>
                          Manage Points
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </section>
  );
}
