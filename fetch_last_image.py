import requests
import os
import sys
from dotenv import load_dotenv

# Load env from the dashboard directory
load_dotenv("workspace/AEGIS-Dashboard/.env")

TOKEN = os.getenv("DISCORD_TOKEN")
# Using the home channel ID from memory
CHANNEL_ID = "1478198538461777951" 

def get_last_image():
    if not TOKEN:
        print("Error: DISCORD_TOKEN not found in workspace/AEGIS-Dashboard/.env")
        return None
    
    headers = {
        "Authorization": f"Bot {TOKEN}",
        "User-Agent": "DiscordBot (https://github.com/Septa-Serpenta-Seraph/AEGIS-Dashboard, 1.0)"
    }
    
    # Fetch last 10 messages
    url = f"https://discord.com/api/v10/channels/{CHANNEL_ID}/messages?limit=50"
    r = requests.get(url, headers=headers)
    
    if r.status_code != 200:
        print(f"Discord API Error: {r.status_code} - {r.text}")
        return None

    messages = r.json()
    for msg in messages:
        # Check attachments (direct uploads)
        if msg.get('attachments'):
            return msg['attachments'][0]['url']
        # Check embeds (webhooks usually send images as embeds)
        if msg.get('embeds'):
            for embed in msg['embeds']:
                if embed.get('image'):
                    return embed['image']['url']
                if embed.get('thumbnail'):
                    return embed['thumbnail']['url']
    
    print("No images found in the last 10 messages.")
    return None

if __name__ == "__main__":
    image_url = get_last_image()
    if image_url:
        print(image_url)
