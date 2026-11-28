import { useEffect, useMemo, useState } from "react";
import { apiRequest } from "../api";

const REPORTS = [
  { name: "Sponsor Accounts", kind: "sponsors" },
  { name: "Driver Accounts", kind: "drivers" },
  { name: "Driver Point Balances", kind: "points" },
  { name: "Orders", kind: "orders" },
];

function parseCSV(text) {
  const data = [];
  let row = [];
  let field = "";
  let quoted = false;

  for (let i = 0; i < text.length; i += 1) {
    const char = text[i];
    if (char === '"') {
      if (quoted && text[i + 1] === '"') {
        field += '"';
        i += 1;
      } else {
        quoted = !quoted;
      }
    } else if (char === "," && !quoted) {
      row.push(field);
      field = "";
    } else if (char === "\n" && !quoted) {
      row.push(field);
      if (row.some((value) => value.trim())) data.push(row);
      row = [];
      field = "";
    } else if (char !== "\r" || quoted) {
      field += char;
    }
  }

  row.push(field);
  if (row.some((value) => value.trim())) data.push(row);
  const headers = data[0] || [];
  const rows = data.slice(1).map((values) =>
    Object.fromEntries(headers.map((header, index) => [header, values[index] || ""]))
  );
  return { headers, rows };
}


// Required sales, invoice, and audit reports. Existing CSV reports remain unchanged.
const REQUIRED_REPORTS = [
  { name: "Sales by Sponsor", kind: "admin_sales_sponsor" },
  { name: "Sales by Driver", kind: "admin_sales_driver" },
  { name: "Sponsor Invoices", kind: "admin_invoices" },
  { name: "Admin Audit Log", kind: "admin_audit" },
];

