import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { reviewRepository, reviewFile } from "../api/reviews";
import { listRepositories } from "../api/repositories";
import SeverityBadge from "../components/SeverityBadge";
import type { Repository, ReviewResponse } from "../types";

export default function ReviewsPage() {
  const [searchParams] = useSearchParams();
  const [repos, setRepos] = useState<Repository[]>([]);
  const [repoId, setRepoId] = useState(searchParams.get("repo") ?? "");
  const [filePath, setFilePath] = useState("");
  const [reviewType, setReviewType] = useState<"repository" | "file">("repository");
  const [review, setReview] = useState<ReviewResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    listRepositories().then((data) =>
      setRepos(data.filter((r) => r.status === "ready"))
    );
  }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!repoId) return;
    setError("");
    setLoading(true);
    setReview(null);
    try {
      const result =
        reviewType === "file"
          ? await reviewFile(repoId, filePath)
          : await reviewRepository(repoId);
      setReview(result);
    } catch {
      setError("Review failed. Make sure the repository is indexed and the LLM is configured.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page">
      <h1>AI Code Review</h1>

      <form className="card form-card" onSubmit={handleSubmit}>
        <div className="form-row">
          <div>
            <label>Repository</label>
            <select
              value={repoId}
              onChange={(e) => setRepoId(e.target.value)}
              required
            >
              <option value="">Select repository…</option>
              {repos.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label>Review type</label>
            <select
              value={reviewType}
              onChange={(e) =>
                setReviewType(e.target.value as "repository" | "file")
              }
            >
              <option value="repository">Entire repository (sample)</option>
              <option value="file">Specific file</option>
            </select>
          </div>
        </div>
        {reviewType === "file" && (
          <>
            <label>File path (relative to repo root)</label>
            <input
              value={filePath}
              onChange={(e) => setFilePath(e.target.value)}
              placeholder="src/main.py"
              required
            />
          </>
        )}
        <button type="submit" className="btn btn-primary" disabled={loading}>
          {loading ? "Running review…" : "Run AI Review"}
        </button>
      </form>

      {error && <div className="alert alert-error">{error}</div>}

      {review && (
        <div className="review-results">
          <div className="review-meta">
            <strong>{review.review_type === "file" ? review.file_path : "Repository review"}</strong>
            &nbsp;·&nbsp;
            {review.issues.length} issue{review.issues.length !== 1 ? "s" : ""} found
            &nbsp;·&nbsp;
            Model: {review.llm_model ?? "n/a"}
          </div>

          {review.issues.length === 0 ? (
            <div className="empty-state">No issues found — looks clean!</div>
          ) : (
            review.issues.map((issue, i) => (
              <div key={i} className="issue-card">
                <div className="issue-header">
                  <SeverityBadge severity={issue.severity} />
                  <strong>{issue.issue}</strong>
                  {issue.line_range && (
                    <span className="line-range">Lines {issue.line_range}</span>
                  )}
                </div>
                <p className="issue-description">{issue.description}</p>
                <div className="issue-fix">
                  <strong>Suggested fix:</strong> {issue.suggested_fix}
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}
