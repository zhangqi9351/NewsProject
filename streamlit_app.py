import streamlit as st
import feedparser
import google.generativeai as genai
import time
import re
from datetime import datetime

# --- 页面基础配置 ---
st.set_page_config(page_title="游戏情报站", layout="wide", page_icon="🎮")

# --- 逻辑函数 (从 main.py 迁移并优化) ---

def fetch_rss_data(sources):
    """抓取所有 RSS 源数据"""
    all_articles = []
    for source in sources:
        try:
            feed = feedparser.parse(source['url'])
            for entry in feed.entries:
                all_articles.append({
                    'title': entry.title,
                    'link': entry.link,
                    'summary': entry.get('summary', ''),
                    'source': source['name']
                })
        except Exception as e:
            st.warning(f"无法抓取 {source['name']}: {e}")
    return all_articles

def ai_batch_judge(articles, api_key):
    """AI 批量判定逻辑 (每 10 条一组)"""
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    relevant_articles = []
    
    # 分组处理
    batch_size = 10
    total_batches = (len(articles) + batch_size - 1) // batch_size
    progress_bar = st.progress(0)
    status_text = st.empty()

    for i in range(0, len(articles), batch_size):
        batch = articles[i:i+batch_size]
        status_text.text(f"🤖 AI 正在审核第 {i//batch_size + 1}/{total_batches} 组数据...")
        
        items_text = ""
        for idx, art in enumerate(batch):
            items_text += f"ID: {idx} | 标题: {art['title']} | 摘要: {art['summary'][:100]}\n"
        
        prompt = f"""
        作为手游 UA 专家，请从以下新闻中筛选出与“移动端休闲游戏”（消除、合成、益智、模拟经营、超休闲、买量动态）相关的条目。
        请直接输出相关的 ID 编号，用逗号分隔（例如：0, 2, 5）。如果都没有，请输出 "NONE"。
        
        待筛选列表：
        {items_text}
        """
        
        try:
            response = model.generate_content(prompt)
            res_text = response.text.strip().upper()
            if "NONE" not in res_text:
                ids = [int(n) for n in re.findall(r'\d+', res_text)]
                for valid_id in ids:
                    if valid_id < len(batch):
                        relevant_articles.append(batch[valid_id])
            
            # 更新进度
            progress_bar.progress((i + batch_size) / len(articles) if (i + batch_size) < len(articles) else 1.0)
            time.sleep(4)  # 频率控制
        except Exception as e:
            st.error(f"AI 判定出错: {e}")
            
    return relevant_articles

# --- UI 界面 ---

st.title("🎮 移动游戏市场智能观察哨")
st.caption("基于 Gemini 1.5 Flash 的自动化情报筛选系统")

# 侧边栏配置
with st.sidebar:
    st.header("配置中心")
    # 默认从你之前的 config.yaml 逻辑中提取源
    api_key_input = st.text_input("Gemini API Key", type="password", value="")
    
    st.divider()
    st.subheader("📡 当前监测源")
    # 这里建议直接列出你 config.yaml 里的源
    sources = [
        {"name": "机核网", "url": "https://www.gcores.com/rss"},
        {"name": "indienova", "url": "https://indienova.com/itunes/blog/rss"},
        {"name": "触乐", "url": "http://www.chuapp.com/feed"},
        {"name": "PocketGamer", "url": "https://www.pocketgamer.com/rss"},
        {"name": "Gamezebo", "url": "https://www.gamezebo.com/feed/"}
    ]
    for s in sources:
        st.text(f"• {s['name']}")

# 主执行逻辑
if st.button("🚀 立即同步并开始 AI 筛选", use_container_width=True):
    if not api_key_input:
        st.error("请输入 API Key 以启动 AI 引擎")
    else:
        # 1. 抓取
        with st.status("正在采集全球 RSS 资讯...", expanded=True) as status:
            raw_data = fetch_rss_data(sources)
            st.write(f"✅ 采集完成，共发现 {len(raw_data)} 条新内容。")
            
            # 2. 筛选
            st.write("🧠 启动 AI 专家模式进行筛选...")
            final_list = ai_batch_judge(raw_data, api_key_input)
            status.update(label="处理完成！", state="complete", expanded=False)

        # 3. 结果展示
        if final_list:
            st.subheader(f"🎯 AI 精选情报 ({len(final_list)})")
            
            # 模仿你 main.py 里的列表展示
            for art in final_list:
                with st.expander(f"【{art['source']}】{art['title']}", expanded=True):
                    st.write(art['summary'][:300] + "...")
                    st.link_button("阅读全文", art['link'])
        else:
            st.success("☕️ 暂无符合休闲游戏标签的新闻。")