# AEGIS Dashboard — Proposed Fixes
## Old Code → New Code (Not Yet Applied)

**Date:** 2026-03-14  
**Purpose:** Show exact changes needed before implementing  
**Status:** PROPOSAL ONLY — no code modified yet

---

## P0 — MUST FIX

---

### FIX #1: Variable Name Redaction Artifacts
**File:** `app.py`  
**Impact:** Code won't run — syntax errors from copy-paste redaction

#### Line 23-25 — Flask Secret Key
```
OLD:
_secret=os.get...EY')
if not _secret:
    _secret=os.ura...ex()

NEW:
_secret = os.getenv('FLASK_SECRET_KEY')
if not _secret:
    _secret = os.urandom(24).hex()
```

#### Line 66 — OpenRouter API Key Lookup
```
OLD:
api_key=_os.ge...EY") or _os.getenv("OPENROUTER_KEY")

NEW:
api_key = _os.getenv("OPENROUTER_API_KEY") or _os.getenv("OPENROUTER_KEY")
```

#### Line 76 — Key Assignment from .env Parse
```
OLD:
api_key=***

NEW:
api_key = parts[1].strip()
```

#### Line 111 — Token Count from DB Metrics
```
OLD:
total_tokens=db_met...ns", 0)

NEW:
total_tokens = db_metrics.get("total_tokens", 0)
```

#### Line 198 — Auth Token
```
OLD:
_AEGIS_TOKEN=os.get...EN')

NEW:
_AEGIS_TOKEN = os.getenv('AEGIS_API_TOKEN')
```

#### Line 209 — Authorization Header Read
```
OLD:
auth=reques...on', '')

NEW:
auth = request.headers.get('Authorization', '')
```

#### Line 210 — Auth Comparison (ALSO A BUG: = vs ==)
```
OLD:
if auth=*** f'Bearer {_AEGIS_TOKEN}':

NEW:
if auth == f'Bearer {_AEGIS_TOKEN}':
```

#### Line 215 — Return Statement Truncated
```
OLD:
return jsonify({'error': 'Unauthorized — set Authorization: Bearer *** 401

NEW:
return jsonify({'error': 'Unauthorized — set Authorization: Bearer <token>'}), 401
```

---

### FIX #2: SSRF Protection Restored
**File:** `app.py`, lines 238-249  
**Impact:** Currently allows scanning internal IPs (127.0.0.1, 10.x, 192.168.x)

```
OLD (lines 238-249):
    # --- SSRF Protection: only allow http/https to public hosts ---
    from urllib.parse import urlparse
    try:
        parsed = urlparse(url)
    except Exception:
        return jsonify({'error': 'Invalid URL'}), 400
    if parsed.scheme not in ('http', 'https'):
        return jsonify({'error': f'Blocked scheme: {parsed.scheme} — only http/https allowed'}), 400
    hostname = (parsed.hostname or '').lower()
    _blocked = ('0.0.0.0', '169.254.169.254', 'metadata.google.internal')  # Temporarily unblocked localhost for image scan
    if hostname in _blocked:  # Temporarily disabled private IP range check
        return jsonify({'error': f'Blocked internal/private host: {hostname}'}), 403

NEW (replace lines 238-249):
    # --- SSRF Protection: only allow http/https to public hosts ---
    from urllib.parse import urlparse
    import socket
    import ipaddress
    try:
        parsed = urlparse(url)
    except Exception:
        return jsonify({'error': 'Invalid URL'}), 400
    if parsed.scheme not in ('http', 'https'):
        return jsonify({'error': f'Blocked scheme: {parsed.scheme} — only http/https allowed'}), 400
    hostname = (parsed.hostname or '').lower()
    
    # Block reserved/special hostnames
    _blocked_hosts = ('0.0.0.0', 'localhost', 'metadata.google.internal', 
                      'metadata.azure.com', '169.254.169.254')
    if hostname in _blocked_hosts:
        return jsonify({'error': f'Blocked host: {hostname}'}), 403
    
    # Resolve hostname and check against private IP ranges
    try:
        resolved_ip = socket.gethostbyname(hostname)
        ip = ipaddress.ip_address(resolved_ip)
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
            return jsonify({'error': f'Blocked private/internal IP: {hostname} ({resolved_ip})'}), 403
    except (socket.gaierror, ValueError):
        return jsonify({'error': f'Cannot resolve hostname: {hostname}'}), 400
```

