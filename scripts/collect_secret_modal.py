#!/usr/bin/env python3
"""
Discord Modal Collector Bot

A standalone Discord bot that collects secrets (API keys, tokens) via a pop-up modal.
The secret is saved to the .env file in the AEGIS-Dashboard workspace.
All interactions are ephemeral – the secret never appears in chat.

Usage:
  1. Create a new Discord application (https://discord.com/developers/applications)
  2. Create a bot user, get the token.
  3. Invite the bot to your server with scope `applications.commands` and `bot`.
     (Permissions: Send Messages, Manage Events, Read Messages, etc.)
  4. Set environment variable DISCORD_BOT_TOKEN to your bot token.
  5. Optionally set CHANNEL_ID (defaults to 1478198538461777951).
  6. Run: python collect_secret_modal.py
  7. In the Discord channel, type /collect-secret and submit.
  8. A modal pops up; paste your secret and submit.
  9. The bot writes the secret to ~/workspace/AEGIS-Dashboard/.env as OPENAI_API_KEY=value
  10. Stop the bot with Ctrl+C.

Note: This bot uses a separate token from your main Hermes agent to avoid conflicts.
"""

import os
import sys
import discord
from discord import app_commands
from discord.ext import commands

# Configuration
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
if not TOKEN:
    print("ERROR: DISCORD_BOT_TOKEN environment variable not set.")
    sys.exit(1)

CHANNEL_ID = int(os.getenv("CHANNEL_ID", "1478198538461777951"))
# Adora's user ID – restrict to you only (optional but recommended)
ALLOWED_USER_ID = int(os.getenv("ALLOWED_USER_ID", "221767496145960960"))

# Path to .env file
ENV_PATH = os.path.expanduser("~/workspace/AEGIS-Dashboard/.env")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    # Get the target channel and guild
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        print(f"Could not find channel with ID {CHANNEL_ID}")
        await bot.close()
        return
    guild = channel.guild
    print(f"Target channel: #{channel.name} in guild {guild.name}")

    # Register slash command in this guild (instant)
    @bot.tree.command(name="collect-secret", description="Securely submit a secret (API key, token) via modal")
    async def collect_secret(interaction: discord.Interaction):
        # Restrict to allowed user
        if interaction.user.id != ALLOWED_USER_ID:
            await interaction.response.send_message("❌ You are not authorized to use this command.", ephemeral=True)
            return

        # Send modal
        await interaction.response.send_modal(
            title="Enter Secret",
            custom_id="secret_modal",
            components=[
                discord.ui.TextInput(
                    label="Secret (API key, token, etc.)",
                    placeholder="Paste your secret here...",
                    style=discord.TextStyle.short,
                    required=True,
                    max_length=200
                )
            ]
        )
        print(f"Sent modal to {interaction.user} in channel {CHANNEL_ID}")

    # Handle modal submission
    @bot.event
    async def on_interaction(interaction: discord.Interaction):
        if interaction.type != discord.InteractionType.modal_submit:
            return
        if interaction.data.get("custom_id") != "secret_modal":
            return

        # Verify user
        if interaction.user.id != ALLOWED_USER_ID:
            await interaction.response.send_message("❌ You are not authorized to submit secrets.", ephemeral=True)
            return

        # Extract secret from modal data
        # The modal has a single TextInput; its value is in components[0]["value"]
        components = interaction.data.get("components", [])
        secret = None
        if components:
            secret = components[0].get("value")
        if not secret:
            await interaction.response.send_message("❌ No secret received.", ephemeral=True)
            return

        # Write to .env file (create/update OPENAI_API_KEY)
        try:
            lines = []
            if os.path.exists(ENV_PATH):
                with open(ENV_PATH, "r") as f:
                    lines = f.readlines()
            # Update or add OPENAI_API_KEY
            found = False
            new_lines = []
            for line in lines:
                if line.strip().startswith("OPENAI_API_KEY="):
                    new_lines.append(f"OPENAI_API_KEY={secret}\n")
                    found = True
                else:
                    new_lines.append(line)
            if not found:
                new_lines.append(f"OPENAI_API_KEY={secret}\n")
            with open(ENV_PATH, "w") as f:
                f.writelines(new_lines)
            print(f"Saved OPENAI_API_KEY to {ENV_PATH}")
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to save secret: {e}", ephemeral=True)
            print(f"Error writing .env: {e}", file=sys.stderr)
            return

        await interaction.response.send_message(
            "✅ Secret saved to `.env`. You can now enable rolling_context in AEGIS Dashboard.",
            ephemeral=True
        )

    # Sync command tree to guild
    try:
        await bot.tree.sync(guild=guild)
        print(f"Slash command /collect-secret registered in guild {guild.name}")
    except Exception as e:
        print(f"Failed to sync commands: {e}", file=sys.stderr)

    print("Bot is ready. Listening for /collect-secret...")

# Run the bot
bot.run(TOKEN)
