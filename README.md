# CX.API：AI 中转站｜新手使用指南

**CX.API 是一个 AI 中转站，让你通过同一个平台接入不同的 AI 模型。** 你在聊天软件里打字提问，CX.API 把问题转给你选的模型，再把回答送回来。可用于聊天问答、写作、翻译等任务，具体能力取决于所选模型。

不会写代码也可以用：按下面的步骤，把自己的密钥填进聊天软件即可。本服务提供第三方 API 接入，不是 ChatGPT 等官方网站的会员代购。

**第一步：[打开 CX.API 官网](https://api.www-cx-api.cn.mt) · [先看模型和价格](https://api.www-cx-api.cn.mt/models)**

## 选适合你的用法

- **我只想用 AI 聊天、写东西：** 按下面的电脑端步骤配置聊天软件，不需要运行代码。
- **我想在网页上生成图片：** 使用站内[便捷出图](https://api.www-cx-api.cn.mt/image)，见下方说明。
- **我要把 AI 接进程序：** 直接看 [Python / JavaScript 开发者教程](docs/developer-guide.md)，有可运行示例和离线测试。

## 要花钱吗？

**实际使用模型会扣除账户额度。** 想先体验，也请先登录查看是否有可用额度；余额不足时，需要按站内条件充值。是否有赠送额度、充值条件和支付方式，以账户页面实际显示为准。

平台的额度口径是：**1 元人民币对应 1 美元标记的平台额度**。具体花多少，要看选择的模型、分组和使用量，详见[模型价格页](https://api.www-cx-api.cn.mt/models)。这不是包月无限使用，下载聊天软件也不代表模型调用免费。

## 想在网页上生成图片？

登录后打开[“便捷出图”](https://api.www-cx-api.cn.mt/image)，填写自己在[“API 密钥”](https://api.www-cx-api.cn.mt/keys)页面创建的密钥，按页面提示操作即可，无需写代码或安装聊天软件。密钥的创建方法见下面第 2 步。

当前入口标注使用 `gpt-image-2`；请先确认密钥所属分组支持它、账户有可用额度。**生成图片仍会计费。** 本指南已核实页面入口和公开说明，尚未实际生成图片。

## 不会写代码，怎么开始聊天？

下面以 **Cherry Studio 电脑桌面版** 为例，适用于 Windows、macOS、Linux。手机端的界面和设置位置可能不同，请使用其对应教程。

### 1. 注册并查看账户额度

打开 [CX.API 官网](https://api.www-cx-api.cn.mt)，点击[注册](https://api.www-cx-api.cn.mt/register)或[登录](https://api.www-cx-api.cn.mt/login)，进入自己的控制台查看余额。需要充值时，查看左侧[“自助充值”](https://api.www-cx-api.cn.mt/redeem)的条件；确认所选模型价格后再继续。

### 2. 选模型，再创建自己的密钥

在[模型与价格页](https://api.www-cx-api.cn.mt/models)选择一个支持文本对话的模型，记下它的**请求名称**和**分组**。模型就是负责回答问题的 AI；请求名称是软件识别它的准确名字，不能凭印象填写。

回到控制台，点击左侧 [**“API 密钥”**](https://api.www-cx-api.cn.mt/keys) → 右上角 **“创建密钥”**，填写一个方便识别的名称，选择与目标模型对应的分组，再创建。分组可以理解为模型的不同接入通道，可用模型和价格可能不同，要和刚才查看的价格对应。

**API 密钥就是让聊天软件连接你账户的凭证，别发给别人。** 创建后复制下来，只填进自己信任的软件；不要贴到群聊、截图或 GitHub。

### 3. 在电脑上安装聊天软件

按 [Cherry Studio 官方安装教程](https://cherryai.com.cn/docs/zh-cn/cherry-studio/installation/)下载适合自己电脑的桌面版。它提供聊天窗口，CX.API 提供模型接入和账户额度。

### 4. 添加 CX.API，填写连接信息

打开 Cherry Studio 左侧的 **“设置” → “模型服务” → “+ 添加服务商”**，按下表填写。端点选择 **OpenAI 兼容的聊天接口（OpenAI Chat / Chat Completions）**；不同版本可能显示为“OpenAI”类型或端点。

| 软件里的项目 | 你要填写什么 |
| --- | --- |
| 服务商名称 | `CX.API`，方便自己识别 |
| API 密钥 / API Key | 第 2 步在 CX.API 创建的密钥 |
| API 地址（Cherry Studio） | `https://api.www-cx-api.cn.mt` |
| 模型 ID / 模型名称（第 5 步填写） | 从 CX.API 模型页复制的准确请求名称，例如 `gpt-5.5`；以当前分组实际支持为准 |

**这里的 Cherry Studio 地址填根地址，不带 `/v1`。** 按其官方文档，软件会自动补上 `/v1/chat/completions`。开发者 SDK 使用的基础地址则是 `https://api.www-cx-api.cn.mt/v1`，两种填法不要混用。[地址填写说明](https://cherryai.com.cn/docs/zh-cn/pre-basic/settings/providers/)

### 5. 添加模型并启用服务商

保存后，在 CX.API 服务商页面点 **“获取模型列表”**，把需要的模型点 `+` 加入列表。如果获取不到，点 `+` 手动添加第 2 步记下的模型 ID。再打开服务商右上角的**启用开关**。[官方自定义服务商步骤](https://cherryai.com.cn/docs/zh-cn/pre-basic/providers/zi-ding-yi-fu-wu-shang/)

### 6. 选中模型，发第一条消息

回到 Cherry Studio 的聊天页面，选择 **CX.API 下的目标模型**，输入一句简单的问题，例如“请把‘今天是个好天气’翻译成英文”，然后发送。收到回答后，回 CX.API 控制台的[“使用记录”](https://api.www-cx-api.cn.mt/usage)查看本次用量和扣费。

发送消息会调用真实模型；软件里的“检测”也可能发起模型请求并扣费。建议先做一次简短尝试，确认费用和效果后再继续使用。

## 如果没有收到回答

| 看到的情况 | 先检查什么 |
| --- | --- |
| 列表里没有模型 | 是否已添加模型，并打开服务商启用开关 |
| 提示密钥错误或无权限 | 是否填了 CX.API 的密钥，有没有复制空格，分组是否对应 |
| 提示找不到模型 | 模型 ID 是否与站内请求名称完全一致 |
| 提示余额不足或请求受限 | 账户额度、模型权限和调用频率 |
| 地址错误 / 404 | Cherry Studio 是否填了上面的根地址，避免重复拼接 `/v1` |
| 超时 | 先查看用量记录；请求可能已被处理，不要连续反复点发送 |

## 给开发者的入口

[查看 Python / JavaScript 教程](docs/developer-guide.md) · [Python 示例](python/chat.py) · [JavaScript 示例](javascript/chat.mjs)

仓库保留环境变量配置、超时与错误处理，以及 23 项已通过的模拟测试。**模拟测试只是检查代码，不联网调用 AI，也不是免费试用模型。**

本指南由 CX.API 运营方提供，非 OpenAI 或 Cherry Studio 官方教程。上述软件步骤依据 Cherry Studio 官方文档和 CX.API 公开接入说明整理，尚未使用真实密钥进行付费对话验证。模型可用性与价格以站内为准。
