import streamlit as st
import pandas as pd

def render_header():
    st.title("游戏情报自动化站")

def render_sidebar(config):
    st.sidebar.title("配置信息")

def render_sidebar_navigation(df):
    st.sidebar.markdown("---")
    if df is None or df.empty:
        return None
    all_dates = sorted(df['crawl_date'].dt.date.unique(), reverse=True)
    date_options = [d.strftime("%Y-%m-%d") for d in all_dates]
    return st.sidebar.radio("选择日期", options=date_options)

def render_daily_dashboard(df, selected_date_str):
    st.write(f"正在查看: {selected_date_str}")