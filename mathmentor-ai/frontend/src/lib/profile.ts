import { api } from "./api";
import type { UserProfile } from "@/types";

export async function getProfile(userId: string): Promise<UserProfile> {
  const res = await api.get(`/users/${userId}/profile`);
  return res.data;
}

export async function updateProfile(
  userId: string,
  data: {
    response_preference?: string;
    hint_dependency_level?: number;
    step_by_step_preference?: number;
  }
): Promise<UserProfile> {
  const res = await api.patch(`/users/${userId}/profile`, data);
  return res.data;
}
