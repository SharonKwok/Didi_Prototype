import os
import datetime
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# ==========================================
# 1. Page Configuration & State Initialization
# ==========================================
st.set_page_config(page_title="Performance Dashboard", layout="wide", initial_sidebar_state="expanded")

# Initialize Session States
if 'lang' not in st.session_state: st.session_state.lang = "English"
if 'font_size' not in st.session_state: st.session_state.font_size = "Medium"
if 'theme' not in st.session_state: st.session_state.theme = "Light"
if 'edit_mode' not in st.session_state: st.session_state.edit_mode = False
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = [{"role": "assistant", "content": "Hello! I am your AI Marketing Agent. I can help analyze your performance data. Ask me anything!"}]

ALL_AVAILABLE_CHARTS = ["Trend Timeline", "Distribution Share", "Efficiency Comparison", "4-Quadrant Scatter", "Activity Heatmap", "Volume Treemap", "Conversion Funnel"]
if 'chart_layout' not in st.session_state:
    st.session_state.chart_layout = {
        "Overview (All)": ["Trend Timeline", "Distribution Share", "Efficiency Comparison", "4-Quadrant Scatter", "Activity Heatmap"],
        "In-App Ads": ["Trend Timeline", "Distribution Share", "Efficiency Comparison", "4-Quadrant Scatter", "Activity Heatmap"],
        "Promo Codes": ["Trend Timeline", "Distribution Share", "Efficiency Comparison", "4-Quadrant Scatter", "Activity Heatmap"],
        "Communications": ["Trend Timeline", "Distribution Share", "Efficiency Comparison", "4-Quadrant Scatter", "Activity Heatmap"]
    }

# Translation Dictionary
TRANSLATIONS = {
    "English": {"home": "Home", "dash": "Dashboards", "set": "Settings", "search": "Quick search", "edit": "✏️ Edit", "done": "✔️ Done Editing", "welcome": "Welcome to Workspace"},
    "Chinese": {"home": "首頁", "dash": "儀表板", "set": "設定", "search": "快速搜尋", "edit": "✏️ 編輯", "done": "✔️ 完成編輯", "welcome": "歡迎來到工作區"},
    "Spanish": {"home": "Inicio", "dash": "Tableros", "set": "Ajustes", "search": "Búsqueda", "edit": "✏️ Editar", "done": "✔️ Listo", "welcome": "Bienvenido al Espacio"}
}
t = TRANSLATIONS.get(st.session_state.lang, TRANSLATIONS["English"])

# Dynamic CSS Theme Engine
FONT_MAP = {"Small": "12px", "Medium": "16px", "Large": "20px"}
fs = FONT_MAP.get(st.session_state.font_size, "16px")

is_dark = st.session_state.theme == "Dark"
bg_color = "#121212" if is_dark else "#f4f6f8"
card_bg = "#1e1e1e" if is_dark else "#ffffff"
text_col = "#ffffff" if is_dark else "#202124"
subtext_col = "#cccccc" if is_dark else "#5f6368"
border_col = "#333333" if is_dark else "#e0e0e0"

st.markdown(f"""
    <style>
    /* Global Font and Theme Colors */
    html, body, [class*="css"] {{ font-size: {fs} !important; color: {text_col} !important; }}
    .stApp {{ background-color: {bg_color}; }}
    h1, h2, h3, h4, h5, h6, p, div {{ color: {text_col}; }}
    
    /* Metrics Cards */
    [data-testid="stMetric"] {{
        background-color: {card_bg}; border: 1px solid {border_col};
        border-radius: 8px; padding: 15px; box-shadow: 0px 2px 4px rgba(0, 0, 0, 0.05);
    }}
    [data-testid="stMetricLabel"] {{ color: {subtext_col} !important; font-weight: 500; }}
    [data-testid="stMetricValue"] {{ font-weight: 700; color: {text_col} !important; }}
    
    /* Strict Business Blue Buttons with Pure White Text */
    button[data-testid="baseButton-secondary"], button[data-testid="baseButton-primary"] {{
        background-color: #0056b3 !important;
        color: #ffffff !important;
        border-radius: 6px !important;
        border: none !important;
        font-weight: 600 !important;
    }}
    button[data-testid="baseButton-secondary"]:hover, button[data-testid="baseButton-primary"]:hover {{
        background-color: #004494 !important;
        color: #ffffff !important;
    }}
    button[data-testid="baseButton-secondary"] p, button[data-testid="baseButton-primary"] p {{
        color: #ffffff !important;
    }}
    
    /* MultiSelect Tags (Force Blue instead of Red) */
    .stMultiSelect div[data-baseweb="tag"] {{ background-color: #0056b3 !important; color: white !important; border-radius: 4px; }}
    .stMultiSelect div[data-baseweb="tag"] span {{ color: white !important; font-weight: 500 !important; }}
    .stMultiSelect div[data-baseweb="tag"] svg {{ fill: white !important; }}
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {{ background-color: {card_bg}; border-right: 1px solid {border_col}; }}
    
    /* Floating AI Agent Popover */
    div[data-testid="stPopover"] {{
        position: fixed !important;
        bottom: 30px !important;
        right: 30px !important;
        z-index: 999999 !important;
    }}
    div[data-testid="stPopover"] > button {{
        background-color: #0056b3 !important;
        color: #ffffff !important;
        border-radius: 50px !important;
        padding: 15px 30px !important;
        font-weight: bold !important;
        box-shadow: 0 6px 16px rgba(0,0,0,0.3) !important;
        border: none !important;
    }}
    div[data-testid="stPopover"] > button p {{
        color: #ffffff !important;
        font-size: 16px !important;
        margin: 0 !important;
    }}
    </style>
""", unsafe_allow_html=True)

