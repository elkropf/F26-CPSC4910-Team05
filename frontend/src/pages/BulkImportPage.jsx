
import { useState } from "react";

function getCookie(name) {
  const cookies = document.cookie.split(";");

  for (const cookie of cookies) {
    const [key, ...value] = cookie.trim().split("=");

    if (key === name) {
      return decodeURIComponent(value.join("="));
    }
  }

  return "";
}

async function readResponse(response) {
  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(
      `${response.status}: ${data.error || data.detail || "Request failed"}`
    );
  }

  return data;
}

export default function BulkImportPage() {
  const [file, setFile] = useState(null);
  const [jobId, setJobId] = useState(null);
  const [status, setStatus] = useState(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function uploadFile(e) {
    e.preventDefault();

    if (!file) return;

    setBusy(true);
    setError("");
    setMessage("");

    try {
      if (!getCookie("csrftoken")) {
        await fetch("/api/auth/csrf/", {
          credentials: "same-origin"
        });
      }

      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch("/api/users/bulk-import/", {
        method: "POST",
        credentials: "same-origin",
        headers: {
          "X-CSRFToken": getCookie("csrftoken")
        },
        body: formData
      });

      const data = await readResponse(response);

      setJobId(data.job_id);
      setStatus(data);
      setMessage("File uploaded. Job #" + data.job_id + " is queued.");
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function checkStatus() {
    if (!jobId) return;

    setBusy(true);
    setError("");

    try {
      const response = await fetch(
        `/api/users/bulk-import/${jobId}/`,
        { credentials: "same-origin" }
      );

      const data = await readResponse(response);
      setStatus(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section>
      <h1>Bulk Import Users</h1>

      <div className="card">
        <h2>Upload File</h2>

        <p>
          Upload a pipe-separated text file with
          organizations, drivers, or sponsors.
        </p>

        <form onSubmit={uploadFile}>
          <input
            type="file"
            accept=".txt,text/plain"
            onChange={e => setFile(e.target.files[0] || null)}
          />

          <button type="submit" disabled={!file || busy}>
            {busy ? "Working..." : "Upload File"}
          </button>
        </form>

        {message && <p>{message}</p>}
        {error && <p style={{ color: "red" }}>{error}</p>}
      </div>

      {jobId && (
        <div className="card">
          <h2>Import Status</h2>

          <p>Job ID: {jobId}</p>
          <p>Status: {status?.status || "Unknown"}</p>
          <p>Processed: {status?.processed_rows ?? 0}</p>
          <p>Successful: {status?.successful_rows ?? 0}</p>
          <p>Failed: {status?.failed_rows ?? 0}</p>

          {status?.error && <p>{status.error}</p>}

          <button
            type="button"
            onClick={checkStatus}
            disabled={busy}
          >
            Refresh Status
          </button>

          {status?.results_available && (
            <p>
              <a href={`/api/users/bulk-import/${jobId}/results/`}>
                Download Results
              </a>
            </p>
          )}
        </div>
      )}
    </section>
  );
}
