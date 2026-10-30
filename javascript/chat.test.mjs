import test from 'node:test';
import assert from 'node:assert/strict';
import { ConfigError, DEFAULT_BASE_URL, DEFAULT_PROMPT, complete, createClient, loadConfig, main } from './chat.mjs';

const FAKE_KEY = 'test-only-not-a-real-key';
const ENV = { CX_API_KEY: FAKE_KEY, CX_MODEL: 'test-model' };
const config = () => loadConfig(ENV);
const jsonResponse = (body, status = 200) => new Response(JSON.stringify(body), {
  status, headers: { 'content-type': 'application/json' },
});
const success = () => jsonResponse({
  id: 'chatcmpl-mock', object: 'chat.completion', created: 0, model: 'test-model',
  choices: [{ index: 0, message: { role: 'assistant', content: '模拟响应成功。' }, finish_reason: 'stop' }],
});

// 所有请求均注入内存 fetch；测试不读取 process.env，也不会发起网络连接。
test('SDK builds the intended request and parses a response', async () => {
  let calls = 0;
  const client = createClient(config(), { fetch: async (url, init) => {
    calls++;
    assert.equal(String(url), `${DEFAULT_BASE_URL}/chat/completions`);
    assert.equal(init.method, 'POST');
    const headers = new Headers(init.headers);
    assert.equal(headers.get('authorization'), `Bearer ${FAKE_KEY}`);
    assert.match(headers.get('content-type'), /application\/json/);
    assert.deepEqual(JSON.parse(init.body), {
      model: 'test-model', messages: [{ role: 'user', content: DEFAULT_PROMPT }],
    });
    assert.equal(init.redirect, 'error');
    return success();
  } });
  assert.equal(client.timeout, 30_000);
  assert.equal(client.maxRetries, 0);
  assert.equal(await complete(client, ENV.CX_MODEL), '模拟响应成功。');
  assert.equal(calls, 1);
});

test('configuration requires key and model', () => {
  for (const env of [{}, { CX_API_KEY: FAKE_KEY }, { CX_MODEL: 'test-model' }, { ...ENV, CX_MODEL: ' ' }]) {
    assert.throws(() => loadConfig(env), ConfigError);
  }
});

test('configuration rejects unsafe or malformed base URLs', () => {
  for (const url of ['bad-url', 'http://example.com/v1', 'https://user:secret@example.com/v1', 'https://example.com/v1?key=secret', 'https://example.com/v1#fragment']) {
    assert.throws(() => loadConfig({ ...ENV, CX_BASE_URL: url }), ConfigError);
  }
  assert.equal(loadConfig({ ...ENV, CX_BASE_URL: 'https://example.com/v1/' }).baseURL, 'https://example.com/v1');
});

for (const status of [401, 403, 404, 429, 500]) {
  test(`HTTP ${status} is handled safely without retries`, async () => {
    let calls = 0;
    const errors = [];
    const exit = await main(ENV, { fetch: async () => {
      calls++;
      return jsonResponse({ error: { message: `sensitive ${FAKE_KEY}`, type: 'mock_error' } }, status);
    }, report: text => errors.push(text), output: () => assert.fail('unexpected output') });
    assert.equal(exit, 1);
    assert.equal(calls, 1);
    assert.equal(errors.length, 1);
    assert.ok(!errors[0].includes(FAKE_KEY));
    assert.ok(!errors[0].includes('sensitive'));
    assert.match(errors[0], status >= 500 ? /服务端/ : new RegExp(String(status)));
  });
}

test('a real SDK timeout aborts mock fetch and is reported without retry', async () => {
  let calls = 0;
  const errors = [];
  const exit = await main(ENV, {
    timeout: 20,
    fetch: async (_url, init) => {
      calls++;
      return new Promise((_resolve, reject) => {
        init.signal.addEventListener('abort', () => reject(new DOMException('mock abort', 'AbortError')), { once: true });
      });
    },
    report: text => errors.push(text), output: () => assert.fail('unexpected output'),
  });
  assert.equal(exit, 1);
  assert.equal(calls, 1);
  assert.match(errors[0], /超时/);
});

test('connection errors do not expose internal details', async () => {
  const errors = [];
  const exit = await main(ENV, { fetch: async () => { throw new TypeError(`sensitive ${FAKE_KEY}`); }, report: text => errors.push(text) });
  assert.equal(exit, 1);
  assert.match(errors[0], /连接失败/);
  assert.ok(!errors[0].includes(FAKE_KEY));
});

test('empty response content is handled clearly', async () => {
  for (const response of [{ choices: [] }, { choices: [{ message: { content: null } }] }]) {
    const errors = [];
    const exit = await main(ENV, { fetch: async () => jsonResponse(response), report: text => errors.push(text), output: () => assert.fail('unexpected output') });
    assert.equal(exit, 1);
    assert.match(errors[0], /没有文本内容/);
  }
});

test('invalid local config never calls fetch', async () => {
  const errors = [];
  const exit = await main({}, { fetch: async () => assert.fail('network must not be called'), report: text => errors.push(text) });
  assert.equal(exit, 1);
  assert.match(errors[0], /CX_API_KEY/);
});

test('placeholder and whitespace-containing keys never call fetch', async () => {
  for (const key of ['your-cx-api-key', 'replace-with-your-cx-api-key', 'test key', 'test\tkey', 'test\nkey']) {
    let calls = 0;
    const errors = [];
    const exit = await main({ ...ENV, CX_API_KEY: key }, {
      fetch: async () => { calls++; return success(); },
      report: text => errors.push(text), output: () => assert.fail('unexpected output'),
    });
    assert.equal(exit, 1);
    assert.equal(calls, 0);
    assert.match(errors[0], /CX_API_KEY/);
    assert.ok(!errors[0].includes(key));
  }
});
