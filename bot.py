import discord
from discord.ext import commands
import requests
import os
import base64
from io import BytesIO
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
DASHBOARD_URL = os.getenv('DASHBOARD_URL', 'http://localhost:5000')

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print(f'Connected to AEGIS Dashboard at {DASHBOARD_URL}')

@bot.command(name='status')
async def status(ctx):
    """Check if the AEGIS Dashboard API is reachable."""
    try:
        response = requests.get(f"{DASHBOARD_URL}/")
        if response.status_code == 200:
            await ctx.send("✅ **AEGIS Dashboard is online.** Systems nominal.")
        else:
            await ctx.send(f"⚠️ **AEGIS Dashboard returned status {response.status_code}.**")
    except requests.ConnectionError:
        await ctx.send("❌ **AEGIS Dashboard is unreachable.** Is the Flask app running?")

@bot.command(name='containers')
async def list_containers(ctx):
    """List running Docker containers in the Sandbox."""
    try:
        response = requests.get(f"{DASHBOARD_URL}/api/containers")
        data = response.json()
        
        if not data.get('success'):
            await ctx.send(f"❌ Error fetching containers: {data.get('error')}")
            return

        containers = data.get('containers', [])
        if not containers:
            await ctx.send("ℹ️ No active containers found in the sandbox.")
            return

        embed = discord.Embed(title="🐋 Active Sandbox Containers", color=0x00ff00)
        for c in containers:
            status_emoji = "🟢" if "Up" in c['status'] else "🔴"
            embed.add_field(
                name=f"{status_emoji} {c['name']} ({c['id']})",
                value=f"Image: `{c['image']}`\nStatus: {c['status']}",
                inline=False
            )
        await ctx.send(embed=embed)

    except Exception as e:
        await ctx.send(f"❌ Connection error: {str(e)}")

@bot.command(name='scan')
async def scan_url(ctx, url: str, extract: bool = False):
    """Order the AEGIS Visual Cortex to scan a URL. Use --extract to also capture page text."""
    msg = f"👁️ **Scanning target:** `{url}`... (This may take a moment)"
    if extract:
        msg += " with text extraction"
    await ctx.send(msg)
    
    try:
        response = requests.post(f"{DASHBOARD_URL}/api/vision/scan", json={'url': url, 'extract': extract})
        data = response.json()
        
        if not data.get('success'):
            await ctx.send(f"❌ Scan failed: {data.get('error', 'Unknown error')}")
            return

        # Decode base64 image
        image_data = data['image'].split(",")[1]
        image_bytes = base64.b64decode(image_data)
        
        file = discord.File(BytesIO(image_bytes), filename="scan_result.png")
        await ctx.send(f"✅ **Visual Cortex Report:** Target acquired.", file=file)
        
        if extract and data.get('extracted_text'):
            text = data['extracted_text']
            if len(text) > 500:
                text = text[:500] + '...'
            await ctx.send(f"📝 **Extracted text:**\n{text}")

    except Exception as e:
        await ctx.send(f"❌ visual_cortex_error: {str(e)}")

@bot.command(name='chat')
async def chat_supervisor(ctx, *, message: str):
    """Chat with the AEGIS Supervisor Agent."""
    try:
        response = requests.post(f"{DASHBOARD_URL}/api/supervisor/chat", json={'message': message})
        data = response.json()
        
        if not data.get('success'):
            await ctx.send(f"❌ Supervisor unavailable: {data.get('error')}")
            return

        embed = discord.Embed(description=data['response'], color=0x3498db)
        embed.set_author(name=data.get('sender', 'Supervisor'))
        await ctx.send(embed=embed)

    except Exception as e:
        await ctx.send(f"❌ Comms link severed: {str(e)}")

if __name__ == '__main__':
    if not TOKEN:
        print("Error: DISCORD_TOKEN not found in environment variables.")
        exit(1)
    bot.run(TOKEN)
