import streamlit as st
import yaml
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# --- 导入自定义模块 (请确保 modules 和 ui 文件夹及文件存在) ---
from modules.data_manager import DataManager
from modules.scraper import fetch_all_rss
from modules.analyzer import get_ai_global_insight
from modules.notifier import send_feishu_message

# 导入 UI 组件
from ui.components import (
    render_header, 
    render_sidebar, 
    render_sidebar_navigation, 
    render_daily_dashboard
)

# --- 1. 页面基础配置 ---
st.set_page_config(page_title="游戏情报自动化站", layout="wide", page_icon="🎮")

def load_config():
    """读取配置文件"""
    try:
        with open('config.yaml', 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        st.error("❌ 找不到 config.yaml 文件，请检查根目录。")
        st.stop()

config = load_config()

# --- 2. 初始化后端连接 ---
# 连接 Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)
dm = DataManager(conn)

# --- 3. 侧边栏导航逻辑 ---
render_sidebar(config) # 显示基础配置（如关键词）

# 获取所有历史数据
history_data = dm.get_all_articles()
df_history = pd.DataFrame(history_data)

# 确保日期格式正确，以便排序
if not df_history.empty and 'crawl_date' in df_history.columns:
    df_history['crawl_date'] = pd.to_datetime(df_history['crawl_date'])

# 在侧边栏渲染日期选择，并获取选中的日期
selected_date = render_sidebar_navigation(df_history)

# --- 4. 主界面布局 ---
render_header()

# 创建两个标签页：一个用于运行任务，一个用于看历史看板
tab_sync, tab_board = st.tabs(["🚀 开启情报同步", "📊 历史情报看板"])

with tab_sync:
    st.subheader("同步控制台")
    st.info("说明：此操作将根据关键词抓取所有匹配新闻，不进行 AI 过滤，保证情报完整。")
    
    if st.button("🚀 执行全网 RSS 抓取并存入数据库", use_container_width=True):
        with st.status("正在执行同步工作流...", expanded=True) as status:
            
            # 第一步：抓取 RSS
            st.write("📡 正在从配置的源获取资讯...")
            raw_data = fetch_all_rss(config.get('rss_sources', []))
            
            # 第二步：获取已存在的链接，避免重复存储
            st.write("🔍 正在比对数据库...")
            seen_links = dm.get_seen_links()
            
            # 第三步：基于关键词过滤 (纯 Python 逻辑)
            st.write("🧹 正在根据关键词筛选...")
            keywords = config.get('filter_keywords', [])
            final_to_save = []
            
            for item in raw_data:
                # 如果链接没存过，且标题或摘要包含关键词
                if item['link'] not in seen_links:
                    content_to_check = (item['title'] + item.get('summary', '')).lower()
                    if any(k.lower() in content_to_check for k in keywords):
                        final_to_save.append(item)
            
            # 第四步：保存结果
            if final_to_save:
                st.write(f"💾 正在将 {len(final_to_save)} 条新资讯存入 Google Sheets...")
                dm.save_new_articles(final_to_save)
                
                # 可选：飞书推送 (仅推送标题预览)
                if config.get('feishu_webhook'):
                    msg = f"✅ 今日采集到 {len(final_to_save)} 条新情报，请前往看板查看。"
                    send_feishu_message(config['feishu_webhook'], msg)
                
                status.update(label="✅ 同步任务成功完成！", state="complete")
                st.success(f"成功更新 {len(final_to_save)} 条情报！")
            else:
                status.update(label="☕ 暂无新资讯", state="complete")
                st.info("没有发现符合关键词的新内容。")

with tab_board:
    # 根据侧边栏选中的日期，显示对应的卡片内容
    if selected_date:
        # 这里传入 Gemini API Key，用于在该页面生成全局总结
        api_key = st.secrets.get("GEMINI_API_KEY")
        render_daily_dashboard(df_history, selected_date, api_key,dm)
    else:
        st.info("👈 请在左侧边栏选择一个日期开始浏览情报。")