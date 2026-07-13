import { useEffect, useState } from "react";
import { semanticSearch } from "../api/search";
import { listRepositories } from "../api/repositories";
import type { Repository, SearchResult } from "../types";

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [repoId, setRepoId] = useState("");
  const [repos, setRepos] = useState<Repository[]>([]);
  const [results, setResults] = useState<SearchResult[]>([]);
  const [searched, setSearched] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    listRepositories().then((data) => setRepos(data.filter((r) => r.status === "ready")));
  }, []);

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!query.trim()) return;
    setError("");
    setLoading(true);
    try {
      const res = await semanticSearch(query, repoId || undefined);
      setResults(res.results);
      setSearched(true);
    } catch {
      setError("Search failed. Make sure at least one repository is indexed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page">
      <h1>Semantic Code Search</h1>

      <form className="search-form" onSubmit={handleSearch}>
        <input
          className="search-input"
          type="text"
          placeholder="e.g. JWT authentication middleware"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          required
        />
        <select value={repoId} onChange={(e) => setRepoId(e.target.value)}>
          <option value="">All repositories</option>
          {repos.map((r) => (
            <option key={r.id} value={r.id}>
              {r.name}
            </option>
          ))}
        </select>
        <button type="submit" className="btn btn-primary" disabled={loading}>
          {loading ? "Searching…" : "Search"}
        </button>
      </form>

      {error && <div className="alert alert-error">{error}</div>}

      {searched && results.length === 0 && (
        <div className="empty-state">No results found.</div>
      )}

      <div className="results-list">
        {results.map((r) => (
          <div key={r.chunk_id} className="result-card">
            <div className="result-header">
              <span className="result-path">{r.file_path}</span>
              <span className="result-meta">
                Lines {r.start_line}–{r.end_line} &nbsp;|&nbsp;
                Score: {(r.similarity * 100).toFixed(1)}%
              </span>
            </div>
            <pre className="code-block">{r.content}</pre>
          </div>
        ))}
      </div>
    </div>
  );
}
