import streamlit as st
import sqlite3
import pandas as pd
import os
import base64
from datetime import datetime

# --- CONFIG ---
st.set_page_config(page_title="DD's GeM Hub", layout="wide", page_icon="🏛️")
DB_FILE = "tenders.db"
LOGO_FILE = "logo.png"

# --- HELPER: CONVERT IMAGE TO BASE64 ---
def get_img_as_base64(file):
    try:
        with open(file, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except:
        return ""

if os.path.exists(LOGO_FILE):
    logo_b64 = get_img_as_base64(LOGO_FILE)
    logo_html = f"data:image/png;base64,{logo_b64}"
else:
    logo_html = "" 

# --- HELPER: GET STATS FOR HEADER ---
def get_scan_stats():
    conn = sqlite3.connect(DB_FILE)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(found_at) FROM tenders")
        last_time = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM tenders WHERE found_at >= date('now', '-1 day')")
        recent_count = cursor.fetchone()[0]

        display_time = "N/A"
        if last_time:
            dt = datetime.strptime(last_time, '%Y-%m-%d %H:%M:%S')
            display_time = dt.strftime('%d %b %H:%M')
            
        return display_time, recent_count
    except:
        return "Offline", 0
    finally:
        conn.close()

last_time_str, recent_count = get_scan_stats()

# --- UI REFINEMENTS CSS ---
st.markdown(f"""
<style>
    header[data-testid="stHeader"], footer, #MainMenu {{ display: none !important; }}
    
    .stApp {{ background-color: #0f172a; color: #f8fafc; }}
    
    /* STICKY HEADER */
    .sticky-header {{
        position: fixed; top: 0; left: 0; width: 100%;
        background-color: #0f172a;
        z-index: 999999;
        padding: 10px 40px; 
        border-bottom: 1px solid #1e293b;
        display: flex; align-items: center; justify-content: space-between;
        height: 140px; 
        box-shadow: 0 10px 30px rgba(0,0,0,0.5); 
    }}
    .header-left {{ display: flex; align-items: center; }}
    .header-logo {{ height: 100px; width: auto; margin-right: 30px; }}
    .header-title {{ font-size: 36px; font-weight: 800; color: #fff; margin: 0; }}

    /* STATUS PILL */
    .status-container {{ text-align: right; }}
    .status-text {{ color: #94a3b8; font-size: 14px; font-weight: 600; margin-bottom: 4px; }}
    .status-sub {{ color: #38bdf8; font-size: 12px; font-weight: 500; }}

    /* SPACER */
    .content-spacer {{ height: 160px; width: 100%; background: transparent; }}

    /* SEARCH BAR */
    div[data-testid="stTextInput"] input {{
        background-color: #1e293b !important;
        border: 1px solid #334155 !important;
        color: white !important;
        border-radius: 50px !important;
        padding: 12px 25px !important;
        font-size: 18px; 
    }}
    div[data-testid="stTextInput"] input:focus {{
        border-color: #38bdf8 !important;
        box-shadow: 0 0 15px rgba(56, 189, 248, 0.2);
    }}

    /* TABS */
    div[data-baseweb="tab-list"] {{
        background-color: transparent !important;
        border: none !important;
        gap: 50px;
        justify-content: center;
        margin-bottom: 40px;
        border-bottom: 1px solid #334155;
    }}
    button[data-baseweb="tab"] {{
        background-color: transparent !important;
        border: none !important;
        color: #94a3b8 !important; 
        font-size: 18px !important; font-weight: 600 !important;
        padding-bottom: 12px !important;
    }}
    button[data-baseweb="tab"][aria-selected="true"] {{
        color: #38bdf8 !important; border-bottom: 3px solid #38bdf8 !important;
    }}

    /* CARD STYLING */
    div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"] {{
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 20px;
    }}
    
    .item-title {{ font-size: 18px; font-weight: 700; color: #f8fafc; margin-bottom: 5px; }}
    .dept-subtitle {{ font-size: 14px; color: #94a3b8; font-weight: 500; margin-bottom: 15px; border-bottom: 1px solid #334155; padding-bottom: 10px; }}
    .badge {{ display: inline-block; padding: 4px 10px; border-radius: 6px; font-size: 11px; font-weight: 700; margin-right: 8px; }}
    .badge-blue {{ background-color: rgba(56, 189, 248, 0.1); color: #38bdf8; border: 1px solid #0ea5e9; }} 
    .badge-purple {{ background-color: rgba(192, 132, 252, 0.1); color: #e879f9; border: 1px solid #d946ef; }}
    .badge-red {{ background-color: rgba(239, 68, 68, 0.1); color: #f87171; border: 1px solid #ef4444; }}
    
    /* BUTTONS */
    div.stButton > button {{
        background-color: transparent !important;
        color: #cbd5e1 !important;
        border: 1px solid #475569 !important;
        border-radius: 8px;
    }}
    div.stButton > button:hover {{
        border-color: #38bdf8 !important;
        color: #38bdf8 !important;
        background-color: rgba(56, 189, 248, 0.1) !important;
    }}

    /* --- FOOTER CSS --- */
    .custom-footer {{
        width: 100%;
        text-align: center;
        padding: 30px 0px;
        margin-top: 50px;
        border-top: 1px solid #1e293b;
        color: #64748b;
        font-size: 13px;
    }}
    .custom-footer a {{
        color: #94a3b8;
        text-decoration: none;
        margin: 0 10px;
        transition: color 0.3s;
    }}
    .custom-footer a:hover {{
        color: #38bdf8;
    }}

</style>

<div class="sticky-header">
    <div class="header-left">
        <img src="{logo_html}" class="header-logo">
        <h1 class="header-title">DD's GeM Hub</h1>
    </div>
    <div class="status-container">
        <div class="status-text">Last Scan: {last_time_str}</div>
        <div class="status-sub">⚡ {recent_count} added recently</div>
    </div>
</div>
""", unsafe_allow_html=True)

# --- DATA FUNCTIONS ---
def get_data(status_filter):
    conn = sqlite3.connect(DB_FILE)
    query = "SELECT * FROM tenders ORDER BY found_at DESC"
    try:
        df = pd.read_sql(query, conn)
    except Exception:
        df = pd.DataFrame()
    conn.close()
    
    if df.empty: return df

    def parse_date(date_str):
        try:
            clean_str = date_str.split(' ')[0] 
            return datetime.strptime(clean_str, "%d-%m-%Y")
        except:
            return datetime.max 

    df['real_end_date'] = df['end_date'].apply(parse_date)
    today = datetime.now()

    if status_filter == "Expired":
        df = df[df['real_end_date'] < today]
    else:
        df = df[df['real_end_date'] >= today]
        if status_filter == "Live":
            df = df[df['status'] == 'New']
        elif status_filter == "Bookmarked":
            df = df[df['status'] == 'Bookmarked']
        elif status_filter == "Ignored":
            df = df[df['status'] == 'Ignored']
            
    return df

def update_status(bid_no, new_status):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE tenders SET status = ? WHERE bid_no = ?", (new_status, bid_no))
    conn.commit()
    conn.close()
    st.rerun()

# --- CARD RENDERER ---
def render_single_card(row, status_mode):
    ukey = f"{row['bid_no']}_{status_mode}"
    is_expired = status_mode == "Expired"
    
    with st.container(border=True):
        st.markdown(f"<div class='item-title'>{row['items']}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='dept-subtitle'>🏢 {row['department']}</div>", unsafe_allow_html=True)
        
        if is_expired:
             st.markdown(f"""<span class="badge badge-red">⚠️ EXPIRED</span>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""
                <span class="badge badge-blue">🎯 {row['title']}</span>
                <span class="badge badge-purple">🆔 {row['bid_no']}</span>
            """, unsafe_allow_html=True)
        
        st.write("") 
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"<div style='color:#94a3b8;font-size:11px;font-weight:700;'>🚀 START</div><div style='color:#f1f5f9;font-weight:600;'>{row['start_date']}</div>", unsafe_allow_html=True)
        with c2:
            color = "#f87171" if is_expired else "#f1f5f9"
            st.markdown(f"<div style='color:#94a3b8;font-size:11px;font-weight:700;'>⏳ END</div><div style='color:{color};font-weight:600;'>{row['end_date']}</div>", unsafe_allow_html=True)
            
        st.divider()
        
        cols = st.columns([1, 1, 1]) 
        with cols[0]:
            st.link_button("📄 PDF", row['link'], use_container_width=True)
        with cols[1]:
            if not is_expired:
                if status_mode != "Bookmarked":
                    if st.button("📌 Save", key=f"bm_{ukey}", use_container_width=True): 
                        update_status(row['bid_no'], "Bookmarked")
                else:
                    if st.button("📤 Unsave", key=f"un_{ukey}", use_container_width=True): 
                        update_status(row['bid_no'], "New")
            else:
                 st.button("🚫 Ended", key=f"end_{ukey}", disabled=True, use_container_width=True)

        with cols[2]:
             if st.button("🗑️ Ignore", key=f"ig_{ukey}", use_container_width=True): 
                 update_status(row['bid_no'], "Ignored")

