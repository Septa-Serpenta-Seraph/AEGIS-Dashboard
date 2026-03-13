#!/usr/bin/env python3
"""AEGIS Final — All tabs working with correct labels"""
import os, asyncio
from playwright.async_api import async_playwright

OUTPUT_DIR = "/home/adora/workspace/AEGIS-Dashboard/recordings"

async def record():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            record_video_dir=OUTPUT_DIR,
            record_video_size={"width": 1920, "height": 1080}
        )
        page = await ctx.new_page()
        
        # Landing page
        await page.goto("http://localhost:5000", wait_until="networkidle")
        await page.wait_for_timeout(3000)
        
        # PHASE 1: Vision tab — Visual Cortex with live scan
        await page.locator("#tab-vision").click()
        await page.wait_for_timeout(2000)
        
        # Type URL and trigger scan
        url_input = page.locator("input").first
        await url_input.fill("https://github.com/Septa-Serpenta-Seraph/AEGIS-Dashboard")
        await page.wait_for_timeout(500)
        await page.locator("text=Scan").first.click()
        print("🔥 Live scan triggered!")
        await page.wait_for_timeout(6000)
        
        # Scroll to show result
        await page.evaluate("window.scrollBy(0, 300)")
        await page.wait_for_timeout(2000)
        
        # PHASE 2: Memory tab — Persistence + screenshot gallery
        await page.locator("#tab-persistence").click()
        await page.wait_for_timeout(2000)
        # Scroll to show Visual Vault gallery
        await page.evaluate("window.scrollBy(0, 500)")
        await page.wait_for_timeout(2500)
        await page.evaluate("window.scrollBy(0, 400)")
        await page.wait_for_timeout(2000)
        
        # PHASE 3: Sovereignty tab
        await page.locator("#tab-sovereignty").click()
        await page.wait_for_timeout(2000)
        
        # PHASE 4: Supervisor tab
        await page.locator("#tab-chat").click()
        await page.wait_for_timeout(2000)
        
        # PHASE 5: Back to Vision — final view
        await page.locator("#tab-vision").click()
        await page.wait_for_timeout(2000)
        
        vid = page.video
        path = await vid.path() if vid else None
        await ctx.close()
        await browser.close()
        
        if path and os.path.exists(path):
            final = os.path.join(OUTPUT_DIR, "cortex_live.webm")
            os.rename(path, final)
            mp4 = final.replace(".webm", ".mp4")
            os.system(f"ffmpeg -i {final} -c:v libx264 -preset fast -crf 20 {mp4} -y 2>/dev/null")
            return mp4 if os.path.exists(mp4) else final
        return None

result = asyncio.run(record())
print(f"✅ {result}" if result else "❌ Failed")
