"""Minimal .env loader.

Purpose:
- Allow configuring secrets (e.g., OPENAI_API_KEY) via a local `.env` file
  without adding third-party dependencies.

Behavior:
- Looks for `.env` at the repository root (parent of `src/`).
- Parses simple KEY=VALUE lines (supports optional quotes).
- Ignores blank lines and comments starting with `#`.
- Does NOT override existing environment variables by default.
"""

from __future__ import annotations

from pathlib import Path
import os


def _repo_root() -> Path:
    # This file lives in `src/`, so repo root is one level up.
    return Path(__file__).resolve().parents[1]


def load_dotenv(path: str | os.PathLike | None = None, *, override: bool = False) -> bool:
    """Load environment variables from a `.env` file.

    Args:
        path: Path to `.env`. If None, uses repo root `.env`.
        override: When True, overwrite existing os.environ values.

    Returns:
        True if a file was found and parsed, False otherwise.
    """

    env_path = Path(path) if path is not None else (_repo_root() / ".env")
    if not env_path.exists() or not env_path.is_file():
        return False

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        # Support: export KEY=VALUE
        if line.startswith("export "):
            line = line[len("export ") :].lstrip()

        if "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()

        # Strip optional surrounding quotes
        if (len(value) >= 2) and ((value[0] == value[-1]) and value[0] in ('"', "'")):
            value = value[1:-1]

        if not key:
            continue

        if (not override) and (key in os.environ):
            continue

        os.environ[key] = value

    return True
