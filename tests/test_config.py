from pathlib import Path
import sys


SKILL_ROOT = Path(__file__).resolve().parents[1]
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))


from scripts.core.config import DEFAULT_EDGE_BIN, load_settings


def test_load_settings_uses_repo_relative_defaults(tmp_path, monkeypatch):
    monkeypatch.delenv("ZJU_EDGE_EDGE_BIN", raising=False)
    monkeypatch.delenv("ZJU_EDGE_PROFILE_DIR", raising=False)
    monkeypatch.delenv("ZJU_EDGE_DOWNLOAD_DIR", raising=False)
    monkeypatch.delenv("ZJU_EDGE_REMOTE_DEBUG_PORT", raising=False)

    settings = load_settings(tmp_path)

    assert settings.edge_bin == DEFAULT_EDGE_BIN
    assert settings.profile_dir == tmp_path / ".local" / "edge-profile"
    assert settings.download_dir == tmp_path / "output" / "final-pdfs"
    assert settings.remote_debug_port == 62777


def test_load_settings_prefers_dotenv_values(tmp_path, monkeypatch):
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                "ZJU_EDGE_PROFILE_DIR=./custom/profile",
                "ZJU_EDGE_DOWNLOAD_DIR=./custom/downloads",
                "ZJU_EDGE_REMOTE_DEBUG_PORT=63333",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.delenv("ZJU_EDGE_PROFILE_DIR", raising=False)
    monkeypatch.delenv("ZJU_EDGE_DOWNLOAD_DIR", raising=False)
    monkeypatch.delenv("ZJU_EDGE_REMOTE_DEBUG_PORT", raising=False)

    settings = load_settings(tmp_path)

    assert settings.profile_dir == tmp_path / "custom" / "profile"
    assert settings.download_dir == tmp_path / "custom" / "downloads"
    assert settings.remote_debug_port == 63333


def test_load_settings_prefers_environment_over_dotenv(tmp_path, monkeypatch):
    (tmp_path / ".env").write_text(
        "ZJU_EDGE_DOWNLOAD_DIR=./from-dotenv\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("ZJU_EDGE_DOWNLOAD_DIR", str(tmp_path / "from-env"))

    settings = load_settings(tmp_path)

    assert settings.download_dir == tmp_path / "from-env"
