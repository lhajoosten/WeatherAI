# WeatherAI — Project Case Document

Version: 1.0  
Date: 2025-08-23  
Author: lhajoosten

---

## 1 — Project overview

An AI-powered weather application that blends authoritative weather data with natural-language intelligence. The app provides standard forecast UI plus LLM-powered human-friendly summaries, actionable advice, conversational Q&A, personalized digests/alerts, and an audit trail of forecasts. Built with FastAPI (Python) backend, React (TypeScript) frontend, Microsoft SQL Server for relational storage, Redis for caching/queues, and OpenAI for LLM capabilities.

High-level objectives:

- Turn raw weather data into useful, contextual guidance (e.g., "Bring a light jacket for your evening run").
- Provide conversational, explainable summaries and safety-focused alerts.
- Enable personalization (commute type, wardrobe, sensitivities).
- Maintain provenance and deterministic facts to avoid hallucinations.

---

## 2 — Goals & success metrics

Primary goals:

- Reduce friction for users to interpret weather by providing concise, accurate summaries and explicit actions.
- Maintain traceability of AI outputs to underlying data (no hallucinated measurements).
- Achieve reliable cost controls for LLM usage.

Success metrics:

- User satisfaction score for summaries ≥ 4/5 (survey).
- Average token usage per summary under threshold (monitoring).
- <1% hallucination incidents detected in QA tests (see testing section).

---

## 3 — Stakeholders & personas

- End users: commuters, outdoor enthusiasts, event planners — want quick actionable advice.
- Admin/Operators: monitor costs, keep system reliable, handle API keys and rate limits.
- Product owner: defines personalization rules, digest cadence, and alert thresholds.

---

## 4 — Requirements

Must have (MVP)

- User registration and authentication (JWT).
- Manage one or more saved locations (lat/lon).
- Fetch and cache forecast for location (48h hourly + 7d daily).
- React UI displaying standard forecast charts and conditions.
- "Explain" action: LLM-generated short summary + 3 actionable recommendations derived strictly from forecast.
- Background scheduler to fetch forecasts and maintain cache.
- Logging of LLM calls with model, tokens, and cost.
- Safety guardrails: no hallucinations of measurements; “I don’t know” fallback.
- Basic rate limits per user.

Should have (post‑MVP / high priority)

- Chat-style interface for natural-language questions about weather (session history).
- Daily digest (email/push) with AI summary for saved locations.
- Alerts ingestion and intelligent summarization of official warnings (with links).
- Personalization: user preferences that influence advice (e.g., commute by bike).
- Token/cost dashboard for operator.

Nice to have (advanced)

- RAG for local microclimate: index user notes & local observations for better personalization (vector store).
- Multilingual summaries and translations.
- Hybrid forecasting augmentation (simple statistical model that LLM can explain).
- Agent tools to create calendar reminders or route recommendations (with strict safeguards).
- Offline PWA and push notifications with rules.

---

## 5 — Technical features & design

Core technologies

- Backend: FastAPI (Python, async), Pydantic models.
- Frontend: React (TypeScript) + Vite, React Query, component library (Chakra/Tailwind).
- DB: Microsoft SQL Server for relational data (users, locations, forecast cache, notifications, audit).
- Cache/queue: Redis for short-term cache and Celery/RQ for background tasks.
- LLM: OpenAI (gpt-4 / latest flagship available) for generation; text-embedding-3 for embeddings (if used).
- Vector DB (optional): Qdrant/Pinecone for RAG & personalization.
- Hosting: Docker Compose for dev; Kubernetes or cloud App Services for prod.

Architecture (concise)

- API layer exposes REST endpoints (auth, locations, forecast, explain, chat, notifications).
- Background worker handles scheduled forecast fetch, digest generation, alert ingestion, and ingestion-to-vector pipeline.
- ForecastCache table stores raw API payloads and expires_at to minimize calls to weather providers.
- LLM calls are proxied through a single service that applies templates, token limits, logging, and guardrails.

Anti-hallucination pattern

- Build a "structured facts" block from authoritative forecast JSON (temperature, precipitation probability, wind, alerts).
- Provide only those facts to the LLM and instruct it not to invent values.
- Use low temperature (0–0.2) and explicit guardrail language in prompts.
- If query requires external knowledge beyond provided facts, respond with "Information unavailable" or fallback resources.

Cost & safety controls

- Per-user request quotas; daily token budget.
- Use cheaper models for non-critical tasks; flagship for user-facing summaries.
- Log model, prompt length, and token consumption; export to cost dashboard.

---

## 6 — Sample DB schema (simplified)

- Users: id (PK), email, password_hash, timezone, prefs_json, created_at
- Locations: id (PK), user_id (FK), name, lat, lon, timezone, created_at
- ForecastCache: id, location_id, source, fetched_at, expires_at, payload_json
- Alerts: id, location_id, provider_id, alert_payload_json, start_at, end_at, processed_at
- Notifications: id, user_id, location_id, type, content_json, status, created_at, sent_at
- LLMAudit: id, user_id, endpoint, model, prompt_summary, tokens_in, tokens_out, cost, created_at

Notes: keep payload_json for source fidelity and debugging. Do not persist PII in prompt logs.

---

## 7 — API endpoints (minimal)

