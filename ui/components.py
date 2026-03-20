import streamlit as st
import pandas as pd

def is_successful_ai_report(report):
    return bool(report) and not report.startswith(("❌", "⚠️", "📅"))

def render_header():
    st.title("🎮 游戏情报自动化站")
    st.caption("全量数据采集 | Gemini 2.0 深度总结")

def render_sidebar(dm):
    """侧边栏：同步控制台"""
    with st.sidebar:
        st.header("🚀 数据同步")
        if st.button("执行全网 RSS 抓取", use_container_width=True):
            with st.status("正在从数据库读取订阅源...", expanded=True) as status:
                # 1. 获取启用的源
                active_feeds = dm.get_active_feeds()
                
                if not active_feeds:
                    status.update(label="❌ feeds 表中没有启用的源，请检查 is_active 列", state="error")
                    return

                # 2. 抓取逻辑
                from modules.scraper import fetch_all_rss
                raw_data = fetch_all_rss(active_feeds)
                seen_links = dm.get_seen_links()
                
                # 3. 仅根据链接去重
                final_to_save = [
                    item for item in raw_data
                    if str(item.get('link', '')).strip() and str(item.get('link', '')).strip() not in seen_links
                ]
                
                if final_to_save:
                    dm.save_new_articles(final_to_save)
                    status.update(label=f"✅ 已更新 {len(final_to_save)} 条", state="complete")
                    st.rerun()
                else:
                    status.update(label="☕ 暂无新资讯", state="complete")
        st.markdown("---")
        st.info("💡 当前已开启全量采集模式")

def render_sidebar_navigation(df):
    st.sidebar.header("📅 历史记录")
    if df is None or df.empty:
        st.sidebar.info("暂无历史数据")
        return None
    df['crawl_date'] = pd.to_datetime(df['crawl_date'])
    all_dates = sorted(df['crawl_date'].dt.date.unique(), reverse=True)
    date_options = [d.strftime("%Y-%m-%d") for d in all_dates]
    return st.sidebar.radio("选择日期：", options=date_options, index=0)

def render_daily_dashboard(df, selected_date_str, api_key, dm):
    target_date = pd.to_datetime(selected_date_str).date()
    day_data = df[df['crawl_date'].dt.date == target_date]
    st.subheader(f"📅 {selected_date_str} 情报简报")

    ai_history = dm.get_ai_history()
    with st.container(border=True):
        if selected_date_str in ai_history:
            st.markdown(f"### 🤖 AI 深度分析\n\n{ai_history[selected_date_str]}")
        else:
            if st.button("✨ 立即生成分析报告", use_container_width=True):
                if not api_key:
                    st.error("❌ 缺少 API_KEY")
                    return
                with st.spinner("AI 正在分析全量资讯..."):
                    from modules.analyzer import get_ai_global_insight
                    report = get_ai_global_insight(day_data.to_dict('records'), api_key)
                    if is_successful_ai_report(report):
                        dm.save_ai_summary(selected_date_str, report)
                        st.rerun()
                    else:
                        st.error(report)

    st.divider()
    if day_data.empty:
        st.info("该日期暂无资讯。")
    else:
        cols = st.columns(2)
        for idx, (_, row) in enumerate(day_data.iterrows()):
            with cols[idx % 2]:
                with st.container(border=True):
                    st.caption(f"📍 {row.get('source', '未知源')}")
                    st.markdown(f"**{row['title']}**")
                    with st.expander("查看摘要"):
                        st.write(row.get('summary', '暂无内容'))
                    st.link_button("阅读原文", row.get('link', '#'), use_container_width=True)
