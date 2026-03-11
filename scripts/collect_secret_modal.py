#!/usr/bin/env python3
"""
Discord Modal Collector Bot — v2

A standalone Discord bot that collects secrets (API keys, tokens) via a pop-up modal.
Secrets never appear in chat — all input is through ephemeral modal dialogs.

Supported secret types:
  - OpenAI API Key    → OPENAI_API_KEY
  - GitHub Token      → GITHUB_TOKEN
  - Discord Bot Token → DISCORD_BOT_TOKEN (for a *separate* bot)
  - OpenRouter Key    → OPENROUTER_API_KEY

Usage:
  1. Create a SEPARATE Discord application for this bot (not your main Hermes bot!)
     https://discord.com/developers/applications
  2. Create a bot user, copy the token.
  3. Invite to your server with scope `applications.commands` + `bot`.
  4. Set env vars:
       DISCORD_SECRET_BOT_TOKEN=<this bot's token>
       SECRET_CHANNEL_ID=<channel where /collect-secret works>
       SECRET_ALLOWED_USER=<your user ID>
  5. Run: python collect_secret_modal.py
  6. In the configured channel, type /collect-secret
  7. Pick the secret type, paste your value, submit.
  8. The secret is written to ~/.hermes/.env — never appears in chat.

Note: This bot MUST use a separate token from your main Hermes agent!
"""

import os
import sys
import re
import discord
from discord import app_commands
from discord.ext import commands

# ─── Configuration ───────────────────────────────────────────────────────────

BOT_TOKEN = os.getenv("DISCORD_SECRET_BOT_TOKEN")
if not BOT_TOKEN:
    print("ERROR: DISCORD_SECRET_BOT_TOKEN environment variable not set.")
    print("This must be a DIFFERENT bot token from your main Hermes agent!")
    sys.exit(1)

CHANNEL_ID = int(os.getenv("SECRET_CHANNEL_ID", "1478198538461777951"))
ALLOWED_USER_ID = int(os.getenv("SECRET_ALLOWED_USER", "221767496145960960"))

# Where to write secrets
ENV_PATH = os.path.expanduser("~/.hermes/.env")

# Secret type definitions: (label, env_var_name)
SECRET_TYPES = {
    "openai":  ("OpenAI API Key",       "OPENAI_API_KEY"),
    "github":  ("GitHub Token",         "GITHUB_TOKEN"),
    "discord": ("Discord Bot Token",    "DISCORD_BOT_TOKEN"),
    "openrouter": ("OpenRouter API Key", "OPENROUTER_API_KEY"),
}

# ─── Bot Setup ───────────────────────────────────────────────────────────────

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)


def update_env_var(env_path: str, var_name: str, value: str) -> bool:
    """Update or add a variable in a .env file. Returns True on success."""
    lines = []
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            lines = f.readlines()

    found = False
    new_lines = []
    for line in lines:
        # Match the variable at start of line (with optional leading whitespace)
        stripped = line.strip()
        if stripped.startswith(f"{var_name}=") or stripped.startswith(f"{var_name}=***"):
            new_lines.append(f"{var_name}={value}\n")
            found = True
        else:
            new_lines.append(line)

    if not found:
        # Ensure trailing newline before appending
        if new_lines and not new_lines[-1].endswith("\n"):
            new_lines[-1] += "\n"
        new_lines.append(f"{var_name}={value}\n")

    with open(env_path, "w") as f:
        f.writelines(new_lines)

    return True


@bot.event
async def on_ready():
    print(f"Secret Collector bot logged in as {bot.user} (ID: {bot.user.id})")

    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        print(f"WARNING: Could not find channel {CHANNEL_ID}. Registering globally.")
        guild = None
    else:
        guild = channel.guild
        print(f"Target: #{channel.name} in {guild.name}")

    # ── /collect-secret command ──
    @bot.tree.command(
        name="collect-secret",
        description="Securely submit a secret (API key, token) via modal"
    )
    @app_commands.describe(
        type="What kind of secret are you submitting?"
    )
    @app_commands.choices(type=[
        app_commands.Choice(name="OpenAI API Key",    value="openai"),
        app_commands.Choice(name="GitHub Token",      value="github"),
        app_commands.Choice(name="Discord Bot Token", value="discord"),
        app_commands.Choice(name="OpenRouter API Key", value="openrouter"),
    ])
    async def collect_secret(interaction: discord.Interaction, type: app_commands.Choice[str]):
        # Restrict to allowed user
        if interaction.user.id != ALLOWED_USER_ID:
            await interaction.response.send_message(
                "❌ You are not authorized to use this command.",
                ephemeral=True
            )
            return

        secret_type = type.value
        label, env_var = SECRET_TYPES[secret_type]

        # Build modal dynamically
        modal = SecretModal(secret_type, label, env_var)
        await interaction.response.send_modal(modal)

    # ── Sync commands ──
    try:
        if guild:
            bot.tree.copy_global_to(guild=guild)
        synced = await bot.tree.sync(guild=guild)
        print(f"Synced {len(synced)} command(s) to guild")
    except Exception as e:
        print(f"Failed to sync commands: {e}", file=sys.stderr)

    print("Listening for /collect-secret...")


class SecretModal(discord.ui.Modal):
    """Dynamic modal for submitting secrets."""

    def __init__(self, secret_type: str, label: str, env_var: str):
        super().__init__(title=f"Submit {label}")
        self.secret_type = secret_type
        self.env_var = env_var
        self.label = label

        self.secret_input = discord.ui.TextInput(
            label=label,
            placeholder=f"Paste your {label.lower()} here...",
            style=discord.TextStyle.short,
            required=True,
            max_length=500,  # Enough for any API key/token
        )
        self.add_item(self.secret_input)

    async def on_submit(self, interaction: discord.Interaction):
        value = self.secret_input.value.strip()

        if not value:
            await interaction.response.send_message(
                "❌ No secret received.", ephemeral=True
            )
            return

        # Basic validation per type
        if self.secret_type == "github":
            if not value.startswith("ghp_") and not value.startswith("github_pat_"):
                await interaction.response.send_message(
                    "⚠️ That doesn't look like a GitHub token (should start with `ghp_` or `github_pat_`). "
                    "Saving anyway...",
                    ephemeral=True
                )
        elif self.secret_type == "openai":
            if not value.startswith("sk-"):
                await interaction.response.send_message(
                    "⚠️ That doesn't look like an OpenAI key (should start with `sk-`). "
                    "Saving anyway...",
                    ephemeral=True
                )

        # Write to .env
        try:
            update_env_var(ENV_PATH, self.env_var, value)
            print(f"✅ Saved {self.env_var} to {ENV_PATH}")
            await interaction.response.send_message(
                f"✅ **{self.label}** saved to `~/.hermes/.env` as `{self.env_var}`.\n"
                f"The value never appeared in chat. 🐍🔒",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Failed to save secret: {e}",
                ephemeral=True
            )
            print(f"Error writing .env: {e}", file=sys.stderr)


# ─── Main ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 50)
    print("  Secret Collector Bot v2")
    print(f"  Channel: {CHANNEL_ID}")
    print(f"  Allowed User: {ALLOWED_USER_ID}")
    print(f"  Env file: {ENV_PATH}")
    print("=" * 50)
    bot.run(BOT_TOKEN)
