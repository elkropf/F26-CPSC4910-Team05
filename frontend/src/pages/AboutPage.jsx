
const aboutData = {
  product_name: "Good Driver Incentive Program",
  product_description:
    "Our program rewards drivers for safe driving behavior. Sponsors can award points, and drivers can redeem their points for rewards.",
  team_number: "05",
  sprint_number: "6",
  release_date: "Not set",
  created_at: null,
};

function AboutPage() {
  return (
    <div className="about-page" style={{ padding: "40px" }}>
      <h1>About</h1>

      <h2>{aboutData.product_name}</h2>

      <p className="description">
        {aboutData.product_description}
      </p>

      <div className="about-info">
        <p>
          <strong>Team Number:</strong> {aboutData.team_number}
        </p>

        <p>
          <strong>Current Sprint:</strong> {aboutData.sprint_number}
        </p>

        <p>
          <strong>Release Date:</strong> {aboutData.release_date}
        </p>

        <p>
          <strong>Created:</strong>{" "}
          {aboutData.created_at
            ? new Date(aboutData.created_at).toLocaleDateString()
            : "Not set"}
        </p>
      </div>
    </div>
  );
}

export default AboutPage;
