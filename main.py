import feedparser
import yaml
import os
import time
from datetime import datetime
from pygtrans import Translate
import google.generativeai as genai

# --- 1. 配置管理 ---
def load_config():
    with open("config.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

# --- 2. 去重管理 ---
DB_FILE = "seen_links.txt"
def load_seen_links():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return set(line.strip() for line in f)
    return set()

def save_seen_links(links):
    with open(DB_FILE, "a", encoding="utf-8") as f:
        for link in links:
            f.write(link + "\n")

# --- 3. 翻译逻辑 ---
def translate_text(text):
    client = Translate()
    if any(ord(c) < 128 for c in text): # 判定是否有英文
        try:
            res = client.translate(text, target='zh-CN')
            return res.translatedText
        except: return None
    return None

# --- 4. AI 批量判定逻辑 (关键重构) ---
def ai_batch_judge(articles, api_key):
    """
    接收文章列表，打包发送给 AI 批量判断。
    返回一个包含'相关'文章索引或标题的列表。
    """
    if not api_key or not articles:
        return []
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # 构造批量 Prompt
    items_text = ""
    for idx, art in enumerate(articles):
        items_text += f"ID: {idx} | 标题: {art['title']} | 摘要: {art['summary'][:100]}\n"
    
    prompt = f"""
    作为手游 UA 专家，请从以下新闻中筛选出与“移动端休闲游戏”（消除、合成、益智、模拟经营、超休闲、买量动态）相关的条目。
    
    待筛选列表：
    {items_text}
    
    请直接输出相关的 ID 编号，用逗号分隔（例如：0, 2, 5）。如果都没有，请输出 "NONE"。
    """
    
    try:
        response = model.generate_content(prompt)
        res_text = response.text.strip().upper()
        if "NONE" in res_text:
            return []
        
        # 解析返回的 ID
        import re
        relevant_ids = [int(i) for i in re.findall(r'\d+', res_text)]
        return [articles[i] for i in relevant_ids if i < len(articles)]
    except Exception as e:
        print(f"❌ AI 批量判断出错: {e}")
        return []

# --- 5. 主程序 ---
def generate_report():
    config = load_config()
    use_ai = config.get('use_ai', False)
    api_key = config.get('gemini_api_key', "")
    sources = config.get('rss_sources', [])
    keywords = config.get('filter_keywords', [])
    seen_links = load_seen_links()
    
    all_pending_articles = []
    final_relevant_articles = []
    
    print(f"🚀 开始采集阶段...")

    # --- 阶段 1: 纯抓取与初步去重 ---
    for source in sources:
        print(f"📡 抓取中: {source['name']}")
        feed = feedparser.parse(source['url'])
        for entry in feed.entries:
            if entry.link not in seen_links:
                all_pending_articles.append({
                    'title': entry.title,
                    'link': entry.link,
                    'summary': entry.get('summary', ''),
                    'source': source['name']
                })

    print(f"📦 采集完成，共发现 {len(all_pending_articles)} 条新资讯。")

    # --- 阶段 2: 判定阶段 ---
    if use_ai and all_pending_articles:
        print(f"🧠 进入 AI 批量筛选模式（每 10 条一组）...")
        # 按照 10 条一组进行切片处理
        for i in range(0, len(all_pending_articles), 10):
            batch = all_pending_articles[i:i+10]
            print(f"🤖 正在处理第 {i//10 + 1} 组数据...")
            relevant_batch = ai_batch_judge(batch, api_key)
            final_relevant_articles.extend(relevant_batch)
            time.sleep(4) # 组与组之间停留，彻底避免 429
    else:
        # 关键词模式逻辑
        print(f"🔍 进入关键词匹配模式...")
        for art in all_pending_articles:
            content = (art['title'] + art['summary']).lower()
            if any(kw.lower() in content for kw in keywords):
                final_relevant_articles.append(art)

    # --- 阶段 3: 翻译与生成报告 ---
    print(f"📝 正在生成最终报告（共 {len(final_relevant_articles)} 条有价值资讯）...")
    new_links_to_save = [art['link'] for art in all_pending_articles] # 记录所有已处理链接
    
    html_items = []
    for art in final_relevant_articles:
        translated = translate_text(art['title'])
        display_title = f"{translated}<br><small>原文: {art['title']}</small>" if translated else art['title']
        html_items.append(f'<li><a href="{art["link"]}" target="_blank">{display_title}</a> <span class="badge">{art["source"]}</span></li>')

    # 生成文件
    current_time_str = datetime.now().strftime("%Y-%m-%d_%H-%M")
    display_time = datetime.now().strftime("%Y年%m月%d日 %H:%M")
    file_name = f"report_{current_time_str}.html"
    
    html_template = f"""
    <html>
    <head><meta charset="utf-8"><title>游戏情报_{current_time_str}</title>
    <style>
        body {{ font-family: sans-serif; padding: 40px; background: #f5f7fa; line-height: 1.6; }}
        .container {{ max-width: 850px; margin: auto; background: white; padding: 40px; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.05); }}
        h1 {{ color: #2d3436; border-left: 8px solid #ff4757; padding-left: 20px; }}
        .badge {{ font-size: 12px; background: #dfe6e9; padding: 2px 8px; border-radius: 4px; color: #636e72; margin-left: 10px; }}
        li {{ padding: 20px 0; border-bottom: 1px solid #f1f1f1; }}
        a {{ color: #0984e3; text-decoration: none; font-size: 19px; font-weight: bold; }}
    </style>
    </head>
    <body>
        <div class="container">
            <h1>🎮 筛选后的休闲游戏情报</h1>
            <p>生成时间：{display_time} | 原始扫描：{len(all_pending_articles)} | 精选：{len(final_relevant_articles)}</p>
            <ul>{"".join(html_items) if html_items else "<li>暂无高价值资讯</li>"}</ul>
        </div>
    </body>
    </html>
    """
    
    with open(file_name, "w", encoding="utf-8") as f:
        f.write(html_template)
    
    save_seen_links(new_links_to_save)
    print(f"✅ 任务大功告成！报告：{file_name}")

if __name__ == "__main__":
    generate_report()