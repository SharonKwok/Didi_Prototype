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

    nz_cities = ['Auckland', 'Wellington', 'Christchurch']
    df_inapp['country'] = df_inapp['city_name'].apply(lambda x: 'New Zealand' if x in nz_cities else 'Australia')
    
    # --- Load Promo Data ---
    df_promo = pd.read_excel(promo_file, sheet_name="Reporting Data")
    df_promo['date'] = pd.to_datetime(df_promo['date'])
    df_promo['country'] = df_promo['city_name'].apply(lambda x: 'New Zealand' if x in nz_cities else 'Australia')
    df_promo['hour_of_day'] = 0 # Default for PoC

    # --- Load Communication Data (Mock if empty) ---
    if os.path.exists(comm_file):
        df_comm = pd.read_excel(comm_file)
        if 'date' not in df_comm.columns:
            # Fallback if structure is unknown
            df_comm['date'] = pd.to_datetime(df_promo['date'].min())
    else:
        dates = pd.date_range(start=df_inapp['pt'].min(), periods=30, freq='D')
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
    
    st.sidebar.markdown("**1. Region Selection**")
    countries = sorted(df_inapp['country'].dropna().unique().tolist())
    selected_countries = st.sidebar.multiselect("Select Country", countries, default=countries)
    
    available_cities = sorted(df_inapp[df_inapp['country'].isin(selected_countries)]['city_name'].dropna().unique().tolist())
    selected_cities = st.sidebar.multiselect("Select City", available_cities, default=available_cities)
    
    st.sidebar.markdown("**2. Precise Datetime Range**")
    min_date = df_inapp['pt'].min().date()
    max_date = df_inapp['pt'].max().date()
    
    col_d1, col_d2 = st.sidebar.columns(2)
    with col_d1:
        start_date = st.date_input("Start Date", min_date)
        start_time = st.time_input("Start Time", datetime.time(0, 0))
    with col_d2:
        end_date = st.date_input("End Date", max_date)
        end_time = st.time_input("End Time", datetime.time(23, 59))
        
    start_dt = pd.to_datetime(f"{start_date} {start_time}")
    end_dt = pd.to_datetime(f"{end_date} {end_time}")
    
    st.sidebar.markdown("**3. Advanced Criteria**")
    name_include = st.sidebar.text_input("Name Include (Search)", placeholder="e.g. BNE, SAFE...")
    
    show_preset = st.sidebar.selectbox("Minimum Shows Volume", ["Default (1,000)", "All Data (0)", "100", "10,000", "Custom..."])
    if show_preset == "Custom...": min_shows = st.sidebar.number_input("Enter Custom Min Shows", min_value=0, value=500, step=100)
    elif show_preset == "Default (1,000)": min_shows = 1000
    elif show_preset == "All Data (0)": min_shows = 0
    elif show_preset == "100": min_shows = 100
    elif show_preset == "10,000": min_shows = 10000
    
    # ==========================================
    # 4. Apply Filters Logic
    # ==========================================
    # In-App Logic (Using combined datetime logic for PoC)
    mask_inapp = (
        (df_inapp['pt'] >= start_dt) & (df_inapp['pt'] <= end_dt) &
        (df_inapp['country'].isin(selected_countries)) &
        (df_inapp['city_name'].isin(selected_cities)) &
        (df_inapp['show_pv'] >= min_shows)
    )
    if name_include: mask_inapp = mask_inapp & (df_inapp['campaign_name'].str.contains(name_include, case=False, na=False))
    f_inapp = df_inapp.loc[mask_inapp]
    
    # Promo Logic
    mask_promo = (df_promo['date'] >= pd.to_datetime(start_date)) & (df_promo['date'] <= pd.to_datetime(end_date)) & (df_promo['country'].isin(selected_countries)) & (df_promo['city_name'].isin(selected_cities))
    if name_include: mask_promo = mask_promo & (df_promo['promocode'].str.contains(name_include, case=False, na=False))
    f_promo = df_promo.loc[mask_promo]
    
    # Comm Logic
    f_comm = df_comm[(df_comm['date'] >= pd.to_datetime(start_date)) & (df_comm['date'] <= pd.to_datetime(end_date))]

    # ==========================================
    # 5. Dashboard Main Content & Rich Tabs
    # ==========================================
    st.title("DiDi Advanced Campaign Analytics")
    st.markdown("Solving data silos with unified tracking across all marketing channels.")
    
    tab_overview, tab_inapp, tab_promo, tab_comm = st.tabs([
        "🌐 Executive Overview", 
        "📱 In-App Ads", 
        "🎟️ Promo Codes", 
        "✉️ Communications"
    ])
    
    # ---------------------------------------------------------
    # TAB 0: EXECUTIVE OVERVIEW (Cross-channel view)
    # ---------------------------------------------------------
    with tab_overview:
        st.subheader("Cross-Channel Performance Summary")
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        kpi1.metric("Total In-App Shows", f"{f_inapp['show_pv'].sum():,.0f}")
        kpi2.metric("Total In-App Clicks", f"{f_inapp['click_pv'].sum():,.0f}")
        kpi3.metric("Promo Redemptions", f"{f_promo['redemption_count'].sum():,.0f}")
        
        total_sends = f_comm['sends'].sum() if 'sends' in f_comm.columns else 0
        kpi4.metric("Total Push Sends", f"{total_sends:,.0f}")
        
        st.markdown("---")
        st.markdown("**Unified Marketing ROI Trend (Normalized)**")
        st.markdown("*A consolidated view of Impressions (In-App), Redemptions (Promo), and Sends (Comm) over time.*")
        
        # Build unified trend data
        t_inapp = f_inapp.groupby('pt')['show_pv'].sum().reset_index().rename(columns={'pt':'Date', 'show_pv':'Value'})
        t_inapp['Channel'] = 'In-App (Shows)'
        t_promo = f_promo.groupby('date')['redemption_count'].sum().reset_index().rename(columns={'date':'Date', 'redemption_count':'Value'})
        t_promo['Channel'] = 'Promo (Redemptions)'
        
        t_comm = pd.DataFrame()
        if not f_comm.empty and 'sends' in f_comm.columns:
            t_comm = f_comm.groupby('date')['sends'].sum().reset_index().rename(columns={'date':'Date', 'sends':'Value'})
            t_comm['Channel'] = 'Comm (Sends)'
            
        unified_df = pd.concat([t_inapp, t_promo, t_comm])
        
        fig_unified = px.line(unified_df, x='Date', y='Value', color='Channel', markers=True)
        st.plotly_chart(fig_unified, use_container_width=True)

    # ---------------------------------------------------------
    # TAB 1: IN-APP ADS
    # ---------------------------------------------------------
    with tab_inapp:
        st.subheader("In-App Advertising Suite")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**1. Campaign Volume Treemap (Top 10)**")
            tree_data = f_inapp.groupby('campaign_name')['show_pv'].sum().reset_index().nlargest(10, 'show_pv')
            fig_tree = px.treemap(tree_data, path=[px.Constant("Campaigns"), 'campaign_name'], values='show_pv', color='show_pv', color_continuous_scale='Blues')
            st.plotly_chart(fig_tree, use_container_width=True)
            
        with col2:
            st.markdown("**2. 4-Quadrant Performance Matrix**")
            quad_data = f_inapp.groupby('campaign_name').agg({'show_pv': 'sum', 'click_pv': 'sum'}).reset_index()
            quad_data['ctr'] = (quad_data['click_pv'] / quad_data['show_pv'] * 100).fillna(0)
            med_shows, med_ctr = quad_data['show_pv'].median(), quad_data['ctr'].median()
            fig_matrix = px.scatter(quad_data, x='show_pv', y='ctr', size='click_pv', color='campaign_name', hover_name='campaign_name', labels={'show_pv': 'Shows', 'ctr': 'CTR %'})
            fig_matrix.add_hline(y=med_ctr, line_dash="dot", line_color="gray", annotation_text="Median CTR")
            fig_matrix.add_vline(x=med_shows, line_dash="dot", line_color="gray", annotation_text="Median Shows")
            st.plotly_chart(fig_matrix, use_container_width=True)

        col3, col4 = st.columns([3, 2])
        with col3:
            st.markdown("**3. Canvas Leaderboard (Shows vs CTR %)**")
            leaderboard_df = quad_data.sort_values(by='show_pv', ascending=True).tail(10)
            fig_lead = go.Figure()
            fig_lead.add_trace(go.Bar(y=leaderboard_df['campaign_name'], x=leaderboard_df['show_pv'], name='Shows #', orientation='h', marker_color='#4C72B0'))
            fig_lead.add_trace(go.Scatter(y=leaderboard_df['campaign_name'], x=leaderboard_df['ctr'], name='CTR %', mode='markers', xaxis='x2', marker=dict(color='#C44E52', size=10)))
            fig_lead.update_layout(barmode='group', height=400, xaxis=dict(title='Shows #'), xaxis2=dict(title='CTR %', overlaying='x', side='top'))
            st.plotly_chart(fig_lead, use_container_width=True)
            
        with col4:
            st.markdown("**4. Day vs. Hour Engagement Heatmap**")
            heat_data = f_inapp.pivot_table(index='day_of_week', columns='hour_of_day', values='show_pv', aggfunc='sum').fillna(0)
            days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            heat_data = heat_data.reindex([d for d in days_order if d in heat_data.index])
            fig_heat = px.imshow(heat_data, aspect="auto", color_continuous_scale='YlOrRd', labels=dict(x="Hour of Day", y="Day of Week", color="Shows"))
            st.plotly_chart(fig_heat, use_container_width=True)

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
            st.markdown("**2. Promocode Utilization Matrix**")
            pm_agg = f_promo.groupby('promocode').agg({'redemption_count':'sum', 'usage_count':'sum'}).reset_index()
            pm_agg['util_rate'] = (pm_agg['usage_count'] / pm_agg['redemption_count'] * 100).fillna(0)
            fig_pmatrix = px.scatter(pm_agg, x='redemption_count', y='util_rate', size='usage_count', color='promocode')
            st.plotly_chart(fig_pmatrix, use_container_width=True)

    # ---------------------------------------------------------
    # TAB 3: COMMUNICATIONS
    # ---------------------------------------------------------
    with tab_comm:
        st.subheader("Push Notification Analytics")
        if not f_comm.empty and 'sends' in f_comm.columns:
            co1, co2 = st.columns(2)
            with co1:
                st.markdown("**1. Push Communication Funnel**")
                t_sends, t_opens, t_clicks = f_comm['sends'].sum(), f_comm['opens'].sum(), f_comm['clicks'].sum()
                fig_cfunnel = go.Figure(go.Funnel(y=['Sent', 'Opened', 'Clicked'], x=[t_sends, t_opens, t_clicks]))
                st.plotly_chart(fig_cfunnel, use_container_width=True)
                
            with co2:
                st.markdown("**2. Campaign Open Rate Leaderboard**")
                c_lead = f_comm.groupby('push_title').agg({'sends':'sum', 'opens':'sum'}).reset_index()
                c_lead['open_rate'] = (c_lead['opens'] / c_lead['sends'] * 100).fillna(0)
                fig_clead = px.bar(c_lead.sort_values(by='open_rate', ascending=True), x='open_rate', y='push_title', orientation='h', color='opens')
                st.plotly_chart(fig_clead, use_container_width=True)
        else:
            st.info("No communication metrics available for the selected period.")

    # ==========================================
    # 6. Detailed Data View with Clickable URLs
    # ==========================================
    st.markdown("---")
    st.subheader("📋 Raw Data & Creatives")
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
        use_container_width=True, hide_index=True
    )

except Exception as err:
    st.error(f"Error rendering dashboard: {err}")
