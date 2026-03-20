import streamlit as st
import pandas as pd

def render_header():
    st.title("🎮 游戏情报自动化站")
    st.caption("关键词驱动采集 | Gemini AI 深度总结")

def render_sidebar(config, dm):
    """侧边栏：同步控制台"""
    with st.sidebar:
        st.header("🚀 数据同步")
        if st.button("执行全网 RSS 抓取", use_container_width=True):
            with st.status("正在同步...", expanded=False) as status:
                from modules.scraper import fetch_all_rss
                raw_data = fetch_all_rss(config.get('rss_sources', []))
                seen_links = dm.get_seen_links()
                
                keywords = config.get('filter_keywords', [])
                final_to_save = []
                for item in raw_data:
                    if item['link'] not in seen_links:
                        text = (item['title'] + item.get('summary', '')).lower()
                        if any(k.lower() in text for k in keywords):
                            final_to_save.append(item)
                
                if final_to_save:
                    dm.save_new_articles(final_to_save)
                    status.update(label=f"✅ 已更新 {len(final_to_save)} 条", state="complete")
                    st.rerun()
                else:
                    status.update(label="☕ 暂无新资讯", state="complete")
        
        st.markdown("---")
        with st.expander("🔍 当前监控关键词"):
            st.write(", ".join(config.get('filter_keywords', [])))

def render_sidebar_navigation(df):
    """日期导航"""
    st.sidebar.header("📅 历史记录")
    if df is None or df.empty:
        return None
    
    all_dates = sorted(df['crawl_date'].dt.date.unique(), reverse=True)
    date_options = [d.strftime("%Y-%m-%d") for d in all_dates]
    
    return st.sidebar.radio("选择日期：", options=date_options, index=0)

def render_daily_dashboard(df, selected_date_str, api_key, dm):
    """看板主内容"""
    target_date = pd.to_datetime(selected_date_str).date()
    day_data = df[df['crawl_date'].dt.date == target_date]

    st.subheader(f"📅 {selected_date_str} 情报简报")

    # AI 总结逻辑：先读库，没有再生成
    ai_history = dm.get_ai_history() # 确保 DataManager 有此方法
    
    with st.container(border=True):
        if selected_date_str in ai_history:
            st.markdown(f"### 🤖 AI 深度分析\n\n{ai_history[selected_date_str]}")
        else:
            st.write("🤖 该日期暂无 AI 分析报告")
            if st.button("✨ 立即生成 (消耗配额)", use_container_width=True):
                with st.spinner("AI 正在阅读..."):
                    from modules.analyzer import get_ai_global_insight
                    report = get_ai_global_insight(day_data.to_dict('records'), api_key)
                    dm.save_ai_summary(selected_date_str, report)
                    # st.rerun()

    st.divider()
    # 渲染卡片
    cols = st.columns(2)
    for idx, (_, row) in enumerate(day_data.iterrows()):
        with cols[idx % 2]:
            with st.container(border=True):
                st.caption(f"📍 {row['source']}")
                st.markdown(f"**{row['title']}**")
                with st.expander("查看摘要"):
                    st.write(row.get('summary', ''))
                st.link_button("阅读原文", row['link'], use_container_width=True)