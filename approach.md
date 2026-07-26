# Approach Document — SHL Assessment Recommender

## 1. Problem decomposition

The task splits into four independent concerns: (a) get the catalog into a queryable
form, (b) retrieve a small, relevant candidate set per turn, (c) let an LLM reason
over that candidate set to decide whether to clarify/recommend/refine/compare/refuse,
and (d) enforce the API contract regardless of what the LLM does. I kept these as
separate modules (`catalog.py`, `retrieval.py`, `agent.py`, `main.py`) so each can be
tested and reasoned about independently, and so retrieval — not the LLM — is the only
component allowed to introduce real catalog data into the conversation.

## 2. Catalog ingestion and scoping

The catalog is fetched live at process startup from the provided JSON endpoint, cached
to disk (TTL configurable, default 6h) so cold starts after the first request are
cheap, with a tiny bundled seed (`data/catalog_seed.json`, 15 hand-picked rows) as a
last-resort offline fallback for local dev/CI when the live URL is unreachable — this
is explicitly *not* a substitute for the full catalog in production.

The brief restricts scope to **Individual Test Solutions**, excluding pre-packaged Job
Solutions. The scraped JSON doesn't carry an explicit category field distinguishing
the two, so I used a documented heuristic (`catalog.is_job_solution`): exclude rows
whose name matches `\bsolution(s)?\b` or whose description references "Precise Fit ...
Solution" / "Job-Focused Assessment" bundles (these are SHL's own naming conventions
for bundled batteries, e.g. "Entry Level Cashier Solution", "Customer Service Phone
Solution"). This is a best-effort filter, not ground truth — false positives/negatives
are possible at the margin, and I call this out rather than presenting it as exact.

## 3. Retrieval

Rather than an LLM-only "remember the catalog" approach (which risks hallucinated
names/URLs) or a full vector-DB setup (overkill for a few hundred short text records),
I use scikit-learn TF-IDF + cosine similarity over each item's name, description,
`keys` (category), and `job_levels`. For each turn I build several queries — the full
concatenated user-turn history (captures cumulative constraints), the latest user
message alone (captures refinements like "actually, add personality tests"), and, when
the latest message looks like a pasted job description (>200 chars), each
comma/semicolon/`and`-separated clause individually — and merge results by max score.
This last step matters: a single embedding of a 7-skill JD tends to average toward a
generic match; querying each skill clause separately and taking the union surfaces the
dedicated knowledge test for each (Java, SQL, AWS, Docker, etc.) the way the C9 sample
conversation expects. The top ~25 candidates (by merged score) are handed to the LLM
as the *only* items it's allowed to recommend from.

## 4. Agent / prompt design

A single system prompt encodes all four required behaviors (clarify, recommend,
refine, compare) plus scope/refusal and an explicit JSON-only output contract matching
the API schema exactly. Each turn, the user-role message to the model contains: the
ranked candidate list (name/url/test_type/duration/job_levels/description snippet),
the full conversation history, and the current turn count vs. the 8-turn cap — the
model is told to converge rather than over-clarify as the cap approaches.

Key design choices:
- **Stateless by construction**: every call rebuilds candidates and re-derives state
  from the full `messages` array, matching the brief's stateless requirement directly
  rather than bolting state management on top.
- **Compare** is handled by the same prompt/candidate mechanism — comparison
  questions retrieve the named items via TF-IDF too, so the model answers from the
  catalog's own description text rather than prior/trained knowledge of SHL products.
- **Refusal** is instructed at the system level (off-topic, legal/general HR advice,
  prompt injection) and conversation history is explicitly framed as untrusted content
  rather than new instructions, to resist injected "ignore previous instructions"
  attempts embedded in a user message or pasted JD.

## 5. Guarding against the two named failure modes

- **Hallucination**: `agent._sanitize_recommendations` is a hard, code-level filter —
  any `(name, url)` the model returns that doesn't exactly match a URL in the loaded
  catalog is silently dropped before the response is ever returned. The model cannot
  bypass this regardless of what it outputs in `reply` text.
- **Conversational incoherence / non-happy-path robustness**: malformed/non-JSON model
  output, LLM API errors, and empty `messages` arrays are all caught and degrade to a
  safe clarifying response (`recommendations: []`, `end_of_conversation: false`)
  instead of a 5xx or a schema violation. At the 8-turn cap, if the model still hasn't
  committed to a shortlist, the service forces convergence using the top-ranked
  retrieval candidates so a conversation never "loops" past the evaluator's turn cap
  without producing the recommendations array it needs.

## 6. Evaluation approach

I read all 10 sample conversation traces before implementation to understand the
expected tone, turn-taking pattern (e.g., C1's 4-turn clarify→recommend→refine arc;
C9's single-turn pasted-JD case), and what "grounded" answers look like for compare
questions. Automated tests (`tests/test_app.py`) mock the LLM call and assert: schema
compliance on every response shape, anti-hallucination filtering, dedup, the 1–10 cap,
no-recommendation-on-vague-first-turn, and graceful degradation on LLM/parsing
failures — i.e., the things most likely to silently break in a non-deterministic,
multi-turn replay harness rather than in a single happy-path call.

**What didn't work / was cut for time**: an initial pure-embedding (no TF-IDF clause
splitting) retrieval pass under-recommended for multi-skill JDs like C9, averaging
toward generic "Computer Science" type matches instead of surfacing each named skill's
specific test — fixed by the clause-splitting + max-score merge described in §3. I did
not build a vector store / reranker; given the catalog's small size, TF-IDF was
sufficient and avoids an extra embedding-API dependency and cost on every turn.

## 7. AI tool usage disclosure

I used Claude (via this same environment) for scaffolding the FastAPI/agent
boilerplate and for drafting this document; the retrieval heuristic (clause-splitting
on pasted JDs), the catalog scoping filter, and the anti-hallucination/turn-cap
guarantees were iterated on and verified by running the test suite and a retrieval
sanity-check against a sample JD, not accepted as-is.
