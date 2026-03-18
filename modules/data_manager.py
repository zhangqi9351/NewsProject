import pandas as pd
from streamlit_gsheets import GSheetsConnection
import streamlit as st

class DataManager:
    """
    数据管理类：负责与 Google Sheets 进行交互，包括读取已处理链接和保存新文章。
    注意：此类不应包含任何顶层执行逻辑。
    """
    def __init__(self, st_connection):
        # 接收从外部（主程序）传入的连接对象
        self.conn = st_connection

    def _get_all_worksheet_names(self):
        """获取 Google Sheet 中所有工作表的名称"""
        try:
            # 基础连接有效性检查
            if not hasattr(self.conn, '_spreadsheet') or self.conn._spreadsheet is None:
                st.error("⚠️ Google Sheets 连接未就绪，请检查 secrets 配置或权限。")
                return []
            
            return [ws.title for ws in self.conn._spreadsheet.worksheets()]
        except Exception as e:
            st.error(f"❌ 无法获取工作表列表: {e}")
            return []

    def _create_worksheet(self, worksheet_name):
        """创建新的工作表"""
        try:
            # 调用连接对象的创建方法
            self.conn.create_worksheet(worksheet_name=worksheet_name)
            return True
        except Exception as e:
            st.error(f"❌ 创建工作表 {worksheet_name} 失败: {e}")
            return False

    def get_seen_links(self):
        """汇总所有工作表中的链接，用于去重"""
        all_articles = self.get_all_articles()
        return set(str(art.get('link', '')) for art in all_articles if 'link' in art)

    def get_all_articles(self):
        """读取所有工作表的数据"""
        all_articles = []
        ws_names = self._get_all_worksheet_names()
        
        for ws_name in ws_names:
            try:
                df = self.conn.read(worksheet=ws_name)
                if not df.empty:
                    # 统一日期字段
                    if 'crawl_date' not in df.columns:
                        df['crawl_date'] = ws_name
                    all_articles.extend(df.to_dict(orient='records'))
            except Exception as e:
                st.warning(f"读取工作表 {ws_name} 失败: {e}")
        
        return all_articles

    def save_new_articles(self, articles):
        """将筛选出的文章存入以日期命名的新工作表"""
        if not articles:
            return
        
        # 使用当前日期作为工作表名
        today_date_str = pd.Timestamp.now().strftime('%Y-%m-%d')

        # 检查并确保工作表存在
        existing_ws = self._get_all_worksheet_names()
        if today_date_str not in existing_ws:
            if not self._create_worksheet(today_date_str):
                return 

        # 写入数据
        try:
            new_df = pd.DataFrame(articles)
            if 'crawl_date' not in new_df.columns:
                new_df['crawl_date'] = today_date_str
            
            # 追加数据到 Google Sheets
            self.conn.update(worksheet=today_date_str, data=new_df)
        except Exception as e:
            st.error(f"❌ 保存数据至 Google Sheets 失败: {e}")

# --- 严禁在此处编写 dm = DataManager(...) 等调用代码 ---