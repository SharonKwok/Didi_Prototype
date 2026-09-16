# 1. 安裝建置 Dashboard 必要的套件
!pip install dash pandas openpyxl plotly -q

import pandas as pd
import plotly.express as px
from dash import Dash, html, dcc

print("正在讀取資料與建置儀表板，請稍候...")

# 2. 讀取並清理資料
# 讀取促銷成效資料
df_promo = pd.read_excel("Promocode_Performance.xlsx", sheet_name="Reporting Data")
df_promo['date'] = pd.to_datetime(df_promo['date'])
df_promo['Day of Week'] = df_promo['date'].dt.day_name() # 提取星期幾供熱力圖使用

# 讀取 App 內廣告資料
df_in_app = pd.read_excel("in_app_analytical_dataset_validated.xlsx", sheet_name="Raw Data")
df_in_app['pt'] = pd.to_datetime(df_in_app['pt'])

# 3. 準備學術級視覺化圖表 (對應你的論文設計)

# [圖表 A: Line Chart] - 趨勢追蹤 (Trend over time)
# 計算每日總核銷與使用量
trend_data = df_promo.groupby('date')[['redemption_count', 'usage_count']].sum().reset_index()
fig_line = px.line(trend_data, x='date', y=['redemption_count', 'usage_count'], 
                   title='1. Campaign Performance Trend (Line Chart)',
                   labels={'value': 'Count', 'date': 'Date', 'variable': 'Metrics'},
                   markers=True)

# [圖表 B: Bar Chart] - 類別比較 (Categorical comparison)
# 比較各城市的總核銷量
bar_data = df_promo.groupby('city_name')['redemption_count'].sum().reset_index().sort_values(by='redemption_count', ascending=False)
fig_bar = px.bar(bar_data, x='city_name', y='redemption_count', 
                 title='2. Redemptions by City (Bar Chart)',
                 labels={'city_name': 'City', 'redemption_count': 'Total Redemptions'},
                 color='city_name')

# [圖表 C: Heatmap] - 高峰期偵測 (Peak periods)
# 建立 城市 vs 星期幾 的使用量矩陣
heat_data = df_promo.pivot_table(index='Day of Week', columns='city_name', values='usage_count', aggfunc='sum').fillna(0)
# 確保星期排序正確
days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
heat_data = heat_data.reindex(days_order)
fig_heat = px.imshow(heat_data, 
                     title='3. Peak Usage Periods by City (Heatmap)',
                     labels=dict(x="City", y="Day of Week", color="Usage Count"),
                     aspect="auto", color_continuous_scale='Blues')

# 4. 使用 Dash 建立儀表板介面
app = Dash(__name__)

app.layout = html.Div(style={'fontFamily': 'Arial, sans-serif', 'padding': '20px'}, children=[
    html.H1("DiDi Promotional Campaign Dashboard", style={'textAlign': 'center', 'color': '#FF5722'}),
    html.P("Empowering decision-makers with tailored visualisations (Popovič et al., 2012).", style={'textAlign': 'center', 'fontStyle': 'italic'}),
    
    html.Hr(),
    
    # 圖表排版：上方放折線圖，下方並排長條圖與熱力圖
    html.Div([
        dcc.Graph(figure=fig_line)
    ], style={'width': '100%', 'display': 'inline-block', 'paddingBottom': '20px'}),
    
    html.Div([
        html.Div([dcc.Graph(figure=fig_bar)], style={'width': '48%', 'display': 'inline-block'}),
        html.Div([dcc.Graph(figure=fig_heat)], style={'width': '48%', 'display': 'inline-block', 'float': 'right'})
    ])
])

# 5. 在 Colab 內嵌顯示儀表板
if __name__ == '__main__':
    app.run(jupyter_mode="inline", port=8050)
