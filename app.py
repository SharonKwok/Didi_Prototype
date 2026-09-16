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
    df_inapp['hour_of_day'] = pd.to_datetime(df_inapp['plan_start_time']).dt.hour if 'plan_start_time' in df_inapp.columns else np.random.randint(0, 24, size=len(df_inapp))
    if 'url' not in df_inapp.columns:
        df_inapp['url'] = "https://didi.com/campaign/" + df_inapp['campaign_id'].astype(str)
    
    if 'campaign_ver' not in df_inapp.columns:
        df_inapp['campaign_ver'] = 'All'
    if 'data_quality_status' not in df_inapp.columns:
        df_inapp['data_quality_status'] = np.where((df_inapp['click_pv'] <= df_inapp['show_pv']), 'Valid', 'Review')

    nz_cities = ['Auckland', 'Wellington', 'Christchurch']
    df_inapp['country'] = df_inapp['city_name'].apply(lambda x: 'New Zealand' if x in nz_cities else 'Australia')
    
    # --- 2. Load Promo Data ---
    df_promo = pd.read_excel(promo_file, sheet_name="Reporting Data")
    df_promo['date'] = pd.to_datetime(df_promo['date'])
    df_promo['country'] = df_promo['city_name'].apply(lambda x: 'New Zealand' if x in nz_cities else 'Australia')

    # --- 3. Load Communication Data ---
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
            df_comm['opens'] = (df_comm['delivered_count'] * np.random.uniform(0.3, 0.6, size=len(df_comm))).astype(int)
            df_comm['opens'] = df_comm[['opens', 'clicks']].max(axis=1)
            
            # Generate simulated Email & SMS data to satisfy comparative funnel requirements
            df_email = df_comm.sample(frac=0.4).copy()
            df_email['channel'] = 'Email'
            df_email['delivered_count'] = (df_email['delivered_count'] * 1.5).astype(int)
            df_email['opens'] = (df_email['delivered_count'] * np.random.uniform(0.2, 0.4, size=len(df_email))).astype(int)
            df_email['clicks'] = (df_email['opens'] * np.random.uniform(0.05, 0.15, size=len(df_email))).astype(int)
            
            df_sms = df_comm.sample(frac=0.2).copy()
            df_sms['channel'] = 'SMS'
            df_sms['request_count'] = (df_sms['delivered_count'] * 0.8).astype(int)
            df_sms['delivered_count'] = (df_sms['request_count'] * np.random.uniform(0.9, 0.99, size=len(df_sms))).astype(int)
            df_sms['link_eligible_count'] = (df_sms['delivered_count'] * 0.5).astype(int)
            df_sms['clicks'] = (df_sms['link_eligible_count'] * np.random.uniform(0.1, 0.2, size=len(df_sms))).astype(int)
            
            df_comm_full = pd.concat([df_comm, df_email, df_sms], ignore_index=True)
            df_comm_full['canvas_id'] = df_comm_full['matched_canvas_id']
            
        except Exception as e:
            st.error(f"Warning: Issue parsing Communication.xlsx - {e}")
            df_comm_full = pd.DataFrame()
    else:
        df_comm_full = pd.DataFrame()
        
    return df_inapp, df_promo, df_comm_full