# ==========================================
# DYNAMIC INSIGHTS GENERATOR
# ==========================================
@st.dialog("📊 Detailed Data Insights & Analysis")
def show_insight(chart_name, view, ia_df, pr_df, co_df):
    st.markdown(f"### Insights for: {chart_name}")
    st.markdown("---")
    
    try:
        if chart_name == "Trend Timeline":
            if view == "Overview (All)":
                ia_vol = ia_df['show_pv'].sum()
                pr_vol = pr_df['redemption_count'].sum()
                co_vol = co_df['delivered_count'].sum() if not co_df.empty else 0
                st.write(f"**Data Summary**: Across all dates selected, In-App generated **{ia_vol:,.0f}** impressions, Promos saw **{pr_vol:,.0f}** redemptions, and Communications delivered **{co_vol:,.0f}** messages.")
                st.write("📈 **Key Takeaway**: Look for synchronised peaks across lines. If Promo spikes when In-App spikes, your cross-channel synergy is working.")
            elif view == "In-App Ads":
                peak_day = ia_df.groupby('pt')['show_pv'].sum().idxmax().strftime('%Y-%m-%d')
                peak_vol = ia_df.groupby('pt')['show_pv'].sum().max()
                st.write(f"**Data Summary**: The highest exposure day was **{peak_day}** with **{peak_vol:,.0f}** views.")
                st.write("⚠️ **Attention**: Ensure your budget didn't cap out prematurely on peak days. Check if CTR matches the exposure trend.")
            elif view == "Promo Codes":
                peak_day = pr_df.groupby('date')['usage_count'].sum().idxmax().strftime('%Y-%m-%d')
                st.write(f"**Data Summary**: Actual promo usage peaked on **{peak_day}**.")
                st.write("📈 **Key Takeaway**: A growing gap between redemptions and usage lines indicates users are saving codes but not converting.")
            elif view == "Communications":
                peak_day = co_df.groupby('date')['clicks'].sum().idxmax().strftime('%Y-%m-%d')
                st.write(f"**Data Summary**: Clicks peaked on **{peak_day}**.")
                st.write("⚠️ **Attention**: Flatlines in delivery indicate disabled campaigns or scheduling errors.")
                
        elif chart_type == "Distribution Share":
            if view == "In-App Ads":
                top_city = ia_df.groupby('city_name')['show_pv'].sum().idxmax()
                top_pct = (ia_df.groupby('city_name')['show_pv'].sum().max() / ia_df['show_pv'].sum()) * 100
                st.write(f"**Data Summary**: **{top_city}** dominates with **{top_pct:.1f}%** of total ad delivery.")
                st.write("💡 **Action**: If regional targeting is meant to be equal, your bidding strategy in other cities is underperforming.")
            elif view == "Promo Codes":
                top_city = pr_df.groupby('city_name')['usage_count'].sum().idxmax()
                st.write(f"**Data Summary**: **{top_city}** has the highest promo conversion volume.")
                st.write("💡 **Action**: Consider running city-specific campaigns for the lowest performing slices to boost market share.")
            else:
                st.write("**Data Summary**: Identifies the primary driver of your traffic.")
                st.write("💡 **Action**: Ensure your budget allocation matches this distribution slice.")
                
        elif chart_type == "Efficiency Comparison":
            st.write("**Data Summary**: Compares the conversion rates directly.")
            st.write("⚠️ **Attention**: High-volume bars with low efficiency (<1%) mean you are paying for junk reach. Pause the lowest performing bar and reallocate.")
            
        elif chart_type == "4-Quadrant Scatter":
            st.write("**Data Summary**: Plots Volume (X) vs Efficiency (Y).")
            st.write("🎯 **Stars (Top-Right)**: High volume, high rate. Scale these up.\n\n📈 **Potential (Top-Left)**: Low volume, high rate. Increase their budget caps.\n\n🛑 **Dogs (Bottom-Right)**: High volume, low rate. Pause these immediately to save ROI.")
            
        elif chart_type == "Activity Heatmap":
            st.write("**Data Summary**: Shows interaction density by day of the week.")
            st.write("💡 **Action**: Locate the darkest cells. These are your golden hours. Shift automated campaign launches to match these specific days.")
            
        elif chart_type == "Volume Treemap":
            st.write("**Data Summary**: Visualizes scale hierarchy.")
            st.write("⚠️ **Attention**: Ensure that your strategically important campaigns occupy the largest boxes. If a minor campaign is massive, it's eating your budget.")
            
        elif chart_type == "Conversion Funnel":
            st.write("**Data Summary**: Step-by-step user journey tracking.")
            st.write("🚨 **Watch out for**: A drop-off greater than 75% between any two stages. This indicates a severe UX bottleneck or broken tracking link.")
        
        else:
            st.write("General analysis: Monitor outliers and correlate with your campaign launch dates.")
            
    except Exception as e:
        st.write("Insufficient data for detailed insights in this specific view.")
        
    st.markdown("---")
    if st.button("Close Insights"):
        st.rerun()

