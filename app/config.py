# --- CONFIGURATION ---

# 1. Discord Webhook URL (Get this from Discord Channel Settings > Integrations > Webhooks)
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1458486688954187927/oYmnjclpoaJ_c3wkO6DnUyttOylxbWsbxbPpCeyBpzSZuO4r4xmWif2WmuY340PyOHRo"

# 2. Keywords to search for (The bot will search these one by one)
SEARCH_KEYWORDS = [
    "blinds",
    "curtains",
    "vinyl",
    "sticker",
    "name plate",
    "name board",
    "reflector",
    "roller blinds",
    "lamination",
    "netlon",
    "led stand",
    "neon sign",
    "led board",
    "nameboard"
]

# 3. How often to check (in minutes)
CHECK_INTERVAL = 30 

# 4. File to store history (so you don't get duplicate alerts)
HISTORY_FILE = "seen_bids.json"
