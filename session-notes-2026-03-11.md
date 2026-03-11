# Session Notes — March 11, 2026

## CRITICAL — Fix These First in New Session

### Gateway Sync Bug (TOP PRIORITY)
**Problem:** Gateway is syncing 0 commands. Discord shows only 4 secret types instead of 6.
**Root cause:** In `discord.py`, `_register_slash_commands()` runs AFTER `tree.sync()` — the tree is empty when synced.
**Fix:** Move `self._register_slash_commands()` call to BEFORE the sync block in `on_ready()`.

### Gateway Not Reloading Python Code
**Problem:** `hermes gateway restart` reconnected to Discord but didn't reload Python code.
**Workaround:** Need to find and kill the Python process manually, let supervisor restart it.
**PID history:** 88206 → 93702 → ???

## What Was Accomplished

### 1. AEGIS Security Hardening ✅
- Both repos (AEGIS + AEGIS-Dashboard) merged to main
- Core: Auth middleware, 19-command blocklist, localhost binding
- Dashboard: Fixed broken get_context_note_by_id, SECRET_KEY warning, CORS hardened

### 2. Compression Disabled ✅
- `~/.hermes/config.yaml` — compression.enabled = false
- Was burning Gemini credits via auto-summarizer every time context hit 60%

### 3. Hunter Alpha Model Active ✅
- Switched to `openrouter/hunter-alpha` (1T params, 1M context, free)
- Replaced StepFun 3.5 Flash which was struggling

### 4. GitHub CLI Authenticated ✅
- gh v2.88.0 installed at ~/.local/bin/gh
- Authenticated as Septa-Serpenta-Seraph
- Full access token submitted via /collect-secret modal

### 5. /collect-secret Slash Command ✅ (mostly)
- Added to gateway at ~/.hermes/hermes-agent/gateway/platforms/discord.py
- Supports: OpenAI, GitHub, Discord Bot, OpenRouter, Username, Password
- Guild ID: 1387534334067736699 (Cultus Anarchia) for instant sync
- Adora successfully submitted GitHub token via modal — it works!

### 6. Guild-Specific Sync ✅ (mostly)
- Changed from global sync (1hr propagation) to guild sync (instant)
- DISCORD_GUILD_ID=1387534334067776699 added to .env

## Known Issues Still Pending

1. **Gateway syncing 0 commands** — need to fix sync order
2. **Duplicate /collect-secret entries** — two registrations happening
3. **Username/Password types not visible** — code is there but not syncing
4. **Memory full** — need to consolidate entries

## Upstreaming Opportunities
- /collect-secret command would be useful for main hermes-agent repo
- Guild-specific sync logic also useful for other Discord bots
- PR to hermes-agent project with both features

## Files Modified Today
- ~/.hermes/config.yaml (compression disabled)
- ~/.hermes/.env (DISCORD_GUILD_ID, GITHUB_TOKEN)
- ~/.hermes/hermes-agent/gateway/platforms/discord.py (guild sync + /collect-secret)
- /home/adora/workspace/AEGIS/docker/core.py (auth, blocklist, docker-compose)
- /home/adora/workspace/AEGIS-Dashboard/app.py (SECRET_KEY, CORS)
- /home/adora/workspace/AEGIS-Dashboard/persistence/database.py (fixed broken function)

## Environment
- Model: openrouter/hunter-alpha (1T params, 1M ctx, free)
- Guild ID: 1387534334067736699
- GH CLI: authenticated as Septa-Serpenta-Seraph
- Memory: nearly full (2185/2200 chars)

## Next Steps After Context Wipe
1. Fix the sync bug (move _register_slash_commands before tree.sync)
2. Hard kill gateway process to reload code
3. Verify /collect-secret shows all 6 types
4. Remove duplicate entries
5. Consider upstreaming /collect-secret to main hermes-agent repo