function RequiredAdminReports() {
  const [kind, setKind] = useState("admin_sales_sponsor");
  const [organizations, setOrganizations] = useState([]);
  const [drivers, setDrivers] = useState([]);
  const [organizationId, setOrganizationId] = useState("");
  const [driverId, setDriverId] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [view, setView] = useState("detail");
  const [action, setAction] = useState("");
  const [report, setReport] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    apiRequest("/api/reports/options/")
      .then((data) => {
        setOrganizations(data.organizations || []);
        setDrivers(data.drivers || []);
      })
      .catch((err) => setError(err.message));
  }, []);

  const shownDrivers = organizationId
    ? drivers.filter((driver) => driver.organization_ids?.includes(Number(organizationId)))
    : drivers;

  function reportUrl(csv = false) {
    const params = new URLSearchParams();
    if (organizationId) params.set("organization_id", organizationId);
    if (kind === "admin_sales_driver" && driverId) params.set("driver_id", driverId);
    if (startDate) params.set("start_date", startDate);
    if (endDate) params.set("end_date", endDate);
    if (kind === "admin_audit" && action.trim()) params.set("action", action.trim());
    params.set("view", view);
    if (csv) params.set("format", "csv");
    return `/api/reports/${kind}/?${params.toString()}`;
  }

  async function generate(event) {
    event.preventDefault();
    setError("");
    setReport(null);
    setLoading(true);
    try {
      setReport(await apiRequest(reportUrl()));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="card" style={{ marginTop: 20 }}>
      <h2>Sales, Invoices, and Audit Reports</h2>
      <form onSubmit={generate}>
        <div className="admin-form-grid">
          <label>Report
            <select value={kind} onChange={(e) => { setKind(e.target.value); setReport(null); }}>
              {REQUIRED_REPORTS.map((option) => (
                <option value={option.kind} key={option.kind}>{option.name}</option>
              ))}
            </select>
          </label>
          <label>Sponsor
            <select value={organizationId} onChange={(e) => { setOrganizationId(e.target.value); setDriverId(""); }}>
              <option value="">All sponsors</option>
              {organizations.map((org) => <option key={org.id} value={org.id}>{org.name}</option>)}
            </select>
          </label>
          {kind === "admin_sales_driver" && (
            <label>Driver
              <select value={driverId} onChange={(e) => setDriverId(e.target.value)}>
                <option value="">All drivers</option>
                {shownDrivers.map((driver) => (
                  <option key={driver.id} value={driver.id}>{driver.name} ({driver.username})</option>
                ))}
              </select>
            </label>
          )}
          <label>Start date
            <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} />
          </label>
          <label>End date
            <input type="date" min={startDate || undefined} value={endDate} onChange={(e) => setEndDate(e.target.value)} />
          </label>
          {kind.startsWith("admin_sales_") && (
            <label>View
              <select value={view} onChange={(e) => setView(e.target.value)}>
                <option value="detail">Detailed</option>
                <option value="summary">Summary</option>
              </select>
            </label>
          )}
          {kind === "admin_audit" && (
            <label>Audit category
              <input value={action} onChange={(e) => setAction(e.target.value)} placeholder="e.g. points" />
            </label>
          )}
        </div>
        <button type="submit" disabled={loading}>{loading ? "Loading..." : "Generate Report"}</button>
      </form>
      {error && <p role="alert" className="error">{error}</p>}
      {report && (
        <div style={{ marginTop: 16 }}>
          <h3>{report.title}</h3>
          <p><a href={reportUrl(true)} download>Download filtered CSV</a></p>
          {Object.entries(report.totals || {}).map(([name, value]) => (
            <p key={name}><strong>{name}:</strong> {value}</p>
          ))}
          {report.rows.length === 0 ? (
            <p>No matching records.</p>
          ) : (
            <div style={{ overflowX: "auto" }}>
              <table className="drivers-table">
                <thead><tr>{report.columns.map((column) => <th key={column}>{column}</th>)}</tr></thead>
                <tbody>
                  {report.rows.map((row, index) => (
                    <tr key={index}>
                      {report.columns.map((column) => <td key={column}>{String(row[column] ?? "")}</td>)}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function AdminReportsPage() {
  const [kind, setKind] = useState("orders");
  const [report, setReport] = useState({ headers: [], rows: [] });
  const [search, setSearch] = useState("");
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");
  const [summary, setSummary] = useState(false);
  const [loading, setLoading] = useState(false);
  const [loadedKind, setLoadedKind] = useState("");
  const [error, setError] = useState("");

  async function loadReport(nextKind = kind) {
    setLoading(true);
    setError("");
    setLoadedKind("");
    setReport({ headers: [], rows: [] });

    try {
      const response = await fetch(`/api/admin/reports/${nextKind}/`, {
        credentials: "same-origin",
      });
      if (!response.ok) throw new Error(`Could not load report (${response.status}).`);
      setReport(parseCSV(await response.text()));
      setLoadedKind(nextKind);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  const filtered = useMemo(() => {
    return report.rows.filter((row) => {
      const matchesText = Object.values(row).some((value) =>
        String(value).toLowerCase().includes(search.toLowerCase())
      );
      const dateValue = String(row.Created || row.Date || "").slice(0, 10);
      const matchesDate = !dateValue || ((!start || dateValue >= start) && (!end || dateValue <= end));
      return matchesText && matchesDate;
    });
  }, [report.rows, search, start, end]);

  const groupColumn = report.headers.includes("Organization")
    ? "Organization"
    : report.headers.includes("Driver")
      ? "Driver"
      : report.headers[0];

  const grouped = useMemo(() => {
    const groups = new Map();
    filtered.forEach((row) => {
      const name = row[groupColumn] || "Unspecified";
      const current = groups.get(name) || { name, count: 0, total: 0 };
      current.count += 1;
      current.total += Number(row.Points || row.Balance || 0) || 0;
      groups.set(name, current);
    });
    return [...groups.values()];
  }, [filtered, groupColumn]);

  return (
    <section className="admin-panel">
      <h1>Admin Reports</h1>
      <p>View existing reports on screen, filter them, and download the original CSV files.</p>

      <div className="card" style={{ marginBottom: 16 }}>
        <label htmlFor="report-kind">Report</label>
        <select
          id="report-kind"
          value={kind}
          onChange={(e) => {
            setKind(e.target.value);
            setReport({ headers: [], rows: [] });
            setLoadedKind("");
            setSummary(false);
            setError("");
          }}
        >
          {REPORTS.map((item) => (
            <option key={item.kind} value={item.kind}>{item.name}</option>
          ))}
        </select>
        <div className="button-row" style={{ marginTop: 12 }}>
          <button onClick={() => loadReport()} disabled={loading}>
            {loading ? "Loading..." : "View Report"}
          </button>
          <a href={`/api/admin/reports/${kind}/`} download>Download CSV</a>
          <a href="/api/audit-logs/download/" download>Download Audit Log CSV</a>
        </div>
      </div>

      {error && <p className="error">{error}</p>}

      {loadedKind === kind && (
        <>
          <div className="card" style={{ marginBottom: 16 }}>
            <label htmlFor="report-search">Search report</label>
            <input
              id="report-search"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search driver, sponsor, status..."
            />
            {report.headers.includes("Created") && (
              <div className="button-row" style={{ marginTop: 10 }}>
                <label>From <input type="date" value={start} onChange={(e) => setStart(e.target.value)} /></label>
                <label>To <input type="date" value={end} onChange={(e) => setEnd(e.target.value)} /></label>
              </div>
            )}
            <label style={{ display: "block", marginTop: 10 }}>
              <input type="checkbox" checked={summary} onChange={(e) => setSummary(e.target.checked)} />
              {" "}Summary view
            </label>
            <p>Showing {filtered.length} of {report.rows.length} records.</p>
          </div>

          <div className="card" style={{ overflowX: "auto" }}>
            {filtered.length === 0 ? (
              <p>No matching records.</p>
            ) : summary ? (
              <table className="drivers-table">
                <thead><tr><th>{groupColumn}</th><th>Records</th><th>Points / Balance Total</th></tr></thead>
                <tbody>
                  {grouped.map((item) => (
                    <tr key={item.name}>
                      <td>{item.name}</td>
                      <td>{item.count}</td>
                      <td>{item.total.toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <table className="drivers-table">
                <thead>
                  <tr>{report.headers.map((header) => <th key={header}>{header}</th>)}</tr>
                </thead>
                <tbody>
                  {filtered.map((row, index) => (
                    <tr key={index}>
                      {report.headers.map((header) => (
                        <td key={header}>{row[header]}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </>
      )}
      <RequiredAdminReports />
    </section>
  );
}
