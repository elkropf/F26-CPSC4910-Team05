
import { NavLink } from "react-router-dom";

const menus = {
  driver: [
    ["Home", "/driver/home"],
    ["Apply", "/driver/apply"],
    ["Applications", "/driver/applications"],
    ["Stores", "/driver/stores"],
  ],

  sponsor: [
    ["Home", "/sponsor/home"],
    ["Applications", "/sponsor/applications"],
    ["Drivers", "/sponsor/drivers"],
    ["Points", "/sponsor/points"],
    ["Stores", "/sponsor/stores"],
  ],

  admin: [
    ["Dashboard", "/admin/dashboard"],
    ["Sponsors", "/admin/sponsors"],
    ["Sponsor Preview", "/admin/sponsor-preview"],
  ],
};

export default function Navbar({ role, username, onLogout }) {
  const links = role
    ? [...(menus[role] || []), ["About", "/about"]]
    : [
        ["Login", "/login"],
        ["Register", "/register"],
      ];

  return (
    <header className="navbar">
      <div className="brand">
        Good Driver Incentive Program
      </div>

      <nav>
        {links.map(([label, path]) => (
          <NavLink
            key={path}
            to={path}
            className={({ isActive }) =>
              isActive ? "active" : ""
            }
          >
            {label}
          </NavLink>
        ))}
      </nav>

      {role && (
        <div className="account">
          <span>{username} ({role})</span>
          <button onClick={onLogout}>Logout</button>
        </div>
      )}
    </header>
  );
}
