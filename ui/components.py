import streamlit as st
import pandas as pd


def is_successful_ai_report(report):
    return bool(report) and not report.startswith(("❌", "⚠️", "📅"))


def inject_global_styles():
    st.markdown(
        """
        <style>
        .stApp {
            background:
                radial-gradient(circle at top left, rgba(246, 222, 177, 0.55), transparent 28%),
                radial-gradient(circle at top right, rgba(155, 209, 197, 0.38), transparent 24%),
                linear-gradient(180deg, #fcfaf4 0%, #f6f1e6 100%);
        }
        .block-container {
            padding-top: 2.2rem;
            padding-bottom: 2rem;
        }
        div[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #f6f0e2 0%, #efe6d2 100%);
            border-right: 1px solid rgba(110, 89, 58, 0.12);
        }
        .hero-card, .summary-card, .detail-card {
            border-radius: 20px;
            border: 1px solid rgba(110, 89, 58, 0.12);
            box-shadow: 0 12px 32px rgba(88, 72, 49, 0.08);
        }
        .hero-card {
            padding: 1.6rem 1.7rem;
            background: linear-gradient(135deg, rgba(255,255,255,0.92), rgba(249, 243, 229, 0.95));
            margin-bottom: 1rem;
        }
        .hero-title {
            font-size: 3rem;
            line-height: 1.05;
            font-weight: 800;
            color: #2f3542;
            margin: 0;
        }
        .hero-subtitle {
            margin-top: 0.55rem;
            color: #736b5e;
            font-size: 1.02rem;
        }
        .summary-card {
            padding: 1rem 1.1rem;
            background: rgba(255, 252, 245, 0.92);
            min-height: 118px;
        }
        .summary-label {
            color: #7a705f;
            font-size: 0.88rem;
            margin-bottom: 0.2rem;
        }
        .summary-value {
            color: #24313d;
            font-size: 1.85rem;
            font-weight: 800;
            margin-bottom: 0.25rem;
        }
        .summary-note {
            color: #6e6559;
            font-size: 0.92rem;
        }
        .detail-card {
            padding: 1rem 1.1rem;
            background: rgba(255,255,255,0.94);
            margin-bottom: 0.9rem;
        }
        .detail-source {
            color: #8d6f3e;
            font-size: 0.84rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }
        .detail-title {
            color: #2b3340;
            font-size: 1.06rem;
            font-weight: 700;
            margin: 0.3rem 0 0.5rem;
        }
        .sync-error-box {
            background: linear-gradient(135deg, rgba(153, 66, 55, 0.08), rgba(255, 244, 240, 0.95));
            border: 1px solid rgba(153, 66, 55, 0.18);
            border-radius: 18px;
            padding: 1rem 1.1rem;
            margin-bottom: 1rem;
        }
        .sync-error-title {
            color: #8d3128;
            font-weight: 800;
            margin-bottom: 0.45rem;
        }
        .sync-error-item {
            color: #5b352f;
            margin: 0.28rem 0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header():
    inject_global_styles()
    st.markdown(
        """
        <section class="hero-card">
            <p class="hero-title">🎮 游戏情报自动化站</p>
            <p class="hero-subtitle">全量数据采集 · RSS 同步 · Gemini 深度总结</p>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_sync_feedback():
    sync_state = st.session_state.get("sync_feedback")
    if not sync_state:
        return

    if sync_state.get("errors"):
        items = "".join(
            f'<div class="sync-error-item">• {msg}</div>'
            for msg in sync_state["errors"][:8]
        )
        extra = ""
        if len(sync_state["errors"]) > 8:
            extra = f'<div class="sync-error-item">另有 {len(sync_state["errors"]) - 8} 条错误已省略</div>'
        st.markdown(
            f"""
            <section class="sync-error-box">
                <div class="sync-error-title">抓取过程中发现部分异常</div>
                {items}
                {extra}
            </section>
            """,
            unsafe_allow_html=True,
        )


def render_overview_cards(df):
    article_count = 0 if df is None else len(df)
    source_count = 0
    latest_date = "暂无"
    if df is not None and not df.empty:
        source_count = df['source'].nunique() if 'source' in df.columns else 0
        if 'crawl_date' in df.columns:
            latest_date = df['crawl_date'].dropna().dt.strftime('%Y-%m-%d').max() or "暂无"

    cards = [
        ("累计情报", str(article_count), "当前知识库内已保存的文章数"),
        ("覆盖源数", str(source_count), "历史数据里出现过的来源站点"),
        ("最新日期", latest_date, "最近一次成功入库的抓取日期"),
    ]
    cols = st.columns(3)
    for col, (label, value, note) in zip(cols, cards):
        with col:
            st.markdown(
                f"""
                <section class="summary-card">
                    <div class="summary-label">{label}</div>
                    <div class="summary-value">{value}</div>
                    <div class="summary-note">{note}</div>
                </section>
                """,
                unsafe_allow_html=True,
            )


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
                result = fetch_all_rss(active_feeds)
                raw_data = result['articles']
                fetch_errors = result['errors']
                seen_links = dm.get_seen_links()
                
                # 3. 仅根据链接去重
                final_to_save = [
                    item for item in raw_data
                    if str(item.get('link', '')).strip() and str(item.get('link', '')).strip() not in seen_links
                ]

                saved_count = dm.save_new_articles(final_to_save) if final_to_save else 0

                st.session_state["sync_feedback"] = {
                    "errors": fetch_errors,
                    "raw_count": len(raw_data),
                    "saved_count": saved_count,
                }

                if saved_count:
                    status.update(
                        label=f"✅ 已抓取 {len(raw_data)} 条，新增 {saved_count} 条",
                        state="complete"
                    )
                    st.rerun()
                elif raw_data:
                    status.update(label=f"☕ 抓取到 {len(raw_data)} 条，但均已存在", state="complete")
                elif fetch_errors:
                    status.update(label="⚠️ 抓取未产出有效资讯，请检查下方错误详情", state="error")
                else:
                    status.update(label="☕ 本次未抓取到任何资讯", state="complete")
        st.markdown("---")
        st.caption("支持从 Google Sheets 维护抓取源，并自动去重入库。")

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
                with st.container():
                    st.markdown(
                        f"""
                        <section class="detail-card">
                            <div class="detail-source">📍 {row.get('source', '未知源')}</div>
                            <div class="detail-title">{row['title']}</div>
                        """,
                        unsafe_allow_html=True,
                    )
                    with st.expander("查看摘要"):
                        st.write(row.get('summary', '暂无内容'))
                    st.link_button("阅读原文", row.get('link', '#'), use_container_width=True)
                    st.markdown("</section>", unsafe_allow_html=True)
