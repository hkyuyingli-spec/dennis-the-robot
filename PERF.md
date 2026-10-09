# NutriBot performance measurements

The localhost failure came from passing `stream_options` as a top-level keyword to the installed Groq SDK, whose `Completions.create()` rejects it before sending a request. Passing the option through `extra_body` fixes streaming, and a live consultation starter then returned HTTP 200 with 277 prompt tokens, 65 completion tokens, and 804.2 ms to first token.

Measurement date: 2026-10-09

## Before numbers

No before baseline was captured before the prompt and retrieval changes. The optimized six starter requests were not invoked: although pytest and the Streamlit server could be run with elevated local execution, no browser was available to click the buttons, and no direct API benchmark was run. No live Groq token counts or timings are available; values are left unmeasured rather than estimated as provider measurements.

| English topic starter | prompt_tokens | completion_tokens | time to first token (ms) | total time (ms) |
| --- | ---: | ---: | ---: | ---: |
| Begin TCM Consultation | Not measured | Not measured | Not measured | Not measured |
| Herb Encyclopedia | Not measured | Not measured | Not measured | Not measured |
| Body Constitution | Not measured | Not measured | Not measured | Not measured |
| Seasonal Health | Not measured | Not measured | Not measured | Not measured |
| Skincare Rituals | Not measured | Not measured | Not measured | Not measured |
| Nutrition Advice | Not measured | Not measured | Not measured | Not measured |

## After numbers

The optimized requests were not run, so provider usage, completion size, latency, and percentage changes cannot be reported yet.

| English topic starter | prompt_tokens | completion_tokens | time to first token (ms) | total time (ms) |
| --- | ---: | ---: | ---: | ---: |
| Begin TCM Consultation | Not measured | Not measured | Not measured | Not measured |
| Herb Encyclopedia | Not measured | Not measured | Not measured | Not measured |
| Body Constitution | Not measured | Not measured | Not measured | Not measured |
| Seasonal Health | Not measured | Not measured | Not measured | Not measured |
| Skincare Rituals | Not measured | Not measured | Not measured | Not measured |
| Nutrition Advice | Not measured | Not measured | Not measured | Not measured |

| Metric | Percentage change |
| --- | ---: |
| Prompt tokens | Not measurable without before/after API usage |
| Completion tokens | Not measurable without before/after API usage |
| Time to first token | Not measurable without before/after API timings |

## Verification checklist

- [ ] Click each of the six topic starters once in English, 中文, and Bahasa; confirm the answer appears and the selected category is highlighted.
- [ ] Confirm a repeated click for the same category/language uses its cached answer and reports the cache date.
- [ ] Ask two follow-up questions after a topic answer; confirm both are included in chat and retain the active topic context.
- [ ] Click Clear conversation; confirm history and active topic reset while the language selection remains.
- [x] `pytest tests/test_topic_chat.py` — 6 tests passed.
- [x] `streamlit run app.py --server.headless true` — server started on port 8501. Browser automation was unavailable, so visual button/API verification remains unchecked.

## Instrumentation and expected changes

`perf_logging.py` writes one structured performance record per Groq request. It records the provider usage fields `prompt_tokens`, `completion_tokens`, and `total_tokens` (also emitted as `total`), request model, approximate prompt-token shares, time to first content token, and total elapsed milliseconds. Streaming requests set `stream_options.include_usage` and capture usage from the final chunk. Logs include category labels and counts only; they never include prompt contents or API keys. Prompt-part counts use a rough character-to-token estimate (CJK characters count as one token) and are monitoring estimates, not provider usage.

| Optimization | Expected effect |
| --- | --- |
| Compact safety prompt, one short language instruction, 200-word default, 600 output-token cap, low reasoning effort | Lower system/reasoning/completion token budgets |
| Starter requests bypass retrieval and Tavily | Lower starter prompt tokens and retrieval latency |
| Three maximum 300-character knowledge snippets; two maximum 300-character web results | Lower retrieved context tokens |
| Four history messages; old assistant turns capped at 500 characters | Lower multi-turn prompt tokens |
| 24-hour cache keyed by topic and language | Repeat starter clicks use no Groq request; caption shows the cached generation date |
| Cached knowledge files, Groq client, and Firebase client | Avoid repeated per-rerun loading and client setup |

The normal chat streams through `st.write_stream`; its generation is logged as the stream is consumed. A cold cached starter is completed and stored before its safe, final answer is displayed; subsequent clicks render the cached answer without an API request.

## Groq documentation checked

- [Groq reasoning settings](https://console.groq.com/docs/reasoning): `low` is supported for `openai/gpt-oss-20b` and `qwen/qwen3.8-27b`.
- [Groq API reference](https://console.groq.com/docs/api-reference): documents `max_completion_tokens`, `stream_options`, and response usage statistics.
- [GPT-OSS 20B model card](https://console.groq.com/docs/model/openai/gpt-oss-20b): lists reasoning support and recommends low/medium/high modes.

## Files changed and why

| File | Reason |
| --- | --- |
| `app.py` | Add privacy-safe Groq metrics, cached clients/loaders/starters, idempotent pending-topic handling, bounded retrieval/history, optional recency search, concise prompt/output settings, and `st.write_stream`. |
| `conversation.py` | Trim history to four messages, cap assistant history text, and provide tested pending-topic and cache-key helpers. |
| `perf_logging.py` | Log provider usage, prompt-part estimates, first-token time and total duration without logging user text or secrets. |
| `nutribot/live_search.py` | Require explicit latest/research/news wording, skip search without a key, and cap results and snippets. |
| `tests/test_topic_chat.py` | Cover history limits, one-time topic consumption, idempotent queueing and topic/language cache keys. |
| `AUDIT.md` | Keep the prior source/system-prompt audit accurate after the performance changes and record the measurement limitation. |
| `PERF.md` | Record measurement status, expected effects, current Groq documentation and this file-change list. |
