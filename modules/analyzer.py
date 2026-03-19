import google.generativeai as genai
import streamlit as st

def get_ai_global_insight(articles, api_key, time_range="当日"):
    """
    对给定的文章列表进行全局总结。
    """
    if not api_key:
        return "⚠️ 未配置 Gemini API Key，请在 config.yaml 中检查。"
    
    if not articles:
        return "📅 该时间段内暂无资讯，无法生成总结。"
    
    try:
        # 配置 AI
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-Flash-Lite')
        
        # 构造阅读列表
        content_summary = ""
        for a in articles:
            source = a.get('source', '未知来源')
            title = a.get('title', '无标题')
            content_summary += f"- [{source}] {title}\n"
        
        prompt = f"""
        你是一位资深的移动游戏市场分析师和 UA 专家。以下是{time_range}采集到的游戏行业情报标题列表：
        {content_summary}
        
        请根据以上内容，提供一份深度的行业简报，包含以下三个部分：
        1. 📌 【核心趋势】：总结最值得关注的行业动向。
        2. 📈 【UA & 营销洞察】：提炼对买量或投放有参考价值的信息。
        3. 💡 【决策建议】：针对中小厂商给出一条行动建议。
        
        要求：专业、干练、使用中文。
        """
        
        response = model.generate_content(prompt)
        return response.text
        
    except Exception as e:
        return f"❌ AI 总结生成失败，错误信息: {str(e)}"