- POST /auth/register — register user (returns JWT)
- POST /auth/login — login (JWT)
- GET /locations — list user locations
- POST /locations — add location
- GET /locations/{id}/weather?hours=48 — cached forecast
- POST /locations/{id}/explain — return AI-generated summary + actions
- POST /query — chat-style Q&A (session_id optional)
- GET /alerts — active alerts aggregated for user
- POST /notifications/subscribe — configure digest settings

Behavioral notes:

- /explain builds structured facts from ForecastCache and only sends those facts to the LLM.
- /query can reuse cached forecast but must attach facts and preserve provenance.

---

## 8 — Prompt templates (examples)

Daily summary (explain)
System:
You are a concise, factual weather assistant. Use only the Data section. Do not invent measurements. If information is missing, say "information unavailable." Tone: friendly and actionable.

User:
Data: {structured_facts_json}
Task: Produce:

1) A 2–3 sentence summary of the important weather for {location} today.
2) Three short action items tailored to a general adult (commute/work/outdoor).
3) One brief explanation of the main driver (e.g., frontal passage, cold air, thunderstorm risk).
   Instructions: Be concise. Do not invent numbers beyond those provided.

Chat Q&A (follow-up)
System:
You are an assistant that answers only using the supplied data; you may add general weather wisdom but do not invent measured values.

User:
Context: {most_relevant_facts}
Question: {user_question}
Answer in 1–4 sentences. If the question cannot be answered from the data, state so.

Model params recommendation:

- model: gpt-4 (or available flagship)
- temperature: 0.0–0.2
- max_tokens: 400 (adjust for digest length)

---

## 9 — Testing & QA

Automated tests

- Unit tests for domain logic (forecast parsing, personalization rules).
- Integration tests for endpoints using TestClient & test MS SQL (Docker or TestContainers).
- Contract tests for external weather API (use recorded fixtures / VCR-style).
- Golden tests for prompt outputs: assert essential parts exist and no fabricated numeric claims.

Manual QA

- Evaluate 100 generated summaries against source data for hallucinations.
- A/B test temperature and prompt variants for clarity.

Monitoring

- Track LLM usage (tokens, cost), API error rates, forecast freshness.
- Alerts for sudden cost spikes and model failures.

---

## 10 — Security & compliance

- Store OpenAI key and other secrets in environment variables or Key Vault; never commit keys.
- Use HTTPS for all traffic; secure CORS policies.
- Rate-limit endpoints to prevent abuse and runaway LLM costs.
- Sanitize any user-provided text before including in prompts when necessary.
- For user-uploaded personal notes (if implemented), consider encryption at rest.

---

## 11 — Observability & ops

- Structured logging (timestamp, user_id, endpoint, model, tokens).
- Trace LLM calls in logs but redact full prompt text if it contains sensitive data.
- Expose health endpoints and readiness probes.
- Create a cost dashboard summarizing model usage per day and per-user quotas.

---

## 12 — 8‑week roadmap (milestones)

Week 1 — Foundations

- Repo skeleton, Docker Compose (FastAPI, MS SQL dev, Redis), React app bootstrap, auth (JWT), user & location models.

Week 2 — Forecast integration

- Integrate weather API, ForecastCache table, background scheduler to refresh cached forecasts; basic UI to add locations and view forecast.

Week 3 — Explain endpoint (LLM)

- Implement /explain endpoint: build structured facts, LLM wrapper, guardrails, show summary in UI.

Week 4 — Chat interface & session history

- Chat endpoint and simple conversation widget; store session history and LLMAudit logs.

Week 5 — Notifications & digests

- Background digest generation & email/push flow, user preferences in DB.

Week 6 — Alerts & authoritative summaries

- Ingest provider alerts, summarize & link back to source, UI for alert management.

Week 7 — Personalization & cost controls

- Add user preferences, personalize action items, implement per-user quotas and operator cost dashboard.

Week 8 — QA, tests & deploy

- Tests, CI pipeline, Docker images, minimal production deployment and monitoring.

---

## 13 — Acceptance criteria (MVP)

- Users can register, add locations, and view cached forecasts.
- The /explain action returns consistent, accurate summaries that match forecast values and include three relevant action items.
- LLMAudit contains model usage, tokens, and cost for each LLM call.
- Background job updates ForecastCache on schedule.
- Basic rate limits and quotas are in place.

---

## 14 — Risks & mitigations

- Hallucinations → mitigation: pass only structured facts and use deterministic model settings.
- Cost overruns → mitigation: quotas, cheaper fallbacks, logging, preview of estimated tokens before long digests.
- Weather API rate limits → mitigation: caching and adaptive polling.
- Data privacy → mitigation: do not store sensitive prompt text, use encryption and secrets vault.

---

## 15 — Deliverables & next steps

What I prepared here:

- A compact, production-oriented case document defining scope, requirements (must/should/nice), technical features, prompt patterns, DB schema, API surface, roadmap and acceptance criteria for an AI-powered weather app using FastAPI + React + MS SQL Server + OpenAI.

Next I can do (pick one):

- Scaffold a starter repository (Docker Compose, FastAPI skeleton, MS SQL and Redis containers, React starter, working /locations/{id}/explain endpoint wired to OpenAI). This will include README and run instructions.
- Produce a more detailed week-by-week task list with tickets and developer subtasks for Sprint 0 and Sprint 1.
- Create example code snippets for the FastAPI LLM wrapper, the forecast ingestion worker, and the React explain UI.

I can scaffold the repository now if you want me to — say "Scaffold repo" and I'll generate the initial files.
