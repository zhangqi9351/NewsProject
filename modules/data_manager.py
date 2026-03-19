import pandas as pd
from streamlit_gsheets import GSheetsConnection
import streamlit as st

class DataManager:
    def __init__(self, st_connection):
        self.conn = st_connection

    def _get_all_worksheet_names(self):
        try:
            if not hasattr(self.conn, '_spreadsheet') or self.conn._spreadsheet is None:
                return []
            return [ws.title for ws in self.conn._spreadsheet.worksheets()]
        except Exception:
            return []

    def _create_worksheet(self, worksheet_name):
        try:
            self.conn.create_worksheet(worksheet_name=worksheet_name)
            return True
        except Exception as e:
            st.error(f"创建工作表失败: {e}")
            return False

    def get_all_articles(self):
        all_articles = []
        ws_names = self._get_all_worksheet_names()
        # 排除掉初始的 Sheet1，只读日期命名的表
        date_sheets = [n for n in ws_names if n != "Sheet1"]
        
        for ws_name in date_sheets:
            try:
                df = self.conn.read(worksheet=ws_name)
                if not df.empty:
                    # 确保包含我们需要的列
                    if 'crawl_date' not in df.columns:
                        df['crawl_date'] = ws_name
                    all_articles.extend(df.to_dict(orient='records'))
            except Exception:
                continue
        return all_articles

    def get_seen_links(self):
        articles = self.get_all_articles()
        return set(str(a.get('link', '')) for a in articles)

    def save_new_articles(self, articles):
        """保存文章，支持 ai_summary 列"""
        if not articles:
            return
        
        today_str = pd.Timestamp.now().strftime('%Y-%m-%d')
        if today_str not in self._get_all_worksheet_names():
            self._create_worksheet(today_str)

        try:
            new_df = pd.DataFrame(articles)
            # 确保保存时包含日期
            new_df['crawl_date'] = today_str
            # 写入数据
            self.conn.update(worksheet=today_str, data=new_df)
        except Exception as e:
            st.error(f"保存失败: {e}")