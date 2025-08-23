# Copilot Development Guidelines — FastAPI + React + OpenAI (Comprehensive)

Version: 1.0  
Date: 2025-08-23  
Author: lhajoosten (guidance + best practices)

Purpose
- Provide a concise, practical, and actionable set of instructions you (and GitHub Copilot) can use during development.
- Focus areas: Python (FastAPI) best practices, TypeScript (React) best practices, LLM integration patterns, security, maintainability, single responsibility, modularity, and testability.

How to use this file
- Keep this doc as a living reference in docs/COPILOT_GUIDELINES.md in your repo.
- When using Copilot, reference the "Patterns" and "Snippets" sections to encourage generated code to follow conventions.
- Use sections as checklists in PR templates and code reviews.

Table of contents
1. Team conventions & coding standards
2. Python (FastAPI) best practices
3. TypeScript (React) best practices
4. LLM integration (OpenAI) best practices
5. Security & secrets management
6. Maintainability, SOLID & modularity
7. Testing strategy & examples
8. Observability, logging & telemetry
9. CI/CD, linters & tooling
10. PR checklist & code review guide
11. Example project layout
12. Useful snippets

---

1. Team conventions & coding standards
- Use explicit typing everywhere possible (Python typing + TypeScript strict mode).
- Keep functions and modules small (< ~200 LOC); single responsibility per function/class.
- Prefer clear, explanatory names: verbs for functions, nouns for classes and models.
- Follow PEP 8 for Python and eslint/Prettier conventions for TypeScript.
- Add docstrings / JSDoc for public functions and endpoints.
- Use feature branches, descriptive commits, and atomic PRs.

2. Python (FastAPI) best practices
- Project layout (example):
  - app/
    - api/ (routes)
    - core/ (config, constants)
    - services/ (business logic, LLM wrapper)
    - models/ (pydantic DTOs)
    - db/ (database models & repositories)
    - workers/ (background tasks)
    - tests/
- Async-first: prefer async def for IO-bound code. Use sync only for CPU-bound tasks or third-party sync libs behind threadpools.
- Use typed Pydantic models for request/response validation. Keep schemas separate from ORM models.
- Dependency injection: use FastAPI Depends for decoupling (e.g., DB session, current_user).
- DB access:
  - Use SQLAlchemy/SQLModel/async drivers (Databases or SQLAlchemy Async). Keep DB sessions per-request lifespan.
  - Repositories: one repository per aggregate/area; expose expressive methods, not generic CRUD.
  - Use AsNoTracking-style patterns when reading for performance.
- Error handling:
  - Centralized exception middleware; translate exceptions to HTTP responses with consistent shape.
  - Return Problem Details (RFC7807) style JSON for errors.
- Background work:
  - Offload long-running tasks to Celery/RQ/Huey or FastAPI background tasks for lightweight jobs.
- Configuration:
  - Keep config in pydantic BaseSettings and load from environment variables.
- Security:
  - Always validate incoming data lengths and types before using them in prompts or DB.
- Reuse & Single Responsibility:
  - Services should encapsulate business rules; controllers should adapt HTTP I/O to service calls.

3. TypeScript (React) best practices
- Project tools:
  - TypeScript with "strict": true.
  - React functional components with hooks.
  - Stable state management (React Query for server data, useContext or Zustand for client-only state).
- Component design:
  - Small, focused components. Prefer composition over inheritance.
  - Presentational (dumb) vs Container (smart) separation.
  - Use Controlled inputs and React Hook Form for complex forms.
- Performance:
  - Use memoization (useMemo/useCallback) only where necessary.
  - On large lists use virtualization (react-window).
  - On data fetching use React Query for caching, background refresh and retry logic.
- Styling:
  - Use CSS-in-JS, Tailwind, or CSS Modules consistently. Keep presentation concerns out of logic.
- API client:
  - Centralized API client wrapper (fetch/axios) with typed responses.
  - Handle retries globally; expose standard error types to UI layer.
- Error handling:
  - Global error boundary component for uncaught exceptions.
  - Show friendly UI messages; preserve developer logs for diagnostics.
- Testing:
  - Unit tests with Jest; component tests with React Testing Library.
  - E2E tests with Playwright or Cypress for critical flows.

4. LLM integration (OpenAI) best practices
- Wrap LLM calls in a dedicated service (LLMClient) that centralizes:
  - Model selection and version, token limits, retries/backoff, rates, and monitoring.
  - Prompt templates and their version metadata.
  - Audit logging: store minimal prompt metadata, tokens consumed, model name and cost in LLMAudit table.
  - Sanitization & PII stripping before logging prompts.
