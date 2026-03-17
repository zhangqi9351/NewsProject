import streamlit as st
import feedparser
import time
import re
from datetime import datetime, timedelta
import yaml
from data_manager import DataManager
import pandas as pd
from streamlit_gsheets import GSheetsConnection

def load_config(config_path):
    with open(config_path, 'r', encoding='utf-8') as file:
        return yaml.safe_load(file)

# --- 页面基础配置 ---
st.set_page_config(page_title="游戏情报站", layout="wide", page_icon="🎮")

# --- 逻辑函数 (从 main.py 迁移并优化) ---

def fetch_rss_data(sources):
    """抓取所有 RSS 源数据"""
    all_articles = []
    for source in sources:
        try:
            feed = feedparser.parse(source['url'])
            for entry in feed.entries:
                all_articles.append({
                    'title': entry.title,
                    'link': entry.link,
                    'summary': entry.get('summary', ''),
                    'source': source['name']
                })
        except Exception as e:
            st.warning(f"无法抓取 {source['name']}: {e}")
    return all_articles

def keyword_filter_articles(articles, keywords):
    """根据关键词筛选文章"""
    filtered_articles = []
    for article in articles:
        # 检查标题和摘要是否包含任何关键词
        title = article.get('title', '').lower()
        summary = article.get('summary', '').lower()
        if any(keyword.lower() in title or keyword.lower() in summary for keyword in keywords):
            filtered_articles.append(article)
    return filtered_articles

# --- UI 界面 ---

st.title("🎮 移动游戏市场情报站")
st.caption("基于关键词筛选的自动化情报系统")

# 侧边栏配置
with st.sidebar:
    st.header("配置中心")
    config = load_config('config.yaml')

# 主执行逻辑
    # 在应用启动时加载已有的数据
    conn = st.connection("gsheets", type=GSheetsConnection)
    data_manager = DataManager(conn)

    # 获取并显示已保存的文章
    saved_articles = data_manager.get_all_articles()

    if saved_articles:
        st.subheader(f"📖 已保存情报 ({len(saved_articles)})")

        # 转换为 DataFrame 进行处理
        df_articles = pd.DataFrame(saved_articles)
        df_articles['crawl_date'] = pd.to_datetime(df_articles['crawl_date'])
        df_articles = df_articles.sort_values(by='crawl_date', ascending=False)

        # 添加年份和周数 (isocalendar返回 (year, week, weekday))
        df_articles['year'] = df_articles['crawl_date'].dt.isocalendar().year
        df_articles['week_of_year'] = df_articles['crawl_date'].dt.isocalendar().week
        
        # 按照年份和周数分组
        for (year, week_of_year), week_group in df_articles.groupby(['year', 'week_of_year']):
            # 获取该周的第一天作为周的标识
            first_day_of_week = week_group['crawl_date'].min()
            week_key = f"{year}年 第{week_of_year}周 ({first_day_of_week.strftime('%Y-%m-%d')})"

            with st.expander(f"📅 **{week_key}**", expanded=True):
                st.info("💡 **AI 一周概要汇总分析 (占位符)**: 本周共抓取X条信息，其中包含Y条重要内容。主要趋势是...")
                # 按日期降序显示
                for day_date, day_group in week_group.groupby(df_articles['crawl_date'].dt.date):
                    day_str = day_date.strftime('%Y-%m-%d')
                    with st.expander(f"##### {day_str}", expanded=False): # 默认折叠每日内容
                        st.info(f"💡 **AI 每日总结分析 (占位符)**: {day_str} 共抓取X条信息，其中...")
                        for _, art in day_group.iterrows():
                            with st.expander(f"【{art['source']}】{art['title']}", expanded=False):
                                st.write(art['summary'][:300] + "...")
                                st.link_button("阅读全文", art['link'])
    else:
        st.info("暂无已保存情报。点击下方按钮开始同步和筛选。")

# 新文章筛选逻辑
if st.button("🚀 立即同步并开始筛选", use_container_width=True):
    # 初始化数据管理器
    conn = st.connection("gsheets", type=GSheetsConnection)
    data_manager = DataManager(conn)

    # 获取已处理的链接，用于去重
    seen_links = data_manager.get_seen_links()

    # 1. 抓取
    with st.status("正在采集全球 RSS 资讯...", expanded=True) as status:
        raw_data = fetch_rss_data(sources)
        st.write(f"✅ 采集完成，共发现 {len(raw_data)} 条新内容。")

        # 过滤掉已读文章
        new_articles = [article for article in raw_data if article['link'] not in seen_links]
        st.write(f"🗑️ 过滤掉 {len(raw_data) - len(new_articles)} 条旧内容，剩余 {len(new_articles)} 条新内容待筛选。")

        if new_articles:
            # 2. 关键词筛选
            st.write("🔍 正在进行关键词筛选...")
            final_list = keyword_filter_articles(new_articles, filter_keywords)
            status.update(label="处理完成！", state="complete", expanded=False)

            # 3. 保存新文章到 Google Sheets
            data_manager.save_new_articles(final_list)
            st.write(f"💾 已将 {len(final_list)} 条精选内容保存到 Google Sheets。")
        else:
            final_list = []
            status.update(label="没有新内容需要处理！", state="complete", expanded=False)
            st.success("🎉 没有新的内容需要筛选和保存。")

    # 3. 结果展示
    if final_list:
        st.subheader(f"🎯 关键词精选情报 ({len(final_list)})")
        
        for art in final_list:
            with st.expander(f"【{art['source']}】{art['title']}", expanded=True):
                st.write(art['summary'][:300] + "...")
                st.link_button("阅读全文", art['link'])
    else:
        st.success("☕️ 暂无符合关键词标签的新闻。")