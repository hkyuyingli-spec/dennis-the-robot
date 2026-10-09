# NutriBot audit and changes

Audit date: 2026-10-09

## Sidebar topic buttons: before the changes

All six buttons were in the sidebar block in `app.py` (previously around lines 691–702). Their handlers assigned one English string to `st.session_state.prompt_trigger`:

| Sidebar button | Previous click action | Writes session state? | Calls LLM in handler? | Where output went |
| --- | --- | --- | --- | --- |
| Begin TCM Consultation | Set a generic consultation prompt | Yes: `prompt_trigger` | No | Consumed later by the chat tab; Groq completion and assistant history were in the chat tab |
| Herb Encyclopedia | Set a generic Bencao Gangmu prompt | Yes: `prompt_trigger` | No | Same chat-tab path |
| Body Constitution | Set a generic constitution prompt | Yes: `prompt_trigger` | No | Same chat-tab path |
| Seasonal Health | Set a generic seasonal prompt | Yes: `prompt_trigger` | No | Same chat-tab path |
| Skincare Rituals | Set a generic skincare prompt | Yes: `prompt_trigger` | No | Same chat-tab path |
| Nutrition Advice | Set a generic nutrition prompt | Yes: `prompt_trigger` | No | Same chat-tab path |

The chat tab consumed `prompt_trigger`, appended the prompt to `st.session_state.messages`, retrieved context, called the model and appended the answer. No empty handlers, mismatched state key, or swallowed exception was present in this path. API failures were caught and shown as generic messages. The main visibility defect was that all six actions relied on the chat-tab code path, while the separate Genetic TCM Analysis tab can be selected and the app does not switch tabs; an answer is rendered only inside Chat with NutriBot. In addition, button prompts had no persistent active-topic context, and the old prompts were generic rather than guided localized topic experiences. RAG follow-up suggestions were conditional on a retrieval match, so many answers had no chips.

The old app also defined a second, relative-path constitution loader in `app.py`, shadowing the shared project-root-aware loader and making this dataset sensitive to the launch working directory. The implementation now uses the shared loader.

## Data and model source map

| Source | How the app uses it | Freshness/review status |
| --- | --- | --- |
| `data/tcm_herbs_formulas.json` | Loaded by `nutribot.rag.load_tcm_herbs_formulas`; keyword/alias matching with `find_relevant_herbs_formulas`; selected records become context via `build_rag_context` | File says `last_updated: 2026-08-29`, `ai_drafted_pending_review`; this is not a clinically reviewed reference set |
| `data/tcm_constitutions.json` | Loaded by `load_tcm_constitutions`; matched by `find_relevant_constitutions`; formatted into RAG context | No date in the original file; the manifest marks its date as not recorded |
| `data/tcm_constitutions.csv` | Present in the repository but not read by the Streamlit app | No date field; manifest marks it as not loaded |
| `data/cancer_education_general.json` | Loaded and matched for general queries; personal symptom queries are redirected using functions in `nutribot.rag` | No date in the original file; the manifest marks its date as not recorded |
| `data/gene_tcm_map.csv` | Standalone SNP-to-pattern mapping file; it is not read by the Streamlit app | No date field; manifest marks it as not loaded by the app |
| `yuanying_core.py` | Hard-coded correlation matrix, mappings, recommendations; cycle 2 uses a random multiplier | Hard-coded, unversioned and explicitly experimental; the values should not be interpreted as validated genetic associations |
| `nutribot/dce_mcc.py` | Rule-based safety gates and consultation hints | Hard-coded rules; not an external clinical source |
| `nutribot/live_search.py` | Optional Tavily search (`requests.post`) when query-recency patterns match or the user opts in; reads `TAVILY_API_KEY` from environment or Streamlit secrets | External/current search, only supplemental; API or configuration failures are converted to an unavailable notice |
| `locales/en.json`, `locales/id.json`, `locales/zh.json`; `nutribot/i18n.py` | Hard-coded UI translations | No explicit data version |
| `chatbot.py` | Separate Gemini SDK prototype; not imported by the Streamlit app’s main chat path | Reads `GEMINI_API_KEY`; not the model used for the main NutriBot chat |

The main chat is in `app.py`. It calls Groq’s chat completions API through `create_groq_completion` / `_request_groq_completion`. The default primary model is `openai/gpt-oss-20b` (Groq provider); `GROQ_MODEL` can override it. The configured transient-error fallback is `qwen/qwen3.8-27b` via `GROQ_MODEL_FALLBACK`. Normal and topic calls now use temperature `0.5`, `max_completion_tokens=600`, and streaming. GPT-OSS 20B and Qwen 3.8 27B requests use `reasoning_effort="low"`; per Groq’s current docs, `low` is supported by both. Stream requests request final-chunk usage metrics.