- Prompt engineering:
  - Keep templates in code or DB with versioning.
  - Use structured inputs (JSON or bullet lists) when passing facts to the model.
  - For factual outputs, use low temperature (0–0.2) and explicit guardrails: "Answer using only Data: section".
- RAG / Retrieval:
  - If using embeddings, modularize embedding calls and retriever components.
  - Use vector DB (Qdrant/Pinecone/PGVector) and treat it as a separate service; index metadata linking back to MS SQL.
  - Limit retrieval size and validate combined context length to avoid token overflows.
- Cost controls:
  - Implement quotas per user, per request token estimation, and model fallback (cheaper models for previews).
  - Cache frequently used completions and embeddings in Redis.
- Safety:
  - For high-risk outputs, require "source citations" and a checklist to avoid hallucinations.
  - If model output would trigger an action (e.g., alert), ensure human review or deterministic rule check.
- Testing & Mocks:
  - Mock OpenAI calls in unit tests; record real calls in integration tests with VCR-style fixtures or dedicated staging keys.
- Versioning:
  - Store model and prompt version in audit logs with deterministic reproducibility.

5. Security & secrets management
- Secrets:
  - Keep keys in environment variables or a secrets manager (Azure Key Vault). Never commit secrets.
- Auth:
  - JWT access tokens + refresh tokens. Validate token audience/issuer and expiry.
  - Use OAuth/OIDC if integrating with third-party identity providers.
- Input validation:
  - Validate length and characters for user inputs to avoid prompt injection and prepending malicious content.
- Rate limiting:
  - Enforce per-user and global rate limits for LLM calls and endpoints.
- CORS & CSP:
  - Configure strict CORS policies and content security policy headers for the frontend.
- HTTPS & headers:
  - Always run over HTTPS. Set HSTS, X-Frame-Options, and other security headers.
- DB security:
  - Use parameterized queries; avoid building raw SQL with string concatenation.
  - Enforce principle of least privilege for DB credentials.
- Logging & Privacy:
  - Avoid storing raw user content used in prompts. If storing, encrypt at rest and redact logs.

6. Maintainability, SOLID & modularity
- Clean architecture:
  - Split code into layers: API (controllers), Application/Services (use cases), Domain (entities, value objects), Infrastructure (DB, external APIs).
  - Keep side-effecting code (DB, network, file system) behind interfaces/abstractions.
- Single Responsibility:
  - One class/function = one reason to change. If a function starts doing more than one thing, extract helpers.
- Modularity:
  - Group related code in modules/packages; expose a small, explicit public API per package.
- Dependency inversion:
  - Depend on interfaces rather than concrete implementations for services (LLMClient, WeatherProvider, Notifier).
- Reuse:
  - Make reusable utilities small and focused. Avoid global mutable state.
- Documentation:
  - Document public APIs, prompt templates, and operational runbooks.

7. Testing strategy & examples
- Unit tests:
  - Mock dependencies; test only business logic.
  - For Python use pytest + pytest-asyncio. For TypeScript use Jest and React Testing Library.
- Integration tests:
  - Use TestContainers or docker-compose test environment for MS SQL, Redis and vector DB.
  - Use real HTTP client (FastAPI TestClient or Playwright) to exercise end-to-end behavior.
- Contract tests:
  - For external APIs (weather providers, OpenAI), record fixtures to assert backward-compatible responses.
- Golden tests for LLMs:
  - Assert required tokens in outputs (presence of action list, no numeric fabrication) rather than exact full string.
  - Use small, focused datasets to validate hallucination rates.
- Mocking LLMs:
  - Provide a deterministic mock LLM server for CI that returns predictable outputs for key prompts.
- Coverage:
  - Aim for meaningful coverage; prefer high coverage of business logic over trivial getters.

8. Observability, logging & telemetry
- Structured logging:
  - Use JSON structured logs with fields: request_id, user_id (nullable), endpoint, duration_ms, status_code, model, tokens_in, tokens_out.
- Tracing:
  - Correlate traces across HTTP handlers, background workers and LLM calls. Use OpenTelemetry.
- Metrics:
  - Track request rate, error rate, LLM token usage/cost, background job durations, forecast freshness.
- Alerts:
  - Set thresholds for cost spikes, failed LLM calls, high error rates.
- Privacy for logs:
  - Redact or hash user text fields; never store raw prompt text without consent and encryption.

9. CI/CD, linters & tooling
- Pre-commit:
  - Use pre-commit hooks for formatting, linting, and security checks (bandit, eslint).
- Linters & formatters:
  - Python: black, isort, flake8/ruff, mypy.
  - TypeScript: prettier, eslint with strict rules.
- Security scanning:
  - Snyk, Dependabot, or GitHub Advanced Security for dependency vulnerabilities.