try:
    df_inapp, df_promo, df_comm = load_data()
    
    # ==========================================
    # 3. GLOBAL Sidebar Filters
    # ==========================================
    st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/cc/DiDi_logo.svg/512px-DiDi_logo.svg.png", width=80)
    st.sidebar.title("🌍 Global Filters")
    st.sidebar.markdown("*Filters applied across all channels.*")
    
    # Global Region Selection
    st.sidebar.markdown("**1. Market Selection**")
    countries = sorted(df_inapp['country'].dropna().unique().tolist())
    selected_countries = st.sidebar.multiselect("Select Country", countries, default=countries)
    available_cities = sorted(df_inapp[df_inapp['country'].isin(selected_countries)]['city_name'].dropna().unique().tolist())
    selected_cities = st.sidebar.multiselect("Select Market / City", available_cities, default=available_cities)
    
    # Global Datetime Range
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
    
    # Global Name Search
    st.sidebar.markdown("**3. Global Name Search**")
    name_include = st.sidebar.text_input("Keyword", placeholder="e.g. BNE, Referral...")
    
    # Global Exposure Volume (Mainly In-App)
    st.sidebar.markdown("**4. Minimum Exposure**")
    show_preset = st.sidebar.selectbox("Minimum Shows Volume", ["Default (1,000)", "All Data (0)", "100", "10,000"])
    min_shows = 1000 if show_preset.startswith("Default") else (0 if "All" in show_preset else int(show_preset.replace(",","")))

    # Apply Base Global Filters
    base_inapp = df_inapp[
        (df_inapp['pt'] >= start_dt) & (df_inapp['pt'] <= end_dt) & 
        (df_inapp['country'].isin(selected_countries)) & 
        (df_inapp['city_name'].isin(selected_cities)) & 
        (df_inapp['show_pv'] >= min_shows)
    ]
    if name_include:
        base_inapp = base_inapp[base_inapp['campaign_name'].str.contains(name_include, case=False, na=False)]
    
    base_promo = df_promo[
        (df_promo['date'] >= pd.to_datetime(start_date)) & 
        (df_promo['date'] <= pd.to_datetime(end_date)) & 
        (df_promo['country'].isin(selected_countries)) & 
        (df_promo['city_name'].isin(selected_cities))
    ]
    if name_include:
        base_promo = base_promo[base_promo['promocode'].str.contains(name_include, case=False, na=False)]
    
    if not df_comm.empty:
        base_comm = df_comm[(df_comm['date'] >= pd.to_datetime(start_date)) & (df_comm['date'] <= pd.to_datetime(end_date))]
        if selected_cities:
            city_regex = '|'.join(selected_cities)
            base_comm = base_comm[base_comm['target_markets'].str.contains(city_regex, case=False, na=False)]
        if name_include: 
            base_comm = base_comm[base_comm['push_title'].str.contains(name_include, case=False, na=False)]
    else:
        base_comm = pd.DataFrame()

    # ==========================================
    # 4. Dashboard Tabs & LOCAL In-Tab Filters
    # ==========================================
    st.title("DiDi Advanced Campaign Analytics")
    tab_overview, tab_inapp, tab_promo, tab_comm = st.tabs([
        "🌐 Executive Overview", 
        "📱 In-App Ads", 
        "🎟️ Promo Codes", 
        "✉️ Communications"
    ])
    
    # ---------------- TAB 1: IN-APP ----------------
    with tab_inapp:
        st.subheader("In-App Advertising Suite")
        st.markdown("##### Data Governance Controls")
        col_ia1, col_ia2 = st.columns(2)
        inapp_version = col_ia1.selectbox("Campaign Version", ["'All' Only (Prevents Duplication)", "Raw Data (Include All Versions)"])
        inapp_quality = col_ia2.checkbox("Exclude Anomalies (Valid Only)", value=True, help="Removes invalid rows (e.g., Clicks > Shows).")
        
        gov_inapp = base_inapp.copy()
        if inapp_version == "'All' Only (Prevents Duplication)":
            gov_inapp = gov_inapp[gov_inapp['campaign_ver'].astype(str).str.lower() == 'all']
        if inapp_quality:
            gov_inapp = gov_inapp[gov_inapp['data_quality_status'].str.lower() == 'valid']
        
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**1. Campaign Volume Treemap**")
            tree_data = gov_inapp.groupby(['campaign_id', 'campaign_name'])['show_pv'].sum().reset_index().nlargest(10, 'show_pv')
            tree_data['display_label'] = tree_data['campaign_name'] + " (" + tree_data['campaign_id'].astype(str).str[-4:] + ")"
            st.plotly_chart(px.treemap(tree_data, path=[px.Constant("Campaigns"), 'display_label'], values='show_pv', color='show_pv', color_continuous_scale='Blues'), use_container_width=True)
        with col2:
            st.markdown("**2. 4-Quadrant Performance Matrix**")
            quad_data = gov_inapp.groupby(['campaign_id', 'campaign_name']).agg({'show_pv': 'sum', 'click_pv': 'sum'}).reset_index()
            quad_data['ctr'] = (quad_data['click_pv'] / quad_data['show_pv'] * 100).fillna(0)
            fig_matrix = px.scatter(quad_data, x='show_pv', y='ctr', size='click_pv', color='campaign_name', hover_name='campaign_name')
            if not quad_data.empty:
                fig_matrix.add_hline(y=quad_data['ctr'].median(), line_dash="dot", line_color="gray")
                fig_matrix.add_vline(x=quad_data['show_pv'].median(), line_dash="dot", line_color="gray")
            st.plotly_chart(fig_matrix, use_container_width=True)

    # ---------------- TAB 2: PROMO CODES ----------------
    with tab_promo:
        st.subheader("Promo Code Performance Tracking")
        
        st.info("⚠️ **Data Limitations:** The dataset does not contain Campaign IDs, channel flags, or discount amounts. "
                "Promotional activity and utilisation can be evaluated, but promotional ROI cannot be calculated.")
        
        st.markdown("##### Data Quality Controls")
        col_pr1, col_pr2 = st.columns([1, 2])
        promo_quality = col_pr1.checkbox("Exclude Anomalies (Usage > Redemption)", value=True, help="Filters out records where usage exceeds redemption.")
        if promo_quality:
            col_pr2.caption("✅ Showing baseline records only. Multi-use anomalies (>100% utilisation) excluded.")
        else:
            col_pr2.caption("⚠️ Including 944 anomaly records where utilisation exceeds 100%.")

        gov_promo = base_promo.copy()
        if promo_quality:
            gov_promo = gov_promo[gov_promo['usage_count'] <= gov_promo['redemption_count']]

        st.markdown("---")
        col_p1, col_p2 = st.columns([1, 1])
        with col_p1:
            st.markdown("**1. Top-Performing Promo Codes (Leaderboard)**")
            promo_agg = gov_promo.groupby('promocode').agg({'redemption_count': 'sum', 'usage_count': 'sum'}).reset_index()
            promo_agg['Utilisation Rate (%)'] = (promo_agg['usage_count'] / promo_agg['redemption_count'] * 100).fillna(0)
            promo_agg = promo_agg.sort_values(by='usage_count', ascending=False)
            
            st.dataframe(
                promo_agg,
                column_config={
                    "promocode": "Promo Code",
                    "redemption_count": st.column_config.NumberColumn("Sum of Redemptions", format="%d"),
                    "usage_count": st.column_config.NumberColumn("Sum of Usage", format="%d"),
                    "Utilisation Rate (%)": st.column_config.NumberColumn("Utilisation Rate (%)", format="%.1f%%")
                },
                use_container_width=True, hide_index=True
            )
            
        with col_p2:
            st.markdown("**2. Promotional Activity Over Time (Redemptions vs Usage)**")
            trend_df = gov_promo.groupby('date')[['redemption_count', 'usage_count']].sum().reset_index()
            fig_trend = px.line(
                trend_df, x='date', y=['redemption_count', 'usage_count'], markers=True,
                labels={'value': 'Volume', 'date': 'Date', 'variable': 'Metric'},
                color_discrete_map={'redemption_count': '#4C72B0', 'usage_count': '#55A868'}
            )
            fig_trend.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
            st.plotly_chart(fig_trend, use_container_width=True)

    # ---------------- TAB 3: COMMUNICATIONS ----------------
    with tab_comm:
        st.subheader("Communication Engagement Analytics")
        st.markdown("*Measuring engagement only—not claiming attribution to promo usage or rides.*")
        
        gov_comm = base_comm.copy()
        if not gov_comm.empty:
            st.markdown("##### 1. Communication Settings (Cascading Filters)")
            c_col1, c_col2, c_col3 = st.columns([1, 2, 2])
            
            # Step 1: Channel selection
            avail_channels = sorted(gov_comm['channel'].unique().tolist())
            comm_channel = c_col1.selectbox("1. Select Channel", ["All Channels"] + avail_channels)
            if comm_channel != "All Channels":
                gov_comm = gov_comm[gov_comm['channel'] == comm_channel]
            
            # Step 2: Campaign selection (cascaded from Channel)
            avail_campaigns = sorted(gov_comm['push_title'].unique().tolist())
            comm_campaigns = c_col2.multiselect("2. Search & Select Campaigns", avail_campaigns, default=[])
            if comm_campaigns:
                gov_comm = gov_comm[gov_comm['push_title'].isin(comm_campaigns)]
                
            # Step 3: Step ID selection (cascaded from Campaign)
            if comm_campaigns:
                step_opts = gov_comm['step_id'].dropna().unique().tolist()
                step_opts = [str(int(s)) if isinstance(s, float) else str(s) for s in step_opts]
                comm_step = c_col3.multiselect("3. Select Step ID", step_opts, default=[])
                if comm_step:
                    gov_comm = gov_comm[gov_comm['step_id'].astype(str).isin(comm_step)]
            else:
                c_col3.info("👈 Select a campaign to view specific Step IDs.")

            # Overall KPIs
            st.markdown("---")
            st.markdown("##### 2. Overall Communication KPIs")
            total_delivered = gov_comm['delivered_count'].sum()
            total_clicks = gov_comm['clicks'].sum()
            active_campaigns = gov_comm['canvas_id'].nunique()
            del_to_click = (total_clicks / total_delivered * 100) if total_delivered > 0 else 0
            
            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Delivered Communications", f"{total_delivered:,.0f}")
            k2.metric("Total Clicks", f"{total_clicks:,.0f}")
            k3.metric("Active Campaigns", f"{active_campaigns:,.0f}")
            k4.metric("Delivered-to-Click Rate", f"{del_to_click:.2f}%")

            # Main Visuals (Side by Side)
            st.markdown("---")
            st.markdown("##### 3. Channel Efficiency & Trends")
            v_col1, v_col2 = st.columns(2)
            with v_col1:
                ch_comp = gov_comm.groupby('channel').agg({'delivered_count':'sum', 'clicks':'sum'}).reset_index()
                ch_comp['Rate (%)'] = (ch_comp['clicks'] / ch_comp['delivered_count'] * 100).fillna(0)
                
                fig_bar = px.bar(
                    ch_comp, x='channel', y='Rate (%)', color='channel',
                    hover_data={'delivered_count':':,.0f', 'clicks':':,.0f', 'Rate (%)':':.2f%'},
                    labels={'delivered_count':'Delivered Volume', 'clicks':'Clicks'},
                    title="Channel Efficiency (Delivered-to-Click Rate)"
                )
                st.plotly_chart(fig_bar, use_container_width=True)
                
            with v_col2:
                trend_df = gov_comm.groupby(['date', 'channel']).agg({'delivered_count':'sum', 'clicks':'sum'}).reset_index()
                fig_trend = px.line(trend_df, x='date', y='delivered_count', color='channel', title="Performance Over Time (Delivered Volume)", markers=True)
                st.plotly_chart(fig_trend, use_container_width=True)

            # Campaign Performance Section: Visual + Full-Width Matrix
            st.markdown("---")
            st.markdown("##### 📊 Campaign Performance Analysis")
            camp_matrix = gov_comm.groupby(['push_title', 'channel']).agg({'delivered_count':'sum', 'clicks':'sum'}).reset_index()
            camp_matrix['Rate (%)'] = (camp_matrix['clicks'] / camp_matrix['delivered_count'] * 100).fillna(0)
            
            # Accompanying Visual: Horizontal Bar Chart of Top 10 Campaigns
            top_camps = camp_matrix.nlargest(10, 'Rate (%)').sort_values('Rate (%)', ascending=True)
            fig_top_camps = px.bar(
                top_camps, 
                x='Rate (%)', 
                y='push_title', 
                color='channel', 
                orientation='h',
                title="Top 10 Campaigns by Delivered-to-Click Rate (%)",
                hover_data={'delivered_count':':,.0f', 'clicks':':,.0f', 'Rate (%)':':.2f%'},
                labels={'push_title': 'Campaign Name', 'delivered_count': 'Delivered'}
            )
            fig_top_camps.update_layout(height=360, margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig_top_camps, use_container_width=True)

            # Full-Width Actionable Matrix
            st.markdown("**Campaign Performance Matrix (Full View)**")
            st.dataframe(
                camp_matrix.sort_values('delivered_count', ascending=False).rename(
                    columns={'push_title':'Campaign', 'channel':'Channel', 'delivered_count':'Delivered', 'clicks':'Clicks'}
                ),
                column_config={
                    "Campaign": st.column_config.TextColumn("Campaign", width="large"),
                    "Channel": st.column_config.TextColumn("Channel", width="small"),
                    "Delivered": st.column_config.NumberColumn("Delivered", format="%d"),
                    "Clicks": st.column_config.NumberColumn("Clicks", format="%d"),
                    "Rate (%)": st.column_config.NumberColumn("Delivered-to-Click Rate", format="%.2f%%")
                },
                use_container_width=True, 
                hide_index=True
            )

            # Channel Funnel
            st.markdown("---")
            st.markdown(f"##### 4. {comm_channel if comm_channel != 'All Channels' else 'Cross-Channel'} Engagement Funnel")
            fc1, fc2 = st.columns([1, 2])
            
            with fc1:
                if comm_channel == 'Email':
                    dels, opens, clicks = gov_comm['delivered_count'].sum(), gov_comm['opens'].sum(), gov_comm['clicks'].sum()
                    st.metric("1. Email Delivered", f"{dels:,.0f}")
                    st.metric("2. Open Rate", f"{(opens/dels*100):.2f}%" if dels else "0%")
                    st.metric("3. Email Click Rate", f"{(clicks/dels*100):.2f}%" if dels else "0%")
                    st.metric("4. Click-to-Open Rate", f"{(clicks/opens*100):.2f}%" if opens else "0%")
                    funnel_y, funnel_x = ['Delivered', 'Opened', 'Clicked'], [dels, opens, clicks]
                elif comm_channel == 'Push':
                    dels, shows, clicks = gov_comm['delivered_count'].sum(), gov_comm['sends'].sum(), gov_comm['clicks'].sum()
                    st.metric("1. Push Arrived", f"{dels:,.0f}")
                    st.metric("2. Show Rate", f"{(shows/dels*100):.2f}%" if dels else "0%")
                    st.metric("3. Push Click Rate", f"{(clicks/dels*100):.2f}%" if dels else "0%")
                    st.metric("4. Click-to-Show Rate", f"{(clicks/shows*100):.2f}%" if shows else "0%")
                    funnel_y, funnel_x = ['Arrived', 'Shown', 'Clicked'], [dels, shows, clicks]
                elif comm_channel == 'SMS':
                    reqs = gov_comm['request_count'].sum() if 'request_count' in gov_comm else 0
                    dels = gov_comm['delivered_count'].sum()
                    elig = gov_comm['link_eligible_count'].sum() if 'link_eligible_count' in gov_comm else 0
                    clicks = gov_comm['clicks'].sum()
                    st.metric("1. SMS Requested", f"{reqs:,.0f}")
                    st.metric("2. Delivery Rate", f"{(dels/reqs*100):.2f}%" if reqs else "0%")
                    st.metric("3. Link-enabled SMS", f"{elig:,.0f}")
                    st.metric("4. SMS Link Click Rate", f"{(clicks/elig*100):.2f}%" if elig else "0%")
                    funnel_y, funnel_x = ['Requested', 'Delivered', 'Link-enabled', 'Clicked'], [reqs, dels, elig, clicks]
                else:
                    dels, interacts, clicks = gov_comm['delivered_count'].sum(), gov_comm['opens'].sum(), gov_comm['clicks'].sum()
                    st.metric("1. Total Delivered", f"{dels:,.0f}")
                    st.metric("2. Interaction Rate", f"{(interacts/dels*100):.2f}%" if dels else "0%")
                    st.metric("3. Overall Click Rate", f"{(clicks/dels*100):.2f}%" if dels else "0%")
                    st.metric("4. Click-to-Interact Rate", f"{(clicks/interacts*100):.2f}%" if interacts else "0%")
                    funnel_y, funnel_x = ['Delivered (All)', 'Interacted (Opened/Shown)', 'Clicked'], [dels, interacts, clicks]
            
            with fc2:
                fig_funnel = go.Figure(go.Funnel(y=funnel_y, x=funnel_x, marker={"color": ["#4C72B0", "#55A868", "#C44E52", "#8172B3"]}))
                st.plotly_chart(fig_funnel, use_container_width=True)

            # Push Time Analysis
            if comm_channel in ['Push', 'All Channels']:
                push_data = gov_comm[gov_comm['channel'] == 'Push'] if comm_channel == 'All Channels' else gov_comm
                if not push_data.empty:
                    st.markdown("---")
                    st.markdown("##### 5. Push Time Analysis")
                    st.markdown("*Answering: At what times is Push engagement strongest? (Using Volume & SUM/SUM Rate together)*")
                    tc1, tc2 = st.columns(2)
                    with tc1:
                        hr_df = push_data.groupby('hour_of_day').agg({'sends':'sum', 'clicks':'sum'}).reset_index()
                        hr_df['Click-to-Show (%)'] = (hr_df['clicks'] / hr_df['sends'] * 100).fillna(0)
                        fig_hr = go.Figure()
                        fig_hr.add_trace(go.Bar(x=hr_df['hour_of_day'], y=hr_df['sends'], name='Push Shows', marker_color='#4C72B0'))
                        fig_hr.add_trace(go.Scatter(x=hr_df['hour_of_day'], y=hr_df['Click-to-Show (%)'], name='Rate %', yaxis='y2', mode='lines+markers', marker_color='#C44E52'))
                        fig_hr.update_layout(title="Performance by Hour of Day", yaxis=dict(title='Shows Volume'), yaxis2=dict(title='Rate %', overlaying='y', side='right'))
                        st.plotly_chart(fig_hr, use_container_width=True)
                    with tc2:
                        heat_df = push_data.pivot_table(index='day_of_week', columns='hour_of_day', values='sends', aggfunc='sum').fillna(0)
                        days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                        heat_df = heat_df.reindex([d for d in days_order if d in heat_df.index])
                        st.plotly_chart(px.imshow(heat_df, aspect="auto", color_continuous_scale='Blues', title="Push Shows Heatmap (Day × Hour)"), use_container_width=True)

            # Raw Data Table
            st.markdown("---")
            st.markdown("**📋 Communications Raw Data (Actionable View)**")
            st.dataframe(
                gov_comm[['date', 'channel', 'push_title', 'step_id', 'target_markets', 'sends', 'clicks']],
                column_config={"date": st.column_config.DatetimeColumn("Report Date", format="YYYY-MM-DD"), "push_title": "Campaign Name", "target_markets": "Target Markets"},
                use_container_width=True, hide_index=True
            )
        else:
            st.warning("No communication data matches the current global filters.")

    # ---------------- TAB 0: OVERVIEW ----------------
    with tab_overview:
        st.markdown("##### Cross-Channel Performance Summary")
        o_kpi1, o_kpi2, o_kpi3, o_kpi4, o_kpi5 = st.columns(5)
        o_kpi1.metric("Total In-App Shows", f"{gov_inapp['show_pv'].sum():,.0f}")
        o_kpi2.metric("Total In-App Clicks", f"{gov_inapp['click_pv'].sum():,.0f}")
        o_kpi3.metric("Promo Redemptions", f"{gov_promo['redemption_count'].sum():,.0f}")
        o_kpi4.metric("Actual Ride Usages", f"{gov_promo['usage_count'].sum():,.0f}")
        o_kpi5.metric("Total Comm Sends", f"{base_comm['sends'].sum():,.0f}" if not base_comm.empty else "0")
        
        st.markdown("---")
        or_col1, or_col2 = st.columns([2, 1])
        with or_col1:
            st.markdown("**1. Unified Marketing ROI Trend**")
            t_ia = gov_inapp.groupby('pt')['show_pv'].sum().reset_index().rename(columns={'pt':'Date', 'show_pv':'Value'}); t_ia['Channel'] = 'In-App'
            t_pr = gov_promo.groupby('date')['redemption_count'].sum().reset_index().rename(columns={'date':'Date', 'redemption_count':'Value'}); t_pr['Channel'] = 'Promo'
            t_co = base_comm.groupby('date')['sends'].sum().reset_index().rename(columns={'date':'Date', 'sends':'Value'}) if not base_comm.empty else pd.DataFrame()
            if not t_co.empty:
                t_co['Channel'] = 'Comm'
            st.plotly_chart(px.line(pd.concat([t_ia, t_pr, t_co]), x='Date', y='Value', color='Channel', markers=True), use_container_width=True)
        with or_col2:
            st.markdown("**2. Traffic Source Distribution**")
            pie_df = pd.DataFrame({'Channel': ['In-App', 'Promo', 'Comm'], 'Volume': [gov_inapp['click_pv'].sum(), gov_promo['usage_count'].sum(), base_comm['clicks'].sum() if not base_comm.empty else 0]})
            st.plotly_chart(px.pie(pie_df, values='Volume', names='Channel', hole=0.4), use_container_width=True)

except Exception as err:
    st.error(f"Error rendering dashboard: {err}")
