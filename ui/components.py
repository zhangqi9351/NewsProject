import streamlit as st
import pandas as pd

def render_sidebar_navigation(df):
    """
    在侧边栏渲染日期导航器
    返回用户选择的日期日期
    """
    st.sidebar.header("📅 情报历程")
    
    if df.empty:
        st.sidebar.info("暂无历史数据")
        return None

    # 提取所有不重复的日期并倒序排列
    all_dates = sorted(df['crawl_date'].dt.date.unique(), reverse=True)
    date_options = [d.strftime("%Y-%m-%d") for d in all_dates]
    
    # 添加一个“最新”选项
    selected_date_str = st.sidebar.radio(
        "选择查看日期：",
        options=date_options,
        index=0
    )
    
    return selected_date_str

def render_content_dashboard(df, selected_date_str):
    """
    主界面：显示指定日期的资讯卡片和 AI 总结
    """
    if df.empty or not selected_date_str:
        return

    # 筛选出选中日期的数据
    target_date = pd.to_datetime(selected_date_str).date()
    day_data = df[df['crawl_date'].dt.date == target_date]

    st.header(f"📑 {selected_date_str} 市场情报回顾")
    
    # 顶部放置一个 AI 总体摘要卡片（假设你以后会存储每日总评）
    with st.container(border=True):
        st.subheader("🤖 AI 本日核心洞察")
        st.write(f"本日共录得 {len(day_data)} 条精选资讯。主要聚焦于：" + 
                 "，".join(day_data['title'].iloc[:3].values) + " 等动态。")

    st.divider()

    # 渲染具体的资讯卡片
    cols = st.columns(2) # 采用两列布局更像看板
    for idx, (_, row) in enumerate(day_data.iterrows()):
        with cols[idx % 2]:
            with st.container(border=True):
                st.markdown(f"**[{row['source']}]**")
                st.markdown(f"#### {row['title']}")
                st.caption(f"链接：{row['link']}")
                # 如果你有 AI 总结字段，显示在这里
                if 'ai_summary' in row and pd.notna(row['ai_summary']):
                    st.info(f"✨ AI 总结：{row['ai_summary']}")
                else:
                    st.write(row.get('summary', '暂无摘要')[:200] + "...")
                st.link_button("查看详情", row['link'], use_container_width=True)