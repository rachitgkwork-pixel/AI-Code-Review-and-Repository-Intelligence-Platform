export interface User {
  id: string;
  email: string;
  full_name: string | null;
  role: "admin" | "user";
  is_active: boolean;
}

export interface Repository {
  id: string;
  name: string;
  url: string;
  description: string | null;
  status: "pending" | "cloning" | "indexing" | "ready" | "error";
  branch: string;
  total_files: number;
  indexed_files: number;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface RepositoryCreate {
  name: string;
  url: string;
  description?: string;
  branch?: string;
}

export interface SearchResult {
  chunk_id: string;
  file_path: string;
  repository_id: string;
  content: string;
  similarity: number;
  start_line: number;
  end_line: number;
}

export interface SearchResponse {
  query: string;
  results: SearchResult[];
  total: number;
}

export type Severity = "critical" | "high" | "medium" | "low" | "info";

export interface ReviewIssue {
  issue: string;
  severity: Severity;
  description: string;
  suggested_fix: string;
  line_range: string | null;
}

export interface ReviewResponse {
  review_id: string;
  repository_id: string;
  file_path: string | null;
  review_type: "file" | "repository";
  status: "pending" | "completed" | "error";
  issues: ReviewIssue[];
  llm_model: string | null;
  created_at: string;
  completed_at: string | null;
}
