#!/usr/bin/env python3
"""
Record terminal walkthrough using Playwright with a styled terminal page.
"""

import os
import json
import asyncio
import subprocess
from playwright.async_api import async_playwright

OUTPUT_DIR = "/home/adora/workspace/AEGIS-Dashboard/recordings"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def get_command_output():
    """Run the actual commands and capture output for display."""
    results = []
    
    # Git log
    r = subprocess.run(["git", "log", "--oneline", "--graph", "--decorate", "-10"], 
                      capture_output=True, text=True, cwd=os.path.expanduser("~/workspace/AEGIS-Dashboard"))
    results.append(("git log --oneline --graph -10", r.stdout.strip()))
    
    # Qdrant stats
    import httpx
    d = httpx.get("http://localhost:6333/collections/hermes_session_memories").json()["result"]
    qdrant_output = f"  Collection: hermes_session_memories\n  Points: {d['points_count']}  |  Vectors: {d['config']['params']['vectors']['size']}-dim  |  Distance: {d['config']['params']['vectors']['distance']}"
    results.append(("curl qdrant/collections", qdrant_output))
    
    # Memory contents
    resp = httpx.post("http://localhost:6333/collections/hermes_session_memories/points/scroll", 
                      json={"limit": 4, "with_payload": True, "with_vector": False})
    memories = ""
    for p in resp.json()["result"]["points"]:
        text = p["payload"].get("text", "")[:75]
        memories += f"  📌 {text}...\n"
    results.append(("qdrant memory search", memories.strip()))
    
    # Architecture
    arch = """  ┌─────────────────────────────────────┐
  │  DeepSeek V3.2 (Orchestrator)       │
  └──────────────┬──────────────────────┘
  ┌──────────────▼──────────────────────┐
  │  Synthia-Curius (Qwen 30B Local)    │
  └──────────────┬──────────────────────┘
  ┌──────────────▼──────────────────────┐
  │  AEGIS Dashboard (Flask + SocketIO) │
  │  ├── Container Monitoring (Docker)  │
  │  ├── Visual Cortex (Playwright)     │
  │  ├── Persistence (SQLite + Qdrant)  │
  │  └── Discord Webhook Integration    │
  └─────────────────────────────────────┘"""
    results.append(("echo architecture", arch))
    
    return results

async def record_terminal():
    # Get real outputs
    commands = get_command_output()
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            record_video_dir=OUTPUT_DIR,
            record_video_size={"width": 1920, "height": 1080}
        )
        
        page = await context.new_page()
        
        # Build terminal HTML with all content
        entries_html = ""
        for cmd, output in commands:
            escaped_cmd = cmd.replace("`", "\\`").replace("$", "\\$")
            escaped_output = output.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            entries_html += f'''
            <div class="entry">
                <div class="cmd"><span class="prompt">adora@narusya:~$ </span><span class="cmd-text">{escaped_cmd}</span></div>
                <pre class="output">{escaped_output}</pre>
            </div>
            '''
        
        terminal_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ 
                background: linear-gradient(135deg, #0a0a1a 0%, #1a1a2e 100%);
                font-family: 'JetBrains Mono', 'Courier New', monospace;
                height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
            }}
            .container {{
                width: 90%;
                max-width: 1600px;
                background: #0f0f23;
                border-radius: 16px;
                overflow: hidden;
                box-shadow: 0 0 60px rgba(0,255,100,0.15), 0 0 120px rgba(0,100,255,0.05);
            }}
            .titlebar {{
                background: #1a1a2e;
                padding: 12px 20px;
                display: flex;
                align-items: center;
                gap: 10px;
                border-bottom: 1px solid #2a2a4e;
            }}
            .dot {{ width: 14px; height: 14px; border-radius: 50%; }}
            .dot.red {{ background: #ff5f57; }}
            .dot.yellow {{ background: #febc2e; }}
            .dot.green {{ background: #28c840; }}
            .titlebar span {{
                color: #888;
                margin-left: auto;
                font-size: 14px;
            }}
            .terminal {{
                padding: 25px;
                overflow-y: auto;
                max-height: 900px;
            }}
            .header {{
                text-align: center;
                margin-bottom: 30px;
                padding-bottom: 20px;
                border-bottom: 1px solid #2a2a4e;
            }}
            .header h1 {{
                color: #00d4ff;
                font-size: 28px;
                letter-spacing: 4px;
                margin-bottom: 8px;
            }}
            .header p {{
                color: #00ff64;
                font-size: 14px;
            }}
            .entry {{
                margin-bottom: 20px;
                animation: fadeIn 0.5s ease-in;
            }}
            @keyframes fadeIn {{
                from {{ opacity: 0; transform: translateY(10px); }}
                to {{ opacity: 1; transform: translateY(0); }}
            }}
            .prompt {{ color: #00ff64; }}
            .cmd-text {{ color: #fff; font-weight: bold; }}
            .output {{
                color: #c0c0c0;
                margin-top: 8px;
                padding: 12px 16px;
                background: rgba(255,255,255,0.03);
                border-radius: 8px;
                border-left: 3px solid #00ff64;
                line-height: 1.6;
            }}
            .footer {{
                text-align: center;
                padding: 20px;
                color: #666;
                font-size: 12px;
                border-top: 1px solid #2a2a4e;
            }}
        </style>
        </head>
        <body>
        <div class="container">
            <div class="titlebar">
                <div class="dot red"></div>
                <div class="dot yellow"></div>
                <div class="dot green"></div>
                <span>AEGIS — Behind the Scenes</span>
            </div>
            <div class="terminal">
                <div class="header">
                    <h1>AEGIS SOVEREIGN DAEMON PROTOCOL</h1>
                    <p>Built in 72 hours with Hermes Agent • {len(commands)} systems inspected</p>
                </div>
                {entries_html}
                <div class="footer">
                    ✅ AEGIS Dashboard • github.com/Septa-Serpenta-Seraph/AEGIS-Dashboard
                </div>
            </div>
        </div>
        </body>
        </html>
        """
        
        await page.set_content(terminal_html)
        
        print("🎬 Recording terminal walkthrough...")
        await page.wait_for_timeout(2000)
        
        # Slow scroll through the content
        await page.evaluate("window.scrollTo(0, 200)")
        await page.wait_for_timeout(1500)
        await page.evaluate("window.scrollTo(0, 400)")
        await page.wait_for_timeout(1500)
        await page.evaluate("window.scrollTo(0, 600)")
        await page.wait_for_timeout(1500)
        await page.evaluate("window.scrollTo(0, 0)")
        await page.wait_for_timeout(1000)
        
        video = page.video
        video_path = await video.path() if video else None
        
        await context.close()
        await browser.close()
        
        if video_path and os.path.exists(video_path):
            final_path = os.path.join(OUTPUT_DIR, "terminal_walkthrough.webm")
            os.rename(video_path, final_path)
            size_mb = os.path.getsize(final_path) / (1024*1024)
            print(f"✅ Saved: {final_path} ({size_mb:.1f} MB)")
            
            # Convert to mp4
            mp4_path = final_path.replace(".webm", ".mp4")
            os.system(f"ffmpeg -i {final_path} -c:v libx264 -preset fast -crf 23 -c:a aac {mp4_path} -y 2>/dev/null")
            if os.path.exists(mp4_path):
                print(f"✅ Converted: {mp4_path}")
                return mp4_path
            return final_path
        
        return None

if __name__ == "__main__":
    result = asyncio.run(record_terminal())
    if result:
        print(f"🎥 Ready: {result}")
