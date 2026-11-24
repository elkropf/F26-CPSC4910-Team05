import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { apiRequest } from "../api";
import "../AdminPanel.css";

const blankUser = { username: "", email: "", password: "", first_name: "", last_name: "" };

function useDirectory() {
  const [data, setData] = useState({ sponsors: [], drivers: [], admins: [], organizations: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      setData(await apiRequest("/api/admin/directory/"));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);
  useEffect(() => { load(); }, [load]);
  return { ...data, loading, error, load };
}

function Note({ message, error = false }) {
  return message ? <p className={error ? "admin-alert error" : "admin-alert"} role="status">{message}</p> : null;
}

function NewUserFields({ form, setForm }) {
  function update(event) {
    setForm((current) => ({ ...current, [event.target.name]: event.target.value }));
  }
  return (
    <div className="admin-form-grid">
      <label>Username<input name="username" value={form.username} onChange={update} required /></label>
      <label>Email<input type="email" name="email" value={form.email} onChange={update} /></label>
      <label>Password<input type="password" name="password" value={form.password} onChange={update} minLength="8" required /></label>
      <label>First name<input name="first_name" value={form.first_name} onChange={update} /></label>
      <label>Last name<input name="last_name" value={form.last_name} onChange={update} /></label>
    </div>
  );
}



function Dashboard() {
  const [summary, setSummary] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    apiRequest("/api/admin/overview/")
      .then(data => setSummary(data.summary))
      .catch(err => setError(err.message));
  }, []);

  const items = [
    ["Sponsors", "/admin/sponsors", "sponsors"],
    ["Drivers", "/admin/drivers", "drivers"],
    ["Administrators", "/admin/admins", "admins"],
    ["Organizations", "/admin/organizations", "organizations"],
    ["Orders", "/admin/reports", "orders"],
    ["Points Outstanding", "/admin/reports", "total_points_outstanding"],
  ];

  return (
    <section className="admin-panel">
      <h1>Admin Dashboard</h1>

      <p>
        Manage sponsor accounts, driver assignments,
        account security, and reports.
      </p>

      <Note message={error} error />

      <div className="admin-stats">
        {items.map(([title, url, key]) => (
          <Link
            to={url}
            className="card admin-stat"
            key={key}
          >
            <strong>{title}</strong>
            <span>{summary ? summary[key] : "..."}</span>
          </Link>
        ))}
      </div>

      <p>
        <Link to="/admin/sponsor-preview">
          View as Sponsor / Driver
        </Link>
      </p>

      <p>
        <Link to="/admin/bulk-import">
          Bulk Import Users
        </Link>
      </p>
    </section>
  );
}





