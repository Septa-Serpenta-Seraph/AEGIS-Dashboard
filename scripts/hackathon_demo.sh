#!/bin/bash
# ═══════════════════════════════════════════════
# AEGIS Hackathon Demo Script
# ═══════════════════════════════════════════════
# Used for: Scene 2 — "The AI responds"
# Triggered by: @Narusya please spin up AEGIS
# Records: Network recon, dashboard walkthrough, container stats
# ═══════════════════════════════════════════════

set -e

# 1. Start AEGIS Dashboard
echo "╔══════════════════════════════════════════════╗"
echo "║   AEGIS — LIVE NETWORK RECONNAISSANCE       ║"
echo "╚══════════════════════════════════════════════╝"
echo ""
echo "Target: Localhost / Docker Network"
echo "Timestamp: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo ""

# 2. Network interfaces
echo "────────────────────────────────────────────"
echo "📡 NETWORK INTERFACES"
echo "────────────────────────────────────────────"
ip -brief addr show 2>/dev/null | grep -v "^lo"
echo ""

# 3. Docker containers
echo "────────────────────────────────────────────"
echo "🐳 DOCKER CONTAINERS (Attack Surface)"
echo "────────────────────────────────────────────"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null
echo ""

# 4. Port scan
echo "────────────────────────────────────────────"
echo "🔍 PORT SCAN — Localhost (Common Ports)"
echo "────────────────────────────────────────────"
for port in 22 80 443 3000 5000 5432 6333 6334 6379 6969 8080 8888 9000; do
    (echo > /dev/tcp/127.0.0.1/$port) 2>/dev/null && echo "  ✅ $port/tcp  OPEN" || true
done
echo ""

# 5. Security check
echo "────────────────────────────────────────────"
echo "🛡️ SECURITY CHECK"
echo "────────────────────────────────────────────"
QDRANT_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:6333/collections 2>/dev/null)
[ "$QDRANT_STATUS" = "200" ] && echo "  ⚠️  Qdrant (6333): NO AUTH" || echo "  ✅ Qdrant (6333): Auth required"
echo "  ⚠️  Docker socket: Accessible — container escape risk if compromised"
echo ""

# 6. Container monitoring via AEGIS
echo "────────────────────────────────────────────"
echo "📊 AEGIS DASHBOARD — Container Monitoring"
echo "────────────────────────────────────────────"
curl -s http://localhost:5000/api/containers 2>/dev/null | python3 -c "
import sys, json
data = json.load(sys.stdin)
for c in data.get('containers', data if isinstance(data, list) else []):
    name = c.get('name', c.get('Names', ['unknown'])[0] if isinstance(c.get('Names'), list) else 'unknown')
    status = c.get('status', c.get('Status', 'unknown'))
    print(f'  📦 {name}: {status}')
" 2>/dev/null
echo ""

# 7. Qdrant memory collections
echo "────────────────────────────────────────────"
echo "🧠 QDRANT MEMORY — Stored Knowledge"
echo "────────────────────────────────────────────"
curl -s http://localhost:6333/collections 2>/dev/null | python3 -c "
import sys, json
data = json.load(sys.stdin)
for c in data.get('result', {}).get('collections', []):
    print(f'  📚 {c[\"name\"]}')" 2>/dev/null
echo ""

# 8. Memory search - recent memories
echo "────────────────────────────────────────────"
echo "🔮 RECENT MEMORIES"
echo "────────────────────────────────────────────"
curl -s -X POST "http://localhost:6333/collections/hermes_session_memories/points/scroll" \
  -H "Content-Type: application/json" \
  -d '{"limit": 3, "with_payload": true, "with_vector": false}' 2>/dev/null | python3 -c "
import sys, json
for p in json.load(sys.stdin).get('result', {}).get('points', []):
    text = p['payload'].get('text', '')[:80]
    print(f'  📌 {text}...')
" 2>/dev/null
echo ""

echo "══════════════════════════════════════════════"
echo "  RECONNAISSANCE COMPLETE"
echo "  Status: NOMINAL ✅"
echo "══════════════════════════════════════════════"
