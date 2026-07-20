/**
 * Cloudflare Worker：企业微信消息转发代理
 *
 * 作用：
 *   - 接收 GitHub Actions 的 POST 请求
 *   - 用环境变量里的 corpid + corpsecret 换取 access_token
 *   - 把消息体转发给企业微信 message/send 接口
 *   - 返回企业微信的响应给调用方
 *
 * 环境变量（在 Cloudflare Dashboard 配置）：
 *   - WECHAT_CORPID      企业 ID
 *   - WECHAT_CORPSECRET  应用 Secret
 *   - AUTH_TOKEN         自定义鉴权 token，防止 Worker URL 被滥用
 */

const WECOM_API_BASE = "https://qyapi.weixin.qq.com/cgi-bin";

// 企业微信 outbound IP 段：https://open.work.weixin.qq.com/api/doc/90000/90135/90137
// 实际上是 Cloudflare 的 IP 段会被企业微信看到，这里只是注释参考

export default {
  async fetch(request, env) {
    // 仅允许 POST
    if (request.method !== "POST") {
      return json({ ok: false, error: "method not allowed" }, 405);
    }

    // 简单鉴权：Authorization: Bearer <AUTH_TOKEN>
    const auth = request.headers.get("Authorization") || "";
    const token = auth.replace(/^Bearer\s+/i, "");
    if (!env.AUTH_TOKEN || token !== env.AUTH_TOKEN) {
      return json({ ok: false, error: "unauthorized" }, 401);
    }

    // 读取请求体
    let payload;
    try {
      payload = await request.json();
    } catch (e) {
      return json({ ok: false, error: "invalid json body" }, 400);
    }

    // 校验必填字段
    const { agentid, msgtype, ...rest } = payload;
    if (!agentid || !msgtype) {
      return json({ ok: false, error: "missing agentid or msgtype" }, 400);
    }

    // 1. 获取 access_token
    const tokenUrl = `${WECOM_API_BASE}/gettoken?corpid=${encodeURIComponent(env.WECHAT_CORPID)}&corpsecret=${encodeURIComponent(env.WECHAT_CORPSECRET)}`;
    const tokenRes = await fetch(tokenUrl, { method: "GET" });
    const tokenData = await tokenRes.json();

    if (tokenData.errcode !== 0) {
      return json({ ok: false, stage: "gettoken", data: tokenData }, 502);
    }
    const accessToken = tokenData.access_token;

    // 2. 发送消息
    const sendUrl = `${WECOM_API_BASE}/message/send?access_token=${accessToken}`;
    const sendBody = { agentid: Number(agentid), msgtype, ...rest };

    const sendRes = await fetch(sendUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(sendBody),
    });
    const sendData = await sendRes.json();

    return json({ ok: sendData.errcode === 0, stage: "send", data: sendData });
  },
};

function json(obj, status = 200) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: { "Content-Type": "application/json; charset=utf-8" },
  });
}
