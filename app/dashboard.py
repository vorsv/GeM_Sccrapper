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

# --- HIGH CONTRAST DARK CSS ---
st.markdown(f"""
<style>
    /* 1. HIDE DEFAULTS */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}} 
    
    /* 2. STICKY HEADER */
    .sticky-header {{
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        background-color: #0b0f19; /* Matches Dark Theme BG */
        z-index: 99999;
        padding: 20px 40px;
        border-bottom: 1px solid #1e293b;
        display: flex;
        align-items: center;
        transition: all 0.3s ease;
    }}

    .sticky-header.shrink {{
        padding: 10px 40px;
        background-color: rgba(11, 15, 25, 0.95);
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 15px rgba(0,0,0,0.5);
    }}

    .header-logo {{ height: 80px; margin-right: 20px; transition: all 0.3s; }}
    .header-title {{ font-size: 30px; font-weight: 800; color: #ffffff !important; margin: 0; transition: all 0.3s; }}
    
    .sticky-header.shrink .header-logo {{ height: 40px; }}
    .sticky-header.shrink .header-title {{ font-size: 20px; }}

    .main .block-container {{ padding-top: 140px !important; }}

    /* 3. CARD CONTAINER - Force Dark Slate */
    div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"] {{
        background-color: #111827 !important; 
        border: 1px solid #374151 !important; 
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }}

    /* 4. TYPOGRAPHY - Force White/Cyan */
    
    /* Title */
    .item-title {{ 
        font-size: 20px !important; 
        font-weight: 700 !important; 
        color: #ffffff !important; /* PURE WHITE */
        margin-bottom: 5px; 
        line-height: 1.4;
    }}
    
    /* Subtitle */
    .dept-subtitle {{ 
        font-size: 14px !important; 
        color: #94a3b8 !important; /* LIGHT BLUE-GRAY */
        font-weight: 500; 
        margin-bottom: 15px; 
        padding-bottom: 10px;
        border-bottom: 1px solid #374151; 
        display: flex;
        align-items: center;
    }}

    /* Badges - Neon Style */
    .badge {{ 
        display: inline-block; 
        padding: 4px 12px; 
        border-radius: 4px; 
        font-size: 12px; 
        font-weight: 700; 
        margin-right: 10px; 
        letter-spacing: 0.5px;
    }}
    
    .badge-blue {{ 
        background-color: rgba(34, 211, 238, 0.1); 
        color: #22d3ee !important; /* NEON CYAN */
        border: 1px solid #0891b2; 
    }} 
    
    .badge-purple {{ 
        background-color: rgba(216, 180, 254, 0.1); 
        color: #e9d5ff !important; /* LIGHT PURPLE */
        border: 1px solid #9333ea; 
    }}

    /* Dates */
    .date-label {{ 
        font-size: 11px; 
        color: #9ca3af !important; 
        text-transform: uppercase; 
        font-weight: 700; 
        margin-bottom: 4px;
        display: flex;
        align-items: center;
    }}
    .date-value {{ 
        font-size: 15px; 
        color: #f3f4f6 !important; /* OFF-WHITE */
        font-weight: 600; 
    }}

    /* 5. BUTTONS */
    /* Primary Action Buttons */
    div.stButton > button {{
        width: 100%;
        border: 1px solid #4b5563 !important;
        background-color: transparent !important;
        color: #e5e7eb !important;
        border-radius: 6px !important;
        padding: 8px 16px !important;
    }}
    
    div.stButton > button:hover {{
        border-color: #38bdf8 !important;
        color: #38bdf8 !important;
        background-color: rgba(56, 189, 248, 0.1) !important;
    }}

    /* Link Button (Open PDF) needs specific targeting */
    a[target="_blank"] {{
        text-decoration: none;
    }}
    /* This targets the internal container of st.link_button if possible, 
       but Streamlit renders it as an <a> tag styled like a button. 
       We rely on theme config for this one mostly. */

</style>

<div id="my-header" class="sticky-header">
    <img src="{logo_html}" class="header-logo">
    <h1 class="header-title">GeM Tender Hub</h1>
</div>

<script>
    function onScroll() {{
        const header = window.parent.document.getElementById("my-header");
        const scrollContainer = window.parent.document.querySelector('section.main');
        if (scrollContainer && header) {{
            if (scrollContainer.scrollTop > 50) {{
                header.classList.add("shrink");
            }} else {{
                header.classList.remove("shrink");
            }}
        }}
    }}
    const checkContainer = setInterval(() => {{
        const scrollContainer = window.parent.document.querySelector('section.main');
        if (scrollContainer) {{
            scrollContainer.addEventListener("scroll", onScroll);
            clearInterval(checkContainer);
        }}
    }}, 500);
</script>
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
        # Header Area
        st.markdown(f"<div class='item-title'>{row['items']}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='dept-subtitle'>🏢 {row['department']}</div>", unsafe_allow_html=True)
        
        # Badges (Keyword=Blue, ID=Purple)
        st.markdown(f"""
            <span class="badge badge-blue">🎯 {row['title']}</span>
            <span class="badge badge-purple">🆔 {row['bid_no']}</span>
        """, unsafe_allow_html=True)
        
        st.write("") 
        
        # Dates Area
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"""
                <div class='date-label'>🚀 Start Date</div>
                <div class='date-value'>{row['start_date']}</div>
            """, unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
                <div class='date-label'>⏳ End Date</div>
                <div class='date-value'>{row['end_date']}</div>
            """, unsafe_allow_html=True)
            
        st.divider()
        
        # Actions
        cols = st.columns([1, 1, 1]) 
        with cols[0]:
            # Use emoji in label for visual pop
            st.link_button("📄 Open PDF", row['link'], use_container_width=True)
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
tab_live, tab_saved, tab_archive = st.tabs(["📡 Live Feed", "📌 Saved Bids", "🗄️ Archive"])

with st.expander("🔍 Filter Tenders", expanded=False):
    search_query = st.text_input("Search", placeholder="Search by Item, Dept, or ID...")

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