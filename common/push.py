import os
import requests

PUSHPLUS_TOKEN = os.getenv("PUSHPLUS_TOKEN")
FEISHU_WEBHOOK = os.getenv("FEISHU_WEBHOOK")


def pushplus_send(title, content, url):
    """通过 PushPlus 推送到个人微信"""
    if not PUSHPLUS_TOKEN:
        print("缺少 PUSHPLUS_TOKEN 环境变量，跳过 PushPlus 推送")
        return

    api_url = "http://www.pushplus.plus/send"
    payload = {
        "token": PUSHPLUS_TOKEN,
        "title": title,
        "content": f"{content}<br><br><a href='{url}'>点击阅读原文</a>",
        "template": "html",
        "channel": "wechat"
    }

    try:
        response = requests.post(api_url, json=payload, timeout=15)
        print("PushPlus 推送结果：", response.json())
    except Exception as e:
        print("PushPlus 推送异常：", e)


def feishu_send(title, content, url):
    """通过飞书机器人 Webhook 推送到飞书群"""
    if not FEISHU_WEBHOOK:
        print("缺少 FEISHU_WEBHOOK 环境变量，跳过飞书推送")
        return

    payload = {
        "msg_type": "text",
        "content": {
            "text": f"{title}\n\n{content}\n\n阅读原文：{url}"
        }
    }

    try:
        response = requests.post(FEISHU_WEBHOOK, json=payload, timeout=15)
        print("飞书推送结果：", response.json())
    except Exception as e:
        print("飞书推送异常：", e)


def send_all(title, content, url):
    """同时推送到所有已配置的渠道"""
    pushplus_send(title=title, content=content, url=url)
    feishu_send(title=title, content=content, url=url)
