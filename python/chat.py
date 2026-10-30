"""CX.API text chat example. Importing this module never sends a request."""

import argparse
from dataclasses import dataclass, field
import logging
import os
import sys
from typing import Mapping, Optional
from urllib.parse import urlsplit

import httpx
from openai import APIConnectionError, APIError, APIStatusError, APITimeoutError, OpenAI, omit

DEFAULT_BASE_URL = "https://api.www-cx-api.cn.mt/v1"
TIMEOUT_SECONDS = 30.0


class ConfigurationError(ValueError):
    """A required setting is missing or invalid."""


class ChatError(RuntimeError):
    """A safe-to-display error without credentials or response bodies."""


@dataclass(frozen=True)
class Config:
    api_key: str = field(repr=False)
    model: str
    base_url: str


def load_config(environ: Optional[Mapping[str, str]] = None) -> Config:
    env = os.environ if environ is None else environ
    key = env.get("CX_API_KEY", "").strip()
    model = env.get("CX_MODEL", "").strip()
    if not key or key in {"your-cx-api-key", "replace-with-your-cx-api-key"}:
        raise ConfigurationError("请设置 CX_API_KEY，且不要使用示例占位值。")
    if not model:
        raise ConfigurationError("请设置 CX_MODEL；可用模型以站内模型页为准。")
    if any(character.isspace() for character in key):
        raise ConfigurationError("CX_API_KEY 格式无效，请检查复制时是否混入空白。")
    base_url = env.get("CX_BASE_URL", DEFAULT_BASE_URL).strip()
    try:
        parsed = urlsplit(base_url)
        valid = (
            parsed.scheme == "https"
            and bool(parsed.hostname)
            and parsed.username is None
            and parsed.password is None
            and not parsed.query
            and not parsed.fragment
            and not any(character.isspace() for character in base_url)
        )
        # Accessing port also validates malformed port strings.
        parsed.port
    except ValueError:
        valid = False
    if not valid:
        raise ConfigurationError("CX_BASE_URL 必须是无账号、查询参数或片段的 HTTPS 地址。")
    return Config(key, model, base_url.rstrip("/"))


def create_client(config: Config, http_client: Optional[httpx.Client] = None) -> OpenAI:
    return OpenAI(
        api_key=config.api_key,
        base_url=config.base_url,
        # Do not inherit settings for a separate OpenAI account from the shell.
        organization="",
        project="",
        webhook_secret="",
        default_headers={"OpenAI-Organization": omit, "OpenAI-Project": omit},
        timeout=TIMEOUT_SECONDS,
        max_retries=0,
        # Do not follow redirects that could send the request to another endpoint.
        http_client=http_client or httpx.Client(follow_redirects=False),
    )


def chat(client: OpenAI, model: str, prompt: str) -> str:
    if not prompt.strip():
        raise ConfigurationError("提示词不能为空。")
    try:
        completion = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
        )
    except APITimeoutError:
        raise ChatError("请求超时；服务端可能已处理，请先检查用量再决定是否重试。") from None
    except APIConnectionError:
        raise ChatError("无法连接服务，请检查网络和 CX_BASE_URL。") from None
    except APIStatusError as error:
        hints = {
            401: "认证失败，请检查 CX_API_KEY。",
            403: "访问被拒绝，请检查账号及模型权限。",
            404: "接口或模型不存在，请检查地址及 CX_MODEL。",
            429: "请求受限，请检查额度、用量和速率限制后再重试。",
        }
        hint = hints.get(error.status_code, "请求失败，请检查服务状态和请求设置。")
        raise ChatError(f"HTTP {error.status_code}：{hint}") from None
    except APIError:
        raise ChatError("SDK 未能解析或处理服务响应，请检查接口兼容性。") from None

    choices = getattr(completion, "choices", None)
    message = getattr(choices[0], "message", None) if choices else None
    content = getattr(message, "content", None)
    if not isinstance(content, str) or not content.strip():
        raise ChatError("响应未包含文本；本示例只处理文本消息。请检查模型能力和用量。")
    return content


def quiet_sdk_logging() -> None:
    """Keep the standalone CLI quiet even when OPENAI_LOG enables SDK debug logs."""
    families = ("openai", "httpx", "httpcore")
    names = set(families) | {
        name for name in logging.Logger.manager.loggerDict
        if any(name.startswith(family + ".") for family in families)
    }
    for name in names:
        logger = logging.getLogger(name)
        logger.disabled = True
        logger.setLevel(logging.CRITICAL + 1)
        logger.propagate = False
        logger.handlers = [logging.NullHandler()]


def main() -> int:
    # Only the CLI changes logging; importing this module does not change it.
    quiet_sdk_logging()
    parser = argparse.ArgumentParser(description="CX.API 文本对话示例（真实请求可能扣费）")
    parser.add_argument("prompt", nargs="?", default="请用一句话介绍什么是 API。")
    args = parser.parse_args()
    try:
        config = load_config()
        print("即将向 CX.API 发送真实请求，可能扣费；自动重试已关闭。", file=sys.stderr)
        with create_client(config) as client:
            print(chat(client, config.model, args.prompt))
    except (ConfigurationError, ChatError) as error:
        print(str(error), file=sys.stderr)
        return 1
    except Exception:
        # Avoid printing third-party exception bodies that may contain sensitive data.
        print("运行失败，请检查本地依赖和配置；未输出原始错误内容。", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
