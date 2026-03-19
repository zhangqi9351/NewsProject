import streamlit as st
import pandas as pd

def render_sidebar_navigation(df):
    """
    在侧边栏渲染日期导航器
    返回：用户选中的日期字符串 (YYYY-MM-DD)
    """
    st.sidebar.markdown("---")
    st.sidebar.header("📅 历史情报历程")
    
    if df is None or df.empty:
        st.sidebar.info("暂无历史数据，请先执行同步。")
        return None

    # 1. 提取所有日期并去重倒序排列
    # 假设 df['crawl_date'] 已经是 datetime 类型
    all_dates = sorted(df['crawl_date'].dt.date.unique(), reverse=True)
    date_options = [d.strftime("%Y-%m-%d") for d in all_dates]
    
    # 2. 侧边栏单选框导航
    selected_date_str = st.sidebar.radio(
        "选择日期查看详情：",
        options=date_options,
        index=0,
        key="date_navigator"
    )
    
    return selected_date_str

def render_daily_dashboard(df, selected_date_str):
    """
    主界面：显示选中日期的资讯看板
    """
    if df is None or df.empty or not selected_date_str:
        return

    # 筛选选中日期的数据
    target_date = pd.to_datetime(selected_date_str).date()
    day_data = df[df['crawl_date'].dt.date == target_date]

    st.header(f"🔍 {selected_date_str} 情报看板")
    
    # 顶部统计小卡片
    col1, col2, col3 = st.columns(3)
    col1.metric("精选条数", len(day_data))
    col2.metric("来源网站", len(day_data['source'].unique()))
    col3.metric("更新状态", "已同步")

    st.markdown("---")

    # 渲染资讯卡片流
    if day_data.empty:
        st.info("该日期暂无数据记录。")
    else:
        # 使用两列布局展示卡片
        display_cols = st.columns(2)
        for idx, (_, row) in enumerate(day_data.iterrows()):
            with display_cols[idx % 2]:
                # 使用 container 模拟卡片外框
                with st.container(border=True):
                    st.markdown(f"**【{row['source']}】**")
                    st.subheader(row['title'])
                    
                    # 摘要展示（限制字数）
                    summary = row.get('summary', '无摘要')
                    st.write(summary[:150] + "..." if len(summary) > 150 else summary)
                    
                    # 底部按钮
                    st.link_button("🔗 查看原文", row['link'], use_container_width=True)