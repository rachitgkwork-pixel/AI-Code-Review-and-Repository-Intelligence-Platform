import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listRepositories } from "../api/repositories";
import { useAuth } from "../context/AuthContext";
import StatusBadge from "../components/StatusBadge";
import type { Repository } from "../types";

export default function DashboardPage() {
  const { user } = useAuth();
  const [repos, setRepos] = useState<Repository[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    listRepositories()
      .then(setRepos)
      .finally(() => setLoading(false));
  }, []);

  const ready = repos.filter((r) => r.status === "ready").length;
  const indexing = repos.filter((r) =>
    ["cloning", "indexing"].includes(r.status)
  ).length;

  return (
    <div className="page">
      <h1>Welcome, {user?.full_name ?? user?.email}</h1>

      <div className="stats-row">
        <div className="stat-card">
          <div className="stat-value">{repos.length}</div>
          <div className="stat-label">Repositories</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{ready}</div>
          <div className="stat-label">Ready</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{indexing}</div>
          <div className="stat-label">Indexing</div>
        </div>
      </div>

      <div className="section-header">
        <h2>Recent Repositories</h2>
        <Link to="/repositories" className="btn btn-primary">
          + Add Repository
        </Link>
      </div>

      {loading ? (
        <p>Loading…</p>
      ) : repos.length === 0 ? (
        <div className="empty-state">
          <p>No repositories yet.</p>
          <Link to="/repositories" className="btn btn-primary">
            Add your first repository
          </Link>
        </div>
      ) : (
        <table className="table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Branch</th>
              <th>Files indexed</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {repos.slice(0, 5).map((repo) => (
              <tr key={repo.id}>
                <td>
                  <strong>{repo.name}</strong>
                </td>
                <td>{repo.branch}</td>
                <td>
                  {repo.indexed_files} / {repo.total_files}
                </td>
                <td>
                  <StatusBadge status={repo.status} />
                </td>
                <td>
                  <Link to={`/reviews?repo=${repo.id}`} className="btn btn-sm">
                    Review
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
