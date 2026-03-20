import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from modules.data_manager import DataManager
from ui.components import render_header, render_sidebar, render_sidebar_navigation, render_daily_dashboard

st.set_page_config(page_title="游戏情报自动化站", layout="wide", page_icon="🎮")

# 初始化连接
conn = st.connection("gsheets", type=GSheetsConnection)
dm = DataManager(conn)

# 侧边栏渲染（修正了传参，只传入 dm）
render_sidebar(dm)

# 数据加载与处理
history_data = dm.get_all_articles()
df_history = pd.DataFrame(history_data)

# 日期导航
selected_date = render_sidebar_navigation(df_history)
render_header()

if not selected_date and not df_history.empty:
    selected_date = df_history['crawl_date'].dt.date.max().strftime('%Y-%m-%d')

if selected_date:
    api_key = st.secrets.get("GEMINI_API_KEY")
    render_daily_dashboard(df_history, selected_date, api_key, dm)
else:
    st.info("👈 请点击左侧按钮执行全网抓取。")