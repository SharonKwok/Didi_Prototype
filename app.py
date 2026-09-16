import os
import streamlit as st
import pandas as pd
import plotly.express as px

# ==========================================
# 1. Page Configuration & Layout
# ==========================================
st.set_page_config(page_title="DiDi Unified Campaign Dashboard", layout="wide", initial_sidebar_state="expanded")

# ==========================================
# 2. Data Loading (Simulating the Database)
# ==========================================
@st.cache_data
def load_data():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    inapp_file = os.path.join(base_dir, "in_app_analytical_dataset_validated.xlsx")
    promo_file = os.path.join(base_dir, "Promocode_Performance.xlsx")
    
    # Load In-App Data
    df_inapp = pd.read_excel(inapp_file, sheet_name="Raw Data")
    df_inapp['pt'] = pd.to_datetime(df_inapp['pt'])
    df_inapp['day_of_week'] = df_inapp['pt'].dt.day_name()
    
    # Load Promo Data
    df_promo = pd.read_excel(promo_file, sheet_name="Reporting Data")
    df_promo['date'] = pd.to_datetime(df_promo['date'])
    
    return df_inapp, df_promo

try:
    df_inapp, df_promo = load_data()
    
    # ==========================================
    # 3. Global Sidebar (Solves Cross-Tab Correlation Issue)
    # ==========================================
    st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/cc/DiDi_logo.svg/512px-DiDi_logo.svg.png", width=100)
    st.sidebar.title("Global Filters")
    st.sidebar.markdown("Filters apply across *all* channels.")
    
    # Date Filter
    min_date = min(df_inapp['pt'].min(), df_promo['date'].min()).date()
    max_date = max(df_inapp['pt'].max(), df_promo['date'].max()).date()
    date_range = st.sidebar.date_input("Select Date Range", [min_date, max_date])
    
    # City Filter
    all_cities = sorted(list(set(df_inapp['city_name'].dropna()) | set(df_promo['city_name'].dropna())))
    selected_cities = st.sidebar.multiselect("Select Cities", all_cities, default=all_cities)
    
    # AI Query Assistant (Simulated Feature for Client Pitch)
    st.sidebar.markdown("---")
    st.sidebar.subheader("🤖 DiDi AI Copilot")
    ai_query = st.sidebar.chat_input("E.g., 'Why did Brisbane drop last week?'")
    if ai_query:
        st.sidebar.success(f"AI Insight: Scanning data for '{ai_query}'... (Feature in development)")

    # ==========================================
    # 4. Apply Filters to Dataframes
    # ==========================================
    if len(date_range) == 2:
        start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
        
        # Filter In-App
        mask_inapp = (df_inapp['pt'] >= start_date) & (df_inapp['pt'] <= end_date) & (df_inapp['city_name'].isin(selected_cities))
        filtered_inapp = df_inapp.loc[mask_inapp]
        
        # Filter Promo
        mask_promo = (df_promo['date'] >= start_date) & (df_promo['date'] <= end_date) & (df_promo['city_name'].isin(selected_cities))
        filtered_promo = df_promo.loc[mask_promo]
    else:
        filtered_inapp, filtered_promo = df_inapp, df_promo

    # ==========================================
    # 5. Main Dashboard UI (Tabs Structure)
    # ==========================================
    st.title("Unified Campaign Tracking Framework")
    st.markdown("Addressing structural data silos and tracking cross-channel performance.")
    
    # Create Native Streamlit Tabs matching the client's needs
    tab_overview, tab_quadrant, tab_inapp, tab_promo = st.tabs([
        "Executive Overview", 
        "Quadrant Analysis", 
        "In-App Ads", 
        "Promo Codes"
    ])

    # --- TAB 1: EXECUTIVE OVERVIEW (For Senior Staff - Low Cognitive Load) ---
    with tab_overview:
        st.subheader("Top-Level Metrics")
        col1, col2, col3, col4 = st.columns(4)
        
        total_shows = filtered_inapp['show_pv'].sum()
        total_clicks = filtered_inapp['click_pv'].sum()
        avg_ctr = (total_clicks / total_shows * 100) if total_shows > 0 else 0
        total_redemptions = filtered_promo['redemption_count'].sum()
        total_usage = filtered_promo['usage_count'].sum()
        conversion_rate = (total_usage / total_redemptions * 100) if total_redemptions > 0 else 0
        
        col1.metric("Total Impressions", f"{total_shows:,.0f}")
        col2.metric("Overall CTR", f"{avg_ctr:.2f}%")
        col3.metric("Promo Redemptions", f"{total_redemptions:,.0f}")
        col4.metric("Ride Conversion (Usage)", f"{conversion_rate:.1f}%")
        
        st.markdown("---")
        # High-level trend combining both channels
        st.subheader("Cross-Channel Performance Trend")
        trend_inapp = filtered_inapp.groupby('pt')['show_pv'].sum().reset_index().rename(columns={'pt': 'Date', 'show_pv': 'Impressions'})
        trend_promo = filtered_promo.groupby('date')['usage_count'].sum().reset_index().rename(columns={'date': 'Date', 'usage_count': 'Actual Rides'})
        combined_trend = pd.merge(trend_inapp, trend_promo, on='Date', how='outer').fillna(0)
        
        fig_combined = px.line(combined_trend, x='Date', y=['Impressions', 'Actual Rides'], markers=True)
        st.plotly_chart(fig_combined, use_container_width=True)

    # --- TAB 2: QUADRANT ANALYSIS (Spotting "Hidden Gems") ---
    with tab_quadrant:
        st.subheader("Campaign Quadrant Analysis (Exposure vs. Efficiency)")
        st.markdown("Identify **Top Performers** (High Exposure, High CTR) and **Hidden Gems** (Low Exposure, High CTR).")
        
        quad_data = filtered_inapp.groupby('campaign_name').agg({'show_pv':'sum', 'click_pv':'sum'}).reset_index()
        quad_data['CTR'] = (quad_data['click_pv'] / quad_data['show_pv'] * 100).fillna(0)
        
        # Calculate Medians for the crosshairs
        median_shows = quad_data['show_pv'].median()
        median_ctr = quad_data['CTR'].median()
        
        fig_quad = px.scatter(
            quad_data, x='show_pv', y='CTR', color='campaign_name', size='click_pv',
            hover_name='campaign_name', labels={'show_pv': 'Total Impressions (Exposure)', 'CTR': 'Click-Through Rate (%)'},
            title="Campaign Efficiency Matrix"
        )
        # Add Quadrant Crosshairs
        fig_quad.add_hline(y=median_ctr, line_dash="dot", line_color="red")
        fig_quad.add_vline(x=median_shows, line_dash="dot", line_color="red")
        
        st.plotly_chart(fig_quad, use_container_width=True)

    # --- TAB 3: IN-APP ADS DETAILED ---
    with tab_inapp:
        st.subheader("In-App Advertising Performance")
        
        col_in1, col_in2 = st.columns(2)
        with col_in1:
            daily_inapp = filtered_inapp.groupby('pt')[['show_pv', 'click_pv']].sum().reset_index()
            fig_daily_inapp = px.line(daily_inapp, x='pt', y=['show_pv', 'click_pv'], title="Daily Shows vs Clicks")
            st.plotly_chart(fig_daily_inapp, use_container_width=True)
            
        with col_in2:
            top_camps = filtered_inapp.groupby('campaign_name')['click_pv'].sum().reset_index().sort_values(by='click_pv', ascending=False)
            fig_top_camps = px.bar(top_camps, x='click_pv', y='campaign_name', orientation='h', title="Top Campaigns by Clicks")
            st.plotly_chart(fig_top_camps, use_container_width=True)

    # --- TAB 4: PROMO CODES (Redemption vs Usage Funnel) ---
    with tab_promo:
        st.subheader("Promocode Conversion Tracking")
        st.markdown("*Tracking the gap between claiming a code (Redemption) and taking a ride (Usage).*")
        
        city_promo = filtered_promo.groupby('city_name')[['redemption_count', 'usage_count']].sum().reset_index()
        fig_funnel = px.bar(
            city_promo, x='city_name', y=['redemption_count', 'usage_count'], barmode='group',
            labels={'value': 'Volume', 'city_name': 'City', 'variable': 'Action'},
            title="Redemption vs. Actual Ride Usage by City"
        )
        st.plotly_chart(fig_funnel, use_container_width=True)

except Exception as err:
    st.error(f"Error initializing prototype. Please ensure data files are in the repository. Details: {err}")
