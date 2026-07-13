import { useEffect, useState } from "react";
import {
  addRepository,
  deleteRepository,
  listRepositories,
  reindexRepository,
} from "../api/repositories";
import StatusBadge from "../components/StatusBadge";
import type { Repository, RepositoryCreate } from "../types";

export default function RepositoriesPage() {
  const [repos, setRepos] = useState<Repository[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [error, setError] = useState("");
  const [form, setForm] = useState<RepositoryCreate>({
    name: "",
    url: "",
    description: "",
    branch: "main",
  });
  const [submitting, setSubmitting] = useState(false);

  async function load() {
    const data = await listRepositories();
    setRepos(data);
    setLoading(false);
  }

  useEffect(() => {
    load();
    // Poll status every 5s while any repo is being processed
    const interval = setInterval(() => {
      const busy = repos.some((r) =>
        ["cloning", "indexing", "pending"].includes(r.status)
      );
      if (busy) load();
    }, 5000);
    return () => clearInterval(interval);
  }, [repos]);

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      const repo = await addRepository(form);
      setRepos((prev) => [repo, ...prev]);
      setShowForm(false);
      setForm({ name: "", url: "", description: "", branch: "main" });
    } catch {
      setError("Failed to add repository.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(id: string) {
    if (!confirm("Delete this repository and all its indexed data?")) return;
    await deleteRepository(id);
    setRepos((prev) => prev.filter((r) => r.id !== id));
  }

  async function handleReindex(id: string) {
    await reindexRepository(id);
    setRepos((prev) =>
      prev.map((r) => (r.id === id ? { ...r, status: "pending" } : r))
    );
  }

  return (
    <div className="page">
      <div className="section-header">
        <h1>Repositories</h1>
        <button className="btn btn-primary" onClick={() => setShowForm((v) => !v)}>
          {showForm ? "Cancel" : "+ Add Repository"}
        </button>
      </div>

      {showForm && (
        <form className="card form-card" onSubmit={handleAdd}>
          <h2>Add Repository</h2>
          {error && <div className="alert alert-error">{error}</div>}
          <label>Name</label>
          <input
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            required
          />
          <label>Git URL</label>
          <input
            value={form.url}
            onChange={(e) => setForm({ ...form, url: e.target.value })}
            placeholder="https://github.com/owner/repo.git"
            required
          />
          <label>Description (optional)</label>
          <input
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
          />
          <label>Branch</label>
          <input
            value={form.branch}
            onChange={(e) => setForm({ ...form, branch: e.target.value })}
          />
          <button type="submit" className="btn btn-primary" disabled={submitting}>
            {submitting ? "Adding…" : "Add & Index"}
          </button>
        </form>
      )}

      {loading ? (
        <p>Loading…</p>
      ) : repos.length === 0 ? (
        <div className="empty-state">No repositories added yet.</div>
      ) : (
        <table className="table">
          <thead>
            <tr>
              <th>Name</th>
              <th>URL</th>
              <th>Branch</th>
              <th>Progress</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {repos.map((repo) => (
              <tr key={repo.id}>
                <td>
                  <strong>{repo.name}</strong>
                  {repo.description && (
                    <div style={{ fontSize: "0.8rem", color: "#6b7280" }}>
                      {repo.description}
                    </div>
                  )}
                </td>
                <td>
                  <a href={repo.url} target="_blank" rel="noreferrer">
                    {repo.url.replace("https://github.com/", "")}
                  </a>
                </td>
                <td>{repo.branch}</td>
                <td>
                  {repo.indexed_files} / {repo.total_files} files
                </td>
                <td>
                  <StatusBadge status={repo.status} />
                  {repo.error_message && (
                    <div style={{ fontSize: "0.75rem", color: "#ef4444" }}>
                      {repo.error_message}
                    </div>
                  )}
                </td>
                <td className="action-cell">
                  <button
                    className="btn btn-sm"
                    onClick={() => handleReindex(repo.id)}
                    disabled={["cloning", "indexing"].includes(repo.status)}
                  >
                    Reindex
                  </button>
                  <button
                    className="btn btn-sm btn-danger"
                    onClick={() => handleDelete(repo.id)}
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
