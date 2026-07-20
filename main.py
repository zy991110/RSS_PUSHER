import os
import requests
import feedparser

# 配置项：订阅的 RSS 链接
RSS_URLS = [
    "https://aihot.virxact.com/feed/daily.xml",  # AI 每日热点
]

PUSHPLUS_TOKEN = os.getenv("PUSHPLUS_TOKEN")
FEISHU_WEBHOOK = os.getenv("FEISHU_WEBHOOK")


def pushplus_send(title, content, url):
    """通过 PushPlus 推送到个人微信"""
    if not PUSHPLUS_TOKEN:
        print("缺少 PUSHPLUS_TOKEN 环境变量")
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
        print("缺少 FEISHU_WEBHOOK 环境变量")
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


def fetch_and_push():
    for rss_url in RSS_URLS:
        feed = feedparser.parse(rss_url)
        if feed.entries:
            latest = feed.entries[0]
            title = latest.title
            link = latest.link
            source = feed.feed.get('title', 'RSS 订阅')

            content = f"来源：{source}"
            full_title = f"📰 {title}"

            pushplus_send(title=full_title, content=content, url=link)
            feishu_send(title=full_title, content=content, url=link)
        else:
            print(f"未抓取到内容：{rss_url}")


if __name__ == "__main__":
    fetch_and_push()
