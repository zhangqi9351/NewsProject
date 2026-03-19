import pandas as pd
from streamlit_gsheets import GSheetsConnection
import streamlit as st

class DataManager:
    def __init__(self, st_connection):
        self.conn = st_connection

    def _get_all_worksheet_names(self):
        """获取所有工作表名称，增加容错处理"""
        try:
            # 尝试从连接对象中获取电子表格的所有 sheet 标题
            # 如果插件版本变动，这里使用最稳健的内部访问方式
            spreadsheet = self.conn._spreadsheet
            return [ws.title for ws in spreadsheet.worksheets()]
        except Exception:
            # 如果获取失败，返回空列表，后续逻辑会尝试直接写入
            return []

    def get_all_articles(self):
        """读取所有有效日期工作表的数据"""
        all_articles = []
        ws_names = self._get_all_worksheet_names()
        
        # 过滤掉默认的 Sheet1
        date_sheets = [n for n in ws_names if n != "Sheet1"]
        
        for ws_name in date_sheets:
            try:
                # 显式指定读取哪个工作表
                df = self.conn.read(worksheet=ws_name)
                if df is not None and not df.empty:
                    # 统一加上日期标识
                    df['crawl_date'] = ws_name
                    all_articles.extend(df.to_dict(orient='records'))
            except Exception:
                continue
        return all_articles

    def get_seen_links(self):
        """获取已存链接用于去重"""
        articles = self.get_all_articles()
        if not articles:
            return set()
        return set(str(a.get('link', '')) for a in articles)

    def save_new_articles(self, articles):
        """保存文章到以日期命名的工作表"""
        if not articles:
            return
        
        # 获取当前日期作为表名
        today_str = pd.Timestamp.now().strftime('%Y-%m-%d')
        
        try:
            new_df = pd.DataFrame(articles)
            # 确保包含日期列
            new_df['crawl_date'] = today_str
            
            # 【核心修复】：不再手动调用 create_worksheet
            # 直接调用 update，大多数版本的 st-gsheets-connection 会自动处理或提示
            # 如果报错，它会指引我们手动在 Google Sheets 里创建一个同名标签页
            self.conn.update(worksheet=today_str, data=new_df)
            st.toast(f"✅ 数据已成功同步至工作表: {today_str}")
        except Exception as e:
            st.error(f"❌ 自动保存失败。请手动在 Google Sheets 中新建一个名为 '{today_str}' 的标签页。")
            st.info(f"错误详情: {e}")