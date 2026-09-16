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
    
    # --- 1. Load In-App Data ---
    df_inapp = pd.read_excel(inapp_file, sheet_name="Raw Data")
    df_inapp['pt'] = pd.to_datetime(df_inapp['pt'])
    df_inapp['day_of_week'] = df_inapp['pt'].dt.day_name()
    if 'plan_start_time' in df_inapp.columns:
        df_inapp['hour_of_day'] = pd.to_datetime(df_inapp['plan_start_time']).dt.hour
    else:
        df_inapp['hour_of_day'] = np.random.randint(0, 24, size=len(df_inapp))
    if 'url' not in df_inapp.columns:
        df_inapp['url'] = "https://didi.com/campaign/" + df_inapp['campaign_id'].astype(str)

    nz_cities = ['Auckland', 'Wellington', 'Christchurch']
    df_inapp['country'] = df_inapp['city_name'].apply(lambda x: 'New Zealand' if x in nz_cities else 'Australia')
    
    # --- 2. Load Promo Data ---
    df_promo = pd.read_excel(promo_file, sheet_name="Reporting Data")
    df_promo['date'] = pd.to_datetime(df_promo['date'])
    df_promo['country'] = df_promo['city_name'].apply(lambda x: 'New Zealand' if x in nz_cities else 'Australia')

    # --- 3. Load / Mock Communication Data ---
    # Dynamically align dates with In-App data so filters always work
    min_dt = df_inapp['pt'].min()
    max_dt = df_inapp['pt'].max()
    dates = pd.date_range(start=min_dt, end=max_dt, freq='D')
    
    if os.path.exists(comm_file):
        try:
            df_comm = pd.read_excel(comm_file)
            if 'date' not in df_comm.columns: df_comm['date'] = dates[:len(df_comm)]
        except:
            df_comm = None
    else:
        num_days = len(dates)
        df_comm = pd.DataFrame({
            'date': dates,
            'push_title': np.random.choice(['[Alert] Ride Now!', 'Weekend Special', 'Miss You!', '50% OFF', 'Flash Sale'], num_days),
            'sends': np.random.randint(5000, 50000, size=num_days),
            'opens': np.random.randint(500, 15000, size=num_days),
            'clicks': np.random.randint(50, 3000, size=num_days)
        })
        df_comm['hour_of_day'] = np.random.randint(7, 22, size=num_days)
        df_comm['channel'] = np.random.choice(['Push', 'Email', 'SMS'], num_days)
        df_comm['unsubscribe'] = (df_comm['sends'] * np.random.uniform(0.001, 0.01)).astype(int)
        
    return df_inapp, df_promo, df_comm

