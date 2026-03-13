#!/usr/bin/env python3
"""
AEGIS Full Demo — Every system in action!
1. Terminal recon (scrolling)
2. Dashboard landing
3. Container Stats with live data
4. Visual Cortex with REAL screenshots
5. Persistence with actual history
"""
import os, asyncio, subprocess, json, httpx, datetime
from playwright.async_api import async_playwright

OUTPUT_DIR = "/home/adora/workspace/AEGIS-Dashboard/recordings"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def get_recon():
    results = [f"⏱️ {datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}"]
    r = subprocess.run(["ip", "-brief", "addr", "show"], capture_output=True, text=True)
    results.append("NETWORK:\n" + "\n".join(l for l in r.stdout.strip().split("\n") if "lo" not in l))
    r = subprocess.run(["docker", "ps", "--format", "{{.Names}}\t{{.Status}}\t{{.Ports}}"], capture_output=True, text=True)
    results.append("DOCKER:\n" + r.stdout.strip())
    import socket
    ports = []
    for p in [22, 5000, 6333, 6334, 6969]:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM); s.settimeout(0.5)
        if s.connect_ex(("127.0.0.1", p)) == 0:
            n = {22:"SSH",5000:"AEGIS",6333:"Qdrant",6334:"Qdrant-gRPC",6969:"LM Studio"}
            ports.append(f"  ✅ {p} — {n.get(p,'?')}")
        s.close()
    results.append("PORTS:\n" + "\n".join(ports))
    data = httpx.get("http://localhost:6333/collections").json()
    cols = data.get("result", {}).get("collections", [])
    results.append("QDRANT MEMORY:\n" + "\n".join(f"  📚 {c['name']}" for c in cols))
    return "\n\n".join(results)

async def record():
    recon = get_recon()
    escaped = recon.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            record_video_dir=OUTPUT_DIR,
            record_video_size={"width": 1920, "height": 1080}
        )
        page = await ctx.new_page()
        
        # ═══ PHASE 1: Terminal Recon ═══
        term_html = f"""<!DOCTYPE html><html><head>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
            * {{ margin:0; padding:0; box-sizing:border-box; }}
            body {{ background:#0f0f23; font-family:'JetBrains Mono',monospace; padding:30px; height:100vh; overflow:hidden; }}
            h1 {{ color:#00d4ff; font-size:22px; letter-spacing:3px; text-align:center; margin-bottom:5px; }}
            .sub {{ color:#00ff64; font-size:13px; text-align:center; margin-bottom:25px; }}
            h2 {{ color:#00d4ff; font-size:14px; letter-spacing:2px; margin:20px 0 10px; border-bottom:1px solid #2a2a4e; padding-bottom:8px; }}
            pre {{ color:#00ff64; font-size:14px; line-height:1.6; white-space:pre-wrap; }}
            .prompt {{ color:#fff; }}
        </style></head><body>
            <h1>AEGIS SOVEREIGN DAEMON PROTOCOL</h1>
            <div class="sub">📡 Live Network Reconnaissance</div>
            <h2>Terminal Output</h2>
            <pre><span class="prompt">adora@narusya:~$ bash scripts/hackathon_demo.sh</span>

{escaped}</pre>
        </body></html>"""
        
        await page.set_content(term_html)
        await page.wait_for_timeout(2500)
        
        # Scroll through terminal — show the action
        for _ in range(6):
            await page.evaluate("window.scrollBy(0, 200)")
            await page.wait_for_timeout(1200)
        await page.wait_for_timeout(2000)
        
        # ═══ PHASE 2: Dashboard — Landing ═══
        await page.goto("http://localhost:5000", wait_until="networkidle")
        await page.wait_for_timeout(3000)
        
        # ═══ PHASE 3: Container Stats Tab ═══
        try:
            await page.locator("text=Container Stats").first.click()
            await page.wait_for_timeout(2000)
            # Click refresh to show live data
            refresh = page.locator("text=Refresh").first
            if await refresh.count() > 0:
                await refresh.click()
                await page.wait_for_timeout(3000)
            await page.evaluate("window.scrollBy(0, 200)")
            await page.wait_for_timeout(1500)
        except: pass
        
        # ═══ PHASE 4: Visual Cortex — THE GOOD STUFF ═══
        try:
            await page.locator("text=Visual Cortex").first.click()
            await page.wait_for_timeout(2000)
            
            # The screenshots should already be there from our earlier scans
            # Scroll down to show the gallery
            await page.evaluate("window.scrollBy(0, 300)")
            await page.wait_for_timeout(2000)
            await page.evaluate("window.scrollBy(0, 300)")
            await page.wait_for_timeout(2000)
        except: pass
        
        # ═══ PHASE 5: Persistence Tab ═══
        try:
            await page.locator("text=Persistence").first.click()
            await page.wait_for_timeout(2000)
            await page.evaluate("window.scrollBy(0, 300)")
            await page.wait_for_timeout(1500)
        except: pass
        
        # ═══ PHASE 6: Final Dashboard Home ═══
        await page.goto("http://localhost:5000", wait_until="networkidle")
        await page.wait_for_timeout(2000)
        
        vid = page.video
        path = await vid.path() if vid else None
        await ctx.close()
        await browser.close()
        
        if path and os.path.exists(path):
            final = os.path.join(OUTPUT_DIR, "full_demo.webm")
            os.rename(path, final)
            mp4 = final.replace(".webm", ".mp4")
            os.system(f"ffmpeg -i {final} -c:v libx264 -preset fast -crf 20 {mp4} -y 2>/dev/null")
            return mp4 if os.path.exists(mp4) else final
        return None

result = asyncio.run(record())
print(f"✅ {result}" if result else "❌ Failed")
