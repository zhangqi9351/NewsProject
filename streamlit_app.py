import streamlit as st
import yaml
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# 1. 导入你自定义的逻辑模块 (确保这些文件在 modules 文件夹下)
from modules.data_manager import DataManager
from modules.scraper import fetch_all_rss
from modules.analyzer import ai_batch_filter
from modules.notifier import send_feishu_message

# 2. 导入你自定义的 UI 模块 (确保这个文件在 ui 文件夹下)
from ui.components import (
    render_header, 
    render_sidebar, 
    render_sidebar_navigation, 
    render_daily_dashboard
)

# --- A. 基础配置加载 ---
st.set_page_config(page_title="游戏情报自动化站", layout="wide", page_icon="🎮")

def load_config():
    with open('config.yaml', 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

config = load_config()

# --- B. 初始化后端连接 ---
# 这里会自动读取你在 Streamlit Cloud 设置的 Secrets
conn = st.connection("gsheets", type=GSheetsConnection)
dm = DataManager(conn)

# --- C. 侧边栏导航部分 ---
# 先渲染原有的基础配置信息
render_sidebar(config)

# 获取所有历史数据用于生成日期列表
history_data = dm.get_all_articles()
df_history = pd.DataFrame(history_data)

# 转换日期格式，确保排序正确
if not df_history.empty and 'crawl_date' in df_history.columns:
    df_history['crawl_date'] = pd.to_datetime(df_history['crawl_date'])

# 在侧边栏渲染日期选择器，并获取用户点击的日期
selected_date = render_sidebar_navigation(df_history)

# --- D. 主界面布局 ---
render_header()

# 使用 Tabs 将“新数据同步”和“历史看板”分开
tab_sync, tab_board = st.tabs(["🚀 开启同步", "📊 情报看板"])

with tab_sync:
    st.subheader("今日数据自动化")
    if st.button("开始执行全自动化任务", use_container_width=True):
        with st.status("正在工作...", expanded=True) as status:
            # 1. 抓取
            st.write("📡 正在采集 RSS...")
            raw_data = fetch_all_rss(config['rss_sources'])
            
            # 2. 去重
            seen_links = dm.get_seen_links()
            new_items = [item for item in raw_data if item['link'] not in seen_links]
            
            if not new_items:
                status.update(label="没有发现新资讯", state="complete")
                st.info("库中已是最新，无需更新。")
            else:
                # 3. AI 筛选
                st.write(f"🧠 发现 {len(new_items)} 条新资讯，正在 AI 筛选...")
                final_list = ai_batch_filter(new_items, config['gemini_api_key'], config.get('ai_prompt', ""))
                
                # 4. 存储与推送
                if final_list:
                    dm.save_new_articles(final_list)
                    # 发送飞书
                    if config.get('feishu_webhook'):
                        msg = f"✅ 今日精选 ({len(final_list)}条):\n" + "\n".join([f"- {a['title']}" for a in final_list])
                        send_feishu_message(config['feishu_webhook'], msg)
                    
                    status.update(label="任务成功完成！", state="complete")
                    st.success(f"已更新 {len(final_list)} 条精选情报！请切换到『情报看板』查看。")
                else:
                    status.update(label="筛选结束", state="complete")
                    st.warning("新资讯未通过 AI 筛选条件。")

with tab_board:
    # 根据侧边栏选中的日期，显示对应的卡片内容
    if selected_date:
        render_daily_dashboard(df_history, selected_date)
    else:
        st.info("👈 请在左侧边栏选择一个日期来查看资讯。")