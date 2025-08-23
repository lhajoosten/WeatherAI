## Summary

<!--
Provide a short, clear description of what this PR accomplishes.
Reference the issue(s) it resolves, e.g. "Fixes #123" or "Implements feature X".
-->

Fixes: #

---

## Type of change

- [ ] Bug fix
- [ ] New feature
- [ ] Improvement / refactor
- [ ] Chore / build / CI
- [ ] Docs

---

## How to test / steps to reproduce

<!--
Provide step-by-step instructions to validate this PR locally (commands, env vars, endpoints).
Example:
1. Checkout branch
2. `docker compose up --build`
3. `python -m pytest app/tests/test_foo.py`
4. Visit http://localhost:5173 and test the Explain flow
-->

1.
2.
3.

---

## Checklist (required where applicable)

- [ ] I added or updated unit tests
- [ ] I ran linters/formatters locally (backend: `black/isort/ruff`, frontend: `eslint/prettier`)
- [ ] Type checks pass (Python mypy, TypeScript `tsc`)
- [ ] All tests pass (`pytest`, frontend tests)
- [ ] I updated or added documentation where relevant (README, docs/, PROMPTS.md)
- [ ] I added/updated any DB migrations (alembic) and included migration instructions
- [ ] I logged relevant LLMAudit metadata for new LLM calls (model/prompt version/tokens) — if applicable
- [ ] I did not commit secrets or .env files

---

## Design notes / implementation details

<!--
Explain important design decisions, trade-offs, and any non-obvious details reviewers should know.
-->

## Rollout & ops notes

- Migration steps:
- Feature flags / toggle plan:
- Monitoring to add (metrics, cost alerts):

---

## Screenshots / logs (if useful)

<!-- Paste screenshots, terminal output, or sample responses -->

---

## Reviewers

/assign @team-member

Please prefer small, focused PRs. If this change is large, consider breaking into multiple PRs (API, migrations, UI).