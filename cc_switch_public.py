#!/usr/bin/env python3
"""
Generic CLI to switch Claude Code providers by editing ~/.claude/settings.json.
- Supports built-in providers (zhipu, 88code) without hardcoded secrets.
- Reads tokens from environment variables by default, or accepts CLI overrides.
- Creates time-stamped backups and survives invalid JSON gracefully.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

SETTINGS_PATH = Path.home() / ".claude" / "settings.json"
CODEX_AUTH_PATH = Path.home() / ".codex" / "auth.json"
BACKUP_SUFFIX_FMT = "%Y%m%d-%H%M%S"

# Built-in provider definitions (no secrets included).
PROVIDERS = {
    "zhipu": {
        "anthropic_base_url": "https://open.bigmodel.cn/api/anthropic",
        "anthropic_token_env": "ZHIPU_ANTHROPIC_AUTH_TOKEN",
        # 没有已知的 OpenAI 兼容端点，默认不更新 Codex。
        "openai_base_url": None,
        "openai_token_env": "ZHIPU_OPENAI_API_KEY",
        "extra": {
            "API_TIMEOUT_MS": "3000000",
            "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": 1,
        },
    },
    "88code": {
        "anthropic_base_url": "https://www.88code.org/api",
        "anthropic_token_env": "CODE88_ANTHROPIC_AUTH_TOKEN",
        "openai_base_url": "https://www.88code.org/openai/v1",
        "openai_token_env": "CODE88_OPENAI_API_KEY",
        "extra": {},
    },
}

REMOVE_ON_88CODE = {"API_TIMEOUT_MS", "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC"}


def load_json(path: Path) -> Dict[str, Any]:
    """Load JSON; on decode error back up corrupt file and return empty dict."""
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        corrupt_backup = path.with_suffix(
            path.suffix + f".corrupt-{datetime.now().strftime(BACKUP_SUFFIX_FMT)}"
        )
        shutil.copy2(path, corrupt_backup)
        print(f"[warn] {path.name} is invalid JSON; backed up to {corrupt_backup}")
        return {}


def ensure_parents() -> None:
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    CODEX_AUTH_PATH.parent.mkdir(parents=True, exist_ok=True)


def backup_file(path: Path) -> Path | None:
    if path.exists():
        backup_path = path.with_suffix(
            path.suffix + f".bak-{datetime.now().strftime(BACKUP_SUFFIX_FMT)}"
        )
        shutil.copy2(path, backup_path)
        return backup_path
    return None


def build_claude_env(profile: str, token: str, base_url: str | None, timeout: str | None, disable_traffic: bool) -> Dict[str, Any]:
    env: Dict[str, Any] = {
        "ANTHROPIC_AUTH_TOKEN": token,
    }
    if base_url:
        env["ANTHROPIC_BASE_URL"] = base_url

    if profile == "88code":
        # Clean zhipu-only keys when switching to 88code.
        env.update({k: None for k in REMOVE_ON_88CODE})
    if timeout:
        env["API_TIMEOUT_MS"] = timeout
    if disable_traffic:
        env["CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC"] = 1
    return env


def apply_profile(data: Dict[str, Any], env_updates: Dict[str, Any]) -> Dict[str, Any]:
    current_env = data.get("env")
    if not isinstance(current_env, dict):
        current_env = {}
    # Remove keys with value None to keep file tidy.
    for k, v in env_updates.items():
        if v is None:
            current_env.pop(k, None)
        else:
            current_env[k] = v
    data["env"] = current_env
    return data


def apply_codex(auth: Dict[str, Any], token: str, base_url: str) -> Dict[str, Any]:
    auth["OPENAI_API_KEY"] = token
    auth["OPENAI_BASE_URL"] = base_url
    return auth


def save_json(path: Path, data: Dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Switch Claude Code / Codex providers")
    parser.add_argument("profile", help="provider name (built-in or custom)")
    parser.add_argument("--token", help="Anthropic-compatible auth token")
    parser.add_argument("--base-url", help="Anthropic Base URL for Claude Code")
    parser.add_argument("--timeout", help="API timeout ms (string or int)")
    parser.add_argument(
        "--disable-nonessential-traffic",
        action="store_true",
        help="Set CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1",
    )
    parser.add_argument(
        "--openai-base-url",
        help="OpenAI-compatible Base URL (for Codex auth.json)",
    )
    parser.add_argument(
        "--codex-token",
        help="OpenAI-compatible API key (for Codex auth.json); defaults to --token",
    )
    parser.add_argument(
        "--skip-codex",
        action="store_true",
        help="Only update Claude Code (skip Codex auth.json)",
    )
    return parser.parse_args()


def resolve_provider(profile: str, args: argparse.Namespace) -> Dict[str, Any]:
    if profile in PROVIDERS:
        meta = PROVIDERS[profile]
        token = args.token or os.environ.get(meta["anthropic_token_env"])
        base_url = args.base_url or meta["anthropic_base_url"]
        timeout = args.timeout or meta["extra"].get("API_TIMEOUT_MS")
        disable_traffic = (
            args.disable_nonessential_traffic
            or bool(meta["extra"].get("CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC"))
        )
        codex_token = args.codex_token or token or os.environ.get(meta.get("openai_token_env", ""))
        openai_base_url = args.openai_base_url or meta.get("openai_base_url")
    else:
        # Custom provider requires token and base URL via CLI.
        token = args.token
        base_url = args.base_url
        timeout = args.timeout
        disable_traffic = args.disable_nonessential_traffic
        codex_token = args.codex_token or args.token
        openai_base_url = args.openai_base_url
    if not token:
        raise SystemExit(
            f"Token is required. Provide --token or set {PROVIDERS.get(profile, {}).get('anthropic_token_env', '<TOKEN_ENV>')}"
        )
    return {
        "token": token,
        "base_url": base_url,
        "timeout": timeout,
        "disable_traffic": disable_traffic,
        "codex_token": codex_token,
        "openai_base_url": openai_base_url,
    }


def main() -> None:
    args = parse_args()
    env_conf = resolve_provider(args.profile, args)
    ensure_parents()

    # Claude Code settings
    settings_data = load_json(SETTINGS_PATH)
    settings_backup = backup_file(SETTINGS_PATH)
    env_updates = build_claude_env(
        profile=args.profile,
        token=env_conf["token"],
        base_url=env_conf["base_url"],
        timeout=env_conf["timeout"],
        disable_traffic=env_conf["disable_traffic"],
    )
    updated_settings = apply_profile(settings_data, env_updates)
    save_json(SETTINGS_PATH, updated_settings)
    if settings_backup:
        print(f"[claude] Backed up previous settings to {settings_backup}")
    print(f"[claude] Switched Claude Code environment to: {args.profile}")

    # Codex auth.json (OpenAI compatible)
    if not args.skip_codex:
        if env_conf["openai_base_url"] and env_conf["codex_token"]:
            codex_data = load_json(CODEX_AUTH_PATH)
            codex_backup = backup_file(CODEX_AUTH_PATH)
            updated_codex = apply_codex(
                codex_data, env_conf["codex_token"], env_conf["openai_base_url"]
            )
            save_json(CODEX_AUTH_PATH, updated_codex)
            if codex_backup:
                print(f"[codex] Backed up previous auth to {codex_backup}")
            print("[codex] Updated auth.json (OpenAI compatible).")
        else:
            print("[codex] Skipped (no openai_base_url or token provided). Use --openai-base-url / --codex-token to enable.")


if __name__ == "__main__":
    main()
