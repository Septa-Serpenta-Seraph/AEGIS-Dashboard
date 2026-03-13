#!/usr/bin/env python3
"""AEGIS Live Demo — Record dashboard + recon for hackathon video"""
import os, asyncio
from playwright.async_api import async_playwright

OUTPUT_DIR = "/home/adora/workspace/AEGIS-Dashboard/recordings"
os.makedirs(OUTPUT_DIR, exist_ok=True)

async def record():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            record_video_dir=OUTPUT_DIR,
            record_video_size={"width": 1920, "height": 1080}
        )
        page = await ctx.new_page()
        
        # Load the actual dashboard
        await page.goto("http://localhost:5000", wait_until="networkidle")
        await page.wait_for_timeout(3000)
        
        # Click through tabs
        for tab in ["Container Stats", "Visual Cortex", "Persistence"]:
            try:
                el = page.locator(f"text={tab}").first
                if await el.count() > 0:
                    await el.click()
                    await page.wait_for_timeout(2000)
            except: pass
        
        # Back to home
        await page.goto("http://localhost:5000", wait_until="networkidle")
        await page.wait_for_timeout(2000)
        
        vid = page.video
        path = await vid.path() if vid else None
        await ctx.close()
        await browser.close()
        
        if path and os.path.exists(path):
            final = os.path.join(OUTPUT_DIR, "live_demo.webm")
            os.rename(path, final)
            mp4 = final.replace(".webm", ".mp4")
            os.system(f"ffmpeg -i {final} -c:v libx264 -preset fast -crf 23 {mp4} -y 2>/dev/null")
            return mp4 if os.path.exists(mp4) else final
        return None

result = asyncio.run(record())
print(f"✅ {result}" if result else "❌ Failed")
