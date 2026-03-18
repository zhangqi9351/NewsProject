import streamlit as st
import pandas as pd

def render_header():
    st.title("🎮 移动游戏市场情报站")
    st.caption("基于关键词与 AI 筛选的自动化系统")

def render_sidebar(config):
    with st.sidebar:
        st.header("⚙️ 配置概览")
        st.write(f"已加载 {len(config['rss_sources'])} 个资讯源")
        st.write(f"监控关键词: {', '.join(config['filter_keywords'][:5])}...")

def render_article_card(article, expanded=False):
    """渲染单条资讯卡片"""
    with st.expander(f"【{article['source']}】{article['title']}", expanded=expanded):
        st.write(article.get('summary', '')[:300] + "...")
        st.link_button("阅读全文识别", article['link'])

def render_stats_info(all_count, filtered_count):
    """渲染扫描统计信息"""
    col1, col2 = st.columns(2)
    col1.metric("原始扫描", all_count)
    col2.metric("精选情报", filtered_count)

def render_history_view(df_articles):
    """渲染历史数据折叠列表"""
    if df_articles.empty:
        st.info("暂无历史情报记录")
        return

    # 这里仅负责遍历并调用 card 渲染，不涉及数据库操作
    for day, day_group in df_articles.groupby(df_articles['crawl_date'].dt.date):
        st.markdown(f"#### 📅 {day}")
        for _, art in day_group.iterrows():
            render_article_card(art, expanded=False)