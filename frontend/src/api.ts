export type ChatRole = "user" | "assistant";
export type Language = "en" | "zh" | "id";

export interface ChatMessage {
  role: ChatRole;
  content: string;
}

interface ChatResponse {
  reply: string;
  classical_reference_used: boolean;
}

const apiBase = (
  import.meta.env.VITE_API_URL || "http://localhost:8000"
).replace(/\/+$/, "");

export async function sendChat(
  messages: ChatMessage[],
  language: Language,
  signal?: AbortSignal
): Promise<ChatResponse> {
  const response = await fetch(`${apiBase}/api/v1/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ messages, language }),
    signal
  });

  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as
      | { detail?: string }
      | null;
    throw new Error(payload?.detail || "NutriBot could not answer. Please try again.");
  }

  return (await response.json()) as ChatResponse;
}
