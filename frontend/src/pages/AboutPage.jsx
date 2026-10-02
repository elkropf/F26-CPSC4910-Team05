return (
    <div className="about-page">
        <h1>About</h1>

        <h2>{aboutData.product_name}</h2>

        <p className="description">
            {aboutData.product_description}
        </p>

        <div className="about-info">
            <p><strong>Team Number:</strong> {aboutData.team_number}</p>

            <p><strong>Current Sprint:</strong> {aboutData.sprint_number}</p>

            <p><strong>Release Date:</strong> {aboutData.release_date}</p>

            <p>
                <strong>Created:</strong>{" "}
                {new Date(aboutData.created_at).toLocaleDateString()}
            </p>
        </div>
    </div>
)