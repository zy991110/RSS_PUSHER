import os
import requests
import feedparser

# 配置项：订阅的 RSS 链接
RSS_URLS = [
    "https://sspai.com/feed",  # 示例：少数派
]

CORPID = os.getenv("WECHAT_CORPID")
AGENTID = os.getenv("WECHAT_AGENTID")
CORPSECRET = os.getenv("WECHAT_CORPSECRET")


def get_access_token():
    """获取企业微信 API 调用的 access_token"""
    url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={CORPID}&corpsecret={CORPSECRET}"
    res = requests.get(url).json()
    if res.get("errcode") == 0:
        return res.get("access_token")
    else:
        print("获取 access_token 失败：", res)
        return None


def send_wechat_textcard(title, description, url):
    """发送文本卡片消息到个人微信"""
    access_token = get_access_token()
    if not access_token:
        return

    send_url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={access_token}"

    payload = {
        "touser": "@all",           # 推送给企业内的所有人（也就是你自己）
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

    response = requests.post(send_url, json=payload)
    print("推送结果：", response.json())


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


if __name__ == "__main__":
    fetch_and_push()
