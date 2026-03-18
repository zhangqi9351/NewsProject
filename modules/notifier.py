import requests
import json

def send_feishu_message(webhook_url, text):
    """
    发送消息到飞书群机器人
    """
    if not webhook_url:
        return
    
    headers = {"Content-Type": "application/json"}
    payload = {
        "msg_type": "text",
        "content": {"text": text}
    }
    
    try:
        response = requests.post(webhook_url, data=json.dumps(payload), headers=headers)
        return response.json()
    except Exception as e:
        print(f"❌ 飞书推送失败: {e}")