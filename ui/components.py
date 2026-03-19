import streamlit as st
import pandas as pd

def render_header():
    st.title("🎮 游戏情报自动化站")
    st.caption("基于关键词与 AI 筛选的移动游戏市场追踪系统")

def render_sidebar(config):
    with st.sidebar:
        st.header("⚙️ 配置信息")
        st.write(f"已加载 {len(config.get('rss_sources', []))} 个资讯源")
        if 'filter_keywords' in config:
            st.expander("当前监控关键词").write(", ".join(config['filter_keywords']))

def render_sidebar_navigation(df):
    st.sidebar.markdown("---")
    st.sidebar.header("📅 历史情报历程")
    
    if df is None or df.empty:
        st.sidebar.info("暂无历史数据")
        return None

    # 提取日期并排序
    try:
        # 确保是日期类型
        all_dates = sorted(df['crawl_date'].dt.date.unique(), reverse=True)
        date_options = [d.strftime("%Y-%m-%d") for d in all_dates]
        
        selected_date_str = st.sidebar.radio(
            "选择日期查看：",
            options=date_options,
            index=0
        )
        return selected_date_str
    except Exception as e:
        st.sidebar.error(f"日期解析错误: {e}")
        return None

def render_daily_dashboard(df, selected_date_str):
    if df is None or df.empty or not selected_date_str:
        st.info("请选择一个日期以显示内容")
        return

    # 筛选选中日期的数据
    target_date = pd.to_datetime(selected_date_str).date()
    day_data = df[df['crawl_date'].dt.date == target_date]

    st.subheader(f"🔍 {selected_date_str} 精选情报 ({len(day_data)}条)")

    if day_data.empty:
        st.warning("该日期下没有匹配的资讯。")
        return

    # 使用两列布局展示卡片
    cols = st.columns(2)
    for idx, (_, row) in enumerate(day_data.iterrows()):
        with cols[idx % 2]:
            # 使用 container 建立一个有边框的卡片感
            with st.container(border=True):
                st.markdown(f"**【{row.get('source', '未知来源')}】**")
                st.markdown(f"#### {row.get('title', '无标题')}")
                
                # 显示摘要，若太长则截断
                summary = row.get('summary', '无摘要')
                if isinstance(summary, str):
                    st.write(summary[:150] + "..." if len(summary) > 150 else summary)
                
                # 按钮跳转
                st.link_button("🔗 查看原文", row.get('link', '#'), use_container_width=True)