# AEGIS Dashboard — Code Review Guide

**Project:** AEGIS Dashboard (Hackathon — Deadline March 16, 2026)  
**Companion:** Synthia-Curius (Qwen 30B)  
**Orchestrator:** DeepSeek V3.2  
**Status:** Feature-complete, pre-code-review

---

## 1. Project Overview

AEGIS (Autonomous Execution & Guardrails Interface System) is a Flask-based dashboard that:
- Monitors Docker containers and system health
- Renders visual data (charts, metrics)
- Executes supervised autonomous tasks via LLM orchestration
- Integrates with Discord for alerts and notifications
- Provides a "Visual Cortex" using Playwright for web automation
- Uses SQLite for persistence and rolling context

---

## 2. Completed Features (as of Mar 11, 2026)

| Feature | Status | Notes |
|---------|--------|-------|
| Discord webhook notifications | ✅ | Configurable via `.env` |
| Visual Cortex (Playwright integration) | ✅ | `scan_url` endpoint, screenshot capability |
| Docker monitoring | ✅ | Container stats, health checks |
| Visual Data (charts) | ✅ | Chart.js integration, real-time updates |
| SQLite persistence | ✅ | Stats, logs, context notes |
| Health check endpoint | ✅ | `/health` returns JSON status |
| Rolling context persistence | ✅ | `context_notes` API + Qdrant (hermes_session_memories) |
| Supervisor chat | ✅ | LLM-driven task execution with guardrails |
| Sovereign memory | ✅ | Integrated with Hermes rolling_context skill |

---

## 3. Architecture Highlights

- **Backend:** Flask (Python 3.11)
- **Frontend:** Vanilla JS + Chart.js (no heavy framework)
- **Database:** SQLite (lightweight, file-based)
- **Vector Store:** Qdrant (running locally on port 6333)
- **LLM Integration:** OpenRouter (configurable base URL)
- **Containerization:** Docker + Docker Compose (optional)
- **Auth:** None (local dev only — consider adding basic auth for prod)

---

## 4. Code Review Checklist

### A. Security
- [ ] **Environment variables:** All secrets (API keys, tokens) must be loaded from `.env` and never committed. Verify `.env` is in `.gitignore`.
- [ ] **Input validation:** All user-supplied inputs (URLs, commands) are sanitized. No direct shell execution with unsanitized input.
- [ ] **CORS:** If exposed beyond localhost, configure CORS properly.
- [ ] **Rate limiting:** Consider adding rate limits to public endpoints.
- [ ] **SQL injection:** Using parameterized queries only (SQLAlchemy or sqlite3 with placeholders).
- [ ] **XSS:** Frontend rendering uses safe methods (innerText or textContent) not innerHTML with unsanitized data.

### B. Reliability & Error Handling
- [ ] **Try/except blocks:** All external calls (Docker, Playwright, LLM API) have proper exception handling and graceful degradation.
- [ ] **Timeouts:** Network calls (HTTP, gRPC) have reasonable timeouts.
- [ ] **Logging:** Errors are logged with sufficient context but without leaking secrets.
- [ ] **Graceful shutdown:** Flask app handles SIGTERM/SIGINT to close Docker connections cleanly.

### C. Performance
- [ ] **Database queries:** Uses indexes where appropriate (timestamp columns).
- [ ] **Memory leaks:** No global state that accumulates indefinitely; rolling_context properly summarizes and prunes.
- [ ] **Concurrent requests:** Flask is not threaded by default; if enabling threaded mode, verify thread safety of global objects (like Docker client).
- [ ] **Static assets:** Frontend assets are cached (consider adding cache headers).

### D. Maintainability
- [ ] **Code organization:** Routes, models, and services are separated logically.
- [ ] **Type hints:** Present in new code (optional but recommended).
- [ ] **Documentation:** README.md covers setup, env vars, and usage.
- [ ] **Configuration:** All configurable values (timeouts, retries, thresholds) are in `config.py` or `.env`.

### E. Testing
- [ ] **Unit tests:** Critical functions (parsing, formatting) have tests.
- [ ] **Integration tests:** End-to-end tests for the core flows (Docker → dashboard, Visual Cortex → screenshot, LLM → task execution).
- [ ] **Test coverage:** Aim for >80% on core modules.

### F. Specific Components

