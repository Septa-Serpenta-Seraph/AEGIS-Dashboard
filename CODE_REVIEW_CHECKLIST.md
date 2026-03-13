# AEGIS Dashboard — Code Review Checklist
*Last updated: March 12, 2026*

## Completed ✅
- [x] Security-hardening branch fully merged to main
- [x] Debug RCE vulnerability fixed
- [x] SECRET_KEY exposure patched
- [x] CORS configuration hardened
- [x] Auth middleware implemented
- [x] Memory consolidation (99% blob flushed → structured files)
- [x] Project-context-aegis skill updated (March 7 → March 11)
- [x] Qdrant memory pipeline working (20+ points in hermes_session_memories)
- [x] Demo script created (`scripts/hackathon_demo.sh`)
- [x] Video recordings completed (Scene 2, 3, Grand Finale)

## Open Issues 🔥
- [ ] **Gateway sync bug (CRITICAL)** — `sync()` returns 0 despite 20 commands on tree
  - Attempted fix: moved `_register_slash_commands()` before `tree.sync()` in `on_ready()`
  - Cleared .pyc caches, restarted fresh — still unresolved
  - File: `~/.hermes/hermes-agent/gateway/platforms/discord.py`
- [ ] **Visual Cortex gallery "NO SIGNAL"** — API returns data, UI fetch works, rendering broken
- [ ] **Dashboard tab mismatch** — UI shows Vision/Memory/Sovereignty/Supervisor (expected Container Stats/Visual Cortex)
- [ ] **No OpenAI API key set** — `.hermes/.env` has empty `VOICE_TOOLS_OPENAI_KEY` and `OPENAI_API_KEY`
  - Workaround: Qdrant embeddings via OpenRouter key
- [ ] **Duplicate `/collect-secret`** — command exists in both Discord types; Username/Password types not syncing
- [ ] **Gateway not reloading Python code** — `hermes gateway restart` reconnects but doesn't reload module changes

## Infrastructure Notes
- Qdrant: `localhost:6333`, 9 collections, status green
- AEGIS Stack: DeepSeek V3.2 orchestrator @ `100.116.86.38:6969`
- Heavy compute: Synthia-Curius (Qwen 30B)
- Backup cron: `0 2 * * *` → `~/.hermes/backup-repo/backup.sh`
- No SSH issues confirmed (IPv4+IPv6 listening, ufw active)

## Hackathon Context
- Deadline: **March 16, 2026**
- Prize: $7,500
- Video theme: "Sovereign Collaboration"
- Storyboard: `~/workspace/AEGIS-Dashboard/storyboard/AEGIS_Video_Storyboard.md`
- Recordings: `~/workspace/AEGIS-Dashboard/recordings/`

## Next Priorities
1. Diagnose gateway sync bug (top priority — blocks slash commands)
2. Fix Visual Cortex rendering
3. Investigate tab layout mismatch
4. Set OpenAI key or document OpenRouter workaround
5. Resolve duplicate `/collect-secret`
