def render_daily_dashboard(df, selected_date_str, api_key):
    # 1. 数据筛选
    target_date = pd.to_datetime(selected_date_str).date()
    day_data = df[df['crawl_date'].dt.date == target_date]

    if day_data.empty:
        st.info(f"📅 {selected_date_str} 暂无资讯记录。")
        return

    # 2. 🤖 AI 深度总结区域
    with st.expander("🤖 查看 AI 行业深度分析报告", expanded=True):
        # 使用 Session State 缓存总结结果，避免每次切换日期都重新消耗 API 额度
        cache_key = f"ai_report_{selected_date_str}"
        
        if cache_key not in st.session_state:
            if st.button("✨ 点击生成今日行情总结", use_container_width=True):
                with st.spinner("AI 正在分析今日所有情报..."):
                    from modules.analyzer import get_ai_global_insight
                    report = get_ai_global_insight(day_data.to_dict('records'), api_key)
                    st.session_state[cache_key] = report
                    st.rerun() # 强制刷新显示结果
        else:
            st.markdown(st.session_state[cache_key])
            if st.button("🔄 重新分析"):
                del st.session_state[cache_key]
                st.rerun()

    st.divider()

    # 3. 原始资讯卡片列表
    st.subheader(f"📑 原始资讯清单 ({len(day_data)})")
    cols = st.columns(2)
    for idx, (_, row) in enumerate(day_data.iterrows()):
        with cols[idx % 2]:
            with st.container(border=True):
                st.caption(f"📍 {row['source']}")
                st.markdown(f"**{row['title']}**")
                with st.expander("查看摘要"):
                    st.write(row.get('summary', '无摘要'))
                st.link_button("阅读原文", row['link'])