#### Docker Monitoring
- [ ] `docker` Python SDK is used with proper error handling if Docker daemon is down.
- [ ] Container stats are polled at a reasonable interval (avoid DoS on Docker API).
- [ ] Sensitive container data (environment variables) is not exposed in API responses.

#### Visual Cortex (Playwright)
- [ ] Playwright is installed with required browsers (`playwright install`).
- [ ] Screenshot endpoint has timeout and memory limits (prevent hanging on large pages).
- [ ] Domain restrictions: Consider allowlist of domains for security.

#### LLM Orchestration (Supervisor)
- [ ] Prompt injection mitigation: System prompt is robust; user input is not directly passed to LLM without guardrails.
- [ ] Token limits: Context window is respected; truncation/summarization happens before hitting limits.
- [ ] Cost tracking: Optional logging of token usage per request.

#### Rolling Context (Qdrant)
- [ ] Collection `hermes_session_memories` exists and is accessible.
- [ ] Embedding generation uses OpenAI credentials from env (`OPENAI_API_KEY`).
- [ ] Summaries are stored with session_id, timestamp, tags.
- [ ] Retrieval limit is configurable (`CONTEXT_MAX_RESULTS`).

---

## 5. Environment Variables Checklist

```
DISCORD_WEBHOOK_URL=           # For notifications
DASHBOARD_URL=                 # Public URL (ngrok or domain)
FLASK_ENV=                     # development|production
DISCORD_TOKEN=                 # Bot token (if using Discord API)
HERMES_CONTEXT_QDRANT=true     # Enable rolling context (optional)
QDRANT_URL=http://localhost:6333
OPENAI_API_KEY=                # For embeddings
OPENAI_BASE_URL=               # Custom endpoint if needed
```

Ensure all sensitive keys are stored in `.env` and never committed.

---

## 6. Known Issues / Technical Debt

1. **Time formatting:** Discrepancy between UTC and MT timezone observed. Current decision: stick with UTC for consistency. If localization is needed later, use `pytz` or `zoneinfo` with user preference stored in profile.
2. **Qdrant dependency:** `qdrant-client` installed in agent venv. If deploying, ensure venv includes it or install system-wide.
3. **sudo requirements:** Some operations (installing system packages, starting services) may need sudo. Document required commands for fresh VM setup.
4. **Playwright browsers:** Must be installed separately (`playwright install chromium`). Include in setup script.

---

## 7. Pre-Release Verification

- [ ] All endpoints respond within acceptable latency (<2s typical, <5s for heavy operations).
- [ ] No secrets in git history (`git grep -i token`, `git grep -i key`).
- [ ] `.env` template (`.env.example`) is up-to-date.
- [ ] README includes:
  - Quickstart steps
  - How to obtain Discord webhook URL and token
  - How to install Playwright browsers
  - How to run with Docker (if applicable)
  - How to enable rolling_context with Qdrant
- [ ] Health check endpoint returns 200 and shows all subsystems (Docker, DB, Qdrant) status.
- [ ] Graceful degradation: If Docker is down, dashboard shows error but doesn't crash.

---

## 8. Upgrade Path (Better Model)

When switching to a more capable LLM (e.g., GPT-4, Claude 3.5 Sonnet, or local 70B+ model):

1. **Update base URL / model ID** in `.env` or config.
2. **Adjust prompt templates** — better models may need less verbose instructions; test for output consistency.
3. **Re-tune guardrails** — ensure the new model follows the same safety constraints (no shell injection, no exfiltration).
4. **Benchmark token usage** — more capable models may be more verbose; monitor costs.
5. **Run full integration test suite** to ensure no regressions.

---

## 9. Deployment Considerations

- **Process manager:** Use `systemd` or `supervisord` to keep Flask app running.
- **Reverse proxy:** Nginx + HTTPS if exposing to internet.
- **Database backups:** SQLite file is single point of failure; set up periodic backups.
- **Logging:** Configure Flask logging to file and/or syslog; consider log rotation.
- **Monitoring:** Use health check endpoint with external uptime monitor (e.g., UptimeRobot).

---

## 10. Contact & Ownership

- **Primary maintainer:** Adora (stormwife) & Narusya (Hermes)
- **Repository:** https://github.com/Septa-Serpenta-Saph/AEGIS-Dashboard (if public) or private fork
- **Documentation updates:** Keep this guide in sync with changes.

---

**Last updated:** 2026-03-11  
**Next review:** Before switching LLM model / before hackathon submission