function Sponsors() {
  const { sponsors, organizations, loading, error, load } = useDirectory();

  const [form, setForm] = useState({
    ...blankUser,
    organization_id: "",
    organization_name: ""
  });

  const [fees, setFees] = useState({});
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [actionError, setActionError] = useState(false);

  const [editingId, setEditingId] = useState(null);
  const [editData, setEditData] = useState({});

  // Delete confirmation
  const [deleteId, setDeleteId] = useState(null);

  useEffect(() => {
    setFees(Object.fromEntries(
      sponsors.map(s => [s.sponsor_id, s.fee_percentage])
    ));
  }, [sponsors]);

  async function run(fn) {
    setBusy(true);
    setMessage("");

    try {
      await fn();
      setActionError(false);
      await load();
    } catch (err) {
      setMessage(err.message);
      setActionError(true);
    } finally {
      setBusy(false);
    }
  }

  function create(e) {
    e.preventDefault();

    run(async () => {
      const result = await apiRequest(
        "/api/admin/sponsors/create/",
        "POST",
        {
          ...form,
          organization_id: form.organization_id || null
        }
      );

      setMessage(`Created sponsor ${result.sponsor.username}.`);

      setForm({
        ...blankUser,
        organization_id: "",
        organization_name: ""
      });
    });
  }

  function saveFee(sponsor) {
    run(async () => {
      await apiRequest(
        `/api/admin/sponsors/${sponsor.sponsor_id}/fee/`,
        "POST",
        {
          fee_percentage: fees[sponsor.sponsor_id]
        }
      );

      setMessage(`Updated fee for ${sponsor.username}.`);
    });
  }

  function setActive(user) {
    const action = user.is_active ? "deactivate" : "activate";

    if (!window.confirm(
      `Are you sure you want to ${action} ${user.username}?`
    )) {
      return;
    }

    run(async () => {
      await apiRequest(
        `/api/admin/users/${user.id}/status/`,
        "POST",
        { active: !user.is_active }
      );

      setMessage(`${user.username} updated.`);
    });
  }

  // Delete sponsor
  
  function remove(user) {
    run(async () => {
      await apiRequest(
        `/api/admin/users/${user.id}/delete/`,
        "POST"
      );

      setMessage(`Deleted ${user.username}.`);
      setDeleteId(null);
    });
  }


  function editSponsor(sponsor) {
    setEditingId(sponsor.id);

    setEditData({
      first_name: sponsor.first_name || "",
      last_name: sponsor.last_name || "",
      email: sponsor.email || ""
    });
  }

  function saveEdit(e, sponsor) {
    e.preventDefault();

    run(async () => {
      await apiRequest(
        `/api/admin/users/${sponsor.id}/edit/`,
        "POST",
        editData
      );

      setEditingId(null);
      setMessage("Sponsor updated.");
    });
  }

  return (
    <section className="admin-panel">
      <h1>Manage Sponsors</h1>

      <Note message={error} error />
      <Note message={message} error={actionError} />

      <div className="card">
        <h2>Create a sponsor</h2>

        <form onSubmit={create}>
          <NewUserFields form={form} setForm={setForm} />

          <div className="admin-form-grid">
            <label>
              Existing organization

              <select
                value={form.organization_id}
                onChange={e => setForm({
                  ...form,
                  organization_id: e.target.value,
                  organization_name: ""
                })}
              >
                <option value="">
                  Create a new organization instead
                </option>

                {organizations.filter(o => o.is_active).map(o => (
                  <option key={o.id} value={o.id}>
                    {o.name}
                  </option>
                ))}
              </select>
            </label>

            {!form.organization_id && (
              <label>
                New organization name

                <input
                  value={form.organization_name}
                  onChange={e => setForm({
                    ...form,
                    organization_name: e.target.value
                  })}
                  required
                />
              </label>
            )}
          </div>

          <button disabled={busy}>
            Create Sponsor
          </button>
        </form>
      </div>

      <h2>Sponsor Accounts</h2>

      {loading && <p>Loading sponsors...</p>}

      {!loading && sponsors.length === 0 && (
        <p>No sponsors yet.</p>
      )}

      <div className="admin-stack">
        {sponsors.map(s => (
          <div className="card" key={s.sponsor_id}>

            <h3>{s.username}</h3>
            <p>{s.organization || "No organization"}</p>
            <p>{s.email || "No email"}</p>
            <p>{s.is_active ? "Active" : "Inactive"}</p>

            <label>Fee percentage (1 = 1%)</label>

            <div className="admin-actions">
              <input
                type="number"
                min="0"
                max="100"
                step="0.01"
                value={fees[s.sponsor_id] ?? ""}
                onChange={e => setFees({
                  ...fees,
                  [s.sponsor_id]: e.target.value
                })}
              />

              <button
                type="button"
                disabled={busy}
                onClick={() => saveFee(s)}
              >
                Save Fee
              </button>

              <button
                type="button"
                disabled={busy}
                onClick={() => setActive(s)}
              >
                {s.is_active ? "Deactivate" : "Activate"}
              </button>

              <button
                type="button"
                disabled={busy}
                className="danger"
                onClick={() => {
                  setDeleteId(s.id);
                  setDeleteText("");
                  setMessage("");
                  setActionError(false);
                }}
              >
                Delete
              </button>

              <button
                type="button"
                disabled={busy}
                onClick={() => editSponsor(s)}
              >
                Edit
              </button>
            </div>

            
            {/* Delete confirmation */}
            {deleteId === s.id && (
              <div className="card">
                <h3>Delete Sponsor</h3>

                <p>
                  Are you sure you want to delete
                  {" "}{s.username} permanently?
                </p>

                <div className="admin-actions">
                  <button
                    type="button"
                    className="danger"
                    disabled={busy}
                    onClick={() => remove(s)}
                  >
                    Yes, Delete
                  </button>

                  <button
                    type="button"
                    disabled={busy}
                    onClick={() => setDeleteId(null)}
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}


            {/* Edit sponsor */}
            {editingId === s.id && (
              <form onSubmit={e => saveEdit(e, s)}>
                <h3>Edit Sponsor</h3>

                <label>First Name</label>
                <input
                  value={editData.first_name}
                  onChange={e => setEditData({
                    ...editData,
                    first_name: e.target.value
                  })}
                />

                <label>Last Name</label>
                <input
                  value={editData.last_name}
                  onChange={e => setEditData({
                    ...editData,
                    last_name: e.target.value
                  })}
                />

                <label>Email</label>
                <input
                  type="email"
                  value={editData.email}
                  onChange={e => setEditData({
                    ...editData,
                    email: e.target.value
                  })}
                  required
                />

                <button type="submit" disabled={busy}>
                  Save
                </button>

                <button
                  type="button"
                  onClick={() => setEditingId(null)}
                >
                  Cancel
                </button>
              </form>
            )}

          </div>
        ))}
      </div>
    </section>
  );
}




function Drivers() {
  const { drivers, sponsors, loading, error, load } = useDirectory();
  const [selection, setSelection] = useState({});
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [actionError, setActionError] = useState(false);

  const [editingId, setEditingId] = useState(null);
  const [editData, setEditData] = useState({});

  async function run(fn) {
    setBusy(true);
    setMessage("");

    try {
      await fn();
      setActionError(false);
      await load();
    } catch (err) {
      setActionError(true);
      setMessage(err.message);
    } finally {
      setBusy(false);
    }
  }

  function assign(driver) {
    const sponsorId = Number(selection[driver.driver_id]);

    if (!sponsorId) {
      setActionError(true);
      setMessage("Select a sponsor first.");
      return;
    }

    const oldOrg = driver.organizations.map(o => o.name).join(", ") || "none";

    if (!window.confirm(`Assign ${driver.username} to the selected sponsor? Current organization: ${oldOrg}. Other active memberships will be removed.`)) {
      return;
    }

    run(async () => {
      await apiRequest(
        `/api/admin/drivers/${driver.driver_id}/assign/`,
        "POST",
        { sponsor_id: sponsorId }
      );

      setMessage(`Assigned ${driver.username}.`);
    });
  }

  function reset(driver) {
    if (!window.confirm(`Email a password reset link to ${driver.username}?`)) {
      return;
    }

    run(async () => {
      const data = await apiRequest(
        `/api/admin/drivers/${driver.driver_id}/reset-password/`,
        "POST"
      );

      setMessage(data.message);
    });
  }

  function deactivate(driver) {
    if (!window.confirm(`${driver.is_active ? "Deactivate" : "Reactivate"} ${driver.username}?`)) {
      return;
    }

    run(async () => {
      await apiRequest(
        `/api/admin/users/${driver.id}/status/`,
        "POST",
        { active: !driver.is_active }
      );

      setMessage(`Updated ${driver.username}.`);
    });
  }

  function remove(driver) {
    const typed = window.prompt(
      `Delete driver ${driver.username} permanently? Type the username to confirm:`
    );

    if (typed !== driver.username) return;

    run(async () => {
      await apiRequest(
        `/api/admin/users/${driver.id}/delete/`,
        "POST"
      );

      setMessage(`Deleted ${driver.username}.`);
    });
  }

  function editDriver(driver) {
    setEditingId(driver.id);

    setEditData({
      first_name: driver.first_name || "",
      last_name: driver.last_name || "",
      email: driver.email || ""
    });
  }

  function saveEdit(e, driver) {
    e.preventDefault();

    run(async () => {
      await apiRequest(
        `/api/admin/users/${driver.id}/edit/`,
        "POST",
        editData
      );

      setEditingId(null);
      setMessage("Driver updated.");
    });
  }

  return (
    <section className="admin-panel">
      <h1>Manage Drivers</h1>

      <p>
        Each driver has one active sponsor organization.
        Assigning a different sponsor replaces their current membership,
        but retains historical orders and point balances.
      </p>

      <Note message={error} error />
      <Note message={message} error={actionError} />

      {loading && <p>Loading drivers...</p>}

      {!loading && drivers.length === 0 && (
        <p>No drivers yet.</p>
      )}

      <div className="admin-stack">
        {drivers.map(d => (
          <div className="card" key={d.driver_id}>

            <h3>{d.username}</h3>
            <p>{d.email || "No email"} - {d.is_active ? "Active" : "Inactive"}</p>
            <p>
              Organization: {d.organizations.map(o => o.name).join(", ") || "Unassigned"}
            </p>

            <label>Select sponsor to assign</label>

            <div className="admin-actions">
              <select
                value={selection[d.driver_id] || ""}
                onChange={e => setSelection({
                  ...selection,
                  [d.driver_id]: e.target.value
                })}
              >
                <option value="">Choose sponsor</option>

                {sponsors.filter(s => s.is_active && s.organization_id).map(s => (
                  <option key={s.sponsor_id} value={s.sponsor_id}>
                    {s.username} ({s.organization})
                  </option>
                ))}
              </select>

              <button disabled={busy} onClick={() => assign(d)}>
                Assign Sponsor
              </button>

              <button disabled={busy} onClick={() => reset(d)}>
                Send Password Reset
              </button>

              <button disabled={busy} onClick={() => deactivate(d)}>
                {d.is_active ? "Deactivate" : "Activate"}
              </button>

              <button disabled={busy} className="danger" onClick={() => remove(d)}>
                Delete
              </button>

              <button disabled={busy} onClick={() => editDriver(d)}>
                Edit
              </button>
            </div>

            {editingId === d.id && (
              <form onSubmit={e => saveEdit(e, d)}>
                <h3>Edit Driver</h3>

                <label>First Name</label>
                <input
                  value={editData.first_name}
                  onChange={e => setEditData({
                    ...editData,
                    first_name: e.target.value
                  })}
                />

                <label>Last Name</label>
                <input
                  value={editData.last_name}
                  onChange={e => setEditData({
                    ...editData,
                    last_name: e.target.value
                  })}
                />

                <label>Email</label>
                <input
                  type="email"
                  value={editData.email}
                  onChange={e => setEditData({
                    ...editData,
                    email: e.target.value
                  })}
                  required
                />

                <button type="submit" disabled={busy}>
                  Save
                </button>

                <button
                  type="button"
                  onClick={() => setEditingId(null)}
                >
                  Cancel
                </button>
              </form>
            )}

          </div>
        ))}
      </div>
    </section>
  );
}


function Preview() {
  const { sponsors, drivers, error, loading } = useDirectory();
  const [role, setRole] = useState("sponsor");
  const [userId, setUserId] = useState("");
  const [data, setData] = useState(null);
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const choices = role === "sponsor" ? sponsors : drivers;
  async function load(event) {
    event.preventDefault();
    setBusy(true);
    setData(null);
    setMessage("");
    try { setData(await apiRequest(`/api/admin/preview/${role}/${userId}/`)); }
    catch (err) { setMessage(err.message); }
    finally { setBusy(false); }
  }
  return (
    <section className="admin-panel">
      <h1>View as Sponsor / Driver</h1>
      <p>This is a read-only preview of the account's data. You remain logged in as an admin, so no one else's actions or permissions are assumed.</p>
      <Note message={error || message} error />
      <div className="card">
        <form onSubmit={load}>
          <div className="admin-form-grid">
            <label>View role
              <select value={role} onChange={e => { setRole(e.target.value); setUserId(""); setData(null); }}>
                <option value="sponsor">Sponsor</option><option value="driver">Driver</option>
              </select>
            </label>
            <label>Account
              <select value={userId} onChange={e => setUserId(e.target.value)} required>
                <option value="">Choose account</option>
                {choices.map(u => <option key={u.id} value={u.id}>{u.username}</option>)}
              </select>
            </label>
          </div>
          <button disabled={busy || loading || !userId}>View Account</button>
        </form>
      </div>
      {data && <div className="card admin-preview">
        <h2>{data.account.username} ({data.role})</h2>
        <p>Email: {data.account.email || "None"}</p>
        {data.role === "sponsor" ? <>
          <p>Organization: {data.account.organization || "None"}</p>
          <p>Fee: {data.account.fee_percentage}%</p>
          <p>Pending applications: {data.pending_applications}</p>
          <h3>Drivers</h3><p>{data.drivers.join(", ") || "None"}</p>
          <h3>Available products</h3>
          <ul>{data.products.map((p, i) => <li key={i}>{p.name} — {p.points} points</li>)}</ul>
        </> : <>
          <p>Organizations: {data.account.organizations.map(o => o.name).join(", ") || "None"}</p>
          <h3>Point balances</h3>
          <ul>{data.balances.map((b, i) => <li key={i}>{b.organization}: {b.points} points</li>)}</ul>
          <h3>Recent orders</h3>
          <ul>{data.orders.map(o => <li key={o.id}>Order {o.id}: {o.status} ({o.points} points)</li>)}</ul>
        </>}
      </div>}
    </section>
  );
}


function Admins() {
  const { admins, error, load } = useDirectory();

  const [form, setForm] = useState({ ...blankUser });
  const [message, setMessage] = useState("");
  const [failed, setFailed] = useState(false);
  const [busy, setBusy] = useState(false);

  const [editingId, setEditingId] = useState(null);
  const [editData, setEditData] = useState({});

  async function create(e) {
    e.preventDefault();
    setBusy(true);
    setMessage("");

    try {
      const result = await apiRequest(
        "/api/admin/admins/create/",
        "POST",
        form
      );

      setForm({ ...blankUser });
      setFailed(false);
      setMessage(`Created admin ${result.admin.username}.`);
      await load();
    } catch (err) {
      setFailed(true);
      setMessage(err.message);
    } finally {
      setBusy(false);
    }
  }

  function editAdmin(admin) {
    setEditingId(admin.id);

    setEditData({
      first_name: admin.first_name || "",
      last_name: admin.last_name || "",
      email: admin.email || ""
    });
  }

  async function saveEdit(e, admin) {
    e.preventDefault();
    setBusy(true);
    setMessage("");

    try {
      await apiRequest(
        `/api/admin/users/${admin.id}/edit/`,
        "POST",
        editData
      );

      setMessage("Admin updated.");
      setFailed(false);
      setEditingId(null);
      await load();
    } catch (err) {
      setFailed(true);
      setMessage(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="admin-panel">
      <h1>Admin Accounts</h1>

      <Note message={error} error />
      <Note message={message} error={failed} />

      <div className="card">
        <h2>Create an Administrator</h2>

        <form onSubmit={create}>
          <NewUserFields form={form} setForm={setForm} />

          <button disabled={busy}>
            Create Admin
          </button>
        </form>
      </div>

      <h2>Existing Administrators</h2>

      <div className="admin-stack">
        {admins.map(a => (
          <div className="card" key={a.id}>
            <h3>{a.username}</h3>
            <p>{a.email || "No email"}</p>
            <p>{a.is_active ? "Active" : "Inactive"}</p>

            <button
              disabled={busy}
              onClick={() => editAdmin(a)}
            >
              Edit
            </button>

            {editingId === a.id && (
              <form onSubmit={e => saveEdit(e, a)}>
                <h3>Edit Admin</h3>

                <label>First Name</label>
                <input
                  value={editData.first_name}
                  onChange={e => setEditData({
                    ...editData,
                    first_name: e.target.value
                  })}
                />

                <label>Last Name</label>
                <input
                  value={editData.last_name}
                  onChange={e => setEditData({
                    ...editData,
                    last_name: e.target.value
                  })}
                />

                <label>Email</label>
                <input
                  type="email"
                  value={editData.email}
                  onChange={e => setEditData({
                    ...editData,
                    email: e.target.value
                  })}
                  required
                />

                <button type="submit" disabled={busy}>
                  Save
                </button>

                <button
                  type="button"
                  onClick={() => setEditingId(null)}
                >
                  Cancel
                </button>
              </form>
            )}
          </div>
        ))}
      </div>
    </section>
  );
}


function Organizations() {
  const { organizations, loading, error, load } = useDirectory();

  const [editingId, setEditingId] = useState(null);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);

  function editOrg(org) {
    setEditingId(org.id);
    setName(org.name);
    setDescription(org.description || "");
    setMessage("");
  }

  async function saveOrg(e, org) {
    e.preventDefault();
    setBusy(true);
    setMessage("");

    try {
      await apiRequest(
        `/api/admin/organizations/${org.id}/edit/`,
        "POST",
        { name, description }
      );

      setMessage("Organization updated.");
      setEditingId(null);
      await load();
    } catch (err) {
      setMessage(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="admin-panel">
      <h1>Manage Organizations</h1>

      {error && <p className="error">{error}</p>}
      {message && <p>{message}</p>}
      {loading && <p>Loading...</p>}

      <div className="admin-stack">
        {organizations.map(org => (
          <div className="card" key={org.id}>
            <h3>{org.name}</h3>
            <p>{org.description || "No description"}</p>
            <p>{org.is_active ? "Active" : "Inactive"}</p>

            <button onClick={() => editOrg(org)}>
              Edit
            </button>

            {editingId === org.id && (
              <form onSubmit={e => saveOrg(e, org)}>
                <h3>Edit Organization</h3>

                <label>Name</label>
                <input
                  value={name}
                  onChange={e => setName(e.target.value)}
                  required
                />

                <label>Description</label>
                <textarea
                  value={description}
                  onChange={e => setDescription(e.target.value)}
                />

                <button disabled={busy} type="submit">
                  Save
                </button>

                <button
                  type="button"
                  onClick={() => setEditingId(null)}
                >
                  Cancel
                </button>
              </form>
            )}
          </div>
        ))}
      </div>
    </section>
  );
}


function Reports() {
  const kinds = [
    ["Sponsor accounts and fees", "sponsors"],
    ["Driver accounts", "drivers"],
    ["Driver points", "points"],
    ["Orders", "orders"],
  ];
  return <section className="admin-panel">
    <h1>Admin Reports</h1>
    <p>Download each report as a CSV that you can open in Excel. You can also use the existing audit log download endpoint.</p>
    <div className="admin-stack">{kinds.map(([title, kind]) => (
      <div className="card admin-report" key={kind}>
        <strong>{title}</strong>
        <a href={`/api/admin/reports/${kind}/`} download>Download CSV</a>
      </div>
    ))}</div>
    <div className="card admin-report"><strong>Audit log</strong>
      <a href="/api/audit-logs/download/" download>Download Audit CSV</a>
    </div>
  </section>;
}

export default function AdminPanel({ view = "dashboard" }) {
  if (view === "sponsors") return <Sponsors />;
  if (view === "drivers") return <Drivers />;
  if (view === "preview") return <Preview />;
  if (view === "admins") return <Admins />;
  if (view === "reports") return <Reports />;
  if (view === "organizations") return <Organizations />;
  return <Dashboard />;
}