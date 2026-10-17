export type ChatApiErrorKind =
  | "connection"
  | "backend_configuration"
  | "provider"
  | "rate_limit"
  | "http";

export class ChatApiError extends Error {
  readonly kind: ChatApiErrorKind;
  readonly status?: number;

  constructor(
    kind: ChatApiErrorKind,
    message: string,
    status?: number,
  ) {
    super(message);
    this.kind = kind;
    this.status = status;
    this.name = "ChatApiError";
  }
}

export function chatApiErrorKind(status: number): ChatApiErrorKind {
  if (status === 429) return "rate_limit";
  if (status === 502) return "provider";
  if (status === 503) return "backend_configuration";
  return "http";
}
