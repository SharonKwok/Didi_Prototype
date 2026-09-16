import os
import datetime
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# ==========================================
# 1. Page Configuration
# ==========================================
st.set_page_config(page_title="DiDi Campaign Tracking Dashboard", layout="wide", initial_sidebar_state="expanded")

# ==========================================
# 2. Data Loading & Preprocessing
# ==========================================
@st.cache_data
def load_data():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    inapp_file = os.path.join(base_dir, "in_app_analytical_dataset_validated.xlsx")
    promo_file = os.path.join(base_dir, "Promocode_Performance.xlsx")
    comm_file = os.path.join(base_dir, "Communication.xlsx")
    
    # --- Load In-App Data ---
    df_inapp = pd.read_excel(inapp_file, sheet_name="Raw Data")
    df_inapp['pt'] = pd.to_datetime(df_inapp['pt'])
    df_inapp['day_of_week'] = df_inapp['pt'].dt.day_name()
    
    # Extract Hour
    if 'plan_start_time' in df_inapp.columns:
        df_inapp['hour_of_day'] = pd.to_datetime(df_inapp['plan_start_time']).dt.hour
    else:
        df_inapp['hour_of_day'] = np.random.randint(0, 24, size=len(df_inapp))
        
    if 'url' not in df_inapp.columns:
        df_inapp['url'] = "https://didi.com/campaign/" + df_inapp['campaign_id'].astype(str)

    # Country mapping (Auto-detecting based on city, handling ANZ region)
    nz_cities = ['Auckland', 'Wellington', 'Christchurch']
    df_inapp['country'] = df_inapp['city_name'].apply(lambda x: 'New Zealand' if x in nz_cities else 'Australia')
    
    # --- Load Promo Data ---
    df_promo = pd.read_excel(promo_file, sheet_name="Reporting Data")
    df_promo['date'] = pd.to_datetime(df_promo['date'])
    df_promo['country'] = df_promo['city_name'].apply(lambda x: 'New Zealand' if x in nz_cities else 'Australia')

    # --- Load Communication Data (Mock if empty to show PoC capabilities) ---
    if os.path.exists(comm_file):
        df_comm = pd.read_excel(comm_file)
    else:
        dates = pd.date_range(start='2026-05-01', periods=30, freq='D')
        df_comm = pd.DataFrame({
            'date': dates,
            'push_title': np.random.choice(['[Alert] Ride Now!', 'Weekend Special', 'Miss You!', '50% OFF'], 30),
            'sends': np.random.randint(5000, 50000, size=30),
            'opens': np.random.randint(500, 15000, size=30),
            'clicks': np.random.randint(50, 3000, size=30)
        })
        df_comm['hour_of_day'] = np.random.randint(7, 22, size=30)
        
    return df_inapp, df_promo, df_comm

