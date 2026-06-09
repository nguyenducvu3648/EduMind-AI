"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import type { User } from "@/types";

export function useAuth() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    const stored = localStorage.getItem("user");
    const token = localStorage.getItem("access_token");
    if (stored && token) {
      try {
        setUser(JSON.parse(stored));
      } catch {
        localStorage.removeItem("user");
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
      }
    }
    setLoading(false);
  }, []);

  const login = useCallback(
    (userData: User, accessToken: string, refreshToken: string) => {
      localStorage.setItem("user", JSON.stringify(userData));
      localStorage.setItem("access_token", accessToken);
      localStorage.setItem("refresh_token", refreshToken);
      setUser(userData);
      router.push("/chat");
    },
    [router]
  );

  const logout = useCallback(() => {
    localStorage.removeItem("user");
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    setUser(null);
    router.push("/login");
  }, [router]);

  return { user, loading, login, logout };
}
