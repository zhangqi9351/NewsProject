import streamlit as st
import yaml
import pandas as pd
from ui.components import render_header, render_sidebar, render_article_card, render_stats_info
from modules.scraper import fetch_all_rss
from streamlit_gsheets import GSheetsConnection
class DataManager:
    def __init__(self, st_connection):
        self.conn = st_connection
# 1. 初始化配置与连接
with open('config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

conn = st.connection("gsheets", type=GSheetsConnection)
dm = DataManager(conn)

# 2. 渲染基础 UI
render_header()
render_sidebar(config)

# 3. 核心功能操作区
if st.button("🚀 开启今日情报自动化同步", use_container_width=True):
    with st.status("正在执行工作流...") as status:
        # --- 调用逻辑层 ---
        raw_data = fetch_all_rss(config['rss_sources'])
        seen_links = dm.get_seen_links()
        new_items = [item for item in raw_data if item['link'] not in seen_links]
        
        # 假设这里经过了关键词筛选
        final_list = [item for item in new_items if any(k in item['title'] for k in config['filter_keywords'])]
        
        if final_list:
            dm.save_new_articles(final_list)
        
        status.update(label="处理完成！", state="complete")

    # --- 调用视图层渲染结果 ---
    render_stats_info(len(raw_data), len(final_list))
    for art in final_list:
        render_article_card(art, expanded=True)

# 4. 历史数据展示区
st.divider()
st.subheader("📜 历史情报回顾")
history_data = dm.get_all_articles()
if history_data:
    df = pd.DataFrame(history_data)
    df['crawl_date'] = pd.to_datetime(df['crawl_date'])
    # 调用专门的渲染函数
    # render_history_view(df)