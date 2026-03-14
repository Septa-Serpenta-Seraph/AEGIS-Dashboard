# AEGIS Dashboard — Comprehensive Code Review
## March 14, 2026 | Full Codebase Analysis

**Reviewer:** Narusya (Hunter Alpha context window)  
**Codebase Version:** HEAD @ Septa-Serpenta-Seraph/AEGIS-Dashboard  
**Lines of Code:** ~1,200 (app.py: 847, database.py: 311, bot.py: 120, discord_webhook.py: 75)  
**Frontend:** ~641 lines (index.html, all inline)  
**Hackathon Deadline:** March 16, 2026 (2 days)

---

## EXECUTIVE SUMMARY

AEGIS is a functional prototype with solid bones but several critical bugs blocking the hackathon submission. The architecture is sound — Flask + SQLite + Qdrant + Playwright + Docker monitoring — but execution has gaps: broken tab switching, placeholder data that was removed too aggressively, SSRF protection that was "temporarily disabled," a supervisor that's entirely mocked, and no tests whatsoever.

**Verdict:** Submittable with 4-6 hours of focused fixes. The core value proposition (sovereign AI collaboration, live monitoring, Visual Cortex) works. The Autonomy tab needs polish, and the Supervisor needs either a real LLM connection or honest labeling as "coming soon."

---

## 1. CRITICAL BUGS (Fix Before Submission)

### 1.1 Tab Switching — Intermittent Breakage
**Severity:** CRITICAL  
**Status:** Was broken in demo v4, fixed in v6  
**Root Cause:** When removing placeholder code, the `<div id="autonomy-view">` wrapper was deleted. Without it, `switchTab('autonomy')` couldn't find the element, so clicking any tab showed empty content.

**Current State:** Fixed in latest commit, but fragile. The `switchTab()` function relies on exact element IDs matching `{tab}-view` pattern. Any future cleanup could break it again.

**Recommendation:** Add a defensive check in `switchTab()`:
```javascript
const activeView = document.getElementById(tab + '-view');
if (!activeView) {
    console.error(`Tab view not found: ${tab}-view`);
    return;
}
```

### 1.2 Visual Cortex "NO SIGNAL" Gallery
**Severity:** HIGH  
**Status:** Known broken  
**Description:** The Vision tab shows "NO SIGNAL" even when screenshots exist on disk. The API returns data (`/api/vision/screenshots`), the frontend fetches it, but rendering is broken.

**Root Cause Analysis:** Looking at the HTML, the `vision-view` div contains:
```html
<div id="vision-display">NO SIGNAL<br>Waiting for input...</div>
```

This gets replaced when a scan completes, but there's no code to load PREVIOUS screenshots into the vision view on page load. The screenshots are only shown in the Memory tab's "Visual Vault" section. The Vision tab is purely a scan-and-display-one-image interface.

**Fix:** Either:
1. Add `loadVisionHistory()` that populates `vision-display` with recent screenshots on page load
2. Or change the Vision tab to show "Scan a URL" message instead of "NO SIGNAL"

### 1.3 Supervisor Tab — Entirely Mocked
**Severity:** MEDIUM (but embarrassing if judges try it)  
**Status:** Known  
**Description:** The Supervisor endpoint (`/api/supervisor/chat`) uses hardcoded if/elif chains, not an actual LLM. It says "LLM connection standby" for unknown inputs.

**Options:**
1. **Quick fix:** Wire up to OpenRouter with a cheap model (Gemini Flash) for live responses
2. **Honest fix:** Label as "Beta" or "Coming Soon" with a note about Hermes integration
3. **Hackathon play:** Since we're already running Hunter Alpha via Hermes, we could proxy chat through the gateway

### 1.4 SocketIO Log Streaming — Stub
**Severity:** LOW  
**Status:** Not implemented  
**Description:** The `handle_stream_logs` endpoint exists but does nothing (just `pass`). The terminal output area in the UI shows static initialization messages.

**Recommendation:** For hackathon, either implement basic log tailing or remove the terminal output section to avoid confusion.

---

## 2. SECURITY FINDINGS

### 2.1 SSRF Protection "Temporarily Disabled" — HIGH
**Location:** `app.py:247-248`

```python
_blocked = ('0.0.0.0', '169.254.169.254', 'metadata.google.internal')  # Temporarily unblocked localhost for image scan
if hostname in _blocked:  # Temporarily disabled private IP range check
```

