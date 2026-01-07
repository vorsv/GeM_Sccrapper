import requests
import config # Imports your config.py settings

data = {
    "content": "✅ **Test Run:** The GeM Bot is connected to Discord!"
}
response = requests.post(config.DISCORD_WEBHOOK_URL, json=data)
print(f"Status Code: {response.status_code}")