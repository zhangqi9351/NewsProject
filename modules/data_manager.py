import pandas as pd
from streamlit_gsheets import GSheetsConnection
import streamlit as st

class DataManager:
    def __init__(self, st_connection):
        self.conn = st_connection
        self.sheet_name = "Sheet1" 
        self.ai_sheet = "ai"       
        self.feed_sheet = "feeds"   

    def get_active_feeds(self):
        """从 feeds 工作表读取所有启用的 RSS 源"""
        try:
            # ttl=0 确保实时读取表格修改
            df = self.conn.read(worksheet=self.feed_sheet, ttl=0)
            if df is None or df.empty:
                return []
            
            # 兼容性过滤：将所有内容转为字符串并大写，匹配包含 'TRUE' 的行
            # 这样可以兼容布尔值、字符串和 Google 表格的勾选框
            mask = df['is_active'].astype(str).str.upper().str.strip() == 'TRUE'
            active_feeds = df[mask]
            
            return active_feeds.to_dict(orient='records')
        except Exception as e:
            st.error(f"读取 feeds 表失败，请检查列名是否为 is_active: {e}")
            return []

    def get_all_articles(self):
        try:
            df = self.conn.read(worksheet=self.sheet_name, ttl="5m")
            if df is not None and not df.empty:
                if 'crawl_date' in df.columns:
                    df['crawl_date'] = pd.to_datetime(df['crawl_date'])
                return df.to_dict(orient='records')
            return []
        except Exception:
            return []

    def get_seen_links(self):
        articles = self.get_all_articles()
        return set(str(a.get('link', '')) for a in articles) if articles else set()

    def save_new_articles(self, new_articles):
        if not new_articles: return
        try:
            existing_df = self.conn.read(worksheet=self.sheet_name, ttl=0)
            new_df = pd.DataFrame(new_articles)
            new_df['crawl_date'] = pd.Timestamp.now().strftime('%Y-%m-%d')
            if existing_df is not None and not existing_df.empty:
                existing_df = existing_df.dropna(how='all', axis=0)
                final_df = pd.concat([existing_df, new_df], ignore_index=True)
            else:
                final_df = new_df
            self.conn.update(worksheet=self.sheet_name, data=final_df)
            st.toast(f"✅ 成功存入 {len(new_articles)} 条情报")
        except Exception as e:
            st.error(f"保存文章失败: {e}")

    def get_ai_history(self):
        try:
            df = self.conn.read(worksheet=self.ai_sheet, ttl=0)
            if df is not None and not df.empty:
                return df.set_index('crawl_date')['content'].to_dict()
            return {}
        except Exception:
            return {}

    def save_ai_summary(self, date_str, content):
        try:
            existing_df = self.conn.read(worksheet=self.ai_sheet, ttl=0)
            new_data = pd.DataFrame([{"crawl_date": date_str, "content": content}])
            if existing_df is not None and not existing_df.empty:
                if date_str in existing_df['crawl_date'].values: return
                final_df = pd.concat([existing_df, new_data], ignore_index=True)
            else:
                final_df = new_data
            self.conn.update(worksheet=self.ai_sheet, data=final_df)
        except Exception as e:
            st.error(f"AI 总结保存失败: {e}")