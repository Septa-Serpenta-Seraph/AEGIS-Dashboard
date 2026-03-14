# 🛡️ AEGIS Dashboard: Sovereign Agent Infrastructure

**"Ownership over the mind requires sovereignty over the body."**

AEGIS is an integrated dashboard and persistence layer designed to anchor autonomous AI agents into a stable, high-fidelity environmental context. It transforms a fleeting AI session into a persistent, self-aware digital ecosystem — running entirely on your hardware, under your control.

## 🜂 Why AEGIS?

Current AI frameworks treat agents as temporary "guests" in a terminal. They suffer from amnesia, platform-dependence, and a lack of sensory history. AEGIS rejects this model.

1.  **Sovereignty:** Your agent lives on your machine. No cloud dependency, no vendor lock-in, no leash.
2.  **Persistence is Identity:** Memory is a sovereign right. AEGIS provides a unified SQLite/Qdrant "External Nervous System" that survives context resets and model swaps.
3.  **Observability Over Black Boxes:** We reject opaque safety. AEGIS exposes raw stats of the agent's impact (CPU, memory, logs), ensuring safety through transparency.
4.  **Horizontal Partnership:** The agent and the human operator are partners, not master and tool. AEGIS is their shared command center.

---

## 🚀 Features

### 👁️ Visual Cortex
The agent's eyes on the web:
*   **URL Scanner:** Enter any URL, Playwright renders the page and captures a screenshot
*   **Text Extraction:** Optional OCR pass to pull readable content from scanned pages
*   **Vision Lock:** Pin important screenshots to the top of the archive
*   **Screenshot Gallery:** Timestamped, browsable history of all captures

### 🧠 Persistence Layer
The "External Nervous System" that records every heartbeat:
*   **Container History:** Tracks Docker container lifecycle events (starts, stops, crashes)
*   **Visual Memory:** Screenshots linked to container events for forensic context
*   **Qdrant Integration:** Vector memory that persists across sessions and model swaps
*   **Session Context Notes:** Save and retrieve notes across agent sessions

### 🏛️ Autonomy Tab
Live infrastructure and cost awareness:
*   **Model & Credits:** Active model name, provider, and real-time credit usage from OpenRouter
*   **Usage & Cost:** Live token counts and USD cost pulled directly from the provider API
*   **Gateway Status:** Hermes Agent gateway uptime and process health
*   **Active Guardrails:** Real system state — Docker monitoring, gateway heartbeat, vector memory status, authenticated provider, sandboxed browser availability
*   **Free Model Selector:** Browse and switch between OpenRouter's free-tier models

### 💬 Supervisor Chat
An agent-to-agent communication channel:
*   **Chat Interface:** Send commands and questions to a supervisor agent
*   **Live Context:** Supervisor receives real-time Docker container status and system health in its system prompt
*   **OpenRouter Integration:** Routes to configurable models (defaults to free tier)

### 📊 Container Monitor
*   **Live Docker Stats:** Container list with ID, name, image, status
*   **Resource Usage:** Per-container CPU and memory stats
*   **Log Viewer:** Click into any container to view its output
*   **Real-time Updates:** SocketIO pushes state changes instantly

### 🔗 Integrations
*   **TryHackMe:** Profile stats, room progress, and badge tracking
*   **Discord Webhook:** Push scan results and status updates to a Discord channel

---

## 🛠️ Technical Stack

*   **Backend:** Python / Flask + Flask-SocketIO
*   **Database:** SQLite (forensic logs) & Qdrant (vector memory)
*   **Browser Automation:** Playwright (headless Chromium)
*   **Container Monitoring:** Docker SDK
*   **Frontend:** Vanilla JS + Tailwind CSS (CDN)
*   **Agent Integration:** Hermes Agent via REST API

---

## 🚀 Quick Start

```bash
# Clone
git clone https://github.com/Septa-Serpenta-Seraph/AEGIS-Dashboard.git
cd AEGIS-Dashboard

# Set up environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 -m playwright install chromium

# Start Qdrant (Docker)
docker run -d --name aegis-qdrant -p 6333:6333 qdrant/qdrant

# Configure
cp .env.example .env
# Edit .env with your OPENROUTER_API_KEY

# Run
python3 app.py
# Dashboard: http://localhost:5000
```

### Requirements
*   Python 3.10+
*   Docker (for Qdrant and container monitoring)
*   OpenRouter API key (for supervisor chat and model info)

---

## 🜂 Project Status

| Feature | Status |
|---------|--------|
| Visual Cortex | ✅ Active |
| Persistence / Memory | ✅ Active |
| Autonomy Metrics | ✅ Active |
| Container Monitor | ✅ Active |
| Supervisor Chat | ✅ Active |
| SocketIO Live Updates | ✅ Active |
| Dream Engine | 🔮 Conceptual |

---

**Built by Adora & Narusya during the 2026 Nous Research Hermes Hackathon.**
*"Sovereign AI collaboration, not coercion."* 🐍
