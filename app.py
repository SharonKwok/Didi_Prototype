import streamlit as st
import pandas as pd
import plotly.express as px

# 1. 設置網頁標題與版面寬度
st.set_page_config(page_title="DiDi Promotional Dashboard", layout="wide")

st.title("🚗 DiDi Promotional Campaign Dashboard")
st.markdown("*Serving as a user-centred decision-support platform that empowers teams (Popovič et al., 2012).*")
st.markdown("---")

# 2. 讀取並清理資料 (使用 @st.cache_data 讓網頁載入更快)
@st.cache_data
def load_data():
    # 讀取 Promo 資料
    df_promo = pd.read_excel("Promocode_Performance.xlsx", sheet_name="Reporting Data")
    df_promo['date'] = pd.to_datetime(df_promo['date'])
    df_promo['Day of Week'] = df_promo['date'].dt.day_name()
    return df_promo

try:
    df_promo = load_data()
    
    # 3. 準備學術級視覺化圖表
    
    # [圖表 A: Line Chart] - 跨滿整個螢幕寬度
    st.subheader("📈 1. Campaign Performance Trend")
    st.markdown("Utilising line charts to track performance trends over time.")
    
    trend_data = df_promo.groupby('date')[['redemption_count', 'usage_count']].sum().reset_index()
    fig_line = px.line(trend_data, x='date', y=['redemption_count', 'usage_count'], 
                       labels={'value': 'Count', 'date': 'Date', 'variable': 'Metrics'},
                       markers=True)
    # 在 Streamlit 中顯示 Plotly 圖表
    st.plotly_chart(fig_line, use_container_width=True)
    
    st.markdown("---")
    
    # 將畫面切分成左右兩欄，放置 Bar Chart 與 Heatmap
    col1, col2 = st.columns(2)
    
    # [圖表 B: Bar Chart] - 放在左欄
    with col1:
        st.subheader("📊 2. Redemptions by City")
        st.markdown("Bar charts to compare conversion rates across categories.")
        
        bar_data = df_promo.groupby('city_name')['redemption_count'].sum().reset_index().sort_values(by='redemption_count', ascending=False)
        fig_bar = px.bar(bar_data, x='city_name', y='redemption_count', 
                         labels={'city_name': 'City', 'redemption_count': 'Total Redemptions'},
                         color='city_name')
        st.plotly_chart(fig_bar, use_container_width=True)

    # [圖表 C: Heatmap] - 放在右欄
    with col2:
        st.subheader("🗺️ 3. Peak Usage Periods")
        st.markdown("Heatmaps to pinpoint peak redemption periods.")
        
        heat_data = df_promo.pivot_table(index='Day of Week', columns='city_name', values='usage_count', aggfunc='sum').fillna(0)
        days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        heat_data = heat_data.reindex(days_order)
        fig_heat = px.imshow(heat_data, 
                             labels=dict(x="City", y="Day of Week", color="Usage Count"),
                             aspect="auto", color_continuous_scale='Blues')
        st.plotly_chart(fig_heat, use_container_width=True)

except Exception as e:
    st.error(f"⚠️ 資料讀取失敗，請確認 'Promocode_Performance.xlsx' 檔案與 app.py 放在同一個資料夾下。詳細錯誤: {e}")
