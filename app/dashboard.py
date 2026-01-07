import streamlit as st
import sqlite3
import pandas as pd
import os

# --- CONFIG ---
st.set_page_config(page_title="GeM Tender Hub", layout="wide", page_icon="🏛️")
DB_FILE = "tenders.db"
LOGO_FILE = "logo.png"

# --- CUSTOM CSS (Larger Fonts & Better Spacing) ---
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Card Container */
    div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"] {
        background-color: white;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding-bottom: 10px;
    }
    
    /* Item Title - Larger */
    .item-title {
        font-size: 18px;
        font-weight: 700;
        color: #1f1f1f;
        margin-bottom: 4px;
        line-height: 1.2;
    }
    
    /* Department Subtitle */
    .dept-subtitle {
        font-size: 15px;
        color: #555;
        font-weight: 500;
        margin-bottom: 12px;
        border-bottom: 1px solid #eee;
        padding-bottom: 8px;
    }

    /* Badges */
    .badge {
        display: inline-block;
        padding: 5px 10px;
        border-radius: 6px;
        font-size: 13px; /* Increased size */
        font-weight: 600;
        margin-right: 6px;
    }
    .badge-blue { background-color: #e3f2fd; color: #1565c0; border: 1px solid #90caf9; }
    .badge-gray { background-color: #f5f5f5; color: #424242; border: 1px solid #e0e0e0; }
    
    /* Date Box - Larger */
    .date-label { font-size: 12px; color: #777; text-transform: uppercase; font-weight: 700; }
    .date-value { font-size: 15px; color: #000; font-weight: 600; margin-top: 2px; }
    
</style>
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

# --- COMPONENT: SINGLE CARD RENDERER ---
def render_single_card(row, status_mode):
    ukey = f"{row['bid_no']}_{status_mode}"
    
    with st.container(border=True):
        # 1. Header Area (Title & Subtitle)
        st.markdown(f"<div class='item-title'>{row['items']}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='dept-subtitle'>🏢 {row['department']}</div>", unsafe_allow_html=True)
        
        # 2. Badges (Keyword & ID)
        st.markdown(f"""
            <span class="badge badge-blue">🎯 {row['title']}</span>
            <span class="badge badge-gray">🆔 {row['bid_no']}</span>
        """, unsafe_allow_html=True)
        
        st.write("") # Spacer

        # 3. Dates Grid (Larger Text)
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"<div class='date-label'>🚀 Start Date</div><div class='date-value'>{row['start_date']}</div>", unsafe_allow_html=True)
        with c2:
            st.markdown(f"<div class='date-label'>⏳ End Date</div><div class='date-value'>{row['end_date']}</div>", unsafe_allow_html=True)

        st.divider()

        # 4. Actions Toolbar (Grouped Tightly)
        # We use a 4-column layout but give buttons more width (0.3) to fit text
        cols = st.columns([1, 1, 1]) 
        
        # Button 1: View Document (Link)
        with cols[0]:
            st.link_button("📄 Open PDF", row['link'], use_container_width=True)
        
        # Button 2: Save / Unsave
        with cols[1]:
            if status_mode != "Bookmarked":
                if st.button("📌 Save", key=f"bm_{ukey}", use_container_width=True): 
                    update_status(row['bid_no'], "Bookmarked")
            else:
                if st.button("📤 Unsave", key=f"un_{ukey}", use_container_width=True): 
                    update_status(row['bid_no'], "New")
        
        # Button 3: Ignore
        with cols[2]:
             if st.button("🗑️ Ignore", key=f"ig_{ukey}", use_container_width=True): 
                 update_status(row['bid_no'], "Ignored")

# --- UI HEADER & NAV ---
c1, c2 = st.columns([1, 8])
with c1:
    if os.path.exists(LOGO_FILE):
        st.image(LOGO_FILE, width=70)
with c2:
    st.subheader("GeM Tender Hub")

tab_live, tab_saved, tab_archive = st.tabs(["📡 Live Feed", "📌 Saved Bids", "🗄️ Archive"])

# --- SEARCH BAR ---
with st.expander("🔍 Filter Tenders", expanded=False):
    search_query = st.text_input("Search", placeholder="Search by Item, Dept, or ID...")

# --- MAIN GRID RENDERER ---
def render_tab_content(status_mode):
    df = get_data(status_mode)
    
    if search_query:
        df = df[df['items'].str.contains(search_query, case=False, na=False) | 
                df['department'].str.contains(search_query, case=False, na=False) | 
                df['title'].str.contains(search_query, case=False, na=False)]
    
    if df.empty:
        st.info("No tenders found in this section.")
        return
    
    st.caption(f"Showing {len(df)} tenders")

    # GRID LOGIC: Process 2 items per row
    for i in range(0, len(df), 2):
        cols = st.columns(2)
        
        # Render first card
        with cols[0]:
            render_single_card(df.iloc[i], status_mode)
        
        # Render second card (if exists)
        if i + 1 < len(df):
            with cols[1]:
                render_single_card(df.iloc[i+1], status_mode)

# --- RENDER TABS ---
with tab_live:
    render_tab_content("Live")
with tab_saved:
    render_tab_content("Bookmarked")
with tab_archive:
    render_tab_content("Ignored")