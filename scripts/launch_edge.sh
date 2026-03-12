#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
eval "$(python3 "$SCRIPT_DIR/core/config.py" export-shell)"
EDGE_BIN="$ZJU_EDGE_EDGE_BIN"
PROFILE_DIR="$ZJU_EDGE_PROFILE_DIR"
DOWNLOAD_DIR="$ZJU_EDGE_DOWNLOAD_DIR"
PORT="$ZJU_EDGE_REMOTE_DEBUG_PORT"
RESTART=0

usage() {
  cat <<'EOF'
Usage:
  launch_edge.sh [--restart]

Options:
  --restart   Restart only the dedicated ZJU Edge profile instance.
  -h, --help  Show help.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --restart)
      RESTART=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "error: unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

if [[ ! -x "$EDGE_BIN" ]]; then
  echo "error: Edge binary not found at $EDGE_BIN" >&2
  exit 1
fi

mkdir -p "$PROFILE_DIR/Default" "$DOWNLOAD_DIR"

is_running() {
  lsof -nP -iTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1
}

profile_process_running() {
  pgrep -f -- "--user-data-dir=$PROFILE_DIR" >/dev/null 2>&1
}

stop_dedicated_edge() {
  pkill -f -- "--user-data-dir=$PROFILE_DIR" >/dev/null 2>&1 || true
  for _ in $(seq 1 20); do
    if ! is_running && ! profile_process_running; then
      return 0
    fi
    sleep 1
  done
  return 1
}

if [[ "$RESTART" -eq 1 ]]; then
  stop_dedicated_edge || {
    echo "error: failed to stop dedicated Edge profile on port $PORT" >&2
    exit 1
  }
fi

if ! is_running || ! profile_process_running; then
  PROFILE_DIR="$PROFILE_DIR" DOWNLOAD_DIR="$DOWNLOAD_DIR" python3 - <<'PY'
import json
import os
from pathlib import Path

profile_dir = Path(os.environ["PROFILE_DIR"])
download_dir = Path(os.environ["DOWNLOAD_DIR"])
prefs_path = profile_dir / "Default" / "Preferences"
prefs_path.parent.mkdir(parents=True, exist_ok=True)

if prefs_path.exists():
    try:
        prefs = json.loads(prefs_path.read_text(encoding="utf-8"))
    except Exception:
        prefs = {}
else:
    prefs = {}

prefs.setdefault("download", {})
prefs["download"]["prompt_for_download"] = False
prefs["download"]["default_directory"] = str(download_dir)
prefs["download"]["directory_upgrade"] = True
prefs.setdefault("savefile", {})
prefs["savefile"]["default_directory"] = str(download_dir)
prefs.setdefault("plugins", {})
prefs["plugins"]["always_open_pdf_externally"] = True

prefs_path.write_text(json.dumps(prefs, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
PY

  open -na "Microsoft Edge" --args \
    --user-data-dir="$PROFILE_DIR" \
    --profile-directory=Default \
    --remote-debugging-port="$PORT" \
    --no-first-run \
    --new-window \
    about:blank >/dev/null 2>&1
fi

for _ in $(seq 1 20); do
  if is_running && profile_process_running; then
    echo "EDGE_READY port=$PORT"
    echo "PROFILE_DIR=$PROFILE_DIR"
    echo "DOWNLOAD_DIR=$DOWNLOAD_DIR"
    exit 0
  fi
  sleep 1
done

echo "error: dedicated Edge did not start on port $PORT" >&2
exit 1