- Pipelines:
  - CI runs unit tests, linters, and build artifacts. CD deploys to staging on merge to main, with manual gate for prod.
- Containerization:
  - Multi-stage Dockerfiles to reduce image size; use non-root user in containers.
- Secrets in CI:
  - Use secrets store in the CI provider, not environment variables in code.

10. PR checklist & code review guide
- Does the code have tests covering new logic?
- Is the change small and focused? If not, break into multiple PRs.
- Are new dependencies vetted? (size, licencing and security)
- Does the implementation follow SRP and keep layers separated?
- Are plumbing concerns (DB, LLM, network) behind interfaces?
- Is sensitive data protected from logs and telemetry?
- Is the prompt template versioned and included in LLMAudit?
- Have performance implications been considered (DB indexes, caching)?
- Is there documentation (README, running instructions, endpoints)?

11. Example project layout
- backend/
  - app/
    - api/
      - v1/
        - routes/
    - core/
      - config.py
    - services/
      - llm_client.py
      - weather_provider.py
    - db/
      - models.py
      - repositories.py
    - schemas/
      - dto.py
    - workers/
      - scheduler.py
    - main.py
  - tests/
- frontend/
  - src/
    - components/
    - hooks/
    - services/
      - apiClient.ts
    - pages/
    - App.tsx
  - tests/
- infra/
  - docker-compose.yml
  - k8s/
- docs/
  - COPILOT_GUIDELINES.md
  - PROMPTS.md

12. Useful snippets and patterns

A. Python LLM client wrapper (pattern)
```python
# app/services/llm_client.py
from typing import Dict, Any
import time
import logging

class LLMClient:
    def __init__(self, openai_client, audit_repo, model: str = "gpt-4"):
        self.openai = openai_client
        self.audit_repo = audit_repo
        self.model = model
        self.logger = logging.getLogger(__name__)

    async def generate(self, prompt: str, user_id: str | None = None, temperature: float = 0.0, max_tokens: int = 400) -> Dict[str, Any]:
        start = time.time()
        # sanitize prompt for logging
        prompt_summary = prompt[:1000]  # store an abbreviated form
        # call provider (wrap retries/backoff)
        resp = await self.openai.create_chat_completion(
            model=self.model, messages=[{"role":"user","content":prompt}], temperature=temperature, max_tokens=max_tokens
        )
        duration = time.time() - start
        tokens_in = resp.usage.prompt_tokens
        tokens_out = resp.usage.completion_tokens
        # record audit (do not store full prompt unless encrypted/consent)
        self.audit_repo.record(user_id=user_id, endpoint="generate", model=self.model, prompt_summary=prompt_summary, tokens_in=tokens_in, tokens_out=tokens_out, duration=duration)
        return {"text": resp.choices[0].message.content, "tokens_in": tokens_in, "tokens_out": tokens_out}
```

B. Prompt template pattern (store versioned)
```text
# docs/PROMPTS.md (versioned)
- explain_v1:
  description: "Daily summary using structured facts"
  template: |
    System: You are a concise weather assistant. Use only the Data section. Do not invent values.
    Data: {facts_json}
    Task: produce a 2-3 sentence summary, 3 short action items, and the main driver explanation.
```

C. TypeScript API client pattern (centralized)
```typescript
// frontend/src/services/apiClient.ts
import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  withCredentials: true,
  timeout: 15000,
});

api.interceptors.response.use(
  (r) => r,
  (error) => {
    // global error mapping
    return Promise.reject(error.response ?? error);
  }
);

export default api;
```

D. Unit test pattern for Python with mocked LLM
```python
# backend/tests/test_explain.py
import pytest
from app.services.llm_client import LLMClient

class DummyOpenAI:
    async def create_chat_completion(self, **kwargs):
        class Resp:
            usage = type("U", (), {"prompt_tokens": 10, "completion_tokens": 20})
            choices = [type("C", (), {"message": type("M", (), {"content": "Summary\\n- Action 1\\n- Action 2"})})]
        return Resp()

@pytest.mark.asyncio
async def test_explain_generates_summary(tmp_path):
    audit_repo = DummyAuditRepo()
    client = LLMClient(openai_client=DummyOpenAI(), audit_repo=audit_repo)
    out = await client.generate("Data: {...}", user_id="u1")
    assert "Summary" in out["text"]
    assert audit_repo.last_record.tokens_in == 10
```

E. Test double for external weather API (fixture)
- Record a JSON payload for each provider and load that in tests rather than hitting the network.

---

Closing notes
- Keep this document updated as you learn prompt improvements, alternative models or new infra (vector DBs).
- Use the PR checklist and automated linters to keep the code consistent and high quality.
- Document any known issues or limitations with the current implementation.