The compact base system prompt is `SYSTEM_SAFETY` in `app.py` (under 300 estimated tokens); it is assembled with one short language line, one topic line and any retrieved context. RAG matches are local keyword/alias retrieval, not a vector store. Normal queries send at most three snippets, each capped near 300 characters; category starters skip retrieval. Tavily is opt-in for an explicit latest/news question, with at most two 300-character results. The prompt requires herb-drug interaction and contraindication flags and prohibits invented citations.

`data/knowledge_sources.json` now records source paths, available update dates and review status. The herb data is dated but still awaits human review; the constitution and cancer education files are undated. The knowledge records remain hard-coded project data rather than a live authoritative clinical feed.

## Follow-up chat before the changes

Yes, the app had `st.session_state.messages`, displayed it in the chat tab and appended both user and assistant turns. It sent only the newest four messages to Groq, truncating assistant messages longer than 800 characters. `st.chat_input` was already at the bottom of the chat tab. Follow-up chips were generated only if herb or constitution retrieval matched. The old Clear History button called `st.session_state.clear()`, resetting unrelated state along with the conversation.

## Changes made

- Added `topics.py` with localized starter prompts and exactly three localized suggestions for each category. Seasonal prompts include today’s date.
- Updated the six keyed sidebar buttons to retain `active_topic`, submit the matching localized starter prompt through the normal chat path, show a check mark and active-category callout, and preserve the selected language.
- Added `conversation.py` for session initialization, scoped clear behavior, topic-aware system-prompt assembly and bounded recent-history trimming. The system prompt is retained separately from history.
- Kept `st.chat_input` available at the bottom with a stable widget key; added stable keys to language/topic/clear widgets.
- Added a running `st.status` indicator and a friendly generation error while preserving the submitted user turn in conversation history.
- Added three topic-specific follow-up chips after every topic response; chip clicks submit as user turns and inherit `active_topic` context.
- Added an educational disclaimer in all three supported languages. Replaced the fixed English response-ending instruction with a selected-language reminder.
- Added per-answer source/model/generation-date captions and knowledge-base update details when retrieval matched. Undated source files say their date is not recorded.
- Added `data/knowledge_sources.json` to document data freshness and review status.
- Removed the duplicate local constitution loader so all three RAG datasets use the shared project-root-aware loader functions.
- Improved sidebar text contrast. The “Dennis with FINANCIAL HANDS!” title text was **not removed**; it remains in the locale strings pending the requested confirmation.
- Kept the genetic analysis tab, existing RAG, optional live search, safety gates, and existing chat flow.

## Credential scan

No Groq, Google API-key, or private-key patterns were found in tracked files. The ignored local `.env` and `serviceAccountKey.json` contain credential material; they were not printed or modified. `.gitignore` already excludes both. Keep them untracked and use Streamlit secrets or environment variables in deployment.

## Manual test checklist

Run `streamlit run app.py`, then repeat each button in each language (English, 中文, Bahasa):

- [ ] Begin TCM Consultation: answer the intake questions about symptoms, sleep, digestion, temperature and emotions.
- [ ] Herb Encyclopedia: verify the assistant asks which herb; type an herb name and check retrieved cautions.
- [ ] Body Constitution: answer the one-at-a-time questionnaire; verify it does not diagnose from one answer.
- [ ] Seasonal Health: verify current date appears in the answer and ask for local-climate tailoring.
- [ ] Skincare Rituals: verify gentle routine and patch-test guidance.
- [ ] Nutrition Advice: verify ordinary-food suggestions and allergy/condition questions.
- [ ] After a topic answer, click a suggested follow-up, then submit a second follow-up in chat input; verify topic context remains active.
- [ ] Click Clear History; verify messages and active topic clear while selected language remains.
- [ ] Force an API error or run without `GROQ_API_KEY`; verify a friendly error and retained user message.
- [ ] Confirm the Genetic TCM Analysis tab still renders.

## Automated/local verification

Added `tests/test_topic_chat.py` for localized prompt coverage, date insertion, three suggestions, bounded history, scoped clearing, one-time topic consumption and cache keys. All six tests passed with the repository virtual environment. `streamlit run app.py --server.headless true` started successfully on port 8501. A browser was unavailable in this environment, so the six buttons were not clicked visually; complete the checklist above for full interaction verification.

## Performance follow-up

The later optimization pass adds privacy-preserving prompt-part and usage logging in `perf_logging.py`, server-resource caches for model/Firebase/knowledge loaders, a 24-hour `(topic, language)` starter cache, idempotent pending-topic consumption, and four-message history trimming. See `PERF.md` for measurement status. This environment can start the app, but no browser was available to trigger six live model requests; before/after API numbers remain unmeasured.