# --- UI LOGIC ---

# 1. SPACER
st.markdown('<div class="content-spacer"></div>', unsafe_allow_html=True)

# 2. SEARCH
c1, c2, c3 = st.columns([1, 2, 1])
with c2:
    search_query = st.text_input("Search", placeholder="🔍 Search tenders by ID, Item, or Department...", label_visibility="collapsed")

# 3. TABS
tab_live, tab_saved, tab_archive, tab_expired = st.tabs(["📡 Live Feed", "📌 Saved Bids", "🗄️ Archive", "⚠️ Expired"])

# 4. CONTENT
def render_tab_content(status_mode):
    df = get_data(status_mode)
    if search_query:
        df = df[df['items'].str.contains(search_query, case=False, na=False) | 
                df['department'].str.contains(search_query, case=False, na=False) | 
                df['title'].str.contains(search_query, case=False, na=False)]
    
    if df.empty:
        st.info("No tenders found here.")
        return
    
    st.caption(f"Showing {len(df)} tenders")
    
    for i in range(0, len(df), 2):
        cols = st.columns(2)
        with cols[0]:
            render_single_card(df.iloc[i], status_mode)
        if i + 1 < len(df):
            with cols[1]:
                render_single_card(df.iloc[i+1], status_mode)

with tab_live: render_tab_content("Live")
with tab_saved: render_tab_content("Bookmarked")
with tab_archive: render_tab_content("Ignored")
with tab_expired: render_tab_content("Expired")

# --- 5. FOOTER (INJECTED AT BOTTOM) ---
st.markdown("""
    <div class="custom-footer">
        Made by <b>VORSV Inc.</b> &copy; 2026<br>
        <br>
        <a href="#">System Status</a> &bull; 
        <a href="#">Logs</a> &bull; 
        <a href="#">Documentation</a>
    </div>
""", unsafe_allow_html=True)