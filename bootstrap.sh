#!/usr/bin/env bash
# Minimal helper to install ccsw alias locally without touching secrets.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="${SCRIPT_DIR}/cc_switch_public.py"

if [[ ! -f "$TARGET" ]]; then
  echo "[error] Cannot find cc_switch_public.py at $TARGET" >&2
  exit 1
fi

# Choose rc file: zsh preferred, fallback bash.
if [[ -n "${ZDOTDIR:-}" && -f "$ZDOTDIR/.zshrc" ]]; then
  RC_FILE="$ZDOTDIR/.zshrc"
elif [[ -f "$HOME/.zshrc" ]]; then
  RC_FILE="$HOME/.zshrc"
elif [[ -f "$HOME/.bashrc" ]]; then
  RC_FILE="$HOME/.bashrc"
else
  RC_FILE="$HOME/.bashrc"
  touch "$RC_FILE"
fi

ALIAS_LINE="alias ccsw=\"python3 ${TARGET}\""
if grep -Fq "$ALIAS_LINE" "$RC_FILE"; then
  echo "[info] alias already present in $RC_FILE"
else
  echo "$ALIAS_LINE" >> "$RC_FILE"
  echo "[ok] added alias to $RC_FILE"
fi

cat <<EOF
Next steps:
1) export your provider tokens, e.g.:
   export ZHIPU_ANTHROPIC_AUTH_TOKEN="<token>"
   export CODE88_ANTHROPIC_AUTH_TOKEN="<token>"
2) reload shell: source $RC_FILE
3) use: ccsw zhipu | ccsw 88code | ccsw myvendor --token ... --base-url ...
EOF
