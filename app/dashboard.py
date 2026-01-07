import streamlit as st
import sqlite3
import pandas as pd
import os
import base64

# --- CONFIG ---
st.set_page_config(page_title="GeM Tender Hub", layout="wide", page_icon="🏛️")
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

# --- UI REFINEMENTS CSS ---
st.markdown(f"""
<style>
    /* 1. HIDE DEFAULT STREAMLIT UI */
    header[data-testid="stHeader"], footer, #MainMenu {{
        display: none !important;
    }}
    
    /* 2. BACKGROUND */
    .stApp {{
        background-color: #0f172a;
        color: #f8fafc;
    }}
    
    /* 3. STICKY HEADER (Fixed Top) */
    .sticky-header {{
        position: fixed; top: 0; left: 0; width: 100%;
        background-color: #0f172a;
        z-index: 999999;
        padding: 15px 40px;
        border-bottom: 1px solid #1e293b;
        display: flex; align-items: center; 
        height: 100px; /* Fixed Height */
        box-shadow: 0 4px 20px rgba(0,0,0,0.4);
    }}
    .header-logo {{ height: 60px; margin-right: 20px; }}
    .header-title {{ font-size: 28px; font-weight: 800; color: #fff; margin: 0; }}

    /* 4. PUSH CONTENT DOWN (The "Gap" Fix) */
    .main .block-container {{ 
        padding-top: 140px !important; /* Clears the 100px header + 40px gap */
        max_width: 1200px;
    }}

    /* 5. CENTRAL SEARCH BAR STYLING */
    div[data-testid="stTextInput"] {{
        margin-bottom: 20px;
    }}
    div[data-testid="stTextInput"] input {{
        background-color: #1e293b !important;
        border: 1px solid #334155 !important;
        color: white !important;
        border-radius: 50px !important; /* Rounded pill shape */
        padding: 10px 20px !important;
        font-size: 16px;
    }}
    div[data-testid="stTextInput"] input:focus {{
        border-color: #38bdf8 !important;
        box-shadow: 0 0 10px rgba(56, 189, 248, 0.3);
    }}

    /* 6. CLEAN TABS (No Borders/Boxes) */
    div[data-baseweb="tab-list"] {{
        background-color: transparent !important;
        border: none !important;
        gap: 40px; /* Space between tab names */
        justify-content: center; /* Center the tabs */
        margin-bottom: 30px;
        border-bottom: 1px solid #334155; /* Subtle line under tabs */
    }}
    button[data-baseweb="tab"] {{
        background-color: transparent !important;
        border: none !important;
        color: #94a3b8 !important; 
        font-size: 16px !important;
        font-weight: 600 !important;
        padding-bottom: 10px !important;
    }}
    button[data-baseweb="tab"][aria-selected="true"] {{
        color: #38bdf8 !important; 
        border-bottom: 3px solid #38bdf8 !important;
    }}
    button[data-baseweb="tab"]:focus {{ outline: none !important; }}

    /* 7. CARD STYLING */
    div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"] {{
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 20px;
    }}
    
    /* 8. TYPOGRAPHY & BADGES */
    .item-title {{ font-size: 18px; font-weight: 700; color: #f8fafc; margin-bottom: 5px; }}
    .dept-subtitle {{ font-size: 14px; color: #94a3b8; font-weight: 500; margin-bottom: 15px; border-bottom: 1px solid #334155; padding-bottom: 10px; }}
    .badge {{ display: inline-block; padding: 4px 10px; border-radius: 6px; font-size: 11px; font-weight: 700; margin-right: 8px; }}
    .badge-blue {{ background-color: rgba(56, 189, 248, 0.1); color: #38bdf8; border: 1px solid #0ea5e9; }} 
    .badge-purple {{ background-color: rgba(192, 132, 252, 0.1); color: #e879f9; border: 1px solid #d946ef; }}
    
    /* 9. BUTTONS */
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

</style>

<div class="sticky-header">
    <img src="{logo_html}" class="header-logo">
    <h1 class="header-title">GeM Tender Hub</h1>
</div>
""", unsafe_allow_html=True)

# --- DATA FUNCTIONS ---
def get_data(status_filter):
    conn = sqlite3.connect(DB_FILE)
    if status_filter == "All":
        query = "SELECT * FROM tenders ORDER BY found_at DESC"
    elif status_filter == "Live":
        query = "SELECT * FROM tenders WHERE status = 'New' ORDER BY found_at DESC"
    else:
        query = f"SELECT * FROM tenders WHERE status = '{status_filter}' ORDER BY found_at DESC"
    try:
        df = pd.read_sql(query, conn)
    except Exception:
        df = pd.DataFrame()
    conn.close()
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
    with st.container(border=True):
        st.markdown(f"<div class='item-title'>{row['items']}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='dept-subtitle'>🏢 {row['department']}</div>", unsafe_allow_html=True)
        
        st.markdown(f"""
            <span class="badge badge-blue">🎯 {row['title']}</span>
            <span class="badge badge-purple">🆔 {row['bid_no']}</span>
        """, unsafe_allow_html=True)
        
        st.write("") 
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"<div style='color:#94a3b8;font-size:11px;font-weight:700;'>🚀 START</div><div style='color:#f1f5f9;font-weight:600;'>{row['start_date']}</div>", unsafe_allow_html=True)
        with c2:
            st.markdown(f"<div style='color:#94a3b8;font-size:11px;font-weight:700;'>⏳ END</div><div style='color:#f1f5f9;font-weight:600;'>{row['end_date']}</div>", unsafe_allow_html=True)
            
        st.divider()
        
        cols = st.columns([1, 1, 1]) 
        with cols[0]:
            st.link_button("📄 PDF", row['link'], use_container_width=True)
        with cols[1]:
            if status_mode != "Bookmarked":
                if st.button("📌 Save", key=f"bm_{ukey}", use_container_width=True): 
                    update_status(row['bid_no'], "Bookmarked")
            else:
                if st.button("📤 Unsave", key=f"un_{ukey}", use_container_width=True): 
                    update_status(row['bid_no'], "New")
        with cols[2]:
             if st.button("🗑️ Ignore", key=f"ig_{ukey}", use_container_width=True): 
                 update_status(row['bid_no'], "Ignored")

# --- UI LOGIC ---

# 1. CENTRAL SEARCH BAR (The "Hero" Section)
# We use columns to center it nicely
c1, c2, c3 = st.columns([1, 2, 1])
with c2:
    search_query = st.text_input("Search", placeholder="🔍 Search tenders by ID, Item, or Department...", label_visibility="collapsed")

# 2. TABS (Now below search)
tab_live, tab_saved, tab_archive = st.tabs(["📡 Live Feed", "📌 Saved Bids", "🗄️ Archive"])

# 3. GRID CONTENT
def render_tab_content(status_mode):
    df = get_data(status_mode)
    if search_query:
        df = df[df['items'].str.contains(search_query, case=False, na=False) | 
                df['department'].str.contains(search_query, case=False, na=False) | 
                df['title'].str.contains(search_query, case=False, na=False)]
    
    if df.empty:
        st.info("No tenders found.")
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