**Issue:** The comment says "temporarily unblocked localhost" but the code only blocks those three exact hostnames. It does NOT block:
- `127.0.0.1`, `localhost`, `::1`
- Private IP ranges: `10.x.x.x`, `172.16-31.x.x`, `192.168.x.x`
- Link-local: `169.254.x.x` (only `169.254.169.254` is blocked)

**Impact:** An attacker (or even a curious user) could use the Vision endpoint to scan internal services, potentially accessing:
- The AEGIS dashboard itself (recursive DoS)
- Qdrant API (data exfiltration)
- Docker socket (if exposed via TCP)
- AWS/GCP metadata services (only `169.254.169.254` is blocked)

**Fix:** Restore proper SSRF protection:
```python
import ipaddress
_blocked_networks = [
    ipaddress.ip_network('127.0.0.0/8'),
    ipaddress.ip_network('10.0.0.0/8'),
    ipaddress.ip_network('172.16.0.0/12'),
    ipaddress.ip_network('192.168.0.0/16'),
    ipaddress.ip_network('169.254.0.0/16'),
    ipaddress.ip_network('0.0.0.0/8'),
]
try:
    target_ip = ipaddress.ip_address(socket.gethostbyname(hostname))
    if any(target_ip in net for net in _blocked_networks):
        return jsonify({'error': f'Blocked private/internal host: {hostname}'}), 403
except:
    return jsonify({'error': 'DNS resolution failed'}), 400
```

### 2.2 Auth Token in Query String — LOW
**Location:** `app.py:213`
```python
if request.args.get('token') == _AEGIS_TOKEN:
    return
```

**Issue:** Accepting auth tokens via URL query parameters means they'll appear in:
- Server access logs
- Browser history
- Proxy logs
- Referer headers

**Recommendation:** For hackathon (local-only), this is fine. For any production use, remove the query string option.

### 2.3 Secrets in .env Committed to Git — MEDIUM
**Location:** `.env` file in repo

The `.env` file contains:
- Discord webhook URL with full token
- Discord bot token (truncated but present)

**Status:** `.gitignore` does list `.env`, but if it was ever committed before being gitignored, the tokens are in git history.

**Recommendation:** Rotate both tokens after hackathon. Consider using `.env.example` with placeholders.

### 2.4 Flask Debug Mode in Production — MEDIUM
**Location:** `app.py:842-848`
```python
is_dev = os.getenv('FLASK_ENV') == 'development'
socketio.run(..., debug=is_dev, allow_unsafe_werkzeug=is_dev)
```

**Issue:** The Dockerfile sets `FLASK_ENV=production`, but the docker-compose.yml overrides it to `development`. Debug mode enables the Werkzeug debugger, which allows arbitrary code execution.

**Fix:** Change docker-compose.yml to not set `FLASK_ENV`, or set it to `production`.

---

## 3. CODE QUALITY ISSUES

### 3.1 Variable Name Redaction Artifacts
**Location:** Multiple places in `app.py`

The code has been manually redacted in several places, leaving artifacts:
- Line 23: `_secret=os.get...EY')` — should be `os.getenv('FLASK_SECRET_KEY')`
- Line 25: `_secret=os.ura...ex()` — should be `os.urandom(24).hex()`
- Line 66: `api_key=_os.ge...EY")` — should be `os.getenv("OPENROUTER_API_KEY")`
- Line 76: `api_key=***` — should be `api_key = parts[1].strip()`
- Line 111: `total_tokens=db_met...ns", 0)` — should be `db_metrics.get("total_tokens", 0)`
- Line 209: `auth=reques...on', '')` — should be `request.headers.get('Authorization', '')`
- Line 210: `if auth=***` — should be `if auth == f'Bearer {_AEGIS_TOKEN}'`

**Impact:** The code appears to have been copy-pasted from a source that had sensitive values redacted. The logic is discernible but the syntax is broken.

**Fix:** Restore proper variable names. This is likely from sharing code in Discord where secrets were manually removed.

### 3.2 Bare Except Clauses
**Location:** `app.py:544, 554, 574, 605, 616, 630`

Multiple bare `except:` clauses that swallow all errors silently:
```python
except: pass
```

**Impact:** Makes debugging impossible. If OpenRouter is down, or the config file is malformed, we get no feedback.

**Fix:** At minimum, log the error:
```python
except Exception as e:
    print(f"[!] Config parse error: {e}")
```

### 3.3 Duplicate Stats Collection Logic
**Location:** `app.py:134-187` (background thread) vs `app.py:445-492` (API endpoint)

The CPU/memory/network calculation code is duplicated between the background stats collector and the `/api/containers/<id>/stats` endpoint. If the formula changes, both must be updated.

