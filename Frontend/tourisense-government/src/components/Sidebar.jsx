import {
  LayoutDashboard,
  MapPin,
  Users,
  Hotel,
  Bus,
  BarChart3,
  Settings
} from "lucide-react";

function Sidebar({ currentPage, setCurrentPage }) {

  const menuItems = [
    {
      name: "Dashboard",
      icon: LayoutDashboard,
      page: "dashboard"
    },
    {
      name: "Destinations",
      icon: MapPin,
      page: "destinations"
    },
    {
      name: "Crowd Monitoring",
      icon: Users,
      page: "crowd"
    },
    {
      name: "Hotels",
      icon: Hotel,
      page: "hotels"
    },
    {
      name: "Transport",
      icon: Bus,
      page: "transport"
    },
    {
      name: "Tourism Intelligence",
      icon: BarChart3,
      page: "analytics"
    },
    {
      name: "Settings",
      icon: Settings,
      page: "settings"
    }
  ];

  return (
    <aside className="sidebar">

      <div className="logo">
        <h2>TouriSense</h2>
        <p>Government Portal</p>
      </div>

      <nav>

        {menuItems.map((item) => {

          const Icon = item.icon;

          return (
            <button
              key={item.page}
              className={currentPage === item.page ? "active" : ""}
              aria-current={currentPage === item.page ? "page" : undefined}
              onClick={() => setCurrentPage(item.page)}
            >
              <Icon size={18} />
              {item.name}
            </button>
          );

        })}

      </nav>

    </aside>
  );
}

export default Sidebar;
