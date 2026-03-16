import pandas as pd
from streamlit_gsheets import GSheetsConnection

class DataManager:
    def __init__(self, st_connection):
        self.conn = st_connection
        self.sheet_name = "Sheet1"

    def get_seen_links(self):
        """获取已阅读的链接列表，用于去重"""
        try:
            df = self.conn.read(worksheet=self.sheet_name)
            return set(df['link'].tolist())
        except:
            return set()

    def get_all_articles(self):
        """获取所有已保存的文章"""
        st.write("尝试从 Google Sheets 读取所有文章...") # 添加日志
        try:
            df = self.conn.read(worksheet=self.sheet_name)
            st.write(f"从 Google Sheets 读取到 {len(df)} 条数据。") # 添加日志
            # 将DataFrame转换为字典列表，以便与文章结构匹配
            return df.to_dict(orient='records')
        except Exception as e: # 捕获具体异常以便调试
            st.error(f"读取 Google Sheets 失败: {e}") # 添加错误日志
            return []

    def save_new_articles(self, articles):
        """将 AI 筛选出的文章存入表格"""
        if not articles:
            return
            
        # 获取现有数据
        try:
            existing_df = self.conn.read(worksheet=self.sheet_name)
        except:
            existing_df = pd.DataFrame(columns=['title', 'link', 'source', 'date'])

        # 转换新数据
        new_df = pd.DataFrame(articles)
        new_df['date'] = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')
        
        # 合并并去重
        final_df = pd.concat([existing_df, new_df]).drop_duplicates(subset=['link'])
        
        # 更新到 Google Sheets
        self.conn.update(worksheet=self.sheet_name, data=final_df)