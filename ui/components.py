import streamlit as st
import pandas as pd

def render_header():
    st.title("🎮 游戏情报自动化站")
    st.caption("数据库驱动采集 | Gemini 2.0 深度总结")

def render_sidebar(config, dm):
    """侧边栏：同步控制台"""
    with st.sidebar:
        st.header("🚀 数据同步")
        if st.button("执行全网 RSS 抓取", use_container_width=True):
            with st.status("正在从数据库读取订阅源...", expanded=True) as status:
                # 1. 改动点：从数据库获取源，而不是从 config 获取
                active_feeds = dm.get_active_feeds()
                
                if not active_feeds:
                    status.update(label="❌ 数据库 feeds 表中没有启用的源", state="error")
                    return

                from modules.scraper import fetch_all_rss
                # 使用数据库里的源进行抓取
                raw_data = fetch_all_rss(active_feeds)
                
                seen_links = dm.get_seen_links()
                keywords = config.get('filter_keywords', [])
                final_to_save = []
                
                for item in raw_data:
                    if item['link'] not in seen_links:
                        text = (item['title'] + item.get('summary', '')).lower()
                        # 如果没有设置关键词，则全部抓取；否则进行过滤
                        if not keywords or any(k.lower() in text for k in keywords):
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
            content = ai_history[selected_date_str]
            st.markdown(f"### 🤖 AI 深度分析\n\n{content}")
            st.caption("✅ 报告已存档。")
        else:
            st.write("🤖 该日期暂无 AI 分析报告")
            if st.button("✨ 立即生成 (消耗配额)", use_container_width=True):
                if not api_key:
                    st.error("❌ 未检测到 API_KEY")
                    return
                with st.spinner("AI 正在深度阅读中..."):
                    from modules.analyzer import get_ai_global_insight
                    report = get_ai_global_insight(day_data.to_dict('records'), api_key)
                    if "失败" not in report and "Quota" not in report:
                        dm.save_ai_summary(selected_date_str, report)
                        st.success("✅ 分析成功并已存档！")
                        st.rerun()
                    else:
                        st.error(f"调用限制：{report}")

    st.divider()
    if day_data.empty:
        st.info("该日期暂无匹配资讯。")
    else:
        cols = st.columns(2)
        for idx, (_, row) in enumerate(day_data.iterrows()):
            with cols[idx % 2]:
                with st.container(border=True):
                    # 显示来源分类标签（如果有的话）
                    cat = row.get('category', '资讯')
                    st.caption(f"📍 {row.get('source', '未知源')} | 🏷️ {cat}")
                    st.markdown(f"**{row['title']}**")
                    with st.expander("查看摘要"):
                        st.write(row.get('summary', '暂无摘要内容'))
                    st.link_button("阅读原文", row.get('link', '#'), use_container_width=True)