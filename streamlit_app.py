import streamlit as st
import yaml
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# 导入自定义模块 (逻辑层)
from modules.data_manager import DataManager
from modules.scraper import fetch_all_rss
from modules.analyzer import ai_batch_filter
from modules.notifier import send_feishu_message

# 导入 UI 组件 (视图层)
from ui.components import (
    render_header, 
    render_sidebar, 
    render_stats_info, 
    render_article_card,
    render_history_view
)

# --- 1. 初始化配置 ---
def load_config():
    with open('config.yaml', 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

config = load_config()

# --- 2. 页面基础设置 ---
st.set_page_config(page_title="游戏情报自动化站", layout="wide", page_icon="🎮")

# --- 3. 初始化后端连接 ---
# 建立 Google Sheets 连接并注入 DataManager
conn = st.connection("gsheets", type=GSheetsConnection)
dm = DataManager(conn)

# --- 4. 渲染 UI 静态部分 ---
render_header()
render_sidebar(config)

# --- 5. 主功能逻辑区 ---
st.subheader("核心控制台")
if st.button("🚀 执行全自动化同步 (抓取 + AI 筛选 + 存储 + 推送)", use_container_width=True):
    # 使用 st.status 展示逻辑执行过程，但不污染主 UI 代码
    with st.status("正在执行工作流...", expanded=True) as status:
        
        # 步骤 1: 抓取原始数据
        st.write("📡 正在从全球 RSS 源采集资讯...")
        raw_articles = fetch_all_rss(config['rss_sources'])
        
        # 步骤 2: 去重过滤
        st.write("🔍 正在比对数据库去重...")
        seen_links = dm.get_seen_links()
        new_items = [a for a in raw_articles if a['link'] not in seen_links]
        
        st.write(f"📦 采集到 {len(raw_articles)} 条，其中新资讯 {len(new_items)} 条。")
        
        if not new_items:
            status.update(label="未发现新资讯，任务结束。", state="complete")
            st.info("所有采集到的内容在数据库中已存在。")
        else:
            # 步骤 3: AI 筛选 (如果 config 开启)
            if config.get('use_ai'):
                st.write("🧠 正在调用 Gemini AI 进行深度价值判定...")
                final_list = ai_batch_filter(new_items, config['gemini_api_key'], config.get('ai_prompt', ""))
            else:
                st.write("🔍 正在进行关键词匹配筛选...")
                keywords = config['filter_keywords']
                final_list = [
                    item for item in new_items 
                    if any(k.lower() in (item['title'] + item['summary']).lower() for k in keywords)
                ]
            
            # 步骤 4: 结果处理
            if final_list:
                st.write(f"💾 正在将 {len(final_list)} 条精选内容写入 Google Sheets...")
                dm.save_new_articles(final_list)
                
                # 步骤 5: 飞书推送
                if config.get('feishu_webhook'):
                    st.write("🤖 正在推送精选摘要至飞书...")
                    msg = f"✅ 今日精选游戏情报 ({len(final_list)}条):\n" + \
                          "\n".join([f"- {a['title']}" for a in final_list])
                    send_feishu_message(config['feishu_webhook'], msg)
                
                status.update(label="同步任务成功完成！", state="complete")
                
                # 渲染今日结果 UI
                render_stats_info(len(raw_articles), len(final_list))
                for art in final_list:
                    render_article_card(art, expanded=True)
            else:
                status.update(label="未筛选出高价值内容。", state="complete")
                st.warning("采集到的新内容未通过 AI/关键词筛选。")

# --- 6. 历史数据展示区 ---
st.divider()
st.subheader("📜 历史情报回顾")

# 只有在用户点击“展开”或页面加载时才从数据库读取，避免浪费性能
with st.expander("查看所有历史记录", expanded=False):
    history_data = dm.get_all_articles()
    if history_data:
        df_history = pd.DataFrame(history_data)
        # 转换日期格式以便 UI 组件排序和分组
        if 'crawl_date' in df_history.columns:
            df_history['crawl_date'] = pd.to_datetime(df_history['crawl_date'])
            render_history_view(df_history)
        else:
            st.dataframe(df_history) # 保底方案
    else:
        st.info("数据库目前为空，请先执行同步。")