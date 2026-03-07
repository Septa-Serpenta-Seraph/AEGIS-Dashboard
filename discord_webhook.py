import os
import requests
import json
import base64
from io import BytesIO

class DiscordIntegration:
    def __init__(self, webhook_url=os.getenv('DISCORD_WEBHOOK_URL')):
        self.webhook_url = webhook_url
        if not self.webhook_url:
            print("[!] DiscordIntegration: No webhook URL found in ENV.")

    def send_message(self, content):
        if not self.webhook_url:
            return False
        
        try:
            payload = {"content": content}
            response = requests.post(self.webhook_url, json=payload)
            if response.status_code == 204:
                return True
            else:
                print(f"[!] Webhook error: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"[!] Webhook exception: {e}")
            return False

    def send_file(self, content, file_bytes, filename="image.png"):
        if not self.webhook_url:
            return False
        
        try:
            files = {
                'file': (filename, file_bytes)
            }
            data = {
                'content': content
            }
            response = requests.post(self.webhook_url, files=files, data=data)
            if response.status_code == 200 or response.status_code == 204:
                return True
            else:
                print(f"[!] Webhook file error: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"[!] Webhook file exception: {e}")
            return False

    def send_embed(self, title, description, color=0x3498db):
        if not self.webhook_url:
            return False
            
        embed = {
            "title": title,
            "description": description,
            "color": color,
            "footer": {
                "text": "AEGIS Dashboard System"
            }
        }
        
        try:
            payload = {
                "embeds": [embed]
            }
            response = requests.post(self.webhook_url, json=payload)
            if response.status_code == 204:
                return True
            else:
                print(f"[!] Webhook embed error: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"[!] Webhook embed exception: {e}")
            return False
