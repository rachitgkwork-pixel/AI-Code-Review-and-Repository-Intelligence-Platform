import api from "./client";
import type { User } from "../types";

export async function login(email: string, password: string): Promise<string> {
  const { data } = await api.post<{ access_token: string }>("/auth/login", {
    email,
    password,
  });
  return data.access_token;
}

export async function register(
  email: string,
  password: string,
  full_name?: string
): Promise<User> {
  const { data } = await api.post<User>("/auth/register", {
    email,
    password,
    full_name,
  });
  return data;
}

export async function getMe(): Promise<User> {
  const { data } = await api.get<User>("/auth/me");
  return data;
}
