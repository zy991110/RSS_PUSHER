import feedparser
from common.push import send_all

# 配置项：订阅的 RSS 链接
RSS_URLS = [
    "https://aihot.virxact.com/feed/daily.xml",  # AI 每日热点
]


def fetch_and_push():
    for rss_url in RSS_URLS:
        feed = feedparser.parse(rss_url)
        if feed.entries:
            latest = feed.entries[0]
            title = latest.title
            link = latest.link
            source = feed.feed.get('title', 'RSS 订阅')

            send_all(
                title=f"📰 {title}",
                content=f"来源：{source}",
                url=link
            )
        else:
            print(f"未抓取到内容：{rss_url}")


if __name__ == "__main__":
    fetch_and_push()
