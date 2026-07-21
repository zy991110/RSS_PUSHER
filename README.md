# RSS_PUSHER

基于 Cloudflare Worker 的 RSS 定时推送服务，支持 PushPlus（个人微信）和飞书机器人双通道。

> 旧版使用 GitHub Actions + cron-job.org 触发，现统一迁移到 Cloudflare Worker Cron Trigger，部署和维护更简单。

## 项目结构

```
RSS_PUSHER/
├── worker.js           # Cloudflare Worker 入口：RSS 抓取 + 推送
├── wrangler.toml       # Wrangler 部署配置 + Cron Trigger
├── common/             # Python 公共推送模块（旧版保留，可选）
├── feeds/              # Python RSS 脚本（旧版保留，可选）
├── requirements.txt    # Python 依赖（旧版保留，可选）
└── README.md           # 本文档
```

## 已集成的推送渠道

- **PushPlus**：推送到个人微信（需实名认证）
- **飞书机器人**：推送到飞书群聊

## 快速开始

### 1. 注册/登录 Cloudflare

访问 https://dash.cloudflare.com/sign-up 注册（免费，无需信用卡）。

### 2. 创建 Worker

1. 左侧菜单 → **Workers & Pages**
2. 点 **Create** → **Create Worker**
3. 名字填 `rss-pusher`（或任意名字）
4. 点 **Deploy**
5. 部署后点 **Edit code**
6. 清空默认代码，粘贴 [worker.js](worker.js) 全部内容
7. 点 **Save and deploy**

> 注意：创建时**不要选 Connect to Git**，避免和之前一样的部署问题。

### 3. 配置环境变量

进入 Worker 详情页 → **Settings** → **Variables and Secrets** → **Add**：

| Type | Name | Value |
| --- | --- | --- |
| Secret | `PUSHPLUS_TOKEN` | 你的 PushPlus Token |
| Secret | `FEISHU_WEBHOOK` | 飞书机器人 Webhook 地址 |

两个至少配置一个，都配置则双推。

### 4. 配置定时触发

Worker 详情页 → **Settings** → **Triggers** → **Cron Triggers** → **Add**：

| Cron Expression | Time zone |
| --- | --- |
| `0 1 * * *` | Asia/Shanghai |

`0 1 * * *` 表示每天 UTC 1:00，即北京时间 9:00。

### 5. 手动测试

Worker 详情页 → **Overview** → 右侧找到 **Triggers** 卡片 → 点你的 Cron Trigger 旁边的 **Run** 按钮（或直接点 **Save and deploy** 后等下次触发）。

也可以发送一次 HTTP POST 到 Worker URL 手动触发（需要在 worker.js 里加 `fetch` 事件处理，当前版本仅支持 Cron）。

## 自定义 RSS 源

编辑 [worker.js](worker.js) 顶部的 `RSS_URLS`：

```javascript
const RSS_URLS = [
  "https://aihot.virxact.com/feed/daily.xml",
  "https://sspai.com/feed",
];
```

保存并重新 Deploy。

## 自定义推送格式

### PushPlus 推送内容

修改 `pushplusSend` 函数里的 `payload`：

```javascript
body: JSON.stringify({
  token,
  title,
  content: `你想展示的内容`,
  template: "html",  // 可选 html / txt / markdown
  channel: "wechat",
}),
```

### 飞书推送内容

修改 `feishuSend` 函数里的 `payload`。

## 修改定时频率

编辑 [wrangler.toml](wrangler.toml)：

```toml
[triggers]
crons = ["0 1 * * *"]
```

常用示例：

| 需求 | Cron（UTC） | 北京时间 |
| --- | --- | --- |
| 每天早 9 点 | `0 1 * * *` | 09:00 |
| 每天早 7 点 | `0 23 * * *` | 07:00（前一天 UTC） |
| 每小时 | `0 * * * *` | 每整点 |
| 每周一早 9 点 | `0 1 * * 1` | 周一 09:00 |

也可以在 Cloudflare Dashboard 的 **Cron Triggers** 里直接修改。

## 多源不同频率推送

如果不同 RSS 源需要不同推送时间，推荐创建多个 Worker：

| Worker | Cron | RSS 源 |
| --- | --- | --- |
| `rss-ai-hot` | 每天 9:00 | AI 热点 |
| `rss-tech-news` | 每天 18:00 | 科技新闻 |
| `rss-weekly` | 每周一 9:00 | 周刊 |

每个 Worker 独立部署、独立管理，互不干扰。

## 推送额度说明

### PushPlus

- 实名用户微信渠道每日 **200 次**
- 1 分钟内最多 **5 次**
- 相同内容 1 小时内最多 **3 条**
- 详情见 [PushPlus 官方限制说明](https://www.pushplus.plus/doc/help/limit.html)

### 飞书机器人

飞书 Webhook 机器人没有明确的每日调用上限，但高频调用可能触发风控。建议用于个人/小群场景。

## 为什么从 GitHub Actions 迁到 Cloudflare Worker

旧方案：

```
GitHub Actions schedule（不触发）
  ↓
cron-job.org + GitHub PAT
  ↓
GitHub Actions workflow_dispatch
  ↓
Python 脚本
```

问题：GitHub Actions 的 `schedule` 事件在该仓库始终不触发，被迫引入 cron-job.org 和 PAT，维护复杂。

新方案：

```
Cloudflare Worker Cron Trigger
  ↓
Worker 抓取 RSS
  ↓
PushPlus / 飞书
```

优势：

- 没有 GitHub Actions
- 没有 cron-job.org
- 没有 PAT
- 定时触发内置于 Cloudflare
- 一个 Worker 文件搞定全部

## 常见问题

### 如何获取 PushPlus Token

1. 访问 http://www.pushplus.plus/
2. 微信扫码登录
3. 复制「一对一推送」Token

### 如何获取飞书 Webhook

1. 飞书群 → 群设置 → 群机器人 → 添加机器人
2. 选「自定义机器人」
3. 复制 Webhook 地址

### 飞书能私聊吗

不能。飞书 Webhook 机器人只能发到群聊。如需近似私聊体验，创建一个只有你一个人的群聊，把机器人加入其中。

### Worker 部署后报错怎么办

1. 检查 Worker 详情页 **Logs**，看具体错误
2. 确认 `PUSHPLUS_TOKEN` 和 `FEISHU_WEBHOOK` 已正确添加为 Secret
3. 确认 Cron Trigger 时区是 `Asia/Shanghai`

## 技术说明

- [Cloudflare Workers](https://workers.cloudflare.com/)：无服务器计算平台
- [Cloudflare Cron Triggers](https://developers.cloudflare.com/workers/configuration/cron-triggers/)：定时触发 Worker
- [PushPlus](http://www.pushplus.plus/)：微信消息推送服务
- 飞书自定义机器人 Webhook

## License

MIT
