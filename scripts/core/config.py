from __future__ import annotations

import os
import shlex
import sys
from dataclasses import dataclass
from pathlib import Path


DEFAULT_EDGE_BIN = "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"
DEFAULT_REMOTE_DEBUG_PORT = 62777


@dataclass(frozen=True)
class Settings:
    edge_bin: str
    profile_dir: Path
    download_dir: Path
    remote_debug_port: int

    @property
    def remote_debug_base_url(self) -> str:
        return f"http://127.0.0.1:{self.remote_debug_port}"

    @property
    def remote_debug_list_url(self) -> str:
        return f"{self.remote_debug_base_url}/json/list"

    @property
    def remote_debug_new_url(self) -> str:
        return f"{self.remote_debug_base_url}/json/new"


def load_settings(skill_root: Path | None = None) -> Settings:
    root = skill_root or Path(__file__).resolve().parents[2]
    dotenv = _read_dotenv(root / ".env")

    edge_bin = _read_value("ZJU_EDGE_EDGE_BIN", dotenv) or DEFAULT_EDGE_BIN
    profile_dir = _resolve_path(
        _read_value("ZJU_EDGE_PROFILE_DIR", dotenv),
        root,
        default=root / ".local" / "edge-profile",
    )
    download_dir = _resolve_path(
        _read_value("ZJU_EDGE_DOWNLOAD_DIR", dotenv),
        root,
        default=root / "output" / "final-pdfs",
    )
    remote_debug_port = int(
        _read_value("ZJU_EDGE_REMOTE_DEBUG_PORT", dotenv) or DEFAULT_REMOTE_DEBUG_PORT
    )

    return Settings(
        edge_bin=edge_bin,
        profile_dir=profile_dir,
        download_dir=download_dir,
        remote_debug_port=remote_debug_port,
    )


def _read_dotenv(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    result: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip()
        if value[:1] == value[-1:] and value[:1] in {"'", '"'}:
            value = value[1:-1]
        result[key] = os.path.expandvars(value)
    return result


def _read_value(name: str, dotenv: dict[str, str]) -> str | None:
    env_value = os.environ.get(name)
    if env_value:
        return env_value
    return dotenv.get(name)


def _resolve_path(raw: str | None, root: Path, *, default: Path) -> Path:
    if not raw:
        return default.resolve()
    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = root / path
    return path.resolve()


def shell_exports(skill_root: Path | None = None) -> str:
    settings = load_settings(skill_root)
    exports = {
        "ZJU_EDGE_EDGE_BIN": settings.edge_bin,
        "ZJU_EDGE_PROFILE_DIR": str(settings.profile_dir),
        "ZJU_EDGE_DOWNLOAD_DIR": str(settings.download_dir),
        "ZJU_EDGE_REMOTE_DEBUG_PORT": str(settings.remote_debug_port),
    }
    return "\n".join(f"export {key}={shlex.quote(value)}" for key, value in exports.items())


def main(argv: list[str] | None = None) -> int:
    args = argv or sys.argv[1:]
    if args == ["export-shell"]:
        print(shell_exports())
        return 0
    print("Usage: python3 scripts/core/config.py export-shell", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
