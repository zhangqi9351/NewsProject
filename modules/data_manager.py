import pandas as pd
from streamlit_gsheets import GSheetsConnection
import streamlit as st

class DataManager:
    def __init__(self, st_connection):
        self.conn = st_connection
        self.sheet_name = "Sheet1" # 存储文章的主表
        self.ai_sheet = "ai"       # 存储AI总结的表
        self.feed_sheet = "feeds"   # 新增：存储订阅源的表

    def get_active_feeds(self):
        """从 feeds 工作表读取所有启用的 RSS 源"""
        try:
            # 读取 feeds 表，ttl=0 确保每次点击都能拿到表格最新修改
            df = self.conn.read(worksheet=self.feed_sheet, ttl=0)
            if df is None or df.empty:
                return []
            
            # 过滤出 is_active 为 TRUE 的行 (处理字符串和布尔值的兼容性)
            mask = df['is_active'].astype(str).str.upper() == 'TRUE'
            active_feeds = df[mask]
            
            return active_feeds.to_dict(orient='records')
        except Exception as e:
            st.error(f"读取订阅源配置失败: {e}")
            return []

    def get_all_articles(self):
        """从 Sheet1 读取所有数据"""
        try:
            df = self.conn.read(worksheet=self.sheet_name, ttl="5m")
            if df is not None and not df.empty:
                if 'crawl_date' in df.columns:
                    df['crawl_date'] = pd.to_datetime(df['crawl_date'])
                return df.to_dict(orient='records')
            return []
        except Exception as e:
            st.error(f"读取数据库失败: {e}")
            return []

    def get_seen_links(self):
        """获取已存链接用于去重"""
        articles = self.get_all_articles()
        if not articles:
            return set()
        return set(str(a.get('link', '')) for a in articles)

    def save_new_articles(self, new_articles):
        """追加新文章到 Sheet1"""
        if not new_articles:
            return
        try:
            existing_df = self.conn.read(worksheet=self.sheet_name, ttl=0)
            today_str = pd.Timestamp.now().strftime('%Y-%m-%d')
            new_df = pd.DataFrame(new_articles)
            new_df['crawl_date'] = today_str
            
            if existing_df is not None and not existing_df.empty:
                existing_df = existing_df.dropna(how='all', axis=0)
                final_df = pd.concat([existing_df, new_df], ignore_index=True)
            else:
                final_df = new_df
            
            self.conn.update(worksheet=self.sheet_name, data=final_df)
            st.toast(f"✅ 成功存入 {len(new_articles)} 条情报")
        except Exception as e:
            st.error(f"保存至 Sheet1 失败: {e}")

    def get_ai_history(self):
        """读取 AI 表单中的所有历史总结"""
        try:
            df = self.conn.read(worksheet=self.ai_sheet, ttl=0)
            if df is not None and not df.empty:
                return df.set_index('crawl_date')['content'].to_dict()
            return {}
        except Exception:
            return {}

    def save_ai_summary(self, date_str, content):
        """将 AI 总结存入 Google Sheets"""
        try:
            existing_df = self.conn.read(worksheet=self.ai_sheet, ttl=0)
            new_data = pd.DataFrame([{"crawl_date": date_str, "content": content}])
            if existing_df is not None and not existing_df.empty:
                if date_str in existing_df['crawl_date'].values:
                    return
                final_df = pd.concat([existing_df, new_data], ignore_index=True)
            else:
                final_df = new_data
            self.conn.update(worksheet=self.ai_sheet, data=final_df)
        except Exception as e:
            st.error(f"AI 总结保存失败: {e}")