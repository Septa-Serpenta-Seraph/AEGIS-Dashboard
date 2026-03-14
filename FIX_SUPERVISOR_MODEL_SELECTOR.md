# Fix #7 Revised: Supervisor with Free Model Selector
## Proposed Implementation (Not Yet Applied)

**Date:** 2026-03-14  
**Status:** PROPOSAL ONLY

---

## Overview

Wire the Supervisor to OpenRouter using free models, with a dropdown selector in the Autonomy tab that lets the user switch between "Auto" (`openrouter/free`) and specific free models.

---

## PART A: New API Endpoint — List Free Models

**File:** `app.py`  
**Location:** Add after the `/api/autonomy/model` endpoint (around line 588)

```python
# --- FREE MODEL CACHE (refresh every 5 minutes) ---
_free_models_cache = {"models": [], "timestamp": 0}

def fetch_free_models():
    """Fetch available free models from OpenRouter, cached for 5 minutes."""
    import time as _time
    now = _time.time()
    
    # Return cache if fresh (5 min)
    if _free_models_cache["models"] and (now - _free_models_cache["timestamp"]) < 300:
        return _free_models_cache["models"]
    
    try:
        resp = requests.get("https://openrouter.ai/api/v1/models", timeout=10)
        if resp.status_code == 200:
            all_models = resp.json().get("data", [])
            free = []
            for m in all_models:
                pricing = m.get("pricing", {})
                if pricing.get("prompt", "1") == "0" or pricing.get("prompt") == 0:
                    free.append({
                        "id": m["id"],
                        "name": m.get("name", m["id"]),
                        "context_length": m.get("context_length", 0),
                    })
            # Sort by context length descending
            free.sort(key=lambda x: x["context_length"], reverse=True)
            _free_models_cache["models"] = free
            _free_models_cache["timestamp"] = now
            return free
    except Exception as e:
        print(f"[!] Free models fetch failed: {e}")
    
    # Return stale cache if fetch failed
    return _free_models_cache["models"]


@app.route('/api/autonomy/free-models', methods=['GET'])
def list_free_models():
    """List available free models on OpenRouter."""
    models = fetch_free_models()
    return jsonify({
        'success': True,
        'models': models,
        'count': len(models),
        'auto_model': 'openrouter/free'
    })
```

---

## PART B: Supervisor — Use Selected Model

**File:** `app.py`  
**Location:** Replace `supervisor_chat()` function (lines 714-778)

```python
@app.route('/api/supervisor/chat', methods=['POST'])
def supervisor_chat():
    """
    The Supervisor Agent — routes to OpenRouter free models.
    Model selection via request body or global preference.
    """
    data = request.json
    user_message = data.get('message', '')
    # Accept model override from request, otherwise use default
    selected_model = data.get('model', 'openrouter/free')
    
    # Gather live system context for the prompt
    system_context = ""
    try:
        # Get container info
        if docker_client:
            containers = docker_client.containers.list()
            if containers:
                container_info = []
                for c in containers:
                    container_info.append(f"- {c.name}: {c.status} ({c.image.tags[0] if c.image.tags else 'unknown'})")
                system_context += "\nActive containers:\n" + "\n".join(container_info)
        
        # Get health status
        health_resp = requests.get('http://localhost:5000/api/health', timeout=2)
        if health_resp.status_code == 200:
            h = health_resp.json()
            system_context += f"\nHealth: DB={h.get('database')}, Docker={h.get('docker')}, Qdrant={h.get('qdrant')}"
    except Exception as e:
        system_context += f"\n(System context unavailable: {e})"
    
    system_prompt = f"""You are the AEGIS Supervisor Agent, a technical assistant for the AEGIS Dashboard.
You monitor Docker containers, system health, and help debug infrastructure issues.

Current system state:{system_context}

Be concise and technical. Use bullet points for lists. If asked about status, reference the data above.
If asked to do something you cannot (like SSH or modify files), explain what you CAN do instead.
You can suggest Docker commands, debugging steps, and explain system behavior."""
    
    # Get API key
    api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENROUTER_KEY")
    if not api_key:
        hermes_env = os.path.expanduser("~/.hermes/.env")
        if os.path.exists(hermes_env):
            with open(hermes_env) as f:
                for line in f:
                    if 'OPENROUTER' in line and ('KEY' in line or 'API' in line):
                        parts = line.split('=', 1)
                        if len(parts) == 2 and len(parts[1].strip()) > 10:
                            api_key = parts[1].strip()
                            break
    
    if not api_key:
        return jsonify({
            'success': True,
            'response': 'Supervisor is offline. No OpenRouter API key configured.\nSet OPENROUTER_API_KEY in ~/.hermes/.env to enable.',
            'sender': 'Supervisor (Offline)',
            'model': None
        })
    
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/Septa-Serpenta-Seraph/AEGIS-Dashboard",
            "X-Title": "AEGIS Supervisor"
        }
        payload = {
            "model": selected_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            "max_tokens": 600,
            "temperature": 0.7
        }
        resp = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=20
        )
        
        if resp.status_code == 200:
            result = resp.json()
            response_text = result["choices"][0]["message"]["content"]
            actual_model = result.get("model", selected_model)
            # Clean up model name for display
            model_display = actual_model.split("/")[-1].replace(":free", "").replace("-", " ").title()
            
            return jsonify({
                'success': True,
                'response': response_text,
                'sender': f'Supervisor ({model_display})',
                'model': actual_model
            })
        else:
            error_detail = resp.text[:200] if resp.text else "Unknown error"
            return jsonify({
                'success': True,
                'response': f'LLM returned status {resp.status_code}: {error_detail}\nTry a different model or check your API key.',
                'sender': 'Supervisor (Error)',
                'model': selected_model
            })
            
    except requests.Timeout:
        return jsonify({
            'success': True,
            'response': 'Request timed out. The model may be overloaded — try again or switch to a different free model.',
            'sender': 'Supervisor (Timeout)',
            'model': selected_model
        })
    except Exception as e:
        return jsonify({
            'success': True,
            'response': f'Connection failed: {str(e)}',
            'sender': 'Supervisor (Error)',
            'model': selected_model
        })
```

