import OriginalAdminPanel from "./AdminPanelOriginal";
import AdminReportsPage from "./AdminReportsPage";

export default function AdminPanel({ view = "dashboard" }) {
  if (view === "reports") {
    return <AdminReportsPage />;
  }

  return <OriginalAdminPanel view={view} />;
}
