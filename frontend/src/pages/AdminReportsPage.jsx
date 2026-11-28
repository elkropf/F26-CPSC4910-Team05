import { useMemo, useState } from "react";

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
    </section>
  );
}
