import pandas as pd
from streamlit_gsheets import GSheetsConnection
import streamlit as st

class DataManager:
    def __init__(self, st_connection):
        self.conn = st_connection
        self.sheet_name = "Sheet1" 
        self.ai_sheet = "ai"       
        self.feed_sheet = "feeds"   

    @staticmethod
    def _normalize_columns(df):
        if df is None or df.empty:
            return pd.DataFrame() if df is None else df
        normalized = df.copy()
        normalized.columns = [
            str(col).replace('\ufeff', '').strip().lower().replace(' ', '_').replace('-', '_')
            for col in normalized.columns
        ]
        return normalized

    @staticmethod
    def _is_truthy(value):
        if pd.isna(value):
            return False
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value == 1
        return str(value).strip().lower() in {
            'true', '1', '1.0', 'yes', 'y', 'on', 'enabled', '是', '启用'
        }

    def _read_sheet(self, worksheet, ttl=0, show_errors=False, error_prefix="读取数据失败"):
        """统一处理表格读取，避免连接异常直接打断整个页面。"""
        try:
            df = self.conn.read(worksheet=worksheet, ttl=ttl)
            if df is None:
                return pd.DataFrame()
            if isinstance(df, pd.DataFrame):
                return self._normalize_columns(df)
            return self._normalize_columns(pd.DataFrame(df))
        except Exception as e:
            if show_errors:
                st.error(f"{error_prefix}: {type(e).__name__}: {e}")
            return pd.DataFrame()

    def get_active_feeds(self):
        """从 feeds 工作表读取所有启用的 RSS 源"""
        try:
            df = self._read_sheet(
                worksheet=self.feed_sheet,
                ttl=0,
                show_errors=True,
                error_prefix="读取 feeds 表失败",
            )
            if df.empty:
                st.warning("feeds 表已读取成功，但当前没有可识别的数据行")
                return []

            if 'url' not in df.columns:
                st.error(f"feeds 表缺少 url 列，当前列为: {', '.join(map(str, df.columns))}")
                return []
            if 'is_active' not in df.columns:
                st.error(f"feeds 表缺少 is_active 列，当前列为: {', '.join(map(str, df.columns))}")
                return []

            df = df.dropna(how='all').copy()
            df['url'] = df['url'].fillna('').astype(str).str.strip()
            df = df[df['url'] != ""]
            if df.empty:
                st.warning("feeds 表中没有有效的 url 配置")
                return []

            # 兼容 Google Sheets 勾选框、布尔值和字符串格式。
            mask = df['is_active'].apply(self._is_truthy)
            active_feeds = df[mask]
            if active_feeds.empty:
                sample_values = ", ".join(sorted({str(v).strip() for v in df['is_active'].dropna().tolist()})) or "空"
                st.warning(
                    f"feeds 表已读取到 {len(df)} 条源，但没有识别出启用项。"
                    f" is_active 当前值示例: {sample_values}"
                )
                return []

            if 'name' not in active_feeds.columns:
                active_feeds['name'] = '未命名源'
            return active_feeds.to_dict(orient='records')
        except Exception as e:
            st.error(f"读取 feeds 表失败: {type(e).__name__}: {e}")
            return []

    def get_all_articles(self, use_cache=True, show_errors=False):
        try:
            # 使用数值型 ttl，兼容更多 Streamlit / connector 版本。
            ttl = 300 if use_cache else 0
            df = self._read_sheet(
                worksheet=self.sheet_name,
                ttl=ttl,
                show_errors=show_errors,
                error_prefix=f"读取文章数据失败，请检查 {self.sheet_name} 工作表",
            )
            if not df.empty:
                if 'crawl_date' in df.columns:
                    df['crawl_date'] = pd.to_datetime(df['crawl_date'], errors='coerce')
                return df.to_dict(orient='records')
            return []
        except Exception as e:
            if show_errors:
                st.error(f"读取文章数据失败，请检查 {self.sheet_name} 工作表: {type(e).__name__}: {e}")
            return []

    def get_seen_links(self):
        articles = self.get_all_articles(use_cache=False)
        return {
            str(a.get('link', '')).strip()
            for a in articles
            if str(a.get('link', '')).strip()
        } if articles else set()

    def save_new_articles(self, new_articles):
        if not new_articles:
            return 0
        try:
            existing_df = self._read_sheet(worksheet=self.sheet_name, ttl=0)
            new_df = pd.DataFrame(new_articles)
            if 'link' in new_df.columns:
                new_df['link'] = new_df['link'].astype(str).str.strip()
                new_df = new_df[new_df['link'] != ""]
                new_df = new_df.drop_duplicates(subset=['link'])

            new_df['crawl_date'] = pd.Timestamp.now().strftime('%Y-%m-%d')

            if existing_df is not None and not existing_df.empty:
                existing_df = existing_df.dropna(how='all', axis=0)
                if 'link' in existing_df.columns:
                    existing_df['link'] = existing_df['link'].astype(str).str.strip()
                    existing_links = set(existing_df['link'][existing_df['link'] != ""])
                    new_df = new_df[~new_df['link'].isin(existing_links)]

                if new_df.empty:
                    st.toast("☕ 本次抓取结果均已存在，未新增数据")
                    return 0

                final_df = pd.concat([existing_df, new_df], ignore_index=True)
            else:
                if new_df.empty:
                    st.toast("☕ 本次抓取结果没有可保存的有效链接")
                    return 0
                final_df = new_df

            saved_count = len(new_df)
            self.conn.update(worksheet=self.sheet_name, data=final_df)
            st.toast(f"✅ 成功存入 {saved_count} 条情报")
            return saved_count
        except Exception as e:
            st.error(f"保存文章失败: {e}")
            return 0

    def get_ai_history(self):
        try:
            df = self._read_sheet(worksheet=self.ai_sheet, ttl=0)
            if not df.empty and {'crawl_date', 'content'}.issubset(df.columns):
                return df.set_index('crawl_date')['content'].to_dict()
            return {}
        except Exception:
            return {}

    def save_ai_summary(self, date_str, content):
        try:
            existing_df = self._read_sheet(worksheet=self.ai_sheet, ttl=0)
            new_data = pd.DataFrame([{"crawl_date": date_str, "content": content}])
            if existing_df is not None and not existing_df.empty:
                if date_str in existing_df['crawl_date'].values: return
                final_df = pd.concat([existing_df, new_data], ignore_index=True)
            else:
                final_df = new_data
            self.conn.update(worksheet=self.ai_sheet, data=final_df)
        except Exception as e:
            st.error(f"AI 总结保存失败: {e}")
