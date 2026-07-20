import os
import requests
import feedparser

# 配置项：订阅的 RSS 链接
RSS_URLS = [
    "https://sspai.com/feed",  # 示例：少数派
]

# 企业微信配置
AGENTID = os.getenv("WECHAT_AGENTID")
TOUSER = os.getenv("WECHAT_TOUSER", "@all")  # 默认 @all，可指定 UserID 如 "ZhangYu"

# Cloudflare Worker 代理配置
WORKER_URL = os.getenv("WORKER_URL")  # 例: https://wecom-rss-proxy.your-subdomain.workers.dev
WORKER_AUTH_TOKEN = os.getenv("WORKER_AUTH_TOKEN")  # 与 Worker 端 AUTH_TOKEN 保持一致


def send_wechat_textcard(title, description, url):
    """通过 Cloudflare Worker 代理发送文本卡片消息到个人微信"""
    if not WORKER_URL or not WORKER_AUTH_TOKEN:
        print("缺少 WORKER_URL 或 WORKER_AUTH_TOKEN 环境变量")
        return

    payload = {
        "touser": TOUSER,
        "msgtype": "textcard",
        "agentid": int(AGENTID),    # 企业微信 API 要求 agentid 为整型
        "textcard": {
            "title": title,
            "description": description,
            "url": url,
            "btntxt": "详情"
        },
        "enable_id_trans": 0,
        "enable_duplicate_check": 0
    }

    headers = {
        "Authorization": f"Bearer {WORKER_AUTH_TOKEN}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(WORKER_URL, json=payload, headers=headers, timeout=15)
        print("推送结果：", response.json())
    except Exception as e:
        print("推送异常：", e)


def fetch_and_push():
    for rss_url in RSS_URLS:
        feed = feedparser.parse(rss_url)
        if feed.entries:
            latest = feed.entries[0]
            title = latest.title
            link = latest.link
            source = feed.feed.get('title', 'RSS 订阅')

            # 简易摘要/描述
            description = f"来源：{source}\n发布更新，点击下方卡片直达文章。"

            send_wechat_textcard(
                title=f"📰 {title}",
                description=description,
                url=link
            )
        else:
            print(f"未抓取到内容：{rss_url}")


if __name__ == "__main__":
    fetch_and_push()
