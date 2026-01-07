import json
import time
import os
import requests
import sqlite3
from datetime import datetime
from playwright.sync_api import sync_playwright
import schedule
import config  # Importing your config.py

# --- DATABASE FUNCTIONS ---
def bid_exists(bid_no):
    """Checks if the bid is already in the database to avoid duplicate alerts."""
    conn = sqlite3.connect("tenders.db")
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM tenders WHERE bid_no = ?", (bid_no,))
    exists = cursor.fetchone() is not None
    conn.close()
    return exists

def save_tender_to_db(tender):
    """Saves a new tender to the SQLite database with all details."""
    conn = sqlite3.connect("tenders.db")
    cursor = conn.cursor()
    try:
        # Note: We use INSERT OR IGNORE to be safe, though bid_exists() checks first
        cursor.execute('''
            INSERT OR IGNORE INTO tenders 
            (bid_no, title, items, department, start_date, end_date, link, status, found_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            tender['bid_no'], 
            tender['title'], 
            tender['items'], 
            tender['department'], 
            tender['start_date'],  # New Column
            tender['end_date'], 
            tender['link'], 
            "New", 
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ))
        conn.commit()
    except Exception as e:
        print(f"⚠️ DB Error: {e}")
    finally:
        conn.close()

# --- DISCORD ALERT FUNCTION ---
def send_discord_alert(tender):
    embed = {
        "title": f"📢 New Tender: {tender['title']}",
        "description": f"**Item:** {tender['items']}",
        "url": tender['link'],
        "color": 3066993,  # Green Color
        "fields": [
            {"name": "🆔 Bid Number", "value": tender['bid_no'], "inline": True},
            {"name": "🚀 Start Date", "value": tender['start_date'], "inline": True},
            {"name": "⏳ End Date", "value": tender['end_date'], "inline": True},
            {"name": "🏢 Department", "value": tender['department'], "inline": False}
        ],
        "footer": {"text": f"Found at {datetime.now().strftime('%H:%M')}"}
    }
    
    payload = {"embeds": [embed]}
    try:
        requests.post(config.DISCORD_WEBHOOK_URL, json=payload)
        print(f"✅ Alert sent for {tender['bid_no']}")
    except Exception as e:
        print(f"❌ Failed to send Discord alert: {e}")

# --- CORE SCRAPING LOGIC ---
def scrape_gem():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Starting scrape cycle...")
    new_bids_count = 0

    with sync_playwright() as p:
        # --- STEALTH LAUNCH (Bypasses Blocking) ---
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled", # Hides "I am a robot" flag
                "--no-sandbox", 
                "--disable-setuid-sandbox"
            ]
        )
        
        # Create a context that mimics a real user
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            ignore_https_errors=True
        )
        
        # Javascript injection to hide WebDriver property
        context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        page = context.new_page()

        try:
            # --- NAVIGATE TO PUBLIC BID LIST ---
            target_url = "https://bidplus.gem.gov.in/all-bids"
            print(f"🌍 Navigating to {target_url}...")
            
            # High timeout for slow government servers
            page.goto(target_url, timeout=60000, wait_until="domcontentloaded")
            
            # Wait for card container to load
            page.wait_for_selector(".card-body", timeout=20000)

            # --- KEYWORD SEARCH LOOP ---
            for keyword in config.SEARCH_KEYWORDS:
                print(f"🔍 Searching for: {keyword}")
                
                try:
                    # Select Search Box and Type
                    search_input = 'input[type="search"]'
                    page.wait_for_selector(search_input, state="visible", timeout=5000)
                    
                    page.fill(search_input, "")
                    page.fill(search_input, keyword)
                    page.press(search_input, "Enter")
                    
                    # Wait for results to refresh (adjust sleep if connection is slow)
                    time.sleep(4) 
                except Exception as e:
                    print(f"⚠️ Search skipped for '{keyword}': {e}")
                    continue

                # Extract all cards currently visible
                cards = page.query_selector_all(".card")
                
                for card in cards:
                    try:
                        full_text = card.inner_text()
                        
                        # 1. Extract BID NO
                        bid_no = "Unknown"
                        link = target_url
                        
                        # Find link (usually contains 'showbidDocument')
                        link_elem = card.query_selector("a[href*='/showbidDocument']")
                        if link_elem:
                            link = "https://bidplus.gem.gov.in" + link_elem.get_attribute("href")
                            bid_no = link_elem.inner_text().strip()
                        elif "BID NO:" in full_text:
                            # Fallback: Parse text if link is hidden
                            lines = full_text.split('\n')
                            for line in lines:
                                if "GEM/" in line:
                                    bid_no = line.strip()
                                    break

                        # SKIP if already in DB
                        if bid_exists(bid_no):
                            continue

                        # 2. Extract Items
                        items = "N/A"
                        if "Items:" in full_text:
                            parts = full_text.split("Items:")
                            if len(parts) > 1:
                                items = parts[1].split("Quantity:")[0].strip()

                        # 3. Extract Dates (Start & End)
                        start_date = "N/A"
                        end_date = "N/A"
                        
                        if "Start Date:" in full_text:
                            parts = full_text.split("Start Date:")
                            if len(parts) > 1:
                                temp = parts[1]
                                start_date = temp.split("End Date:")[0].strip()
                                # Clean up formatting
                                start_date = start_date.replace("\n", "").strip()

                        if "End Date:" in full_text:
                            parts = full_text.split("End Date:")
                            if len(parts) > 1:
                                end_date = parts[1].split("\n")[0].strip()

                        # 4. Extract Department
                        department = "Unknown"
                        if "Department Name And Address:" in full_text:
                            parts = full_text.split("Department Name And Address:")
                            if len(parts) > 1:
                                department = parts[1].split("\n")[1].strip()

                        # Construct Data Object
                        tender_data = {
                            "bid_no": bid_no,
                            "title": keyword,  # Using the matched keyword as title tag
                            "items": items[:150], # Truncate long item lists
                            "start_date": start_date,
                            "end_date": end_date,
                            "department": department,
                            "link": link
                        }

                        # SAVE & ALERT
                        save_tender_to_db(tender_data)
                        send_discord_alert(tender_data)
                        new_bids_count += 1
                        
                    except Exception as e:
                        # print(f"Card parse error: {e}") # Uncomment for debugging
                        continue
                
                # Polite pause between keywords
                time.sleep(2)

        except Exception as e:
            print(f"❌ Error during scraping: {e}")

        finally:
            browser.close()
            print(f"✅ Cycle complete. New Bids: {new_bids_count}")

# --- SCHEDULER ---
if __name__ == "__main__":
    print("🤖 GeM Scraper Bot Initialized.")
    
    # Run once immediately on startup to test
    scrape_gem()
    
    # Schedule runs based on config
    schedule.every(config.CHECK_INTERVAL).minutes.do(scrape_gem)
    
    while True:
        schedule.run_pending()
        time.sleep(1)