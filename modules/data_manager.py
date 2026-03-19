import pandas as pd
from streamlit_gsheets import GSheetsConnection
import streamlit as st

class DataManager:
    def __init__(self, st_connection):
        self.conn = st_connection
        self.sheet_name = "Sheet1" # 固定使用 Sheet1

    def get_all_articles(self):
        """从 Sheet1 读取所有数据"""
        try:
            df = self.conn.read(worksheet=self.sheet_name)
            if df is not None and not df.empty:
                # 确保日期列是 datetime 格式，方便后续筛选
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
            # 1. 获取现有数据
            existing_df = self.conn.read(worksheet=self.sheet_name)
            
            # 2. 准备新数据
            today_str = pd.Timestamp.now().strftime('%Y-%m-%d')
            new_df = pd.DataFrame(new_articles)
            new_df['crawl_date'] = today_str # 打上日期标签
            
            # 3. 合并新旧数据
            if existing_df is not None and not existing_df.empty:
                # 排除掉全是空的列或行
                existing_df = existing_df.dropna(how='all', axis=0)
                final_df = pd.concat([existing_df, new_df], ignore_index=True)
            else:
                final_df = new_df
            
            # 4. 全量覆盖回 Sheet1 (这是最稳妥的追加方式)
            self.conn.update(worksheet=self.sheet_name, data=final_df)
            st.toast(f"✅ 成功存入 {len(new_articles)} 条情报至 {self.sheet_name}")
            
        except Exception as e:
            st.error(f"保存至 Sheet1 失败: {e}")

    # AI分析相关
    def get_ai_history(self):
        """读取 AI 表单中的所有历史总结"""
        try:
            df = self.conn.read(worksheet="ai", ttl=0)
            if df is not None and not df.empty:
                return df.set_index('crawl_date')['content'].to_dict()
            return {}
        except Exception:
            return {}

    def save_ai_summary(self, date_str, content):
        """将 AI 总结存入 Google Sheets 的 'ai' 表单"""
        try:
            # 读取现有数据
            existing_df = self.conn.read(worksheet="ai", ttl=0)
            new_data = pd.DataFrame([{"crawl_date": date_str, "content": content}])
            
            if existing_df is not None and not existing_df.empty:
                # 检查是否已存在该日期，存在则不覆盖（实现一次性功能）
                if date_str in existing_df['crawl_date'].values:
                    return
                final_df = pd.concat([existing_df, new_data], ignore_index=True)
            else:
                final_df = new_data
            
            self.conn.update(worksheet="ai", data=final_df)
        except Exception as e:
            st.error(f"AI 总结保存失败: {e}")
