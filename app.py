import os
import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Page Configuration
st.set_page_config(page_title="DiDi Marketing Performance Dashboard", layout="wide")

# 2. Data Loading and Preprocessing
@st.cache_data
def load_data():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    inapp_file = os.path.join(base_dir, "in_app_analytical_dataset_validated.xlsx")
    promo_file = os.path.join(base_dir, "Promocode_Performance.xlsx")
    comm_file = os.path.join(base_dir, "Communication.xlsx")
    
    # Load In-App Campaign Performance Data
    df_inapp = pd.read_excel(inapp_file, sheet_name="Raw Data")
    df_inapp['pt'] = pd.to_datetime(df_inapp['pt'])
    df_inapp['day_of_week'] = df_inapp['pt'].dt.day_name()
    
    # Load Promocode Performance Data
    df_promo = pd.read_excel(promo_file, sheet_name="Reporting Data")
    df_promo['date'] = pd.to_datetime(df_promo['date'])
    df_promo['day_of_week'] = df_promo['date'].dt.day_name()
    
    # Check for optional Communication dataset
    df_comm = None
    if os.path.exists(comm_file):
        try:
            df_comm = pd.read_excel(comm_file)
        except Exception:
            df_comm = None
            
    return df_inapp, df_promo, df_comm

try:
    df_inapp, df_promo, df_comm = load_data()

    # 3. Chart Generation

    # Chart 1: Daily Shows and Clicks
    daily_comm = df_inapp.groupby('pt')[['show_pv', 'click_pv']].sum().reset_index()
    fig_daily_comm = px.line(
        daily_comm, 
        x='pt', 
        y=['show_pv', 'click_pv'], 
        labels={'value': 'Volume', 'pt': 'Date', 'variable': 'Metric'},
        markers=True
    )

    # Chart 2: Daily Click-Through Rate (CTR)
    daily_comm['ctr'] = (daily_comm['click_pv'] / daily_comm['show_pv'] * 100).fillna(0)
    fig_daily_ctr = px.line(
        daily_comm, 
        x='pt', 
        y='ctr', 
        labels={'ctr': 'CTR (%)', 'pt': 'Date'},
        markers=True
    )

    # Chart 3: Top 10 Campaigns by Clicks
    top_campaigns = (
        df_inapp.groupby('campaign_name')['click_pv']
        .sum()
        .reset_index()
        .sort_values(by='click_pv', ascending=True)
        .tail(10)
    )
    fig_top_campaigns = px.bar(
        top_campaigns, 
        x='click_pv', 
        y='campaign_name', 
        orientation='h',
        labels={'click_pv': 'Total Clicks', 'campaign_name': 'Campaign'}
    )

    # Chart 4: Heatmap (Clicks by Day of Week and City)
    heat_data = df_inapp.pivot_table(
        index='day_of_week', 
        columns='city_name', 
        values='click_pv', 
        aggfunc='sum'
    ).fillna(0)
    days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    heat_data = heat_data.reindex([d for d in days_order if d in heat_data.index])
    fig_heatmap = px.imshow(
        heat_data, 
        labels=dict(x="City", y="Day of Week", color="Clicks"),
        aspect="auto", 
        color_continuous_scale='Blues'
    )

    # Chart 5: Daily Promocode Redemptions and Usages
    daily_promo = df_promo.groupby('date')[['redemption_count', 'usage_count']].sum().reset_index()
    fig_daily_promo = px.line(
        daily_promo, 
        x='date', 
        y=['redemption_count', 'usage_count'],
        labels={'value': 'Count', 'date': 'Date', 'variable': 'Metric'},
        markers=True
    )

    # Chart 6: Top 10 Promocodes by Usage
    top_promos = (
        df_promo.groupby('promocode')['usage_count']
        .sum()
        .reset_index()
        .sort_values(by='usage_count', ascending=False)
        .head(10)
    )
    fig_top_promocodes = px.bar(
        top_promos, 
        x='promocode', 
        y='usage_count',
        labels={'usage_count': 'Total Usage', 'promocode': 'Promo Code'},
        color='usage_count'
    )

    # Chart 7: Promocode Redemptions and Usages by City
    city_promo = df_promo.groupby('city_name')[['redemption_count', 'usage_count']].sum().reset_index()
    fig_city_promo = px.bar(
        city_promo, 
        x='city_name', 
        y=['redemption_count', 'usage_count'], 
        barmode='group',
        labels={'value': 'Volume', 'city_name': 'City', 'variable': 'Metric'}
    )

    # 4. User Interface and Dashboard Layout
    st.title('🚗 DiDi Marketing Performance Dashboard')
    st.markdown('*Empowering decision-makers with unified analytics (Popovič et al., 2012).*')
    st.markdown('---')

    # Communication Section
    st.header('Communication & In-App Performance')
    st.markdown('Performance metrics evaluating exposure and customer engagement.')

    col1, col2 = st.columns(2)
    with col1:
        st.subheader('Daily Impressions and Clicks')
        st.plotly_chart(fig_daily_comm, use_container_width=True)
    with col2:
        st.subheader('Daily Click-Through Rate (CTR)')
        st.plotly_chart(fig_daily_ctr, use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        st.subheader('Top 10 Campaigns by Clicks')
        st.plotly_chart(fig_top_campaigns, use_container_width=True)
    with col4:
        st.subheader('Engagement Heatmap by Day and City')
        st.plotly_chart(fig_heatmap, use_container_width=True)

    st.markdown('---')

    # Promocode Section
    st.header('Promotional Campaign Performance')
    st.markdown('Analysis of coupon redemptions, actual trip usages, and regional conversion.')

    col5, col6 = st.columns(2)
    with col5:
        st.subheader('Daily Redemptions vs. Usages')
        st.plotly_chart(fig_daily_promo, use_container_width=True)
    with col6:
        st.subheader('Top 10 Promocodes by Usage')
        st.plotly_chart(fig_top_promocodes, use_container_width=True)

    st.subheader('Redemption and Usage Distribution by City')
    st.plotly_chart(fig_city_promo, use_container_width=True)

except Exception as err:
    st.error(f"Error loading datasets or generating visuals. Details: {err}")
