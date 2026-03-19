import streamlit as st
import pandas as pd

def render_header():
    """渲染页面顶部标题"""
    st.title("🎮 游戏情报自动化站")
    st.caption("基于关键词抓取与 Gemini AI 深度分析的行业看板")

def render_sidebar(config):
    """渲染侧边栏基础配置信息"""
    with st.sidebar:
        st.header("⚙️ 当前配置")
        st.write(f"已加载 {len(config.get('rss_sources', []))} 个资讯源")
        if 'filter_keywords' in config:
            with st.expander("查看监控关键词"):
                st.write(", ".join(config['filter_keywords']))

def render_sidebar_navigation(df):
    """渲染侧边栏日期导航"""
    st.sidebar.markdown("---")
    st.sidebar.header("📅 历史情报历程")
    
    if df is None or df.empty:
        st.sidebar.info("暂无历史数据")
        return None

    # 从 df['crawl_date'] 这一列里提取所有不重复的日期
    all_dates = sorted(df['crawl_date'].dt.date.unique(), reverse=True)
    date_options = [d.strftime("%Y-%m-%d") for d in all_dates]
    
    selected_date_str = st.sidebar.radio(
        "选择查看日期：",
        options=date_options,
        index=0
    )
    return selected_date_str

def render_daily_dashboard(df, selected_date_str, api_key):
    """渲染主界面的情报看板，包含 AI 总结和资讯卡片"""
    if df is None or df.empty or not selected_date_str:
        st.info("👈 请在左侧选择一个日期")
        return

    # 1. 筛选选中日期的数据
    target_date = pd.to_datetime(selected_date_str).date()
    day_data = df[df['crawl_date'].dt.date == target_date]

    st.header(f"🔍 {selected_date_str} 深度看板")

    # 2. 🤖 AI 深度总结区域 (核心功能)
    with st.container(border=True):
        st.subheader("🤖 AI 今日深度分析报告")
        # 使用 Session State 缓存，避免重复消耗 API
        cache_key = f"ai_report_{selected_date_str}"
        
        if cache_key not in st.session_state:
            if st.button("✨ 立即生成今日行情总结", use_container_width=True):
                with st.spinner("AI 正在分析今日所有情报，请稍候..."):
                    # 动态导入分析函数
                    from modules.analyzer import get_ai_global_insight
                    report = get_ai_global_insight(day_data.to_dict('records'), api_key)
                    st.session_state[cache_key] = report
                    st.rerun()
        else:
            st.markdown(st.session_state[cache_key])
            if st.button("🔄 重新分析该日情报"):
                del st.session_state[cache_key]
                st.rerun()

    st.divider()

    # 3. 原始资讯卡片列表
    st.subheader(f"📑 原始资讯清单 ({len(day_data)} 条)")
    
    if day_data.empty:
        st.warning("该日期下没有匹配的资讯。")
    else:
        # 采用两列布局显示卡片
        cols = st.columns(2)
        for idx, (_, row) in enumerate(day_data.iterrows()):
            with cols[idx % 2]:
                with st.container(border=True):
                    # 显示来源和标题
                    source_name = row.get('source', '未知源')
                    st.caption(f"📍 {source_name}")
                    st.markdown(f"#### {row.get('title', '无标题')}")
                    
                    # 摘要放在折叠框里，保持界面整洁
                    with st.expander("查看摘要原文"):
                        st.write(row.get('summary', '暂无摘要内容'))
                    
                    # 跳转链接
                    st.link_button("🔗 阅读原文", row.get('link', '#'), use_container_width=True)