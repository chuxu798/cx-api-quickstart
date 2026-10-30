# 开发者：Python / JavaScript 接入教程

[返回 AI 中转站新手指南](../README.md)

用一个最小的聊天请求，了解如何配置 API 地址、通过环境变量传入密钥、选择模型，以及处理超时和常见错误。仓库包含可运行的命令行示例和不调用真实接口的模拟测试。

本资料由 **CX.API 运营方提供**，用于接入 CX.API 这一第三方 API 服务。它不是 OpenAI 官方教程，也不代表 OpenAI 对 CX.API 的认证或背书。示例使用 OpenAI SDK 的 Chat Completions 客户端；这不意味着平台兼容该 SDK 的全部接口或功能。

- [CX.API 官网与控制台](https://api.www-cx-api.cn.mt)
- [公开模型与价格页](https://api.www-cx-api.cn.mt/models)：选择模型前查看请求名称、分组、计费单位和适用条件。

## 先运行离线模拟测试（检查代码，不是体验 AI）

此步骤只检查代码，不会获得真实 AI 回答。测试使用固定的虚拟密钥和内存模拟响应，**不需要注册、充值或设置真实 API 密钥**，也不会向 CX.API 发请求。首次安装依赖需要联网下载软件包。

```bash
git clone https://github.com/chuxu798/cx-api-quickstart.git
cd cx-api-quickstart
```

### Python

建议 Python 3.11 或更新版本。Windows PowerShell：

```powershell
cd python
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m unittest -v
```

macOS / Linux：

```bash
cd python
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m unittest -v
```

### JavaScript（Node.js）

使用 Node.js 22 或更新版本。另开终端，在仓库根目录运行（PowerShell、macOS、Linux 均适用）：

```bash
cd javascript
npm ci --ignore-scripts
npm test
```

## 配置一次真实调用

**以下步骤会向 CX.API 发起真实请求，可能扣除账户额度。** 请先在站内确认价格、模型权限和余额，再自行运行。测试成功仅验证客户端行为；本教程发布前没有使用真实密钥验证付费接口、模型可用性或输出质量。

在 CX.API 控制台创建自己的 API 密钥，不要使用 OpenAI 的密钥。把它留在本机或服务端环境变量中，不要放入浏览器前端、截图、聊天记录或 Git 提交。

| 变量 | 用途 | 设置方式 |
| --- | --- | --- |
| `CX_API_KEY` | CX.API API 密钥 | 必填；从自己的控制台获取 |
| `CX_MODEL` | 模型请求名称 | 必填；从模型页复制，例如 `gpt-5.5` |
| `CX_BASE_URL` | API 基础地址 | 可选，默认 `https://api.www-cx-api.cn.mt/v1` |

`gpt-5.5` 是站内公开教程的请求名示例，不是可用性承诺。模型能否调用取决于当前目录、所选分组和账户权限。示例仅演示文本、非流式的 `POST /v1/chat/completions`，不覆盖图像、音频、工具调用或其他接口。

### Windows PowerShell

在准备执行示例的同一个终端中输入：

```powershell
$cxSecret = Read-Host '请输入 CX.API 密钥' -AsSecureString
$env:CX_API_KEY = [System.Net.NetworkCredential]::new('', $cxSecret).Password
Remove-Variable cxSecret
$env:CX_MODEL = 'gpt-5.5'
$env:CX_BASE_URL = 'https://api.www-cx-api.cn.mt/v1'
```

### macOS / Linux（Bash 或 Zsh）

```bash
printf '请输入 CX.API 密钥：'
read -r -s CX_API_KEY
printf '\n'
export CX_API_KEY
export CX_MODEL='gpt-5.5'
export CX_BASE_URL='https://api.www-cx-api.cn.mt/v1'
```

密钥通过交互输入，避免把真实值写进命令历史。环境变量仍是进程可读的秘密；不要输出完整环境或在共享终端留下密钥。根目录的 [`.env.example`](../.env.example) 仅作字段参考，示例**不会自动读取 `.env` 文件**。

### 发送请求（会产生实际 API 使用）

从 `python` 目录运行：

```powershell
# Windows PowerShell
.\.venv\Scripts\python.exe chat.py
```

```bash
# macOS / Linux
.venv/bin/python chat.py
```

或者从 `javascript` 目录运行：

```bash
npm start
```

两套示例都发送一个简短的中文问题，将返回的文本写到终端；模型回复内容并不固定。要修改提问，可编辑示例中的 `messages`。如需切换模型，更新 `CX_MODEL` 后再运行。

使用结束后可关闭终端，或清除本次会话的密钥变量：

```powershell
# PowerShell
Remove-Item Env:CX_API_KEY
```

```bash
# Bash / Zsh
unset CX_API_KEY
```

## 人民币价格怎么看

平台当前的账户额度规则是：**充值 1 元人民币，对应 1 美元标记的账户额度**。这是平台内部额度口径。具体模型消费以[站内价格页](https://api.www-cx-api.cn.mt/models)和账户账单为准；分组、上下文档位及可选加价会影响消费。本仓库不固定单次调用价格，也不保证未来价格不变。

## 超时、错误与费用

两个示例都配置 30 秒 SDK 超时，关闭 SDK 自动重试，并使用简短错误提示，避免把服务返回的完整错误正文或密钥打印出来。超时不是费用上限，也不能证明服务端没有处理请求；重试前先检查账单或请求记录。

| 情况 | 排查方法 |
| --- | --- |
| 缺少配置 | 检查当前终端的 `CX_API_KEY` 与 `CX_MODEL` 是否已设置；`.env.example` 不会自动生效 |
| HTTP 401 / 403 | 检查密钥是否有效、是否属于 CX.API，以及模型 / 分组权限 |
| HTTP 404 | 检查基础地址包含 `/v1`，并核对站内的模型请求名 |
| HTTP 429 | 查看余额、配额及限流信息；不要立即连续重试 |
| HTTP 5xx | 服务暂时无法完成请求，稍后查看站内状态再决定是否重试 |
| 连接失败或超时 | 检查本机网络和地址；请求可能已被处理，请先查记录 |
| 返回为空或格式异常 | 示例需要 `choices[0].message.content` 中的文本；核对所选模型是否支持本例的接口和返回格式 |

如需反馈问题，可附上已脱敏的错误类别、HTTP 状态码和复现步骤；不要公开密钥、完整请求头或含私人内容的提示词。请自行评估发给第三方服务的数据。

## 文件与验证范围

```text
cx-api-quickstart/
├── README.md       # 面向普通用户的新手指南
├── docs/developer-guide.md
├── .env.example
├── .gitignore
├── python/        # Python SDK 示例、固定依赖和 unittest 测试
└── javascript/    # Node.js SDK 示例、依赖锁文件和 node:test 测试
```

模拟测试检查实际 SDK 构造的请求和错误处理，包括请求地址、模型名称、消息结构、虚拟鉴权头、错误状态与超时。所有响应均为测试构造，不代表真实服务能力；本仓库不承诺速度、稳定性或底层模型真实性。

发布前验证：Python 3.11.6 / `openai==2.9.0` / `httpx==0.28.1` 的 10 项测试通过；Node.js 24.14.0 / `openai@7.45.1` 的 13 项测试通过。以上为本项目实际安装测试的固定版本，不代表所有版本组合均兼容。

SDK 用法参考 [OpenAI Python SDK](https://github.com/openai/openai-python) 与 [OpenAI JavaScript SDK](https://github.com/openai/openai-node)。平台接入信息参考[公开前端教程](https://api.www-cx-api.cn.mt/platform-theme.js?v=monitor-hybrid-20261029)及[模型页](https://api.www-cx-api.cn.mt/models)。本项目依赖版本以 `requirements.txt`、`package.json` 和锁文件为准。