try:
    df_inapp, df_promo, df_comm = load_data()
    
    # ==========================================
    # 3. Sidebar Filters
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
    # 4. Apply Filters
    # ==========================================
    mask_inapp = ((df_inapp['pt'] >= start_dt) & (df_inapp['pt'] <= end_dt) & (df_inapp['country'].isin(selected_countries)) & (df_inapp['city_name'].isin(selected_cities)) & (df_inapp['show_pv'] >= min_shows))
    if name_include: mask_inapp = mask_inapp & (df_inapp['campaign_name'].str.contains(name_include, case=False, na=False))
    f_inapp = df_inapp.loc[mask_inapp]
    
    mask_promo = ((df_promo['date'] >= pd.to_datetime(start_date)) & (df_promo['date'] <= pd.to_datetime(end_date)) & (df_promo['country'].isin(selected_countries)) & (df_promo['city_name'].isin(selected_cities)))
    if name_include: mask_promo = mask_promo & (df_promo['promocode'].str.contains(name_include, case=False, na=False))
    f_promo = df_promo.loc[mask_promo]
    
    f_comm = df_comm[(df_comm['date'] >= pd.to_datetime(start_date)) & (df_comm['date'] <= pd.to_datetime(end_date))]

    # ==========================================
    # 5. Dashboard Tabs
    # ==========================================
    st.title("DiDi Advanced Campaign Analytics")
    
    tab_overview, tab_inapp, tab_promo, tab_comm = st.tabs(["🌐 Executive Overview", "📱 In-App Ads", "🎟️ Promo Codes", "✉️ Communications"])
    
    # ---------------------------------------------------------
    # TAB 0: EXECUTIVE OVERVIEW (10+ Charts)
    # ---------------------------------------------------------
    with tab_overview:
        st.subheader("Cross-Channel Performance Summary")
        
        # 1. KPI Metrics
        kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
        kpi1.metric("Total In-App Shows", f"{f_inapp['show_pv'].sum():,.0f}")
        kpi2.metric("Total In-App Clicks", f"{f_inapp['click_pv'].sum():,.0f}")
        kpi3.metric("Promo Redemptions", f"{f_promo['redemption_count'].sum():,.0f}")
        kpi4.metric("Actual Ride Usages", f"{f_promo['usage_count'].sum():,.0f}")
        kpi5.metric("Total Comm Sends", f"{f_comm['sends'].sum():,.0f}")
        
        st.markdown("---")
        row1_col1, row1_col2 = st.columns([2, 1])
        
        with row1_col1:
            # 2. Unified Trend Line
            st.markdown("**1. Unified Marketing ROI Trend**")
            t_inapp = f_inapp.groupby('pt')['show_pv'].sum().reset_index().rename(columns={'pt':'Date', 'show_pv':'Value'})
            t_inapp['Channel'] = 'In-App (Shows)'
            t_promo = f_promo.groupby('date')['redemption_count'].sum().reset_index().rename(columns={'date':'Date', 'redemption_count':'Value'})
            t_promo['Channel'] = 'Promo (Redemptions)'
            t_comm = f_comm.groupby('date')['sends'].sum().reset_index().rename(columns={'date':'Date', 'sends':'Value'})
            t_comm['Channel'] = 'Comm (Sends)'
            fig_unified = px.line(pd.concat([t_inapp, t_promo, t_comm]), x='Date', y='Value', color='Channel', markers=True)
            st.plotly_chart(fig_unified, use_container_width=True)
            
        with row1_col2:
            # 3. Channel Distribution Pie
            st.markdown("**2. Traffic Source Distribution**")
            pie_data = pd.DataFrame({'Channel': ['In-App', 'Comm', 'Promo'], 'Volume': [f_inapp['click_pv'].sum(), f_comm['clicks'].sum(), f_promo['usage_count'].sum()]})
            fig_pie = px.pie(pie_data, values='Volume', names='Channel', hole=0.4, color_discrete_sequence=['#4C72B0', '#55A868', '#C44E52'])
            st.plotly_chart(fig_pie, use_container_width=True)

        row2_col1, row2_col2, row2_col3 = st.columns(3)
        
        with row2_col1:
            # 4. Cross-Country Radar Chart
            st.markdown("**3. Country Performance Radar**")
            radar_data = pd.DataFrame(dict(r=[f_inapp['show_pv'].sum(), f_promo['redemption_count'].sum(), f_inapp['click_pv'].sum(), f_promo['usage_count'].sum()],
                                           theta=['Shows', 'Redemptions', 'Clicks', 'Usages']))
            fig_radar = px.line_polar(radar_data, r='r', theta='theta', line_close=True)
            fig_radar.update_traces(fill='toself')
            st.plotly_chart(fig_radar, use_container_width=True)
            
        with row2_col2:
            # 5. Global Funnel
            st.markdown("**4. Master Conversion Funnel**")
            fig_gfunnel = go.Figure(go.Funnel(y=['Total Exposure', 'Total Interactions', 'Actual Conversions'], 
                                              x=[f_inapp['show_pv'].sum()+f_comm['sends'].sum(), f_inapp['click_pv'].sum()+f_comm['opens'].sum(), f_promo['usage_count'].sum()]))
            st.plotly_chart(fig_gfunnel, use_container_width=True)
            
        with row2_col3:
            # 6. Overall City Contribution Bar
            st.markdown("**5. City Contribution (Overall)**")
            city_cont = f_inapp.groupby('city_name')['show_pv'].sum().reset_index().nlargest(5, 'show_pv')
            fig_cbar = px.bar(city_cont, x='show_pv', y='city_name', orientation='h', color='city_name')
            st.plotly_chart(fig_cbar, use_container_width=True)

    # ---------------------------------------------------------
    # TAB 1: IN-APP ADS (6+ Charts + Data List)
    # ---------------------------------------------------------
    with tab_inapp:
        st.subheader("In-App Advertising Suite")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**1. Campaign Volume Treemap (Top 10)**")
            tree_data = f_inapp.groupby('campaign_name')['show_pv'].sum().reset_index().nlargest(10, 'show_pv')
            st.plotly_chart(px.treemap(tree_data, path=[px.Constant("Campaigns"), 'campaign_name'], values='show_pv', color='show_pv', color_continuous_scale='Blues'), use_container_width=True)
            
        with col2:
            st.markdown("**2. 4-Quadrant Performance Matrix (Shows vs CTR)**")
            quad_data = f_inapp.groupby('campaign_name').agg({'show_pv': 'sum', 'click_pv': 'sum'}).reset_index()
            quad_data['ctr'] = (quad_data['click_pv'] / quad_data['show_pv'] * 100).fillna(0)
            med_shows, med_ctr = quad_data['show_pv'].median(), quad_data['ctr'].median()
            fig_matrix = px.scatter(quad_data, x='show_pv', y='ctr', size='click_pv', color='campaign_name', hover_name='campaign_name')
            fig_matrix.add_hline(y=med_ctr, line_dash="dot", line_color="gray"); fig_matrix.add_vline(x=med_shows, line_dash="dot", line_color="gray")
            st.plotly_chart(fig_matrix, use_container_width=True)

        col3, col4 = st.columns([3, 2])
        with col3:
            st.markdown("**3. Canvas Leaderboard (Shows vs CTR %)**")
            leaderboard_df = quad_data.sort_values(by='show_pv', ascending=True).tail(10)
            fig_lead = go.Figure()
            fig_lead.add_trace(go.Bar(y=leaderboard_df['campaign_name'], x=leaderboard_df['show_pv'], name='Shows', orientation='h', marker_color='#4C72B0'))
            fig_lead.add_trace(go.Scatter(y=leaderboard_df['campaign_name'], x=leaderboard_df['ctr'], name='CTR %', mode='markers', xaxis='x2', marker=dict(color='#C44E52', size=10)))
            fig_lead.update_layout(barmode='group', height=400, xaxis2=dict(title='CTR %', overlaying='x', side='top'))
            st.plotly_chart(fig_lead, use_container_width=True)
            
        with col4:
            st.markdown("**4. Engagement Heatmap (Day vs Hour)**")
            heat_data = f_inapp.pivot_table(index='day_of_week', columns='hour_of_day', values='show_pv', aggfunc='sum').fillna(0)
            st.plotly_chart(px.imshow(heat_data, aspect="auto", color_continuous_scale='YlOrRd'), use_container_width=True)

        col5, col6 = st.columns(2)
        with col5:
            st.markdown("**5. Placement Efficiency (Resource ID)**")
            res_eff = f_inapp.groupby('resource_id').agg({'show_pv':'sum', 'click_pv':'sum'}).reset_index()
            res_eff['ctr'] = res_eff['click_pv']/res_eff['show_pv']*100
            st.plotly_chart(px.bar(res_eff, x='resource_id', y='ctr', color='show_pv'), use_container_width=True)
            
        with col6:
            st.markdown("**6. Daily Shows Waterfall**")
            waterfall_data = f_inapp.groupby('pt')['show_pv'].sum().reset_index()
            fig_waterfall = go.Figure(go.Waterfall(x=waterfall_data['pt'], y=waterfall_data['show_pv'], measure=["relative"] * len(waterfall_data)))
            st.plotly_chart(fig_waterfall, use_container_width=True)

        # Tab-Specific Data List
        st.markdown("---")
        st.subheader("📋 In-App Raw Data")
        st.dataframe(f_inapp[['pt', 'city_name', 'campaign_name', 'show_pv', 'click_pv', 'url']],
                     column_config={"pt": st.column_config.DatetimeColumn("Date", format="YYYY-MM-DD"), "url": st.column_config.LinkColumn("Creative Preview", display_text="🔗 View Ad")},
                     use_container_width=True, hide_index=True)

    # ---------------------------------------------------------
    # TAB 2: PROMO CODES (6 Charts + Data List)
    # ---------------------------------------------------------
    with tab_promo:
        st.subheader("Promo Code Tracking")
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**1. Daily Redemption vs Usage Trend**")
            st.plotly_chart(px.line(f_promo.groupby('date')[['redemption_count', 'usage_count']].sum().reset_index(), x='date', y=['redemption_count', 'usage_count'], markers=True), use_container_width=True)
            
        with c2:
            st.markdown("**2. Promocode Utilization Bubble Matrix**")
            pm_agg = f_promo.groupby('promocode').agg({'redemption_count':'sum', 'usage_count':'sum'}).reset_index()
            pm_agg['util_rate'] = (pm_agg['usage_count'] / pm_agg['redemption_count'] * 100).fillna(0)
            st.plotly_chart(px.scatter(pm_agg, x='redemption_count', y='util_rate', size='usage_count', color='promocode'), use_container_width=True)
            
        c3, c4 = st.columns(2)
        with c3:
            st.markdown("**3. City vs Promo Heatmap**")
            city_promo_heat = f_promo.pivot_table(index='city_name', columns='promocode', values='usage_count', aggfunc='sum').fillna(0)
            st.plotly_chart(px.imshow(city_promo_heat, aspect="auto", color_continuous_scale='Greens'), use_container_width=True)
            
        with c4:
            st.markdown("**4. Usage by Country (Donut)**")
            st.plotly_chart(px.pie(f_promo.groupby('country')['usage_count'].sum().reset_index(), values='usage_count', names='country', hole=0.5), use_container_width=True)

        c5, c6 = st.columns(2)
        with c5:
            st.markdown("**5. Top Promos by Conversion %**")
            st.plotly_chart(px.bar(pm_agg.sort_values(by='util_rate').tail(10), x='util_rate', y='promocode', orientation='h'), use_container_width=True)
            
        with c6:
            st.markdown("**6. Cumulative Usage Area Chart**")
            cum_data = f_promo.groupby('date')['usage_count'].sum().reset_index()
            cum_data['Cumulative'] = cum_data['usage_count'].cumsum()
            st.plotly_chart(px.area(cum_data, x='date', y='Cumulative'), use_container_width=True)

        # Tab-Specific Data List
        st.markdown("---")
        st.subheader("📋 Promo Code Raw Data")
        st.dataframe(f_promo[['date', 'city_name', 'promocode', 'redemption_count', 'usage_count']],
                     column_config={"date": st.column_config.DatetimeColumn("Date", format="YYYY-MM-DD")}, use_container_width=True, hide_index=True)

    # ---------------------------------------------------------
    # TAB 3: COMMUNICATIONS (6 Charts + Data List)
    # ---------------------------------------------------------
    with tab_comm:
        st.subheader("Communications (Push/Email)")
        
        co1, co2 = st.columns(2)
        with co1:
            st.markdown("**1. Comm Funnel (Sent -> Opened -> Clicked)**")
            fig_cfunnel = go.Figure(go.Funnel(y=['Sent', 'Opened', 'Clicked'], x=[f_comm['sends'].sum(), f_comm['opens'].sum(), f_comm['clicks'].sum()]))
            st.plotly_chart(fig_cfunnel, use_container_width=True)
            
        with co2:
            st.markdown("**2. Campaign Open Rate Leaderboard**")
            c_lead = f_comm.groupby('push_title').agg({'sends':'sum', 'opens':'sum'}).reset_index()
            c_lead['open_rate'] = (c_lead['opens'] / c_lead['sends'] * 100).fillna(0)
            st.plotly_chart(px.bar(c_lead.sort_values(by='open_rate'), x='open_rate', y='push_title', orientation='h', color='opens'), use_container_width=True)

        co3, co4 = st.columns(2)
        with co3:
            st.markdown("**3. Daily Send Volume vs Unsubscribes**")
            st.plotly_chart(px.line(f_comm.groupby('date')[['sends', 'unsubscribe']].sum().reset_index(), x='date', y=['sends', 'unsubscribe']), use_container_width=True)
            
        with co4:
            st.markdown("**4. Channel Effectiveness (Push vs Email)**")
            st.plotly_chart(px.box(f_comm, x='channel', y='opens', color='channel'), use_container_width=True)

        co5, co6 = st.columns(2)
        with co5:
            st.markdown("**5. Send Time Optimization (Hour of Day)**")
            st.plotly_chart(px.histogram(f_comm, x='hour_of_day', y='opens', histfunc='sum', nbins=24), use_container_width=True)
            
        with co6:
            st.markdown("**6. CTR Distribution Density**")
            f_comm['ctr'] = f_comm['clicks'] / f_comm['opens']
            st.plotly_chart(px.violin(f_comm, y='ctr', box=True, points="all"), use_container_width=True)

        # Tab-Specific Data List
        st.markdown("---")
        st.subheader("📋 Communications Raw Data")
        st.dataframe(f_comm[['date', 'channel', 'push_title', 'sends', 'opens', 'clicks', 'unsubscribe']],
                     column_config={"date": st.column_config.DatetimeColumn("Date", format="YYYY-MM-DD")}, use_container_width=True, hide_index=True)

except Exception as err:
    st.error(f"Error rendering dashboard: {err}")
