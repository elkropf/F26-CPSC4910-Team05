
import { NavLink } from "react-router-dom";
import "./Navbar.css";

const navigation = {
  driver: [
    { name: "Home", path: "/driver/home" },
    { name: "Apply", path: "/driver/apply" },
    { name: "Applications", path: "/driver/applications" },
    { name: "Stores", path: "/driver/stores" },
    { name: "About", path: "/about" },
  ],

  sponsor: [
    { name: "Home", path: "/sponsor/home" },
    { name: "Applications", path: "/sponsor/applications" },
    { name: "Drivers", path: "/sponsor/drivers" },
    { name: "Points", path: "/sponsor/points" },
    { name: "Stores", path: "/sponsor/stores" },
    { name: "About", path: "/about" },
  ],

  admin: [
    { name: "Dashboard", path: "/admin/dashboard" },
    { name: "Sponsors", path: "/admin/sponsors" },
    { name: "Sponsor Preview", path: "/admin/sponsor-preview" },
    { name: "About", path: "/about" },
  ],
};

function Navbar({ role }) {
  const links = navigation[role] || [];

  return (
    <header className="navbar">
      <h2>Good Driver Incentive Program</h2>

      <nav className="nav-links">
        {links.map((link) => (
          <NavLink
            key={link.path}
            to={link.path}
            className={({ isActive }) =>
              isActive ? "nav-link active" : "nav-link"
            }
          >
            {link.name}
          </NavLink>
        ))}
      </nav>
    </header>
  );
}

export default Navbar;
