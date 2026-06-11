import axios from "axios";
import { api } from "./api";
import type { User } from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export interface AuthResult {
  user: User;
  access_token: string;
  refresh_token: string;
}

export async function login(email: string, password: string): Promise<AuthResult> {
  const res = await api.post("/auth/login", { email, password });
  const tokens = res.data;

  // Fetch user info from token (no /me endpoint, decode from token or use email)
  const userRes = await api.get("/users/me", {
    headers: { Authorization: `Bearer ${tokens.access_token}` },
  }).catch(() => null);

  let user: User;
  if (userRes?.data) {
    user = userRes.data;
  } else {
    // Fallback: return basic user object
    user = { id: "", email, grade_level: null, created_at: new Date().toISOString() };
  }

  return {
    user,
    access_token: tokens.access_token,
    refresh_token: tokens.refresh_token,
  };
}

export async function adminLogin(email: string, password: string): Promise<{ access_token: string; user: User }> {
  const res = await axios.post(`${API_BASE}/admin/auth/login`, { email, password });
  return res.data;
}

export async function register(
  email: string,
  password: string,
  grade_level: number
): Promise<AuthResult> {
  const res = await api.post("/auth/register", { email, password, grade_level });
  const user = res.data;

  // Auto login after register
  const loginRes = await api.post("/auth/login", { email, password });
  const tokens = loginRes.data;

  return {
    user,
    access_token: tokens.access_token,
    refresh_token: tokens.refresh_token,
  };
}
