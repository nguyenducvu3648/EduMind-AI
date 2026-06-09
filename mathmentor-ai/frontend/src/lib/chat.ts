import type { SessionDetail } from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export async function sendMessage(message: string, sessionId?: string | null) {
  const token = localStorage.getItem("access_token");
  const res = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify({ message, session_id: sessionId || null }),
  });
  return res.json();
}

export async function sendMessageStream(
  message: string,
  sessionId?: string | null,
  onToken?: (token: string) => void,
  onDone?: (metadata: Record<string, unknown>) => void
): Promise<void> {
  const token = localStorage.getItem("access_token");
  const params = new URLSearchParams({ message });
  if (sessionId) params.set("session_id", sessionId);

  const res = await fetch(`${API_BASE}/chat/stream?${params.toString()}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);

  const reader = res.body!.getReader();
  const decoder = new TextDecoder();
  let buf = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buf += decoder.decode(value, { stream: true });

    const parts = buf.split("\n");
    buf = parts.pop() || "";

    for (const line of parts) {
      if (line.startsWith("data: ")) {
        try {
          const data = JSON.parse(line.slice(6));
          if (data.token) onToken?.(data.token);
          else onDone?.(data);
        } catch { /* ignore */ }
      }
    }
  }
}

export async function getSessionMessages(sessionId: string): Promise<SessionDetail> {
  const token = localStorage.getItem("access_token");
  const res = await fetch(`${API_BASE}/sessions/${sessionId}/messages`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return res.json();
}
