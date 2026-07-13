import api from "./client";
import type { SearchResponse } from "../types";

export async function semanticSearch(
  query: string,
  repository_id?: string,
  top_k = 5
): Promise<SearchResponse> {
  const { data } = await api.post<SearchResponse>("/search/", {
    query,
    repository_id: repository_id || undefined,
    top_k,
  });
  return data;
}
