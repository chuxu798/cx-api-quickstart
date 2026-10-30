import OpenAI from 'openai';
import { pathToFileURL } from 'node:url';

export const DEFAULT_BASE_URL = 'https://api.www-cx-api.cn.mt/v1';
export const DEFAULT_PROMPT = '请用一句话介绍你能帮助我做什么。';

export class ConfigError extends Error {}
export class EmptyResponseError extends Error {}

// 传入环境变量对象，方便测试使用完全独立的虚构配置。
export function loadConfig(env) {
  const apiKey = env.CX_API_KEY?.trim();
  const model = env.CX_MODEL?.trim();
  if (!apiKey) throw new ConfigError('请设置 CX_API_KEY。');
  if (['your-cx-api-key', 'replace-with-your-cx-api-key'].includes(apiKey) || /\s/.test(apiKey)) {
    throw new ConfigError('请将 CX_API_KEY 替换为实际密钥，且不要包含空白字符。');
  }
  if (!model) throw new ConfigError('请设置 CX_MODEL；模型请求名以站内模型页为准。');
  let baseURL;
  try {
    baseURL = new URL(env.CX_BASE_URL?.trim() || DEFAULT_BASE_URL);
  } catch {
    throw new ConfigError('CX_BASE_URL 必须是有效的 HTTPS API 地址。');
  }
  if (baseURL.protocol !== 'https:' || baseURL.username || baseURL.password || baseURL.search || baseURL.hash) {
    throw new ConfigError('CX_BASE_URL 必须使用 HTTPS，且不能包含用户名、密码、查询参数或片段。');
  }
  return { apiKey, model, baseURL: baseURL.toString().replace(/\/+$/, '') };
}

export function createClient(config, { fetch, timeout = 30_000 } = {}) {
  return new OpenAI({
    apiKey: config.apiKey,
    baseURL: config.baseURL,
    organization: null,
    project: null,
    timeout,
    maxRetries: 0, // 超时后先检查消费记录，避免自动重试产生重复消费。
    logLevel: 'off',
    fetchOptions: { redirect: 'error' },
    ...(fetch ? { fetch } : {}), // 测试注入内存模拟；正常运行使用 SDK 默认 fetch。
  });
}

export async function complete(client, model, prompt = DEFAULT_PROMPT) {
  const completion = await client.chat.completions.create({
    model,
    messages: [{ role: 'user', content: prompt }],
  });
  const content = completion?.choices?.[0]?.message?.content;
  if (typeof content !== 'string' || !content.trim()) {
    throw new EmptyResponseError('响应中没有文本内容，请检查所选模型及接口支持情况。');
  }
  return content;
}

// 不直接输出 error.message / response / headers，避免服务端错误回显密钥或请求内容。
export function safeError(error) {
  if (error instanceof ConfigError || error instanceof EmptyResponseError) return error.message;
  if (error instanceof OpenAI.APIConnectionTimeoutError) return '请求超时。请先检查平台消费记录，再决定是否重试。';
  if (error instanceof OpenAI.APIConnectionError) return '连接失败。请检查网络和 CX_BASE_URL。';
  if (error instanceof OpenAI.APIError) {
    if (error.status === 401) return 'HTTP 401：鉴权失败，请检查 CX_API_KEY。';
    if (error.status === 403) return 'HTTP 403：没有访问权限，请检查令牌及分组权限。';
    if (error.status === 404) return 'HTTP 404：请检查 API 地址及模型请求名。';
    if (error.status === 429) return 'HTTP 429：请求受限，请检查配额、余额和频率限制。';
    if (error.status >= 500) return '服务端暂时出错，请稍后检查平台状态和消费记录。';
    return 'API 请求失败，请核对模型和请求参数。';
  }
  return '请求未完成，请检查本地配置及依赖版本。';
}

export async function main(env, { fetch, timeout, output = console.log, report = console.error } = {}) {
  try {
    const config = loadConfig(env);
    const client = createClient(config, { fetch, timeout });
    output(await complete(client, config.model));
    return 0;
  } catch (error) {
    report(safeError(error));
    return 1;
  }
}

// import 本模块不会读取密钥或发送请求。仅直接运行时使用环境变量。
if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  console.error('提示：此命令使用配置的 API 地址发送真实请求，可能产生费用。');
  process.exitCode = await main(process.env);
}