# ==========================================
# 2. Data Loading
# ==========================================
@st.cache_data
def load_data():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    inapp_file = os.path.join(base_dir, "in_app_analytical_dataset_validated.xlsx")
    promo_file = os.path.join(base_dir, "Promocode_Performance.xlsx")
    comm_file = os.path.join(base_dir, "Communication.xlsx")
    mock_url = "https://web.didiglobal.com/au/store/"
    
    df_inapp = pd.read_excel(inapp_file, sheet_name="Raw Data")
    df_inapp['pt'] = pd.to_datetime(df_inapp['pt'])
    df_inapp['day_of_week'] = df_inapp['pt'].dt.day_name()
    if 'campaign_ver' not in df_inapp.columns: df_inapp['campaign_ver'] = 'All'
    df_inapp['url'] = mock_url
    
    df_promo = pd.read_excel(promo_file, sheet_name="Reporting Data")
    df_promo['date'] = pd.to_datetime(df_promo['date'])
    df_promo['day_of_week'] = df_promo['date'].dt.day_name()
    df_promo['url'] = mock_url

    if os.path.exists(comm_file):
        try:
            xls_comm = pd.ExcelFile(comm_file)
            df_comm_raw = pd.read_excel(xls_comm, sheet_name="Push_Hourly_Performance")
            df_bridge = pd.read_excel(xls_comm, sheet_name="Bridge_Canvas_Market")
            df_comm_raw['date'] = pd.to_datetime(df_comm_raw['report_date'])
            df_comm = df_comm_raw.rename(columns={'canvas_name': 'push_title', 'show_count': 'sends', 'click_count': 'clicks'})
            bridge_agg = df_bridge.groupby('canvas_id')['market'].apply(lambda x: ', '.join(x)).reset_index()
            df_comm = pd.merge(df_comm, bridge_agg, left_on='matched_canvas_id', right_on='canvas_id', how='left')
            df_comm['target_markets'] = df_comm['market'].fillna('Unknown')
            df_comm['channel'] = 'Push'
            df_comm['sends'] = df_comm['sends'].fillna(0)
            df_comm['clicks'] = df_comm['clicks'].fillna(0)
            df_comm['delivered_count'] = (df_comm['sends'] * np.random.uniform(1.0, 1.1, size=len(df_comm))).astype(int) 
            df_comm['url'] = mock_url
        except Exception:
            df_comm = pd.DataFrame()
    else:
        df_comm = pd.DataFrame()
        
    return df_inapp, df_promo, df_comm

