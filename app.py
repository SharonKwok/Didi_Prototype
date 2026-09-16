import os
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
    
    # Extract Hour for Heatmap (Using plan_start_time if available, else mock hours for PoC)
    if 'plan_start_time' in df_inapp.columns:
        df_inapp['hour_of_day'] = pd.to_datetime(df_inapp['plan_start_time']).dt.hour
    else:
        df_inapp['hour_of_day'] = np.random.randint(0, 24, size=len(df_inapp))
        
    # Mock URLs for the detailed table if they don't exist in raw data
    if 'url' not in df_inapp.columns:
        df_inapp['url'] = "https://didi.com/campaign/" + df_inapp['campaign_id'].astype(str)

    # Add dummy Country column for the filter functionality
    df_inapp['country'] = 'Australia' 
    df_inapp.loc[df_inapp['city_name'] == 'Auckland', 'country'] = 'New Zealand'
    
    # --- Load Promo Data ---
    df_promo = pd.read_excel(promo_file, sheet_name="Reporting Data")
    df_promo['date'] = pd.to_datetime(df_promo['date'])
    df_promo['country'] = 'Australia'

    # --- Load Communication Data (if exists, else mock for PoC) ---
    if os.path.exists(comm_file):
        df_comm = pd.read_excel(comm_file)
    else:
        # Mock communication data for PoC if file is missing/empty
        df_comm = pd.DataFrame({
            'date': pd.date_range(start='2026-05-01', periods=30, freq='D'),
            'push_title': ['[Alert] Ride Now!'] * 30,
            'sends': np.random.randint(5000, 20000, size=30),
            'opens': np.random.randint(1000, 5000, size=30)
        })
        df_comm['open_rate'] = df_comm['opens'] / df_comm['sends']
        
    return df_inapp, df_promo, df_comm

