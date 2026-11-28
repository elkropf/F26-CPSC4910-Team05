
import { useEffect, useState } from "react";
import { apiRequest } from "../api";
import "./AboutPage.css";

export default function AboutPage() {
  const [aboutData, setAboutData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    apiRequest("/api/about/")
      .then((data) => {
        if (data.error) {
          throw new Error(data.error);
        }
        setAboutData(data);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="about-page">
      <h1>About</h1>

      {loading && <p>Loading information...</p>}

      {error && (
        <p className="error">
          Could not load About information: {error}
        </p>
      )}

      {aboutData && (
        <>
          <h2>{aboutData.product_name}</h2>

          <p className="description">
            {aboutData.product_description}
          </p>

          <div className="about-info">
            <p>
              <strong>Team Number:</strong>{" "}
              {aboutData.team_number}
            </p>

            <p>
              <strong>Current Sprint:</strong>{" "}
              {aboutData.sprint_number}
            </p>

            <p>
              <strong>Release Date:</strong>{" "}
              {aboutData.release_date}
            </p>

            <p>
              <strong>Created:</strong>{" "}
              {aboutData.created_at
                ? new Date(
                    aboutData.created_at
                  ).toLocaleDateString()
                : "Not available"}
            </p>
          </div>
        </>
      )}
    </div>
  );
}
