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
BACKUP_SUFFIX_FMT = "%Y%m%d-%H%M%S"

# Built-in provider definitions (no secrets included).
PROVIDERS = {
    "zhipu": {
        "base_url": "https://open.bigmodel.cn/api/anthropic",
        "token_env": "ZHIPU_ANTHROPIC_AUTH_TOKEN",
        "extra": {
            "API_TIMEOUT_MS": "3000000",
            "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": 1,
        },
    },
    "88code": {
        "base_url": "https://www.88code.org/api",
        "token_env": "CODE88_ANTHROPIC_AUTH_TOKEN",
        "extra": {},
    },
}

REMOVE_ON_88CODE = {"API_TIMEOUT_MS", "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC"}


def load_settings() -> Dict[str, Any]:
    """Load settings.json; backup invalid JSON and return an empty dict on failure."""
    if not SETTINGS_PATH.exists():
        return {}
    try:
        with SETTINGS_PATH.open("r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        corrupt_backup = SETTINGS_PATH.with_suffix(
            SETTINGS_PATH.suffix + f".corrupt-{datetime.now().strftime(BACKUP_SUFFIX_FMT)}"
        )
        shutil.copy2(SETTINGS_PATH, corrupt_backup)
        print(f"[warn] settings.json is invalid JSON; backed up to {corrupt_backup}")
        return {}


def ensure_parent_dir() -> None:
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)


def backup_settings() -> Path | None:
    if SETTINGS_PATH.exists():
        backup_path = SETTINGS_PATH.with_suffix(
            SETTINGS_PATH.suffix + f".bak-{datetime.now().strftime(BACKUP_SUFFIX_FMT)}"
        )
        shutil.copy2(SETTINGS_PATH, backup_path)
        return backup_path
    return None


def build_env(profile: str, token: str, base_url: str | None, timeout: str | None, disable_traffic: bool) -> Dict[str, Any]:
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


def save_settings(data: Dict[str, Any]) -> None:
    with SETTINGS_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Switch Claude Code provider")
    parser.add_argument("profile", help="provider name (built-in or custom)")
    parser.add_argument("--token", help="Anthropic-compatible auth token")
    parser.add_argument("--base-url", help="Base URL for the provider API")
    parser.add_argument("--timeout", help="API timeout ms (string or int)")
    parser.add_argument(
        "--disable-nonessential-traffic",
        action="store_true",
        help="Set CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1",
    )
    return parser.parse_args()


def resolve_provider(profile: str, args: argparse.Namespace) -> Dict[str, Any]:
    if profile in PROVIDERS:
        meta = PROVIDERS[profile]
        token = args.token or os.environ.get(meta["token_env"])
        base_url = args.base_url or meta["base_url"]
        timeout = args.timeout or meta["extra"].get("API_TIMEOUT_MS")
        disable_traffic = (
            args.disable_nonessential_traffic
            or bool(meta["extra"].get("CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC"))
        )
    else:
        # Custom provider requires token and base URL via CLI.
        token = args.token
        base_url = args.base_url
        timeout = args.timeout
        disable_traffic = args.disable_nonessential_traffic
    if not token:
        raise SystemExit(
            f"Token is required. Provide --token or set {PROVIDERS.get(profile, {}).get('token_env', '<TOKEN_ENV>')}"
        )
    return {
        "token": token,
        "base_url": base_url,
        "timeout": timeout,
        "disable_traffic": disable_traffic,
    }


def main() -> None:
    args = parse_args()
    env_conf = resolve_provider(args.profile, args)
    ensure_parent_dir()
    data = load_settings()
    backup_path = backup_settings()
    env_updates = build_env(
        profile=args.profile,
        token=env_conf["token"],
        base_url=env_conf["base_url"],
        timeout=env_conf["timeout"],
        disable_traffic=env_conf["disable_traffic"],
    )
    updated = apply_profile(data, env_updates)
    save_settings(updated)
    if backup_path:
        print(f"Backed up previous settings to {backup_path}")
    print(f"Switched Claude Code environment to: {args.profile}")


if __name__ == "__main__":
    main()
