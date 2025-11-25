# ccsw – Claude Code provider switcher

一个本地 CLI，小而实用，用来在多家 Claude Code 兼容 API 提供商之间一键切换 `~/.claude/settings.json` 的 `env` 配置。

## 特性
- 预置 `zhipu`、`88code` 两个 provider，**不含密钥**，默认从环境变量读取令牌。
- 支持自定义 provider（通过 `--token`/`--base-url` 等参数）。
- 写入前自动备份 `settings.json`，并在 JSON 损坏时保留副本后重建。
- 切换到 `88code` 时会自动清理智谱特有的超时/流量键。

## 快速开始（最简 3 步）
1. 克隆并进入目录：
   ```bash
   git clone https://github.com/Boulea7/ccsw.git && cd ccsw
   ```
2. 一键安装 alias（不写入密钥）：
   ```bash
   ./bootstrap.sh
   ```
3. 在当前终端导出令牌并使用：
   ```bash
   export ZHIPU_ANTHROPIC_AUTH_TOKEN="<your_zhipu_token>"
   export CODE88_ANTHROPIC_AUTH_TOKEN="<your_88code_token>"
   source ~/.zshrc  # 或 ~/.bashrc
   ccsw zhipu
   ccsw 88code
   ```

## 安装为全局别名
推荐直接运行仓库提供的 `bootstrap.sh`（自动检测 zsh/bash）：\n```bash\n./bootstrap.sh\nsource ~/.zshrc  # 或 ~/.bashrc\n```\n如需手动：\n```bash\nalias ccsw=\"python3 $HOME/ccsw/cc_switch_public.py\"\n```

## 自定义 provider
```bash
python3 cc_switch_public.py myvendor \
  --token "<token>" \
  --base-url "https://api.myvendor.com/anthropic" \
  --timeout 30000 \
  --disable-nonessential-traffic
```
- `--token` 必填（或在内置 provider 场景下通过环境变量提供）。
- `--base-url` 可选：内置 provider 已有默认值，自定义 provider 建议显式提供。
- `--timeout`：传入字符串或数字（毫秒）。
- `--disable-nonessential-traffic`：写入 `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1`。

### 与常见 AI 编程 CLI 配合
- **Codex CLI**：在有 Python3 的环境直接用 `ccsw ...` 切换后即可调用 Codex（无需额外依赖）。\n- **Claude Code 本地 CLI**：本工具修改的 `~/.claude/settings.json` 即为 Claude Code 配置，切换后重新打开/重连即可生效。\n- **其他 MCP/LLM CLI**：只要遵循 Anthropic 兼容接口，传入 `--base-url` 与 `--token` 即可无缝接入。

## 设计约定
- 配置文件固定为 `~/.claude/settings.json`。
- 备份策略：每次写入前复制为 `settings.json.bak-YYYYmmdd-HHMMSS`；当文件损坏时另存为 `.corrupt-...`。
- 不把密钥写入仓库：项目 `.gitignore` 已忽略本地专用脚本与备份文件。

## 常见问题
- **找不到 token**：确认已设置对应环境变量，或在命令中显式传入 `--token`。
- **alias 不生效**：运行 `source ~/.zshrc` 或在当前 shell 重新声明 alias。
- **想复原旧配置**：在 `~/.claude` 目录使用最近的备份文件覆盖 `settings.json` 即可。

## 路线图 / TODO
- 增加 provider 配置文件（YAML/JSON）读取，避免修改代码即可扩展。
- 增加 `--list` 输出当前配置和可用 provider。
- 支持 Windows PowerShell 配置别名的辅助脚本。

## 许可证
本项目采用 MIT License，详见 [LICENSE](./LICENSE)。
