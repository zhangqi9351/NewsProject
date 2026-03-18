import google.generativeai as genai
import re
import time

def ai_batch_filter(articles, api_key, prompt_template):
    """
    将文章分组发送给 AI 进行手游 UA 视角下的筛选
    """
    if not api_key or not articles:
        return []
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # 构造批量 Prompt
    items_text = "\n".join([f"ID: {i} | 标题: {a['title']}" for i, a in enumerate(articles)])
    full_prompt = f"{prompt_template}\n\n待筛选列表：\n{items_text}"
    
    try:
        response = model.generate_content(full_prompt)
        res_text = response.text.strip().upper()
        if "NONE" in res_text:
            return []
        
        relevant_ids = [int(i) for i in re.findall(r'\d+', res_text)]
        return [articles[i] for i in relevant_ids if i < len(articles)]
    except Exception as e:
        print(f"❌ AI 筛选出错: {e}")
        return []