from discord_webhook import DiscordIntegration
import os
from dotenv import load_dotenv

load_dotenv()

webhook = DiscordIntegration(os.getenv('DISCORD_WEBHOOK_URL'))
webhook.send_message("✅ **AEGIS Dashboard Connected.**\nProtocol Link Established via Webhook.\n\n_System Online._")