---

### FIX #3: TryHackMe Import Fallback
**File:** `app.py`, line 17  
**Impact:** App crashes if `tryhackme_api` module not installed

```
OLD (line 17):
from tryhackme_api import get_client

NEW (replace line 17):
try:
    from tryhackme_api import get_client
    THM_AVAILABLE = True
except ImportError:
    THM_AVAILABLE = False
    get_client = None
    print("[!] tryhackme_api not installed — TryHackMe features disabled")
```

**Also need to update THM endpoints (lines 674-695):**
```
OLD (line 674-695):
@app.route('/api/tryhackme/profile', methods=['GET'])
def tryhackme_profile():
    client = get_client()
    ...

NEW:
@app.route('/api/tryhackme/profile', methods=['GET'])
def tryhackme_profile():
    if not THM_AVAILABLE:
        return jsonify({'success': False, 'error': 'TryHackMe module not installed'}), 501
    client = get_client()
    ...
```

Same pattern for `/api/tryhackme/rooms` and `/api/tryhackme/progress`.

---

### FIX #4: Docker Compose Debug Mode
**File:** `docker-compose.yml`, line 21  
**Impact:** Flask debug mode enabled in Docker (allows arbitrary code execution)

```
OLD (line 21):
    environment:
      - FLASK_ENV=development
      - DOCKER_HOST=unix:///var/run/docker.sock

NEW:
    environment:
      - FLASK_ENV=production
      - DOCKER_HOST=unix:///var/run/docker.sock
```

Or simply remove the `FLASK_ENV` line entirely (the Dockerfile already sets it to production).

---

### FIX #5: Defensive Tab Switching
**File:** `templates/index.html`, lines 343-370  
**Impact:** Tab switching crashes if any view element is missing

```
OLD (lines 343-370):
        function switchTab(tab) {
            // Views — hide all, then show the target
            const views = ['vision-view', 'persistence-view', 'autonomy-view', 'chat-view'];
            views.forEach(v => {
                const el = document.getElementById(v);
                el.style.display = 'none';
            });
            
            // Highlight buttons
            const buttons = ['tab-vision', 'tab-persistence', 'tab-autonomy', 'tab-chat'];
            buttons.forEach(b => {
                document.getElementById(b).classList.add('bg-black', 'text-gray-500');
                document.getElementById(b).classList.remove('bg-gray-900', 'text-gray-300', 'text-white');
            });

            // Activate current view
            const activeView = document.getElementById(tab + '-view');
            activeView.style.display = 'flex';
            ...

NEW:
        function switchTab(tab) {
            // Views — hide all, then show the target
            const views = ['vision-view', 'persistence-view', 'autonomy-view', 'chat-view'];
            views.forEach(v => {
                const el = document.getElementById(v);
                if (el) el.style.display = 'none';
            });
            
            // Highlight buttons
            const buttons = ['tab-vision', 'tab-persistence', 'tab-autonomy', 'tab-chat'];
            buttons.forEach(b => {
                const btn = document.getElementById(b);
                if (btn) {
                    btn.classList.add('bg-black', 'text-gray-500');
                    btn.classList.remove('bg-gray-900', 'text-gray-300', 'text-white');
                }
            });

            // Activate current view
            const activeView = document.getElementById(tab + '-view');
            if (!activeView) {
                console.error(`Tab view not found: ${tab}-view`);
                return;
            }
            activeView.style.display = 'flex';
            
            const tabId = tab === 'persistence' ? 'tab-persistence' : 'tab-' + tab;
            const activeBtn = document.getElementById(tabId);
            if (activeBtn) {
                activeBtn.classList.remove('bg-black', 'text-gray-500');
                activeBtn.classList.add('bg-gray-900', 'text-white');
            }

            if (tab === 'persistence') {
                loadPersistenceData();
            } else if (tab === 'autonomy') {
                loadAutonomyData();
            }
        }
```