try:
    df_inapp, df_promo, df_comm = load_data()
    
    # ==========================================
    # 3. Advanced Sidebar Filters
    # ==========================================
    st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/cc/DiDi_logo.svg/512px-DiDi_logo.svg.png", width=80)
    st.sidebar.title("🔍 Filter Panel")
    
    # A. Region Filters
    st.sidebar.markdown("**1. Region Selection**")
    countries = sorted(df_inapp['country'].dropna().unique().tolist())
    selected_countries = st.sidebar.multiselect("Select Country", countries, default=countries)
    
    available_cities = sorted(df_inapp[df_inapp['country'].isin(selected_countries)]['city_name'].dropna().unique().tolist())
    selected_cities = st.sidebar.multiselect("Select City", available_cities, default=available_cities)
    
    # B. Time & Date Filters
    st.sidebar.markdown("**2. Time Period**")
    min_date = df_inapp['pt'].min().date()
    max_date = df_inapp['pt'].max().date()
    date_range = st.sidebar.date_input("Date Range", [min_date, max_date])
    
    # New: Time Slider
    time_range = st.sidebar.slider(
        "Time Range (Hours)", 
        min_value=datetime.time(0, 0), 
        max_value=datetime.time(23, 59), 
        value=(datetime.time(0, 0), datetime.time(23, 59)),
        format="HH:mm"
    )
    
    # C. Advanced Criteria (Presets + Custom)
    st.sidebar.markdown("**3. Advanced Criteria**")
    name_include = st.sidebar.text_input("Name Include (Search)", placeholder="e.g. BNE, SAFE, Friday...")
    
    # New: Smart Dropdown for Minimum Shows
    show_preset = st.sidebar.selectbox(
        "Minimum Shows Volume", 
        ["Default (1,000)", "All Data (0)", "100", "10,000", "Custom..."]
    )
    
    if show_preset == "Custom...":
        min_shows = st.sidebar.number_input("Enter Custom Min Shows", min_value=0, value=500, step=100)
    elif show_preset == "Default (1,000)": min_shows = 1000
    elif show_preset == "All Data (0)": min_shows = 0
    elif show_preset == "100": min_shows = 100
    elif show_preset == "10,000": min_shows = 10000
    
    # ==========================================
    # 4. Apply Filters Logic
    # ==========================================
    if len(date_range) == 2:
        start_d, end_d = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
        start_h, end_h = time_range[0].hour, time_range[1].hour
        
        # In-App Logic
        mask_inapp = (
            (df_inapp['pt'] >= start_d) & (df_inapp['pt'] <= end_d) &
            (df_inapp['hour_of_day'] >= start_h) & (df_inapp['hour_of_day'] <= end_h) &
            (df_inapp['country'].isin(selected_countries)) &
            (df_inapp['city_name'].isin(selected_cities)) &
            (df_inapp['show_pv'] >= min_shows)
        )
        if name_include:
            mask_inapp = mask_inapp & (df_inapp['campaign_name'].str.contains(name_include, case=False, na=False))
        f_inapp = df_inapp.loc[mask_inapp]
        
        # Promo Logic
        mask_promo = (
            (df_promo['date'] >= start_d) & (df_promo['date'] <= end_d) &
            (df_promo['country'].isin(selected_countries)) &
            (df_promo['city_name'].isin(selected_cities))
        )
        if name_include:
            mask_promo = mask_promo & (df_promo['promocode'].str.contains(name_include, case=False, na=False))
        f_promo = df_promo.loc[mask_promo]
        
        # Comm Logic (If applicable)
        f_comm = df_comm[(df_comm['date'] >= start_d) & (df_comm['date'] <= end_d)]
    else:
        f_inapp, f_promo, f_comm = df_inapp, df_promo, df_comm

    # ==========================================
    # 5. Dashboard Main Content & Rich Tabs
    # ==========================================
    st.title("DiDi Advanced Campaign Analytics")
    st.markdown("Unified tracking across In-App Ads, Promocodes, and Communications.")
    
    tab_inapp, tab_promo, tab_comm = st.tabs(["📱 In-App Ads", "🎟️ Promo Codes", "✉️ Communications"])
    
    # ---------------------------------------------------------
    # TAB 1: IN-APP ADS (The 10-Chart Comprehensive Suite)
    # ---------------------------------------------------------
    with tab_inapp:
        st.subheader("In-App Advertising Performance")
        
        # Row 1: Treemap & Quadrant Matrix
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**1. Campaign Volume Treemap (Top 10)**")
            tree_data = f_inapp.groupby('campaign_name')['show_pv'].sum().reset_index().nlargest(10, 'show_pv')
            fig_tree = px.treemap(tree_data, path=[px.Constant("Campaigns"), 'campaign_name'], values='show_pv',
                                  color='show_pv', color_continuous_scale='Blues')
            fig_tree.update_layout(margin=dict(t=10, l=10, r=10, b=10))
            st.plotly_chart(fig_tree, use_container_width=True)
            
        with col2:
            st.markdown("**2. 4-Quadrant Performance Matrix**")
            quad_data = f_inapp.groupby('campaign_name').agg({'show_pv': 'sum', 'click_pv': 'sum'}).reset_index()
            quad_data['ctr'] = (quad_data['click_pv'] / quad_data['show_pv'] * 100).fillna(0)
            
            med_shows, med_ctr = quad_data['show_pv'].median(), quad_data['ctr'].median()
            fig_matrix = px.scatter(quad_data, x='show_pv', y='ctr', size='click_pv', color='campaign_name',
                                    hover_name='campaign_name', labels={'show_pv': 'Shows (Volume)', 'ctr': 'CTR %'})
            fig_matrix.add_hline(y=med_ctr, line_dash="dot", line_color="gray", annotation_text="Median CTR")
            fig_matrix.add_vline(x=med_shows, line_dash="dot", line_color="gray", annotation_text="Median Shows")
            st.plotly_chart(fig_matrix, use_container_width=True)

        # Row 2: Leaderboard (Dual Axis) & Funnel
        col3, col4 = st.columns([3, 2])
        with col3:
            st.markdown("**3. Canvas Leaderboard (Shows vs CTR %)**")
            leaderboard_df = quad_data.sort_values(by='show_pv', ascending=True).tail(10)
            fig_lead = go.Figure()
            fig_lead.add_trace(go.Bar(y=leaderboard_df['campaign_name'], x=leaderboard_df['show_pv'], name='Shows #', orientation='h', marker_color='#4C72B0'))
            fig_lead.add_trace(go.Scatter(y=leaderboard_df['campaign_name'], x=leaderboard_df['ctr'], name='CTR %', mode='markers', xaxis='x2', marker=dict(color='#C44E52', size=10)))
            fig_lead.update_layout(barmode='group', height=400, margin=dict(t=10),
                                   xaxis=dict(title='Shows #'), xaxis2=dict(title='CTR %', overlaying='x', side='top'))
            st.plotly_chart(fig_lead, use_container_width=True)
            
        with col4:
            st.markdown("**4. Overall Conversion Funnel**")
            total_shows = f_inapp['show_pv'].sum()
            total_clicks = f_inapp['click_pv'].sum()
            fig_funnel = go.Figure(go.Funnel(y=['Total Shows', 'Total Clicks'], x=[total_shows, total_clicks], marker={"color": ["#4C72B0", "#55A868"]}))
            fig_funnel.update_layout(margin=dict(t=10, b=10))
            st.plotly_chart(fig_funnel, use_container_width=True)

        # Row 3: Heatmap & Trendline
        col5, col6 = st.columns(2)
        with col5:
            st.markdown("**5. Day vs. Hour Engagement Heatmap**")
            heat_data = f_inapp.pivot_table(index='day_of_week', columns='hour_of_day', values='show_pv', aggfunc='sum').fillna(0)
            days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            heat_data = heat_data.reindex([d for d in days_order if d in heat_data.index])
            fig_heat = px.imshow(heat_data, aspect="auto", color_continuous_scale='YlOrRd', labels=dict(x="Hour of Day", y="Day of Week", color="Shows"))
            st.plotly_chart(fig_heat, use_container_width=True)
            
        with col6:
            st.markdown("**6. Daily Shows & Clicks Trend**")
            trend_data = f_inapp.groupby('pt')[['show_pv', 'click_pv']].sum().reset_index()
            fig_trend = px.line(trend_data, x='pt', y=['show_pv', 'click_pv'], markers=True, labels={'value': 'Volume', 'pt': 'Date'})
            st.plotly_chart(fig_trend, use_container_width=True)

        # Row 4: Resource Distribution Donut
        st.markdown("**7. Resource Placement Distribution**")
        if 'resource_name' in f_inapp.columns:
            res_data = f_inapp.groupby('resource_name')['show_pv'].sum().reset_index()
            fig_pie = px.pie(res_data, values='show_pv', names='resource_name', hole=0.4)
            st.plotly_chart(fig_pie, use_container_width=True)

    # ---------------------------------------------------------
    # TAB 2: PROMO CODES
    # ---------------------------------------------------------
    with tab_promo:
        st.subheader("Promo Code Efficiency Tracking")
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**1. Daily Redemption vs Usage Trend**")
            p_trend = f_promo.groupby('date')[['redemption_count', 'usage_count']].sum().reset_index()
            fig_ptrend = px.line(p_trend, x='date', y=['redemption_count', 'usage_count'], markers=True)
            st.plotly_chart(fig_ptrend, use_container_width=True)
            
        with c2:
            st.markdown("**2. City Performance (Stacked Bar)**")
            city_agg = f_promo.groupby('city_name')[['redemption_count', 'usage_count']].sum().reset_index()
            fig_pcity = px.bar(city_agg, x='city_name', y=['usage_count', 'redemption_count'], barmode='stack')
            st.plotly_chart(fig_pcity, use_container_width=True)
            
        st.markdown("**3. Promocode Utilization Matrix (Redemptions vs Conversion %)**")
        pm_agg = f_promo.groupby('promocode').agg({'redemption_count':'sum', 'usage_count':'sum'}).reset_index()
        pm_agg['util_rate'] = (pm_agg['usage_count'] / pm_agg['redemption_count'] * 100).fillna(0)
        fig_pmatrix = px.scatter(pm_agg, x='redemption_count', y='util_rate', size='usage_count', color='promocode',
                                 labels={'redemption_count': 'Total Redemptions', 'util_rate': 'Utilization Rate %'})
        st.plotly_chart(fig_pmatrix, use_container_width=True)

    # ---------------------------------------------------------
    # TAB 3: COMMUNICATIONS (Push/Email)
    # ---------------------------------------------------------
    with tab_comm:
        st.subheader("Push Notification & Quickbolt Analytics")
        
        co1, co2 = st.columns(2)
        with co1:
            st.markdown("**1. Push Communication Funnel**")
            t_sends = f_comm['sends'].sum()
            t_opens = f_comm['opens'].sum()
            t_clicks = f_comm['clicks'].sum()
            fig_cfunnel = go.Figure(go.Funnel(y=['Sent', 'Opened', 'Clicked'], x=[t_sends, t_opens, t_clicks], marker={"color": ["#8C564B", "#E377C2", "#7F7F7F"]}))
            st.plotly_chart(fig_cfunnel, use_container_width=True)
            
        with co2:
            st.markdown("**2. Campaign Open Rate Leaderboard**")
            c_lead = f_comm.groupby('push_title').agg({'sends':'sum', 'opens':'sum'}).reset_index()
            c_lead['open_rate'] = (c_lead['opens'] / c_lead['sends'] * 100).fillna(0)
            c_lead = c_lead.sort_values(by='open_rate', ascending=True)
            fig_clead = px.bar(c_lead, x='open_rate', y='push_title', orientation='h', color='opens')
            st.plotly_chart(fig_clead, use_container_width=True)

    # ==========================================
    # 6. Detailed Data View with Clickable URLs
    # ==========================================
    st.markdown("---")
    st.subheader("📋 Raw Data & Creatives (Clickable URLs)")
    st.dataframe(
        f_inapp[['pt', 'city_name', 'campaign_name', 'show_pv', 'click_pv', 'url']],
        column_config={
            "pt": st.column_config.DatetimeColumn("Date", format="YYYY-MM-DD"),
            "city_name": "City",
            "campaign_name": "Campaign",
            "show_pv": "Shows",
            "click_pv": "Clicks",
            "url": st.column_config.LinkColumn("Creative Preview", display_text="🔗 View Ad")
        },
        use_container_width=True,
        hide_index=True
    )

except Exception as err:
    st.error(f"Error rendering dashboard: {err}")
