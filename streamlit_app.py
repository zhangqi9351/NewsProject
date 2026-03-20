import streamlit as st
import yaml
import pandas as pd
from streamlit_gsheets import GSheetsConnection


from modules.data_manager import DataManager
from ui.components import (
    render_header, 
    render_sidebar, 
    render_sidebar_navigation, 
    render_daily_dashboard
)

# 页面基础配置
st.set_page_config(page_title="游戏情报自动化站", layout="wide", page_icon="🎮")

def load_config():
    try:
        with open('config.yaml', 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception:
        st.error("❌ 配置文件读取失败")
        st.stop()

config = load_config()
conn = st.connection("gsheets", type=GSheetsConnection)
dm = DataManager(conn)

# 1. 侧边栏：放置抓取按钮和基础信息
render_sidebar(config, dm)

# 2. 读取所有数据并处理日期
history_data = dm.get_all_articles()
df_history = pd.DataFrame(history_data)

if not df_history.empty and 'crawl_date' in df_history.columns:
    df_history['crawl_date'] = pd.to_datetime(df_history['crawl_date'])

# 3. 侧边栏：日期选择器
selected_date = render_sidebar_navigation(df_history)

# 4. 主界面渲染
render_header()

# 如果用户没点日期，默认显示最新的一天
if not selected_date and not df_history.empty:
    selected_date = df_history['crawl_date'].dt.date.max().strftime('%Y-%m-%d')

if selected_date:
    api_key = st.secrets.get("GEMINI_API_KEY")
    # 直接调用看板渲染，不再使用 Tab
    render_daily_dashboard(df_history, selected_date, api_key, dm)
else:
    st.info("👈 请点击左侧“执行全网抓取”获取首批情报。")