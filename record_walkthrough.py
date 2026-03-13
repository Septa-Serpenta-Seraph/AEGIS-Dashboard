#!/usr/bin/env python3
"""
AEGIS Dashboard — Playwright Video Walkthrough Recorder
Records a full dashboard tour for the hackathon video (Scene 2).
Output: MP4 video at /home/adora/workspace/AEGIS-Dashboard/recordings/
"""

import os
import time
import asyncio
from playwright.async_api import async_playwright

OUTPUT_DIR = "/home/adora/workspace/AEGIS-Dashboard/recordings"
os.makedirs(OUTPUT_DIR, exist_ok=True)

DASHBOARD_URL = "http://localhost:5000"

async def record_walkthrough():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        # Create context with video recording
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            record_video_dir=OUTPUT_DIR,
            record_video_size={"width": 1920, "height": 1080}
        )
        
        page = await context.new_page()
        
        print("🎬 Recording started...")
        
        # SCENE: Dashboard landing page
        print("[1/6] Loading dashboard...")
        await page.goto(DASHBOARD_URL, wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(3000)  # Let animations play
        
        # SCENE: Click through tabs
        
        # Container Stats tab
        print("[2/6] Container Stats tab...")
        try:
            stats_tab = page.locator("text=Container Stats").first
            if await stats_tab.count() > 0:
                await stats_tab.click()
                await page.wait_for_timeout(2000)
                # Trigger container listing
                try:
                    refresh_btn = page.locator("text=Refresh").first
                    if await refresh_btn.count() > 0:
                        await refresh_btn.click()
                        await page.wait_for_timeout(2000)
                except:
                    pass
        except Exception as e:
            print(f"  Stats tab: {e}")
        
        # Visual Cortex tab
        print("[3/6] Visual Cortex tab...")
        try:
            cortex_tab = page.locator("text=Visual Cortex").first
            if await cortex_tab.count() > 0:
                await cortex_tab.click()
                await page.wait_for_timeout(2000)
                # Try to trigger a scan
                try:
                    scan_btn = page.locator("text=Scan").first
                    if await scan_btn.count() > 0:
                        await scan_btn.click()
                        await page.wait_for_timeout(3000)
                except:
                    pass
        except Exception as e:
            print(f"  Cortex tab: {e}")
        
        # Persistence tab
        print("[4/6] Persistence tab...")
        try:
            persist_tab = page.locator("text=Persistence").first
            if await persist_tab.count() > 0:
                await persist_tab.click()
                await page.wait_for_timeout(2000)
        except Exception as e:
            print(f"  Persist tab: {e}")
        
        # Health Check
        print("[5/6] Health endpoint...")
        await page.goto(f"{DASHBOARD_URL}/api/health", wait_until="networkidle")
        await page.wait_for_timeout(2000)
        
        # Back to main - final wide shot
        print("[6/6] Final dashboard view...")
        await page.goto(DASHBOARD_URL, wait_until="networkidle")
        await page.wait_for_timeout(3000)
        
        # Get video path before closing
        video = page.video
        video_path = None
        if video:
            video_path = await video.path()
        
        await context.close()
        await browser.close()
        
        if video_path and os.path.exists(video_path):
            # Move to predictable name
            final_path = os.path.join(OUTPUT_DIR, "aegis_walkthrough.webm")
            os.rename(video_path, final_path)
            size_mb = os.path.getsize(final_path) / (1024*1024)
            print(f"\n✅ Recording saved: {final_path}")
            print(f"   Size: {size_mb:.1f} MB")
            return final_path
        else:
            print("\n❌ No video file produced")
            return None

if __name__ == "__main__":
    result = asyncio.run(record_walkthrough())
    if result:
        print(f"\n🎥 Ready for editing: {result}")