---

## PART C: Model Preference Storage Endpoint

**File:** `app.py`  
**Location:** Add after the free-models endpoint

```python
# In-memory model preference (resets on restart, use localStorage on frontend)
_supervisor_model = 'openrouter/free'

@app.route('/api/autonomy/supervisor-model', methods=['GET'])
def get_supervisor_model():
    """Get current supervisor model preference."""
    return jsonify({
        'success': True,
        'model': _supervisor_model
    })

@app.route('/api/autonomy/supervisor-model', methods=['POST'])
def set_supervisor_model():
    """Set supervisor model preference."""
    global _supervisor_model
    data = request.json
    model = data.get('model', 'openrouter/free')
    _supervisor_model = model
    print(f"[*] Supervisor model set to: {model}")
    return jsonify({
        'success': True,
        'model': _supervisor_model,
        'message': f'Supervisor model set to {model}'
    })
```

---

## PART D: Autonomy Tab UI — Model Selector

**File:** `templates/index.html`  
**Location:** Add a new section in the Autonomy view, after the "Usage & Cost" div (around line 228)

Insert this HTML block after the `<!-- Usage & Cost -->` section and before `<!-- System Guardrails -->`:

```html
                    <!-- Supervisor Model Selector -->
                    <div class="border border-gray-800 p-2 bg-black">
                        <span class="text-[10px] uppercase text-gray-500 font-bold tracking-widest block mb-2">Supervisor Model</span>
                        <div class="flex items-center space-x-2">
                            <select id="supervisor-model-select" 
                                    class="flex-1 bg-gray-900 border border-gray-700 p-2 text-xs font-mono text-white focus:border-blue-500 outline-none"
                                    onchange="setSupervisorModel(this.value)">
                                <option value="openrouter/free">Auto (Best Free)</option>
                                <option disabled>── Loading models... ──</option>
                            </select>
                            <button onclick="loadFreeModels()" class="text-xs text-blue-500 hover:text-white px-2" title="Refresh model list">
                                ↻
                            </button>
                        </div>
                        <div id="model-select-status" class="text-[9px] text-gray-600 mt-1"></div>
                    </div>
```

And add this JavaScript after the `loadAutonomyData()` function (around line 428):