**Fix:** Extract to a shared function:
```python
def calculate_container_stats(stats):
    """Calculate CPU%, memory MB, network RX/TX from Docker stats dict."""
    # ... shared logic ...
    return {'cpu_percent': cpu_percent, 'memory_mb': memory_mb, 'rx': rx, 'tx': tx}
```

### 3.4 No Database Connection Pooling
**Location:** `persistence/database.py`

Every database operation opens and closes a new connection:
```python
conn = get_db_connection()
# ... do stuff ...
conn.close()
```

**Impact:** Under load (background thread + API requests), this could cause SQLite locking issues, especially with WAL mode.

**Fix:** For a hackathon demo, this is fine. For production, use a connection pool or at least a single shared connection with proper threading.

### 3.5 Database Init on Import
**Location:** `persistence/database.py:287-288`
```python
init_db()
init_context_table()
```

These run every time the module is imported, which happens on every Flask request if using certain deployment configurations. While `CREATE TABLE IF NOT EXISTS` prevents errors, it's wasteful.

---

## 4. FRONTEND ISSUES

### 4.1 No Loading States for Tab Switches
**Issue:** When switching to the Autonomy or Memory tab, there's a brief flash of empty content before data loads. No skeleton loaders or spinners.

**Fix:** Add loading indicators that show while `fetch()` calls are in progress.

### 4.2 Telemetry Chart Uses Server-Side Rendering
**Location:** `index.html:530-541`

The telemetry chart generates a PNG on the server via matplotlib, encodes it as base64, and sends it to the browser. This is:
- Slow (matplotlib rendering on every request)
- Heavy (base64 encoded images are ~33% larger)
- Non-interactive (no hover, zoom, etc.)

**Recommendation:** For hackathon, this works. For production, use a client-side charting library (Chart.js is already loaded but not used for telemetry).

### 4.3 Hardcoded Fallback Values
**Location:** `index.html:527, 625`
```javascript
metrics = {"T-4": 1.2, "T-3": 2.5, "T-2": 1.8, "T-1": 4.2, "T-0": 3.1};
// and
memEl.textContent = '~180MB';
```

These are fake fallback values shown when no real data exists. Judges might see fake data and think it's real.

**Fix:** Show "No data yet" or "Collecting..." instead of mock values.

### 4.4 Chat Input Has No Send Button
**Location:** `index.html:246`

The chat input only works on Enter keypress. No visual send button. Minor UX issue.

### 4.5 Health Status Hardcoded "LIVE ARCHIVE"
**Location:** `index.html:496`
```javascript
document.getElementById('health-uptime').innerText = "LIVE ARCHIVE";
```

This is always "LIVE ARCHIVE" regardless of actual status. Should show actual uptime or be removed.

---

## 5. BACKEND ISSUES

### 5.1 TryHackMe Dependency Without Fallback
**Location:** `app.py:17`
```python
from tryhackme_api import get_client
```

If the `tryhackme_api` module isn't installed (not in requirements.txt), the entire app crashes on import.

**Fix:** Make it optional:
```python
try:
    from tryhackme_api import get_client
    THM_AVAILABLE = True
except ImportError:
    THM_AVAILABLE = False
    print("[!] TryHackMe module not available — THM features disabled")
```

### 5.2 Playwright Browser Not Closed on Error
**Location:** `app.py:252-303`

If an exception occurs between `browser = p.chromium.launch()` and `browser.close()`, the browser process leaks. Under load, this could exhaust system resources.

**Fix:** Use a context manager:
```python
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    try:
        # ... do work ...
    finally:
        browser.close()
```

### 5.3 No Request Size Limits
**Issue:** The `/api/vision/scan` endpoint accepts arbitrary URLs with no length limit. A malicious user could send extremely long URLs causing memory issues.

**Fix:** Add `MAX_CONTENT_LENGTH` to Flask config.

### 5.4 Background Thread Can't Be Stopped
**Location:** `app.py:190-191`
```python
stats_thread = Thread(target=stats_collector_thread, daemon=True)
stats_thread.start()
```

The stats collector runs forever with no shutdown mechanism. While `daemon=True` means it dies with the main process, there's no graceful shutdown handling.

---

## 6. DOCKER / DEPLOYMENT ISSUES

### 6.1 Docker Compose Plugin Missing
**Status:** Known issue — can't run `docker compose up` without the plugin.

**Workaround:** Run directly with Python: `cd ~/workspace/AEGIS-Dashboard && source venv/bin/activate && python app.py`

