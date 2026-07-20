# RSS_PUSHER

基于 GitHub Actions 的 RSS 定时推送服务，支持 PushPlus（个人微信）和飞书机器人双通道。

## 项目结构

```
RSS_PUSHER/
├── .github/workflows/        # GitHub Actions 定时任务
│   └── rss-ai.yml            # AI 热点：每天早 9 点推送
├── common/
│   └── push.py               # 公共推送逻辑（PushPlus + 飞书）
├── feeds/
│   └── ai_hot.py             # AI 热点 RSS 抓取脚本
├── requirements.txt          # Python 依赖
└── README.md                 # 本文档
```

## 已集成的推送渠道

- **PushPlus**：推送到个人微信（需实名认证）
- **飞书机器人**：推送到飞书群聊

## 快速开始

### 1. Fork 或克隆本仓库

```bash
git clone https://github.com/zy991110/RSS_PUSHER.git
```

### 2. 配置 GitHub Secrets

进入仓库 `Settings → Secrets and variables → Actions → New repository secret`，添加：

| Secret 名称 | 说明 | 是否必填 |
| --- | --- | --- |
| `PUSHPLUS_TOKEN` | PushPlus 一对一推送 Token | 否（不填则跳过微信推送） |
| `FEISHU_WEBHOOK` | 飞书自定义机器人 Webhook 地址 | 否（不填则跳过飞书推送） |

> 注意：两个至少填一个，否则脚本不会推送任何消息。

### 3. 手动测试

进入仓库 `Actions` 页面，选择对应 workflow，点击 **Run workflow** 手动触发一次。

## 添加新的 RSS 源

### 方式一：修改现有脚本

直接编辑 `feeds/ai_hot.py` 中的 `RSS_URLS` 列表：

```python
RSS_URLS = [
    "https://aihot.virxact.com/feed/daily.xml",
    "https://sspai.com/feed",
]
```

### 方式二：新增独立脚本和定时任务（推荐）

1. 在 `feeds/` 目录下新建脚本，例如 `feeds/tech_news.py`：

```python
import feedparser
from common.push import send_all

RSS_URLS = ["https://www.36kr.com/feed"]


def fetch_and_push():
    for rss_url in RSS_URLS:
        feed = feedparser.parse(rss_url)
        if feed.entries:
            latest = feed.entries[0]
            send_all(
                title=f"📰 {latest.title}",
                content="来源：36氪",
                url=latest.link
            )


if __name__ == "__main__":
    fetch_and_push()
```

2. 在 `.github/workflows/` 下新建 workflow，例如 `.github/workflows/rss-tech.yml`：

```yaml
name: 科技新闻推送

on:
  schedule:
    - cron: '0 * * * *'   # 每小时
  workflow_dispatch:

jobs:
  push-rss:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
      - env:
          PUSHPLUS_TOKEN: ${{ secrets.PUSHPLUS_TOKEN }}
          FEISHU_WEBHOOK: ${{ secrets.FEISHU_WEBHOOK }}
        run: PYTHONPATH=. python feeds/tech_news.py
```

## 修改定时频率

GitHub Actions 使用 UTC 时间，北京时间 = UTC + 8。

常用 cron 示例：

| 需求 | cron |
| --- | --- |
| 每天早 9 点 | `0 1 * * *` |
| 每天早 7 点 | `0 23 * * *` |
| 每小时 | `0 * * * *` |
| 每周一早 9 点 | `0 1 * * 1` |

## 推送额度说明

### PushPlus

- 实名用户微信渠道每日 **200 次**
- 1 分钟内最多 **5 次**
- 相同内容 1 小时内最多 **3 条**
- 详情见 [PushPlus 官方限制说明](https://www.pushplus.plus/doc/help/limit.html)

### 飞书机器人

飞书 Webhook 机器人本身没有明确的每日调用上限，但高频调用可能触发风控。建议用于个人/小群场景。

## 更换电脑是否有影响

**没有任何影响。**

- 代码保存在 GitHub 仓库中
- 定时任务由 GitHub Actions 在云端执行
- Secrets 存储在 GitHub 服务器上
- 本地电脑仅用于编辑代码，换电脑后 `git clone` 即可

## 常见问题

### PushPlus 返回 `905 账户未进行实名认证`

访问 https://verify.pushplus.plus 完成实名认证后再试。

### 飞书机器人只能发到群聊？

飞书 Webhook 机器人确实只能发到群。如需近似私聊体验，可创建一个只有你一个人的群聊，把机器人加入其中。

### 可以只推送到其中一个渠道吗？

可以。只配置 `PUSHPLUS_TOKEN` 就推微信，只配置 `FEISHU_WEBHOOK` 就推飞书，两个都配则双推。

## 技术说明

本项目使用：

- [feedparser](https://pypi.org/project/feedparser/) 解析 RSS
- [requests](https://pypi.org/project/requests/) 发送 HTTP 请求
- [PushPlus](http://www.pushplus.plus/) 推送到个人微信
- 飞书自定义机器人 Webhook 推送到飞书群
- GitHub Actions 提供定时任务调度

## License

MIT
