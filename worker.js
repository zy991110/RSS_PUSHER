/**
 * Cloudflare Worker：RSS 抓取 + 推送到微信（PushPlus）和飞书
 *
 * 触发方式：Cloudflare Cron Trigger
 * 默认配置：每天北京时间 9:00 运行一次
 */

const RSS_URLS = [
  "https://aihot.virxact.com/feed/daily.xml",
];

export default {
  async fetch(request, env, ctx) {
    // 支持 HTTP 访问手动触发，便于测试
    ctx.waitUntil(run(env));
    return new Response("RSS 推送已触发，请查看 Logs", { status: 200 });
  },
  async scheduled(event, env, ctx) {
    ctx.waitUntil(run(env));
  },
};

async function run(env) {
  for (const rssUrl of RSS_URLS) {
    try {
      const entry = await fetchLatestEntry(rssUrl);
      if (!entry) {
        console.log(`未抓取到内容：${rssUrl}`);
        continue;
      }

      const title = `📰 ${entry.title}`;
      const content = `来源：${entry.source}`;

      await Promise.all([
        pushplusSend(env.PUSHPLUS_TOKEN, title, content, entry.link),
        feishuSend(env.FEISHU_WEBHOOK, title, content, entry.link),
      ]);
    } catch (e) {
      console.error(`处理 RSS 失败：${rssUrl}`, e);
    }
  }
}

async function fetchLatestEntry(rssUrl) {
  const res = await fetch(rssUrl, {
    headers: {
      "User-Agent": "Mozilla/5.0 (compatible; RSS-Pusher/1.0)",
    },
  });
  if (!res.ok) {
    throw new Error(`HTTP ${res.status}`);
  }

  const xml = await res.text();
  const title = extractTag(xml, "title");
  const link = extractTag(xml, "link");
  const source = extractChannelTitle(xml) || "RSS 订阅";

  if (!title || !link) {
    return null;
  }

  return { title, link, source };
}

function extractTag(xml, tagName) {
  // 匹配第一个 <tagName>内容</tagName>，支持 CDATA
  const regex = new RegExp(`<${tagName}[^>]*>(?:<!\\[CDATA\\[)?(.*?)(?:\\]\\]>)?</${tagName}>`, "i");
  const match = xml.match(regex);
  return match ? decodeXmlEntities(match[1].trim()) : null;
}

function extractChannelTitle(xml) {
  const channelMatch = xml.match(/<channel[^>]*>([\s\S]*?)<\/channel>/i);
  if (channelMatch) {
    return extractTag(channelMatch[1], "title");
  }
  return null;
}

function decodeXmlEntities(str) {
  return str
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&amp;/g, "&")
    .replace(/&quot;/g, '"')
    .replace(/&apos;/g, "'");
}

async function pushplusSend(token, title, content, url) {
  if (!token) {
    console.log("缺少 PUSHPLUS_TOKEN，跳过微信推送");
    return;
  }

  const res = await fetch("http://www.pushplus.plus/send", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      token,
      title,
      content: `${content}<br><br><a href='${url}'>点击阅读原文</a>`,
      template: "html",
      channel: "wechat",
    }),
  });

  const data = await res.json();
  console.log("PushPlus 推送结果：", JSON.stringify(data));
}

async function feishuSend(webhook, title, content, url) {
  if (!webhook) {
    console.log("缺少 FEISHU_WEBHOOK，跳过飞书推送");
    return;
  }

  const res = await fetch(webhook, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      msg_type: "text",
      content: {
        text: `${title}\n\n${content}\n\n阅读原文：${url}`,
      },
    }),
  });

  const data = await res.json();
  console.log("飞书推送结果：", JSON.stringify(data));
}