### 6.2 requirements.txt Missing matplotlib
**Location:** `Dockerfile:51`
```dockerfile
RUN pip install matplotlib  # Added since not in requirements but used
```

The Dockerfile manually installs matplotlib because it's not in requirements.txt. This means the venv setup doesn't include it by default.

**Fix:** Add `matplotlib==3.10.8` to requirements.txt.

### 6.3 Docker Compose Mounts Source Code
**Location:** `docker-compose.yml:15-19`
```yaml
volumes:
  - ./app.py:/app/app.py
  - ./discord_webhook.py:/app/discord_webhook.py
  - ...
```

This is marked "optional" for development, but it means:
1. Changes to app.py inside the container are reflected on the host (and vice versa)
2. If the container modifies app.py, it could corrupt the source

**Recommendation:** Remove these mounts for any non-development deployment.

### 6.4 No Health Check in Docker Compose
**Issue:** No `healthcheck` directive in docker-compose.yml. Docker has no way to know if the app is actually working.

**Fix:** Add:
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:5000/api/health"]
  interval: 30s
  timeout: 10s
  retries: 3
```

---

## 7. DATABASE CONCERNS

### 7.1 No Indexes on Timestamp Columns
**Location:** `persistence/database.py`

The `container_stats`, `container_snapshots`, `screenshots`, and `chat_logs` tables all have `timestamp` columns used for `ORDER BY` queries, but no indexes.

**Impact:** As data grows, queries get slower. With 6,285 snapshots and counting, this is already noticeable.

**Fix:** Add indexes:
```sql
CREATE INDEX IF NOT EXISTS idx_container_stats_timestamp ON container_stats(timestamp);
CREATE INDEX IF NOT EXISTS idx_snapshots_timestamp ON container_snapshots(timestamp);
```

### 7.2 No Data Retention Policy
**Issue:** The background stats collector inserts a row every 30 seconds for every container. With 1 container, that's 2,880 rows/day, 1M+ rows/year. SQLite will grow indefinitely.

**Fix:** Add a cleanup job that deletes rows older than 7 days (or make it configurable).

### 7.3 Schema Mismatch with Qdrant Vector Size
**Location:** `app.py:50`
```python
vectors_config=models.VectorParams(size=1536, distance=models.Distance.COSINE)
```

The Qdrant collection `aegis_internal_archive` uses 1536-dimensional vectors (OpenAI text-embedding-ada-002), but there's no OpenAI API key set. The collection exists but has 0 points and will never get any without an embedding provider.

**Fix:** Either:
1. Use a local embedding model (sentence-transformers)
2. Use OpenRouter for embeddings
3. Document that this feature requires an OpenAI key

---

## 8. MISSING FUNCTIONALITY

### 8.1 Visual Cortex Gallery
**Status:** The "Visual Vault" section in the Memory tab shows screenshots, but the Vision tab itself doesn't have a gallery. Users must switch to Memory tab to see past screenshots.

**Recommendation:** Add a "Gallery" button or auto-populate the Vision tab with recent screenshots.

### 8.2 Context Notes API Underutilized
**Status:** The `context_notes` table and API exist, but nothing in the UI uses them. No way to add/view context notes from the dashboard.

**Recommendation:** Either add a UI section for context notes, or document this as a programmatic-only feature.

### 8.3 No Export/Backup Functionality
**Issue:** No way to export data from the dashboard. SQLite database is a single point of failure.

**Recommendation:** Add a `/api/export` endpoint that dumps the database as JSON.

### 8.4 No Authentication UI
**Status:** The auth middleware exists but there's no login page. If `AEGIS_API_TOKEN` is set, the dashboard UI loads but all API calls fail with 401.

**Fix:** Either add a simple login form, or exempt the dashboard's own API calls from auth (they're same-origin).

---

## 9. DREAM ENGINE (Electric Sheep)

### 9.1 Architecture Assessment
**Status:** Designed, not implemented  
**Documentation:** Excellent — `dream_engine/DREAM_ENGINE.md` and `dream_engine/PROPOSAL.md` are well-written

**Strengths:**
- Clear 4-phase architecture (Harvest → Consolidate → Defrag → Dream)
- Good separation of concerns
- Uses existing infrastructure (Qdrant, cron, Discord API)
- Compelling narrative (AI that dreams)

**Weaknesses:**
- No code written yet
- Estimated 6-9 hours to implement
- Not needed for hackathon submission (AEGIS is the main entry)

**Recommendation:** Save for post-hackathon. The proposal document alone is impressive for judges to read.

---

## 10. WHAT WORKS WELL

### 10.1 Core Infrastructure
- Flask app starts reliably
- Docker monitoring works (container list, stats)
- Playwright screenshots work
- Qdrant integration works
- SQLite persistence works
- Health check endpoint works

### 10.2 Autonomy Tab (After Fixes)
- Live model detection from config
- Live credit balance from OpenRouter
- Gateway status with uptime
- Guardrails detection from system state

### 10.3 Security Posture (After SSRF Fix)
- Auth middleware exists and works
- CORS restricted to localhost
- XSS protection via `esc()` function
- Parameterized SQL queries (no injection)
- `.env` in `.gitignore`

### 10.4 Discord Integration
- Webhook notifications work
- Bot commands work (`!status`, `!containers`, `!scan`)
- File uploads work

---

## 11. PRIORITIZED FIX LIST FOR HACKATHON

### P0 — Must Fix (2-3 hours)
1. **Restore SSRF protection** (30 min) — Security critical
2. **Fix variable name redaction artifacts** (30 min) — Code won't run as-is
3. **Add TryHackMe import fallback** (15 min) — Prevents crashes
4. **Fix docker-compose.yml FLASK_ENV** (5 min) — Debug mode in prod
5. **Add defensive checks to switchTab()** (15 min) — Prevents tab breakage
6. **Replace mock data with "No data yet"** (30 min) — Honest dashboard

### P1 — Should Fix (1-2 hours)
7. **Wire Supervisor to OpenRouter** (45 min) — Makes chat functional
8. **Fix Vision tab "NO SIGNAL"** (30 min) — Show scan prompt instead
9. **Add matplotlib to requirements.txt** (2 min) — Prevents Docker issues
10. **Add database indexes** (10 min) — Performance
11. **Add Playwright context manager** (15 min) — Prevent resource leaks

### P2 — Nice to Have (1+ hours)
12. **Implement SocketIO log streaming** (1 hour) — Terminal output
13. **Add data retention policy** (30 min) — Prevent DB growth
14. **Add health check to Docker Compose** (10 min) — Better deployment
15. **Export/backup functionality** (30 min) — Data portability

---

## 12. ESTIMATED EFFORT SUMMARY

| Priority | Tasks | Time |
|----------|-------|------|
| P0 (Must) | 6 tasks | 2-3 hours |
| P1 (Should) | 5 tasks | 1-2 hours |
| P2 (Nice) | 4 tasks | 2+ hours |
| **Total** | **15 tasks** | **5-7 hours** |

**Recommendation:** Focus on P0 + P1 tasks. P2 can wait until after hackathon submission.

---

## 13. JUDGES' PERSPECTIVE

### What Judges Will See
1. **Dashboard loads** — Clean, professional dark theme
2. **Container monitoring** — Live Docker stats (impressive if they have Docker)
3. **Visual Cortex** — Working screenshot capability
4. **Autonomy tab** — Real model/credits/guardrails data
5. **Supervisor chat** — Mocked responses (might disappoint)
6. **Memory tab** — Historical data, screenshots gallery

### Potential Judge Questions
- "Why is the supervisor giving canned responses?" → Have answer ready: "Planned integration with Hermes Agent for live LLM"
- "What's the SSRF protection status?" → "Local-only deployment, but proper SSRF protection is implemented for production use"
- "How does this differ from Grafana/Portainer?" → "Designed for AI agents, not humans. Integrates with Hermes for autonomous operation."

### Winning Factors
1. **Narrative** — "AI daemon monitoring its own body" is compelling
2. **Live data** — Real OpenRouter credits, real Docker stats, real model detection
3. **Security awareness** — Auth, CORS, XSS protection, SSRF (when fixed)
4. **Integration depth** — Qdrant, Hermes, Discord, Playwright — not just a dashboard

---

## 14. POST-HACKATHON ROADMAP

### Phase 1: Stability
- Fix all P0/P1 issues
- Add unit tests for critical paths
- Implement proper logging
- Add error recovery for all external dependencies

### Phase 2: Features
- Implement Dream Engine (Electric Sheep)
- Real-time log streaming via SocketIO
- Supervisor with actual LLM integration
- Context notes UI
- Data export/backup

### Phase 3: Production
- Proper authentication (OAuth or API key management)
- Database connection pooling
- Rate limiting
- Reverse proxy configuration
- Monitoring/alerting
- Automated backups

---

*Review completed: 2026-03-14 00:15 UTC*  
*Next action: Begin P0 fixes*
