# ccsw – Claude Code provider switcher

一个轻量级“配置切换器”，专注修改 `~/.claude/settings.json` 里的 `env`，帮助你在多家 Claude Code 兼容 API 提供商之间一键切换。不会发送请求、不托管密钥。

## 特性
- 预置 `zhipu`、`88code` 两个 provider，**不含密钥**，默认从环境变量读取令牌。
- 支持自定义 provider（通过 `--token`/`--base-url` 等参数）。
- 写入前自动备份 `settings.json`，并在 JSON 损坏时保留副本后重建。
- 切换到 `88code` 时会自动清理智谱特有的超时/流量键。

## 快速开始（最简 3 步）
1) 克隆并进入目录  
   ```bash
   git clone https://github.com/Boulea7/ccsw.git && cd ccsw
   ```
2) 运行一键脚本（只写入 alias，不写密钥）  
   ```bash
   ./bootstrap.sh
   ```
3) 导出令牌并使用  
   ```bash
   export ZHIPU_ANTHROPIC_AUTH_TOKEN="<your_zhipu_token>"
   export CODE88_ANTHROPIC_AUTH_TOKEN="<your_88code_token>"
   source ~/.zshrc  # 或 ~/.bashrc
   ccsw zhipu
   ccsw 88code
   ```

## 安装为全局别名
推荐运行 `bootstrap.sh`（自动检测 zsh/bash）：
```bash
./bootstrap.sh
source ~/.zshrc  # 或 ~/.bashrc
```
如需手动：
```bash
alias ccsw="python3 $HOME/ccsw/cc_switch_public.py"
```

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

### 与常见 AI 编程 CLI 的关系
- 本项目**只做配置切换**，不替代任何 CLI。你仍使用原有工具（Codex、Claude Code、其他 Anthropic 兼容 CLI），但在调用前用 `ccsw ...` 切到目标提供商即可。
- 切换后重新打开/重连 Claude Code，或在新终端运行 Codex，即可使用最新的 `env`。

## 设计约定
- 配置文件固定为 `~/.claude/settings.json`。
- 备份策略：每次写入前复制为 `settings.json.bak-YYYYmmdd-HHMMSS`；当文件损坏时另存为 `.corrupt-...`。
- 不把密钥写入仓库：项目 `.gitignore` 已忽略本地专用脚本与备份文件。

## 常见问题
- **找不到 token**：确认已设置对应环境变量，或在命令中显式传入 `--token`。
- **alias 不生效**：运行 `source ~/.zshrc` 或在当前 shell 重新声明 alias。
- **想复原旧配置**：在 `~/.claude` 目录使用最近的备份文件覆盖 `settings.json` 即可。
- **这是 CLI 吗？** 不是，它只是一个小脚本/alias，职责单一：改写 `settings.json` 的 `env`。

## 路线图 / TODO
- 增加 provider 配置文件（YAML/JSON）读取，避免修改代码即可扩展。
- 增加 `--list` 输出当前配置和可用 provider。
- 支持 Windows PowerShell 配置别名的辅助脚本。

## 许可证
本项目采用 MIT License，详见 [LICENSE](./LICENSE)。
