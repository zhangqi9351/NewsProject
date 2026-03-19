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

def render_daily_dashboard(df, selected_date_str, api_key,dm):
    """渲染主界面的情报看板，包含 AI 总结和资讯卡片"""
    if df is None or df.empty or not selected_date_str:
        st.info("👈 请在左侧选择一个日期")
        return

    # 1. 筛选选中日期的数据
    target_date = pd.to_datetime(selected_date_str).date()
    day_data = df[df['crawl_date'].dt.date == target_date]

    st.header(f"🔍 {selected_date_str} 深度看板")

    # 1. 加载 AI 历史记录
    ai_history = dm.get_ai_history()
    
    with st.container(border=True):
        st.subheader("🤖 AI 行业深度分析报告")
        
        # 逻辑：如果数据库里已有该日期的总结
        if selected_date_str in ai_history:
            st.markdown(ai_history[selected_date_str])
            st.success("✅ 本报告已存档，无需重复生成。")
        else:
            # 数据库里没有，才显示生成按钮
            if st.button("✨ 立即生成今日行情总结 (限执行一次)", use_container_width=True):
                with st.spinner("AI 正在分析并存档..."):
                    from modules.analyzer import get_ai_global_insight
                    report = get_ai_global_insight(day_data.to_dict('records'), api_key)
                    
                    # 关键动作：存入数据库
                    dm.save_ai_summary(selected_date_str, report)
                    st.rerun() # 只有存完之后才刷新一次以显示内容

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