---

### FIX #6: Remove Fake Fallback Data
**File:** `templates/index.html`  
**Impact:** Shows fake CPU/memory values when no data exists

#### Line 527 — Telemetry Mock Data
```
OLD (line 527):
                    metrics = {"T-4": 1.2, "T-3": 2.5, "T-2": 1.8, "T-1": 4.2, "T-0": 3.1};

NEW:
                    // No data available yet — show empty state
                    display.innerHTML = '<div class="text-gray-600 text-xs">No telemetry data yet. Stats collect every 30s.</div>';
                    return;
```

#### Line 625 — Memory Fallback
```
OLD (line 625):
                        memEl.textContent = '~180MB';

NEW:
                        memEl.textContent = 'No data';
```

---

## P1 — SHOULD FIX

---

### FIX #7: Supervisor → OpenRouter Connection
**File:** `app.py`, lines 714-778  
**Impact:** Supervisor chat is entirely mocked

```
OLD (lines 714-778):
@app.route('/api/supervisor/chat', methods=['POST'])
def supervisor_chat():
    data = request.json
    user_message = data.get('message', '')
    
    system_prompt = """..."""
    
    # Mock logic for MVP (replace with real LLM call later)
    if "status" in user_message.lower():
        response = "All systems nominal..."
    elif "error" in user_message.lower():
        response = "Scanning logs..."
    # ... more elif chains ...
    else:
        response = f"Supervisor acknowledges: {user_message}. (LLM connection standby)"

    return jsonify({
        'success': True, 
        'response': response,
        'sender': 'Supervisor (Phi-3)'
    })

NEW:
@app.route('/api/supervisor/chat', methods=['POST'])
def supervisor_chat():
    data = request.json
    user_message = data.get('message', '')
    
    system_prompt = """You are the AEGIS Supervisor Agent. You monitor Docker containers, 
    system health, and help debug issues. You have access to container stats and logs.
    Be concise and technical. If asked about system status, check /api/health."""
    
    # Gather system context
    system_context = ""
    try:
        health = requests.get('http://localhost:5000/api/health').json()
        system_context = f"\nCurrent system status: {health}"
    except:
        pass
    
    # Call OpenRouter
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        # Try hermes .env
        hermes_env = os.path.expanduser("~/.hermes/.env")
        if os.path.exists(hermes_env):
            with open(hermes_env) as f:
                for line in f:
                    if 'OPENROUTER' in line and 'KEY' in line:
                        parts = line.split('=', 1)
                        if len(parts) == 2:
                            api_key = parts[1].strip()
                            break
    
    if not api_key:
        return jsonify({
            'success': True,
            'response': 'Supervisor is in standby mode. No LLM API key configured. Set OPENROUTER_API_KEY to enable.',
            'sender': 'Supervisor (Offline)'
        })
    
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "google/gemini-2.0-flash-001",  # Cheap, fast model
            "messages": [
                {"role": "system", "content": system_prompt + system_context},
                {"role": "user", "content": user_message}
            ],
            "max_tokens": 500
        }
        resp = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=15
        )
        if resp.status_code == 200:
            response = resp.json()["choices"][0]["message"]["content"]
            return jsonify({
                'success': True,
                'response': response,
                'sender': 'Supervisor (Gemini Flash)'
            })
        else:
            return jsonify({
                'success': True,
                'response': f'LLM returned status {resp.status_code}. Falling back to diagnostics.',
                'sender': 'Supervisor (Degraded)'
            })
    except Exception as e:
        return jsonify({
            'success': True,
            'response': f'LLM connection failed: {str(e)}',
            'sender': 'Supervisor (Error)'
        })
```

---

### FIX #8: Vision Tab — Replace "NO SIGNAL" with Scan Prompt
**File:** `templates/index.html`, lines 129-133  
**Impact:** Vision tab shows confusing "NO SIGNAL" on load