try:
    df_inapp, df_promo, df_comm = load_data()
    
    # ==========================================
    # 3. Advanced Sidebar Filters
    # ==========================================
    st.sidebar.title("🔍 Filter Panel")
    
    # Country & City Selectors
    countries = sorted(df_inapp['country'].dropna().unique().tolist())
    selected_countries = st.sidebar.multiselect("Select Country", countries, default=countries)
    
    # Filter cities based on selected country
    available_cities = sorted(df_inapp[df_inapp['country'].isin(selected_countries)]['city_name'].dropna().unique().tolist())
    selected_cities = st.sidebar.multiselect("Select City", available_cities, default=available_cities)
    
    # Date Range
    min_date = df_inapp['pt'].min().date()
    max_date = df_inapp['pt'].max().date()
    date_range = st.sidebar.date_input("Date Range", [min_date, max_date])
    
    # Advanced: Text Search & Numeric Filters
    st.sidebar.markdown("**Advanced Criteria**")
    name_include = st.sidebar.text_input("Name Include (Campaign/Promo)", placeholder="e.g. BNE, SAFE...")
    min_shows = st.sidebar.number_input("Minimum Shows (#)", min_value=0, value=0, step=100)
    
    # ==========================================
    # 4. Apply Filters Logic
    # ==========================================
    if len(date_range) == 2:
        start_d, end_d = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
        
        # In-App Filter
        mask_inapp = (
            (df_inapp['pt'] >= start_d) & (df_inapp['pt'] <= end_d) &
            (df_inapp['country'].isin(selected_countries)) &
            (df_inapp['city_name'].isin(selected_cities)) &
            (df_inapp['show_pv'] >= min_shows)
        )
        if name_include:
            mask_inapp = mask_inapp & (df_inapp['campaign_name'].str.contains(name_include, case=False, na=False))
        f_inapp = df_inapp.loc[mask_inapp]
        
        # Promo Filter
        mask_promo = (
            (df_promo['date'] >= start_d) & (df_promo['date'] <= end_d) &
            (df_promo['country'].isin(selected_countries))
        )
        if 'city_name' in df_promo.columns:
            mask_promo = mask_promo & (df_promo['city_name'].isin(selected_cities))
        if name_include:
            mask_promo = mask_promo & (df_promo['promocode'].str.contains(name_include, case=False, na=False))
        f_promo = df_promo.loc[mask_promo]
    else:
        f_inapp, f_promo = df_inapp, df_promo

    # ==========================================
    # 5. Dashboard Main Content & Tabs
    # ==========================================
    st.title("🚗 Campaign Tracking Dashboard")
    
    # High-level KPI Banner
    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("Total Shows (In-App)", f"{f_inapp['show_pv'].sum():,.0f}")
    kpi2.metric("Total Clicks (In-App)", f"{f_inapp['click_pv'].sum():,.0f}")
    kpi3.metric("Total Promos Redeemed", f"{f_promo['redemption_count'].sum():,.0f}")
    st.markdown("---")
    
    # Define Tabs
    tab_inapp, tab_promo, tab_comm = st.tabs(["In-App Ads", "Promo Code", "Communication (Push/Email)"])
    
    # ---------------- TAB 1: IN-APP ADS ----------------
    with tab_inapp:
        st.subheader("Campaign Leaderboard (Volume vs CTR %)")
        
        # Leaderboard Data Preparation
        leaderboard_df = f_inapp.groupby('campaign_name').agg({'show_pv': 'sum', 'click_pv': 'sum'}).reset_index()
        leaderboard_df['ctr'] = (leaderboard_df['click_pv'] / leaderboard_df['show_pv'] * 100).fillna(0)
        leaderboard_df = leaderboard_df.sort_values(by='show_pv', ascending=True).tail(15) # Top 15
        
        # Dual-Axis Plotly Chart
        fig_leaderboard = go.Figure()
        # Bar chart for Shows
        fig_leaderboard.add_trace(go.Bar(
            y=leaderboard_df['campaign_name'], x=leaderboard_df['show_pv'],
            name='Shows #', orientation='h', marker_color='#4C72B0'
        ))
        # Scatter markers for CTR
        fig_leaderboard.add_trace(go.Scatter(
            y=leaderboard_df['campaign_name'], x=leaderboard_df['ctr'],
            name='CTR %', mode='markers', xaxis='x2',
            marker=dict(color='#C44E52', size=10, symbol='circle')
        ))
        # Update layout for Dual Axis
        fig_leaderboard.update_layout(
            barmode='group', height=500,
            xaxis=dict(title='Shows #', showgrid=False),
            xaxis2=dict(title='CTR %', overlaying='x', side='top', showgrid=True, range=[0, max(leaderboard_df['ctr'])+2]),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_leaderboard, use_container_width=True)

        st.markdown("---")
        
        # Heatmap Section
        st.subheader("Engagement Heatmap (Day of Week vs Hour)")
        heatmap_data = f_inapp.pivot_table(index='day_of_week', columns='hour_of_day', values='show_pv', aggfunc='sum').fillna(0)
        days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        heatmap_data = heatmap_data.reindex([d for d in days_order if d in heatmap_data.index])
        
        fig_heatmap = px.imshow(
            heatmap_data, 
            labels=dict(x="Hour of Day", y="Day of Week", color="Shows #"),
            aspect="auto", color_continuous_scale='YlOrRd'
        )
        st.plotly_chart(fig_heatmap, use_container_width=True)

    # ---------------- TAB 2: PROMO CODE ----------------
    with tab_promo:
        st.subheader("Redemption vs Usage by Promocode")
        promo_agg = f_promo.groupby('promocode')[['redemption_count', 'usage_count']].sum().reset_index()
        fig_promo = px.bar(promo_agg, x='promocode', y=['redemption_count', 'usage_count'], barmode='group',
                           labels={'value': 'Volume', 'promocode': 'Code Name', 'variable': 'Action'})
        st.plotly_chart(fig_promo, use_container_width=True)

    # ---------------- TAB 3: COMMUNICATION ----------------
    with tab_comm:
        st.subheader("Push Notification Performance")
        if not df_comm.empty and 'sends' in df_comm.columns:
            comm_agg = df_comm.groupby('date')[['sends', 'opens']].sum().reset_index()
            fig_comm = px.line(comm_agg, x='date', y=['sends', 'opens'], markers=True,
                               labels={'value': 'Volume', 'date': 'Date', 'variable': 'Metric'})
            st.plotly_chart(fig_comm, use_container_width=True)
        else:
            st.info("Communication data loaded but waiting for column mapping.")

    # ==========================================
    # 6. Detailed Data View with Clickable URLs
    # ==========================================
    st.markdown("---")
    st.subheader("📋 Detailed Data View")
    st.markdown("Review record-level data. Click on the URLs directly to preview the creatives.")
    
    # Configure the dataframe columns to make the URL clickable
    st.dataframe(
        f_inapp[['pt', 'city_name', 'campaign_name', 'show_pv', 'click_pv', 'url']],
        column_config={
            "pt": st.column_config.DatetimeColumn("Date Time", format="YYYY-MM-DD"),
            "city_name": "City",
            "campaign_name": "Campaign Name",
            "show_pv": "View (PV)",
            "click_pv": "Click (PV)",
            "url": st.column_config.LinkColumn("Creative URL", display_text="Open Link")
        },
        use_container_width=True,
        hide_index=True
    )

except Exception as err:
    st.error(f"Error rendering dashboard: {err}")