```javascript
        // --- Supervisor Model Selector ---
        let _freeModelsLoaded = false;
        
        async function loadFreeModels() {
            const select = document.getElementById('supervisor-model-select');
            const status = document.getElementById('model-select-status');
            
            if (!select) return;
            
            status.textContent = 'Fetching free models...';
            
            try {
                const resp = await fetch('/api/autonomy/free-models');
                const data = await resp.json();
                
                if (data.success && data.models.length > 0) {
                    // Keep the "Auto" option, clear the rest
                    select.innerHTML = '<option value="openrouter/free">Auto (Best Free)</option>';
                    
                    // Group by provider
                    const byProvider = {};
                    data.models.forEach(m => {
                        const provider = m.id.split('/')[0];
                        if (!byProvider[provider]) byProvider[provider] = [];
                        byProvider[provider].push(m);
                    });
                    
                    // Add optgroups
                    Object.keys(byProvider).sort().forEach(provider => {
                        const group = document.createElement('optgroup');
                        group.label = provider.toUpperCase();
                        
                        byProvider[provider].forEach(m => {
                            const opt = document.createElement('option');
                            opt.value = m.id;
                            const ctxStr = m.context_length >= 1000 
                                ? (m.context_length / 1000).toFixed(0) + 'K' 
                                : m.context_length;
                            opt.textContent = `${m.name} (${ctxStr})`;
                            group.appendChild(opt);
                        });
                        
                        select.appendChild(group);
                    });
                    
                    status.textContent = `${data.models.length} free models available`;
                    _freeModelsLoaded = true;
                    
                    // Restore saved preference
                    loadSupervisorPreference();
                } else {
                    status.textContent = 'No free models found';
                }
            } catch (e) {
                console.error('Free models fetch failed:', e);
                status.textContent = 'Failed to load models — check connection';
            }
        }
        
        async function setSupervisorModel(modelId) {
            const status = document.getElementById('model-select-status');
            
            // Save to backend
            try {
                await fetch('/api/autonomy/supervisor-model', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({model: modelId})
                });
            } catch (e) {
                console.warn('Failed to save model preference:', e);
            }
            
            // Save to localStorage for persistence across restarts
            localStorage.setItem('aegis_supervisor_model', modelId);
            
            // Update UI
            const displayName = modelId === 'openrouter/free' 
                ? 'Auto (Best Free)' 
                : modelId.split('/').pop().replace(':free', '');
            status.textContent = `Selected: ${displayName}`;
            status.className = 'text-[9px] text-green-500 mt-1';
            
            // Reset status after 3 seconds
            setTimeout(() => {
                status.textContent = '';
                status.className = 'text-[9px] text-gray-600 mt-1';
            }, 3000);
        }
        
        async function loadSupervisorPreference() {
            const select = document.getElementById('supervisor-model-select');
            if (!select) return;
            
            // Try localStorage first (persists across restarts)
            const saved = localStorage.getItem('aegis_supervisor_model');
            if (saved) {
                select.value = saved;
                return;
            }
            
            // Fall back to backend
            try {
                const resp = await fetch('/api/autonomy/supervisor-model');
                const data = await resp.json();
                if (data.success && data.model) {
                    select.value = data.model;
                }
            } catch (e) {
                // Default to auto
                select.value = 'openrouter/free';
            }
        }
        
        // Load free models when Autonomy tab is opened
        // (Already called from loadAutonomyData, but also load models)
        const originalLoadAutonomyData = loadAutonomyData;
        loadAutonomyData = async function() {
            await originalLoadAutonomyData();
            if (!_freeModelsLoaded) {
                await loadFreeModels();
            }
        };
```

---

## PART E: Chat — Pass Selected Model

**File:** `templates/index.html`  
**Location:** In the chat input event listener (around line 559)

```
OLD (lines 559-563):
                const res = await fetch('/api/supervisor/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({message: msg})
                });

NEW:
                // Get selected model from dropdown (or default to auto)
                const modelSelect = document.getElementById('supervisor-model-select');
                const selectedModel = modelSelect ? modelSelect.value : 'openrouter/free';
                
                const res = await fetch('/api/supervisor/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        message: msg,
                        model: selectedModel
                    })
                });
```

Also update the response display to show which model responded:

```
OLD (line 567):
                history.innerHTML += `<div class="text-blue-400 font-bold">${esc(data.sender)}: ${esc(data.response)}</div>`;

NEW:
                const senderName = data.sender || 'Supervisor';
                history.innerHTML += `<div class="text-blue-400 font-bold">${esc(senderName)}:</div>`;
                history.innerHTML += `<div class="text-gray-300 whitespace-pre-wrap">${esc(data.response)}</div>`;
```

---

## Summary of Changes

| File | What Changes | Lines Affected |
|------|--------------|----------------|
| `app.py` | New endpoint: `/api/autonomy/free-models` | ~40 lines added |
| `app.py` | New endpoints: `/api/autonomy/supervisor-model` GET/POST | ~20 lines added |
| `app.py` | Replace `supervisor_chat()` with OpenRouter integration | ~70 lines replaced |
| `index.html` | Add model selector dropdown to Autonomy tab | ~15 lines added |
| `index.html` | Add JavaScript for model loading/selection | ~90 lines added |
| `index.html` | Update chat to pass selected model | ~10 lines modified |

**Total:** ~245 lines changed/added across 2 files

---

## User Experience Flow

1. User opens Autonomy tab
2. Dropdown shows "Auto (Best Free)" selected by default
3. Dropdown fetches and populates with all 28+ free models, grouped by provider
4. User switches to Supervisor tab
5. Types a message → sent with selected model
6. Response shows which model answered (e.g., "Supervisor (Gemma 3 27B):")
7. Model preference saved to localStorage + backend (persists across refreshes)

---

## Fallback Behavior

- If API key missing → "Supervisor (Offline)" message
- If model overloaded/timeout → Error message suggesting try again or switch model
- If OpenRouter down → Graceful error, no crash
- If free models list fails to fetch → Dropdown still has "Auto" option

---

*Generated: 2026-03-14*  
*Not yet applied — proposal only*
