import streamlit as st
import pandas as pd

def render_header():
    """渲染页面标题"""
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
    """侧边栏：日期导航"""
    st.sidebar.header("📅 历史记录")
    if df is None or df.empty:
        st.sidebar.info("暂无历史数据")
        return None
    
    # 确保日期列为日期格式
    df['crawl_date'] = pd.to_datetime(df['crawl_date'])
    all_dates = sorted(df['crawl_date'].dt.date.unique(), reverse=True)
    date_options = [d.strftime("%Y-%m-%d") for d in all_dates]
    
    return st.sidebar.radio("选择日期：", options=date_options, index=0)

def render_daily_dashboard(df, selected_date_str, api_key, dm):
    """主界面看板渲染"""
    target_date = pd.to_datetime(selected_date_str).date()
    day_data = df[df['crawl_date'].dt.date == target_date]

    st.subheader(f"📅 {selected_date_str} 情报简报")

    # 1. 尝试从数据库读取已存的 AI 总结
    ai_history = dm.get_ai_history()
    
    with st.container(border=True):
        if selected_date_str in ai_history:
            # 如果已有记录且不是报错信息，直接显示
            content = ai_history[selected_date_str]
            st.markdown(f"### 🤖 AI 深度分析\n\n{content}")
            st.caption("✅ 报告已存档，不可重复修改。")
        else:
            st.write("🤖 该日期暂无 AI 分析报告")
            if st.button("✨ 立即生成 (消耗配额)", use_container_width=True):
                if not api_key:
                    st.error("❌ 未在 Secrets 中检测到 GEMINI_API_KEY")
                    return
                
                with st.spinner("AI 正在深度阅读中，请稍候..."):
                    from modules.analyzer import get_ai_global_insight
                    # 传入文章数据进行打包分析
                    report = get_ai_global_insight(day_data.to_dict('records'), api_key)
                    
                    # --- 错误拦截逻辑 ---
                    # 只有当返回内容不包含 429 或 失败 关键字时才保存
                    if "429" not in report and "失败" not in report and "Quota" not in report:
                        dm.save_ai_summary(selected_date_str, report)
                        st.success("✅ 分析成功并已存档！")
                        st.rerun() # 成功保存后刷新页面以切换到显示模式
                    else:
                        # 如果 AI 返回了错误信息，仅显示不保存
                        st.error(f"AI 调用触发限制：{report}")
                        st.info("💡 建议：请等待 1 分钟后再次尝试，或检查 API 配额。")

    st.divider()
    # 2. 原始资讯卡片渲染
    if day_data.empty:
        st.info("该日期暂无匹配资讯。")
    else:
        cols = st.columns(2)
        for idx, (_, row) in enumerate(day_data.iterrows()):
            with cols[idx % 2]:
                with st.container(border=True):
                    st.caption(f"📍 {row.get('source', '未知源')}")
                    st.markdown(f"**{row['title']}**")
                    with st.expander("查看摘要"):
                        st.write(row.get('summary', '暂无摘要内容'))
                    st.link_button("阅读原文", row.get('link', '#'), use_container_width=True)