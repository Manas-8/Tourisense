function Topbar({ user, onLogout }) {
  return (
    <header className="topbar">
      <div>
        <h2>Tourism intelligence</h2>
        <p>Verified source datasets · historical reporting</p>
      </div>

      <div className="admin-profile">
        <div className="avatar">{user?.name?.[0] || "A"}</div>

        <div>
          <strong>{user?.name || "Administrator"}</strong>
          <small>Government administrator</small>
        </div>
        <button type="button" className="topbar-signout" onClick={onLogout}>Sign out</button>
      </div>
    </header>
  );
}

export default Topbar;
