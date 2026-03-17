import pandas as pd
from streamlit_gsheets import GSheetsConnection
import streamlit as st

class DataManager:
    def __init__(self, st_connection):
        self.conn = st_connection

    def _get_all_worksheet_names(self):
        """获取 Google Sheet 中所有工作表的名称"""
        try:
            # GSheetsConnection 内部封装了 gspread.Spreadsheet 对象，通过 _spreadsheet 属性访问
            return [ws.title for ws in self.conn._spreadsheet.worksheets()]
        except Exception as e:
            st.warning(f"无法获取工作表列表: {e}")
            return []

    def _create_worksheet(self, worksheet_name):
        """创建新的工作表"""
        try:
            self.conn.create_worksheet(worksheet_name)
            st.success(f"成功创建工作表: {worksheet_name}")
            return True
        except Exception as e:
            st.error(f"创建工作表 {worksheet_name} 失败: {e}")
            return False

    def get_seen_links(self):
        """获取所有日期工作表中已阅读的链接列表，用于全局去重"""
        all_seen_links = set()
        worksheet_names = self._get_all_worksheet_names()
        
        st.write(f"发现 {len(worksheet_names)} 个历史数据工作表。")

        for ws_name in worksheet_names:
            try:
                df = self.conn.read(worksheet=ws_name)
                if not df.empty and 'link' in df.columns:
                    all_seen_links.update(df['link'].tolist())
            except Exception as e:
                st.warning(f"读取工作表 {ws_name} 失败，跳过: {e}")
        return all_seen_links

    def get_all_articles(self):
        """获取所有日期工作表中的文章"""
        all_articles = []
        worksheet_names = self._get_all_worksheet_names()

        for ws_name in worksheet_names:
            try:
                df = self.conn.read(worksheet=ws_name)
                if not df.empty:
                    # 确保 'crawl_date' 列存在
                    if 'crawl_date' not in df.columns:
                        df['crawl_date'] = ws_name  # 如果没有，则使用工作表名称作为日期
                    all_articles.extend(df.to_dict(orient='records'))
            except Exception as e:
                st.warning(f"读取工作表 {ws_name} 失败，跳过: {e}")
        
        return all_articles

    def save_new_articles(self, articles):
        """将筛选出的文章存入以日期命名的新工作表"""
        if not articles:
            return
        
        today_date_str = pd.Timestamp.now().strftime('%Y-%m-%d')

        # 检查并创建工作表
        if today_date_str not in self._get_all_worksheet_names():
            if not self._create_worksheet(today_date_str):
                return # 创建失败则退出

        # 获取现有数据
        try:
            existing_df = self.conn.read(worksheet=today_date_str)
        except Exception as e:
            st.warning(f"读取工作表 {today_date_str} 失败，将创建新的 DataFrame: {e}")
            existing_df = pd.DataFrame(columns=['title', 'link', 'source', 'summary', 'crawl_date'])

        # 转换新数据，并添加抓取日期
        new_df = pd.DataFrame(articles)
        new_df['crawl_date'] = today_date_str # 添加抓取日期字段
        
        # 合并并去重 (基于link)
        final_df = pd.concat([existing_df, new_df]).drop_duplicates(subset=['link'])
        
        # 更新到 Google Sheets 对应的工作表
        self.conn.update(worksheet=today_date_str, data=final_df)