try:
    df_inapp, df_promo, df_comm = load_data()
    all_cities = set(df_inapp['city_name'].dropna().unique()) | set(df_promo['city_name'].dropna().unique())
    available_cities = sorted(list(all_cities))
    
    # ==========================================
    # 3. SIDEBAR NAVIGATION
    # ==========================================
    st.sidebar.text_input(t["search"], placeholder="🔍 Search...")
    st.sidebar.markdown("---")
    nav_selection = st.sidebar.radio("NAVIGATION", [f"🏠 {t['home']}", f"📈 {t['dash']}", f"⚙️ {t['set']}"], index=1)

    # ==========================================
    # 4. PAGE ROUTING
    # ==========================================
    
    if nav_selection.endswith(t['set']):
        st.title(t["set"])
        st.markdown("---")
        s_col1, s_col2 = st.columns(2)
        with s_col1:
            st.selectbox("Timezone", ["UTC", "AEST", "PST", "EST"])
            st.selectbox("AI Agent Language", ["English", "Chinese", "Spanish", "French"])
        with s_col2:
            new_lang = st.selectbox("Display Language (UI)", ["English", "Chinese", "Spanish"], index=["English", "Chinese", "Spanish"].index(st.session_state.lang))
            new_font = st.selectbox("Font Size", ["Small", "Medium", "Large"], index=["Small", "Medium", "Large"].index(st.session_state.font_size))
            new_theme = st.selectbox("Dashboard Appearance", ["Light", "Dark"], index=["Light", "Dark"].index(st.session_state.theme))
            
        if st.button("Save Settings"):
            st.session_state.lang = new_lang
            st.session_state.font_size = new_font
            st.session_state.theme = new_theme
            st.rerun()

    elif nav_selection.endswith(t['home']):
        st.title(t["welcome"])
        st.info("Home view is currently being set up. Please navigate to Dashboards.")

    elif nav_selection.endswith(t['dash']):
        # TOP TITLE (Simplified)
        col_title, col_edit = st.columns([8, 1])
        col_title.caption(f"Home / Dashboard")
        col_title.title("Dashboard")
        
        if col_edit.button(t['done'] if st.session_state.edit_mode else t['edit']):
            st.session_state.edit_mode = not st.session_state.edit_mode
            st.rerun()

        st.markdown("##### Filters")
        selected_cities = st.multiselect("City", available_cities, default=available_cities)
        
        f_col1, f_col2, f_col3 = st.columns([1.5, 1.5, 1.5])
        min_d, max_d = df_inapp['pt'].min().date(), df_inapp['pt'].max().date()
        date_range = f_col1.date_input("Date Range", [min_d, max_d])
        start_date, end_date = date_range if isinstance(date_range, tuple) and len(date_range) == 2 else (min_d, max_d)
        
        channel_view = f_col2.selectbox("Dashboard View (Platform)", ["Overview (All)", "In-App Ads", "Promo Codes", "Communications"])
        min_amount = f_col3.number_input("Minimum Exposure / Volume", min_value=0, value=0, step=100)
        
        name_include = st.text_input("Keyword Search", placeholder="Filter by Campaign Name or Code...")

        # Base Data Filtering
        ia_data = df_inapp[(df_inapp['pt'] >= pd.to_datetime(start_date)) & (df_inapp['pt'] <= pd.to_datetime(end_date)) & (df_inapp['city_name'].isin(selected_cities)) & (df_inapp['show_pv'] >= min_amount)]
        ia_data = ia_data[ia_data['campaign_ver'].astype(str).str.lower() == 'all']
        if name_include: ia_data = ia_data[ia_data['campaign_name'].str.contains(name_include, case=False, na=False)]
        
        pr_data = df_promo[(df_promo['date'] >= pd.to_datetime(start_date)) & (df_promo['date'] <= pd.to_datetime(end_date)) & (df_promo['city_name'].isin(selected_cities)) & (df_promo['redemption_count'] >= min_amount)]
        pr_data = pr_data[pr_data['usage_count'] <= pr_data['redemption_count']]
        if name_include: pr_data = pr_data[pr_data['promocode'].str.contains(name_include, case=False, na=False)]
        
        co_data = df_comm[(df_comm['date'] >= pd.to_datetime(start_date)) & (df_comm['date'] <= pd.to_datetime(end_date))]
        if selected_cities and not co_data.empty:
            city_regex = '|'.join(selected_cities)
            co_data = co_data[co_data['target_markets'].str.contains(city_regex, case=False, na=False)]
        if not co_data.empty: co_data = co_data[co_data['delivered_count'] >= min_amount]
        if name_include and not co_data.empty: co_data = co_data[co_data['push_title'].str.contains(name_include, case=False, na=False)]

        st.markdown("<br>", unsafe_allow_html=True)
        
        # EDIT MODE CUSTOMIZATION
        if st.session_state.edit_mode:
            st.warning("✏️ Edit Mode: Add, remove, or reorder the diagrams below.")
            st.session_state.chart_layout[channel_view] = st.multiselect(
                f"Customize Diagrams for {channel_view}",
                options=ALL_AVAILABLE_CHARTS,
                default=st.session_state.chart_layout[channel_view]
            )
            st.markdown("---")

        # 1. RENDER KPIs
        st.markdown("##### Performance Metrics")
        k1, k2, k3, k4, k5 = st.columns(5)
        
        if channel_view == "Overview (All)":
            k1.metric("Total In-App Shows", f"{ia_data['show_pv'].sum():,.0f}")
            k2.metric("Total In-App Clicks", f"{ia_data['click_pv'].sum():,.0f}")
            k3.metric("Promo Redemptions", f"{pr_data['redemption_count'].sum():,.0f}")
            k4.metric("Actual Ride Usages", f"{pr_data['usage_count'].sum():,.0f}")
            k5.metric("Total Comm Delivered", f"{co_data['delivered_count'].sum():,.0f}" if not co_data.empty else "0")
            
        elif channel_view == "In-App Ads":
            ts = ia_data['show_pv'].sum()
            k1.metric("Show PV", f"{ts:,.0f}")
            k2.metric("Daily Show UV", f"{ia_data['show_uv'].sum():,.0f}")
            k3.metric("Click PV", f"{ia_data['click_pv'].sum():,.0f}")
            k4.metric("Daily Click UV", f"{ia_data['click_uv'].sum():,.0f}")
            k5.metric("CTR (%)", f"{(ia_data['click_pv'].sum()/ts*100):.2f}%" if ts else "0%")
            
        elif channel_view == "Promo Codes":
            tr = pr_data['redemption_count'].sum()
            tu = pr_data['usage_count'].sum()
            k1.metric("Total Redemptions", f"{tr:,.0f}")
            k2.metric("Total Usage", f"{tu:,.0f}")
            k3.metric("Active Promos", f"{pr_data['promocode'].nunique():,.0f}")
            k4.metric("Utilisation Rate (%)", f"{(tu/tr*100):.1f}%" if tr else "0%")
            k5.metric("Markets Active", f"{pr_data['city_name'].nunique():,.0f}")
            
        elif channel_view == "Communications":
            td = co_data['delivered_count'].sum()
            tc = co_data['clicks'].sum()
            k1.metric("Total Delivered", f"{td:,.0f}")
            k2.metric("Total Clicks", f"{tc:,.0f}")
            k3.metric("Active Campaigns", f"{co_data['canvas_id'].nunique():,.0f}")
            k4.metric("Delivered-to-Click Rate", f"{(tc/td*100):.2f}%" if td else "0%")
            k5.metric("Total Sends", f"{co_data['sends'].sum():,.0f}")

        st.markdown("---")
        st.markdown(f"##### Analytics Diagrams")
        
        def render_chart_with_insight(chart_name, fig):
            col_ch, col_btn = st.columns([15, 1])
            with col_btn:
                if st.button("💡 Insights", key=f"btn_{chart_name}"):
                    show_insight(chart_name, channel_view, ia_data, pr_data, co_data)
            
            if st.session_state.theme == "Dark":
                fig.update_layout(template="plotly_dark", plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
            else:
                fig.update_layout(template="plotly_white", plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
            
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
            st.markdown("<br>", unsafe_allow_html=True)

        # RENDER DYNAMIC CHARTS
        for chart_type in st.session_state.chart_layout[channel_view]:
            if chart_type == "Trend Timeline":
                if channel_view == "Overview (All)":
                    t1 = ia_data.groupby('pt')['show_pv'].sum().reset_index().rename(columns={'pt':'Date', 'show_pv':'Value'}); t1['Metric'] = 'In-App Shows'
                    t2 = pr_data.groupby('date')['redemption_count'].sum().reset_index().rename(columns={'date':'Date', 'redemption_count':'Value'}); t2['Metric'] = 'Promo Claims'
                    t3 = co_data.groupby('date')['delivered_count'].sum().reset_index().rename(columns={'date':'Date', 'delivered_count':'Value'}) if not co_data.empty else pd.DataFrame()
                    if not t3.empty: t3['Metric'] = 'Comm Delivered'
                    fig = px.line(pd.concat([t1, t2, t3]), x='Date', y='Value', color='Metric', title="Cross-Platform Trend Timeline")
                elif channel_view == "In-App Ads":
                    fig = px.line(ia_data.groupby('pt')[['show_pv', 'click_pv']].sum().reset_index(), x='pt', y=['show_pv', 'click_pv'], title="Daily Show vs Click PV Trend")
                elif channel_view == "Promo Codes":
                    fig = px.line(pr_data.groupby('date')[['redemption_count', 'usage_count']].sum().reset_index(), x='date', y=['redemption_count', 'usage_count'], title="Redemptions vs Usage Trend")
                elif channel_view == "Communications":
                    fig = px.line(co_data.groupby('date')[['delivered_count', 'clicks']].sum().reset_index(), x='date', y=['delivered_count', 'clicks'], title="Delivery vs Clicks Trend")
                render_chart_with_insight(chart_type, fig)

            elif chart_type == "Distribution Share":
                if channel_view == "Overview (All)":
                    df_p = pd.DataFrame({'Source': ['In-App', 'Promo', 'Comm'], 'Vol': [ia_data['click_pv'].sum(), pr_data['usage_count'].sum(), co_data['clicks'].sum() if not co_data.empty else 0]})
                    fig = px.pie(df_p, values='Vol', names='Source', hole=0.4, title="Interaction Distribution")
                elif channel_view == "In-App Ads":
                    fig = px.pie(ia_data.groupby('city_name')['show_pv'].sum().reset_index(), values='show_pv', names='city_name', hole=0.4, title="Shows by City")
                elif channel_view == "Promo Codes":
                    fig = px.pie(pr_data.groupby('city_name')['usage_count'].sum().reset_index(), values='usage_count', names='city_name', hole=0.4, title="Usage by City")
                elif channel_view == "Communications":
                    fig = px.pie(co_data.groupby('channel')['delivered_count'].sum().reset_index(), values='delivered_count', names='channel', hole=0.4, title="Delivery by Channel")
                render_chart_with_insight(chart_type, fig)
                
            elif chart_type == "Efficiency Comparison":
                if channel_view == "Overview (All)":
                    e1 = (ia_data['click_pv'].sum() / ia_data['show_pv'].sum() * 100) if ia_data['show_pv'].sum() else 0
                    e2 = (pr_data['usage_count'].sum() / pr_data['redemption_count'].sum() * 100) if pr_data['redemption_count'].sum() else 0
                    e3 = (co_data['clicks'].sum() / co_data['delivered_count'].sum() * 100) if not co_data.empty and co_data['delivered_count'].sum() else 0
                    fig = px.bar(pd.DataFrame({'Platform': ['In-App', 'Promo', 'Comm'], 'Rate (%)': [e1, e2, e3]}), x='Platform', y='Rate (%)', color='Platform', title="Efficiency Comparison")
                elif channel_view == "In-App Ads":
                    e_df = ia_data.groupby('campaign_name').agg({'show_pv':'sum', 'click_pv':'sum'}).reset_index()
                    e_df['Rate'] = (e_df['click_pv']/e_df['show_pv']*100).fillna(0)
                    fig = px.bar(e_df.nlargest(10, 'show_pv'), x='campaign_name', y='Rate', title="Top Campaign CTRs")
                elif channel_view == "Promo Codes":
                    e_df = pr_data.groupby('promocode').agg({'redemption_count':'sum', 'usage_count':'sum'}).reset_index()
                    e_df['Rate'] = (e_df['usage_count']/e_df['redemption_count']*100).fillna(0)
                    fig = px.bar(e_df.nlargest(10, 'redemption_count'), x='promocode', y='Rate', title="Top Promo Utilisation Rates")
                elif channel_view == "Communications":
                    e_df = co_data.groupby('channel').agg({'delivered_count':'sum', 'clicks':'sum'}).reset_index()
                    e_df['Rate'] = (e_df['clicks']/e_df['delivered_count']*100).fillna(0)
                    fig = px.bar(e_df, x='channel', y='Rate', color='channel', title="Channel Click Rates")
                render_chart_with_insight(chart_type, fig)

            elif chart_type == "4-Quadrant Scatter":
                if channel_view == "Overview (All)":
                    q1 = ia_data.groupby('campaign_name').agg({'show_pv':'sum', 'click_pv':'sum'}).reset_index().rename(columns={'campaign_name':'ID', 'show_pv':'Vol', 'click_pv':'Int'}); q1['Plat'] = 'In-App'
                    q2 = pr_data.groupby('promocode').agg({'redemption_count':'sum', 'usage_count':'sum'}).reset_index().rename(columns={'promocode':'ID', 'redemption_count':'Vol', 'usage_count':'Int'}); q2['Plat'] = 'Promo'
                    df_q = pd.concat([q1, q2], ignore_index=True)
                    df_q['Rate'] = (df_q['Int'] / df_q['Vol'] * 100).fillna(0)
                    fig = px.scatter(df_q, x='Vol', y='Rate', size='Int', color='Plat', hover_name='ID', title="Cross-Platform Matrix")
                elif channel_view == "In-App Ads":
                    df_q = ia_data.groupby('campaign_name').agg({'show_pv':'sum', 'click_pv':'sum'}).reset_index()
                    df_q['Rate'] = (df_q['click_pv'] / df_q['show_pv'] * 100).fillna(0)
                    fig = px.scatter(df_q, x='show_pv', y='Rate', size='click_pv', hover_name='campaign_name', title="In-App Performance Matrix")
                elif channel_view == "Promo Codes":
                    df_q = pr_data.groupby('promocode').agg({'redemption_count':'sum', 'usage_count':'sum'}).reset_index()
                    df_q['Rate'] = (df_q['usage_count'] / df_q['redemption_count'] * 100).fillna(0)
                    fig = px.scatter(df_q, x='redemption_count', y='Rate', size='usage_count', hover_name='promocode', title="Promo Efficiency Matrix")
                elif channel_view == "Communications":
                    df_q = co_data.groupby('push_title').agg({'delivered_count':'sum', 'clicks':'sum'}).reset_index()
                    df_q['Rate'] = (df_q['clicks'] / df_q['delivered_count'] * 100).fillna(0)
                    fig = px.scatter(df_q, x='delivered_count', y='Rate', size='clicks', hover_name='push_title', title="Communication Efficiency Matrix")
                render_chart_with_insight(chart_type, fig)

            elif chart_type == "Activity Heatmap":
                days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                if channel_view == "Overview (All)":
                    h1 = ia_data.groupby('day_of_week')['click_pv'].sum().reset_index().rename(columns={'click_pv':'Vol'}); h1['Plat'] = 'In-App'
                    h2 = pr_data.groupby('day_of_week')['usage_count'].sum().reset_index().rename(columns={'usage_count':'Vol'}); h2['Plat'] = 'Promo'
                    heat = pd.concat([h1, h2]).pivot_table(index='Plat', columns='day_of_week', values='Vol', aggfunc='sum').fillna(0).reindex(columns=days_order)
                    fig = px.imshow(heat, aspect="auto", color_continuous_scale='YlOrRd', title="Platform Activity by Day")
                elif channel_view == "In-App Ads":
                    heat = ia_data.pivot_table(index='city_name', columns='day_of_week', values='show_pv', aggfunc='sum').fillna(0).reindex(columns=days_order)
                    fig = px.imshow(heat, aspect="auto", color_continuous_scale='Blues', title="City Activity Heatmap")
                elif channel_view == "Promo Codes":
                    heat = pr_data.pivot_table(index='city_name', columns='day_of_week', values='usage_count', aggfunc='sum').fillna(0).reindex(columns=days_order)
                    fig = px.imshow(heat, aspect="auto", color_continuous_scale='Greens', title="Promo Usage Heatmap")
                elif channel_view == "Communications":
                    heat = co_data.pivot_table(index='channel', columns='day_of_week', values='delivered_count', aggfunc='sum').fillna(0).reindex(columns=days_order)
                    fig = px.imshow(heat, aspect="auto", color_continuous_scale='Purples', title="Delivery Heatmap")
                render_chart_with_insight(chart_type, fig)

            elif chart_type == "Volume Treemap":
                if channel_view in ["Overview (All)", "In-App Ads"]:
                    tree = ia_data.groupby('campaign_name')['show_pv'].sum().reset_index().nlargest(15, 'show_pv')
                    fig = px.treemap(tree, path=[px.Constant("In-App Campaigns"), 'campaign_name'], values='show_pv', title="Campaign Volume Treemap")
                elif channel_view == "Promo Codes":
                    tree = pr_data.groupby('promocode')['redemption_count'].sum().reset_index().nlargest(15, 'redemption_count')
                    fig = px.treemap(tree, path=[px.Constant("Promo Codes"), 'promocode'], values='redemption_count', title="Promo Volume Treemap")
                elif channel_view == "Communications":
                    tree = co_data.groupby('push_title')['delivered_count'].sum().reset_index().nlargest(15, 'delivered_count')
                    fig = px.treemap(tree, path=[px.Constant("Communications"), 'push_title'], values='delivered_count', title="Comm Volume Treemap")
                render_chart_with_insight(chart_type, fig)
                
            elif chart_type == "Conversion Funnel":
                if channel_view in ["Overview (All)", "In-App Ads"]:
                    fig = go.Figure(go.Funnel(y=['Show PV', 'Click PV'], x=[ia_data['show_pv'].sum(), ia_data['click_pv'].sum()]))
                    fig.update_layout(title="In-App Master Funnel")
                elif channel_view == "Promo Codes":
                    fig = go.Figure(go.Funnel(y=['Redemptions', 'Usages'], x=[pr_data['redemption_count'].sum(), pr_data['usage_count'].sum()]))
                    fig.update_layout(title="Promo Master Funnel")
                elif channel_view == "Communications":
                    fig = go.Figure(go.Funnel(y=['Delivered', 'Clicks'], x=[co_data['delivered_count'].sum(), co_data['clicks'].sum()]))
                    fig.update_layout(title="Communications Master Funnel")
                render_chart_with_insight(chart_type, fig)

        # 3. INTERACTIVE TOP PERFORMANCE TABLE & DYNAMIC DIAGRAM
        st.markdown("---")
        st.markdown("##### 🏆 Interactive Performance Leaderboard")
        
        if channel_view == "Overview (All)":
            m1 = ia_data.groupby('campaign_name').agg({'show_pv':'sum', 'click_pv':'sum'}).reset_index().rename(columns={'campaign_name':'Code/Campaign', 'show_pv':'Volume', 'click_pv':'Interact'}); m1['Platform'] = 'In-App'
            m2 = pr_data.groupby('promocode').agg({'redemption_count':'sum', 'usage_count':'sum'}).reset_index().rename(columns={'promocode':'Code/Campaign', 'redemption_count':'Volume', 'usage_count':'Interact'}); m2['Platform'] = 'Promo'
            mat = pd.concat([m1, m2], ignore_index=True)
            mat['Rate (%)'] = (mat['Interact'] / mat['Volume'] * 100).fillna(0)
        elif channel_view == "In-App Ads":
            mat = ia_data.groupby('campaign_name').agg({'show_pv':'sum', 'click_pv':'sum'}).reset_index().rename(columns={'campaign_name':'Code/Campaign', 'show_pv':'Volume', 'click_pv':'Interact'})
            mat['Rate (%)'] = (mat['Interact'] / mat['Volume'] * 100).fillna(0); mat['Platform'] = 'In-App'
        elif channel_view == "Promo Codes":
            mat = pr_data.groupby('promocode').agg({'redemption_count':'sum', 'usage_count':'sum'}).reset_index().rename(columns={'promocode':'Code/Campaign', 'redemption_count':'Volume', 'usage_count':'Interact'})
            mat['Rate (%)'] = (mat['Interact'] / mat['Volume'] * 100).fillna(0); mat['Platform'] = 'Promo'
        elif channel_view == "Communications":
            mat = co_data.groupby('push_title').agg({'delivered_count':'sum', 'clicks':'sum'}).reset_index().rename(columns={'push_title':'Code/Campaign', 'delivered_count':'Volume', 'clicks':'Interact'})
            mat['Rate (%)'] = (mat['Interact'] / mat['Volume'] * 100).fillna(0); mat['Platform'] = 'Comm'

        c_tab, c_chart = st.columns([1.5, 1])
        with c_tab:
            st.caption("Click any column header to reorder data dynamically.")
            st.dataframe(
                mat,
                column_config={
                    "Platform": "Platform", "Code/Campaign": "Campaign / Promo Code", "Volume": st.column_config.NumberColumn("Exposure / Claims", format="%d"),
                    "Interact": st.column_config.NumberColumn("Interactions / Usage", format="%d"), "Rate (%)": st.column_config.NumberColumn("Efficiency Rate", format="%.2f%%")
                },
                use_container_width=True, hide_index=True
            )
            
        with c_chart:
            fig_leader = px.bar(mat.nlargest(10, 'Rate (%)').sort_values('Rate (%)'), x='Rate (%)', y='Code/Campaign', orientation='h', color='Platform', title="Top 10 by Efficiency Rate")
            if st.session_state.theme == "Dark": fig_leader.update_layout(template="plotly_dark", plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
            else: fig_leader.update_layout(template="plotly_white", plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_leader, use_container_width=True)

        # 4. RAW DATA VIEW
        st.markdown("---")
        st.markdown("##### 📋 Raw Data (Actionable View)")
        
        if channel_view == "Overview (All)":
            r1 = ia_data[['pt', 'city_name', 'campaign_name', 'show_pv', 'url']].rename(columns={'pt':'Date', 'city_name':'City', 'campaign_name':'Code/Campaign', 'show_pv':'Volume', 'url':'URL'}); r1['Platform'] = 'In-App'
            r2 = pr_data[['date', 'city_name', 'promocode', 'redemption_count', 'url']].rename(columns={'date':'Date', 'city_name':'City', 'promocode':'Code/Campaign', 'redemption_count':'Volume', 'url':'URL'}); r2['Platform'] = 'Promo'
            raw = pd.concat([r1, r2], ignore_index=True)
        elif channel_view == "In-App Ads":
            raw = ia_data[['pt', 'city_name', 'campaign_name', 'show_pv', 'click_pv', 'data_quality_status', 'url']].rename(columns={'pt':'Date', 'city_name':'City', 'campaign_name':'Code/Campaign', 'show_pv':'Volume', 'click_pv':'Interactions', 'data_quality_status':'Status', 'url':'URL'})
            raw['Platform'] = 'In-App'
        elif channel_view == "Promo Codes":
            raw = pr_data[['date', 'city_name', 'promocode', 'redemption_count', 'usage_count', 'url']].rename(columns={'date':'Date', 'city_name':'City', 'promocode':'Code/Campaign', 'redemption_count':'Volume', 'usage_count':'Interactions', 'url':'URL'})
            raw['Platform'] = 'Promo'
        elif channel_view == "Communications":
            raw = co_data[['date', 'target_markets', 'push_title', 'delivered_count', 'clicks', 'url']].rename(columns={'date':'Date', 'target_markets':'City', 'push_title':'Code/Campaign', 'delivered_count':'Volume', 'clicks':'Interactions', 'url':'URL'})
            raw['Platform'] = 'Comm'

        st.dataframe(
            raw,
            column_config={"Date": st.column_config.DatetimeColumn("Date", format="YYYY-MM-DD"), "Platform": "Platform", "City": "City / Market", "Code/Campaign": "Campaign Name / Code", "Volume": "Total Volume", "URL": st.column_config.LinkColumn("Redirect URL", display_text="🔗 Link")},
            use_container_width=True, hide_index=True
        )

# ==========================================
# 5. FLOATING AI AGENT CHAT UI
# ==========================================
with st.popover("💬 Ask AI Agent"):
    st.markdown("### 🤖 Marketing AI Agent")
    st.caption("Ask me to analyze trends, find anomalies, or summarize campaign data.")
    
    chat_container = st.container(height=300)
    for msg in st.session_state.chat_history:
        chat_container.chat_message(msg["role"]).write(msg["content"])
        
    with st.form("chat_form", clear_on_submit=True):
        c1, c2 = st.columns([4, 1])
        user_msg = c1.text_input("Type your question...", label_visibility="collapsed")
        submit = c2.form_submit_button("Send")
        if submit and user_msg:
            st.session_state.chat_history.append({"role": "user", "content": user_msg})
            # Dummy AI Response Logic
            bot_reply = f"Analyzing your request regarding '{user_msg}'... Based on the current view, overall performance is steady. Please check the 4-Quadrant matrix above to identify specific campaigns that require budget reallocation."
            st.session_state.chat_history.append({"role": "assistant", "content": bot_reply})
            st.rerun()

except Exception as err:
    st.error(f"Error rendering dashboard: {err}")