```
OLD (lines 129-133):
                <div id="vision-view" class="absolute inset-0 bg-black p-2 flex flex-col items-center justify-center">
                    <div class="text-gray-700 text-xs text-center" id="vision-display">
                        NO SIGNAL<br>Waiting for input...
                    </div>
                </div>

NEW:
                <div id="vision-view" class="absolute inset-0 bg-black p-2 flex flex-col items-center justify-center">
                    <div class="text-gray-700 text-xs text-center" id="vision-display">
                        <div class="text-blue-500 mb-2">👁️ VISUAL CORTEX READY</div>
                        Enter a URL above and click SCAN to capture a screenshot.<br>
                        <span class="text-gray-600 text-[10px]">Supports http/https. Extract text option available.</span>
                    </div>
                </div>
```

---

### FIX #9: Add matplotlib to requirements.txt
**File:** `requirements.txt`  
**Impact:** Docker builds fail without manual `pip install matplotlib`

```
OLD (requirements.txt has no matplotlib entry):
matplotlib==3.10.8  # <-- Missing, installed manually in Dockerfile

NEW — Add line anywhere in requirements.txt:
matplotlib==3.10.8
```

Also remove the manual install from Dockerfile line 51:
```
OLD (Dockerfile line 51):
RUN pip install matplotlib  # Added since not in requirements but used

NEW:
# (delete this line — matplotlib now in requirements.txt)
```

---

### FIX #10: Database Indexes
**File:** `persistence/database.py`, after `init_db()` function  
**Impact:** Slow queries as data grows (6,285+ snapshots already)

Add after the `conn.commit()` in `init_db()` (around line 87):

```
OLD (lines 87-89):
    conn.commit()
    conn.close()
    print(f"[*] Database initialized at {DB_PATH}")

NEW:
    conn.commit()
    
    # Add indexes for timestamp-based queries
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_stats_timestamp ON container_stats(timestamp)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_stats_container ON container_stats(container_id, timestamp)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_snapshots_timestamp ON container_snapshots(timestamp)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_screenshots_timestamp ON screenshots(timestamp)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_chat_timestamp ON chat_logs(timestamp)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_token_usage_timestamp ON token_usage(timestamp)')
    conn.commit()
    
    conn.close()
    print(f"[*] Database initialized at {DB_PATH} (with indexes)")
```

---

### FIX #11: Playwright Context Manager
**File:** `app.py`, lines 252-270  
**Impact:** Browser process leaks on exception

```
OLD (lines 252-270):
    try:
        with sync_playwright() as p:
            # Launch the browser (headless)
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(viewport={'width': 1280, 'height': 720})
            page = context.new_page()
            
            # Navigate
            page.goto(url, timeout=30000, wait_until='domcontentloaded')
            
            # Take screenshot
            screenshot_bytes = page.screenshot(full_page=False)
            
            # Optional text extraction
            extracted_text = None
            if data.get('extract'):
                extracted_text = page.evaluate('document.body.innerText')
            
            browser.close()

NEW:
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            try:
                context = browser.new_context(viewport={'width': 1280, 'height': 720})
                page = context.new_page()
                
                # Navigate
                page.goto(url, timeout=30000, wait_until='domcontentloaded')
                
                # Take screenshot
                screenshot_bytes = page.screenshot(full_page=False)
                
                # Optional text extraction
                extracted_text = None
                if data.get('extract'):
                    extracted_text = page.evaluate('document.body.innerText')
            finally:
                browser.close()
```

---

## P2 — NICE TO HAVE

---

### FIX #12: Bare Except Clauses
**Files:** `app.py` lines 544, 554, 574, 605, 616, 630  
**Impact:** Silent failures, impossible to debug

Example pattern — apply to all bare `except: pass`:

```
OLD:
    except: pass

NEW:
    except Exception as e:
        print(f"[!] Config parse error: {e}")
```

