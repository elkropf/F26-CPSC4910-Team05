import { useEffect, useState } from "react";
import { apiRequest } from "../api";

export default function SponsorReportsPage() {
  const [kind, setKind] = useState("sponsor_points");
  const [drivers, setDrivers] = useState([]);
  const [driverId, setDriverId] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [category, setCategory] = useState("");
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    apiRequest("/api/reports/options/")
      .then((data) => setDrivers(data.drivers || []))
      .catch((err) => setError(err.message));
  }, []);

  function getUrl(csv = false) {
    const params = new URLSearchParams();
    if (kind === "sponsor_points" && driverId) params.set("driver_id", driverId);
    if (startDate) params.set("start_date", startDate);
    if (endDate) params.set("end_date", endDate);
    if (kind === "sponsor_audit" && category.trim()) params.set("action", category.trim());
    if (csv) params.set("format", "csv");
    return `/api/reports/${kind}/?${params.toString()}`;
  }

  async function generate(event) {
    event.preventDefault();
    setError("");
    setLoading(true);
    setReport(null);
    try {
      setReport(await apiRequest(getUrl()));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="admin-panel">
      <h1>Sponsor Reports</h1>
      <div className="card">
        <form onSubmit={generate}>
          <div className="admin-form-grid">
            <label>
              Report
              <select value={kind} onChange={(e) => { setKind(e.target.value); setReport(null); }}>
                <option value="sponsor_points">Driver Point Tracking</option>
                <option value="sponsor_audit">Sponsor Audit Log</option>
              </select>
            </label>
            {kind === "sponsor_points" && (
              <label>
                Driver
                <select value={driverId} onChange={(e) => setDriverId(e.target.value)}>
                  <option value="">All Drivers</option>
                  {drivers.map((driver) => (
                    <option key={driver.id} value={driver.id}>
                      {driver.name} ({driver.username})
                    </option>
                  ))}
                </select>
              </label>
            )}
            <label>
              Start Date
              <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} />
            </label>
            <label>
              End Date
              <input type="date" value={endDate} min={startDate || undefined}
                onChange={(e) => setEndDate(e.target.value)} />
            </label>
            {kind === "sponsor_audit" && (
              <label>
                Audit Category
                <input value={category} onChange={(e) => setCategory(e.target.value)}
                  placeholder="e.g. points or application" />
              </label>
            )}
          </div>
          <button type="submit" disabled={loading}>
            {loading ? "Loading..." : "Generate Report"}
          </button>
        </form>
      </div>

      {error && <p className="error" role="alert">{error}</p>}
      {report && (
        <div className="card" style={{ marginTop: 16 }}>
          <h2>{report.title}</h2>
          <p><a href={getUrl(true)} download>Download CSV</a></p>
          {Object.entries(report.totals || {}).map(([name, value]) => (
            <p key={name}><strong>{name}:</strong> {value}</p>
          ))}
          {report.rows.length === 0 ? (
            <p>No matching records.</p>
          ) : (
            <div style={{ overflowX: "auto" }}>
              <table className="drivers-table">
                <thead>
                  <tr>{report.columns.map((column) => <th key={column}>{column}</th>)}</tr>
                </thead>
                <tbody>
                  {report.rows.map((row, index) => (
                    <tr key={index}>
                      {report.columns.map((column) => (
                        <td key={column}>{String(row[column] ?? "")}</td>
                      ))}
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
