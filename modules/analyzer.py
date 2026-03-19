import google.generativeai as genai
import streamlit as st

def get_ai_global_insight(articles, api_key, time_range="当日"):
    """
    对给定的文章列表进行全局总结。
    time_range: 可以是 '当日' 或 '当周'
    """
    if not api_key or not articles:
        return "⚠️ 未发现资讯或未配置 API Key，无法生成总结。"
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # 提取所有标题和来源，构造精简的阅读列表
    content_summary = "\n".join([f"- [{a['source']}] {a['title']}" for a in articles])
    
    prompt = f"""
    你是一位资深的移动游戏市场分析师和 UA 专家。以下是{time_range}采集到的游戏行业情报标题列表：
    {content_summary}
    
    请根据以上内容，提供一份深度的行业简报，包含以下三个部分：
    1. 📌 【核心趋势】：用 2-3 句话总结今天/本周最值得关注的行业动向。
    2. 📈 【UA & 营销洞察】：从这些资讯中，提炼出对移动游戏买量或投放有参考价值的信息。
    3. 💡 【开发者建议】：针对休闲游戏的独立开发者或中小厂商，给出一条行动建议。
    
    要求：专业、干练、不要口水话。
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"❌ AI 总结生成失败: {str(e)}"