import { api } from "./api";
import type { WikiChunk } from "@/types";

export async function getWikiChunks(
  params?: {
    grade?: number;
    subject?: string;
    limit?: number;
  }
): Promise<WikiChunk[]> {
  const res = await api.get("/wiki/chunks", { params });
  return res.data;
}
