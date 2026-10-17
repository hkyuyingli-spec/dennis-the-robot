import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { chatApiErrorKind, ChatApiError } from "../src/apiErrors.ts";

describe("chat API error classification", () => {
  it("distinguishes connection failures", () => {
    const error = new ChatApiError("connection", "Network request failed");

    assert.equal(error.kind, "connection");
    assert.equal(error.status, undefined);
  });

  it("identifies provider failures returned by the backend", () => {
    assert.equal(chatApiErrorKind(502), "provider");
  });

  it("identifies backend configuration failures returned by the backend", () => {
    assert.equal(chatApiErrorKind(503), "backend_configuration");
  });

  it("preserves the rate-limit response category", () => {
    assert.equal(chatApiErrorKind(429), "rate_limit");
  });

  it("keeps unrelated HTTP errors separate", () => {
    assert.equal(chatApiErrorKind(400), "http");
    assert.equal(chatApiErrorKind(500), "http");
  });
});
