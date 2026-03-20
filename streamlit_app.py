import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from modules.data_manager import DataManager
from ui.components import render_header, render_sidebar, render_sidebar_navigation, render_daily_dashboard

# 1. 页面基础配置
st.set_page_config(page_title="游戏情报自动化站", layout="wide", page_icon="🎮")

# 2. 初始化连接与数据管理器
conn = st.connection("gsheets", type=GSheetsConnection)
dm = DataManager(conn)

# 3. 渲染侧边栏（注意：现在只传入 dm 一个参数）
render_sidebar(dm)

# 4. 获取历史文章数据
try:
    history_data = dm.get_all_articles(show_errors=True)
except Exception as e:
    st.error(f"初始化文章数据失败，已回退为空列表: {type(e).__name__}: {e}")
    history_data = []

df_history = pd.DataFrame(history_data)

# 5. 处理日期逻辑
if not df_history.empty and 'crawl_date' in df_history.columns:
    df_history['crawl_date'] = pd.to_datetime(df_history['crawl_date'])
    selected_date = render_sidebar_navigation(df_history)
else:
    selected_date = None

# 6. 主界面头部渲染
render_header()

# 7. 确定当前显示的日期内容
if not selected_date and not df_history.empty:
    selected_date = df_history['crawl_date'].dt.date.max().strftime('%Y-%m-%d')

# 8. 执行主看板渲染
if selected_date:
    api_key = st.secrets.get("GEMINI_API_KEY")
    render_daily_dashboard(df_history, selected_date, api_key, dm)
else:
    st.info("👈 请点击左侧按钮开始抓取情报。")
