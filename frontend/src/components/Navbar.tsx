import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate("/login");
  }

  return (
    <nav className="navbar">
      <Link to="/" className="navbar-brand">
        🔍 AI Code Review
      </Link>
      <div className="navbar-links">
        <Link to="/repositories">Repositories</Link>
        <Link to="/search">Search</Link>
        <Link to="/reviews">Reviews</Link>
      </div>
      <div className="navbar-user">
        <span>{user?.email}</span>
        <button onClick={handleLogout} className="btn btn-sm">
          Logout
        </button>
      </div>
    </nav>
  );
}