Locations:
- Line 544: `get_model_info()` — config.yaml parse
- Line 554: `get_model_info()` — session file parse  
- Line 574: `get_model_info()` — OpenRouter credits fetch
- Line 605: `get_guardrails()` — Docker stats
- Line 616: `get_guardrails()` — Gateway heartbeat check
- Line 630: `get_guardrails()` — Qdrant health check

---

### FIX #13: Health Status Hardcoded "LIVE ARCHIVE"
**File:** `templates/index.html`, line 496

```
OLD (line 496):
                    document.getElementById('health-uptime').innerText = "LIVE ARCHIVE";

NEW:
                    // Show actual uptime if available, otherwise show system status
                    const uptime = data.uptime || 'ACTIVE';
                    document.getElementById('health-uptime').innerText = uptime;
```

---

### FIX #14: Duplicate Stats Calculation
**File:** `app.py`  
**Impact:** Same calculation in two places, must update both if formula changes

Extract to shared function (add before the background thread, around line 130):

```
NEW FUNCTION (add at line ~130):
def calculate_container_stats(stats):
    """Calculate CPU%, memory MB, network RX/TX from Docker stats dict."""
    cpu_stats = stats.get('cpu_stats', {})
    precpu_stats = stats.get('precpu_stats', {})
    memory_stats = stats.get('memory_stats', {})
    network_stats = stats.get('networks', {})
    
    cpu_delta = cpu_stats.get('cpu_usage', {}).get('total_usage', 0) - \
                precpu_stats.get('cpu_usage', {}).get('total_usage', 0)
    system_delta = cpu_stats.get('system_cpu_usage', 0) - \
                   precpu_stats.get('system_cpu_usage', 0)
    
    cpu_percent = 0.0
    if system_delta > 0 and cpu_delta > 0:
        num_cores = cpu_stats.get('online_cpus', 1)
        cpu_percent = (cpu_delta / system_delta) * num_cores * 100.0
    
    memory_mb = memory_stats.get('usage', 0) / (1024 * 1024)
    
    rx = 0
    tx = 0
    for interface, data in network_stats.items():
        rx += data.get('rx_bytes', 0)
        tx += data.get('tx_bytes', 0)
    
    return {
        'cpu_percent': cpu_percent,
        'memory_mb': memory_mb,
        'rx': rx,
        'tx': tx
    }
```

Then simplify both callers to use this function.

---

## SUMMARY TABLE

| # | Severity | Fix | File | Lines | Time |
|---|----------|-----|------|-------|------|
| 1 | CRITICAL | Variable name redaction artifacts | app.py | 23,25,66,76,111,198,209,210,215 | 30 min |
| 2 | CRITICAL | SSRF protection restoration | app.py | 238-249 | 30 min |
| 3 | HIGH | TryHackMe import fallback | app.py | 17, 674-695 | 15 min |
| 4 | HIGH | Docker debug mode | docker-compose.yml | 21 | 5 min |
| 5 | HIGH | Defensive tab switching | index.html | 343-370 | 15 min |
| 6 | MEDIUM | Remove fake fallback data | index.html | 527, 625 | 15 min |
| 7 | MEDIUM | Supervisor → OpenRouter | app.py | 714-778 | 45 min |
| 8 | LOW | Vision tab prompt | index.html | 129-133 | 5 min |
| 9 | LOW | matplotlib in requirements | requirements.txt | new line | 2 min |
| 10 | LOW | Database indexes | database.py | after line 87 | 10 min |
| 11 | LOW | Playwright context manager | app.py | 252-270 | 10 min |
| 12 | LOW | Bare except clauses | app.py | 544,554,574,605,616,630 | 15 min |
| 13 | LOW | Health status hardcoded | index.html | 496 | 5 min |
| 14 | LOW | Duplicate stats calc | app.py | ~130 | 15 min |

**Total estimated time: ~3.5 hours for all 14 fixes**  
**P0 only (1-6): ~1.5 hours**  
**P0 + P1 (1-11): ~2.5 hours**

---

*Generated: 2026-03-14 00:30 UTC*  
*No code modified — this is a proposal document only*
