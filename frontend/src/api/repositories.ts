import api from "./client";
import type { Repository, RepositoryCreate } from "../types";

export async function listRepositories(): Promise<Repository[]> {
  const { data } = await api.get<Repository[]>("/repositories/");
  return data;
}

export async function getRepository(id: string): Promise<Repository> {
  const { data } = await api.get<Repository>(`/repositories/${id}`);
  return data;
}

export async function addRepository(payload: RepositoryCreate): Promise<Repository> {
  const { data } = await api.post<Repository>("/repositories/", payload);
  return data;
}

export async function deleteRepository(id: string): Promise<void> {
  await api.delete(`/repositories/${id}`);
}

export async function reindexRepository(id: string): Promise<void> {
  await api.post(`/repositories/${id}/reindex`);
}
