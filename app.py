import streamlit as st
import plotly.express as px

# --- 假設你的資料處理與圖表 (fig_daily_comm, fig_daily_ctr 等) 已經在程式碼上半部定義好了 ---
# 例如: fig_daily_comm = px.line(...)

# 1. 初始化 Streamlit 頁面設定 (必須放在所有 st 指令的最前面)
st.set_page_config(page_title="Didi Marketing Performance Dashboard", layout="wide")

# ==========================================
# 標題區塊
# ==========================================
st.title('🚗 Didi Marketing Performance Dashboard')

# ==========================================
# 區塊 1: Communication Performance
# ==========================================
st.header('Communication Performance')
st.markdown('*Key metrics for in-app and communication campaigns.*')

# 使用 st.columns 建立左右並排的雙欄排版
col1, col2 = st.columns(2)

with col1:
    st.subheader('Daily Shows and Clicks')
    # st.plotly_chart 專門用來在 Streamlit 顯示 Plotly 的圖表
    # 請確保 fig_daily_comm 已經存在
    st.plotly_chart(fig_daily_comm, use_container_width=True)

with col2:
    st.subheader('Daily Click-Through Rate (CTR)')
    st.plotly_chart(fig_daily_ctr, use_container_width=True)

# 建立第二排的雙欄
col3, col4 = st.columns(2)

with col3:
    st.subheader('Top 10 Campaigns by Clicks')
    st.plotly_chart(fig_top_campaigns, use_container_width=True)

with col4:
    st.subheader('Clicks by Day of Week and Hour')
    st.plotly_chart(fig_heatmap, use_container_width=True)

st.markdown("---") # 畫一條分隔線

# ==========================================
# 區塊 2: Promocode Performance
# ==========================================
st.header('Promocode Performance')
st.markdown('*Analysis of promocode redemptions and usages across cities.*')

# 建立第三排的雙欄
col5, col6 = st.columns(2)

with col5:
    st.subheader('Daily Promocode Redemptions and Usages')
    st.plotly_chart(fig_daily_promo, use_container_width=True)

with col6:
    st.subheader('Top 10 Promocodes by Usage')
    st.plotly_chart(fig_top_promocodes, use_container_width=True)

# 最後一個圖表占滿全寬
st.subheader('Promocode Redemptions and Usages by City')
st.plotly_chart(fig_city_promo, use_container_width=True)
