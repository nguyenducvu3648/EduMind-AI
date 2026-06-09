import { api } from "./api";
import type { SessionItem } from "@/types";

export async function listSessions(): Promise<SessionItem[]> {
  const res = await api.get("/sessions");
  return res.data;
}
