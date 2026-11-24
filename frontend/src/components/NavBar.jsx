
import { NavLink } from "react-router-dom";

const menus = {
  driver: [
    ["Home", "/driver/home"],
    ["Apply", "/driver/apply"],
    ["Stores", "/driver/stores"],
    ["Orders", "/driver/orders"],
  ],

  sponsor: [
    ["Home", "/sponsor/home"],
    ["Drivers", "/sponsor/drivers"],
    ["Points", "/sponsor/points"],
    ["Stores", "/sponsor/stores"],
  ],

  admin: [
    ["Dashboard", "/admin/dashboard"],
    ["Sponsors", "/admin/sponsors"],
    ["Drivers", "/admin/drivers"],
    ["Reports", "/admin/reports"],
  ],
};

export default function Navbar({ role, username, onLogout }) {
  const links = role
    ? [
        ...(menus[role] || []),
        ["Notifications", "/notifications"],
        ["About", "/about"]
      ]
    : [
        ["Login", "/login"],
        ["Register", "/register"]
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
