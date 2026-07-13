import api from "./client";
import type { ReviewResponse } from "../types";

export async function reviewFile(
  repository_id: string,
  file_path: string
): Promise<ReviewResponse> {
  const { data } = await api.post<ReviewResponse>("/reviews/file", {
    repository_id,
    file_path,
  });
  return data;
}

export async function reviewRepository(
  repository_id: string
): Promise<ReviewResponse> {
  const { data } = await api.post<ReviewResponse>("/reviews/repository", {
    repository_id,
  });
  return data;
}
