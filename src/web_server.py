"""Local web server for the red/blue eyes puzzle demo.

Serves:
- Static UI from ./web
- JSON API under /api/* backed by the Python simulation engine

Design goals:
- Zero third-party dependencies (stdlib only)
- Keep state in-memory for quick iteration
- Minimal surface area to support the existing web UI controls
"""

from __future__ import annotations

import json
import os
import threading
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import traceback
from typing import Any

from .puzzle import Village
from .reasoning import OpenAIReasoningPolicy, PerfectInductionPolicy, PolicyByVillagerType, ReasoningPolicy
from .simulation import create_village
from .env import load_dotenv


_WEB_DIR = (Path(__file__).resolve().parent.parent / "web").resolve()

# Load environment variables (including password)
load_dotenv()

# Get password from environment or use default
_APP_PASSWORD = os.getenv("APP_PASSWORD", "redblue")


class _AppState:
    village: Village | None = None
    num_red: int = 0
    num_blue: int = 0
    reasoning_policy: ReasoningPolicy | None = None
    lock: threading.Lock

    def __init__(self):
        self.lock = threading.Lock()


APP_STATE = _AppState()


def _read_json_body(handler: SimpleHTTPRequestHandler) -> dict[str, Any]:
    length = int(handler.headers.get("Content-Length", "0") or "0")
    raw = handler.rfile.read(length) if length > 0 else b"{}"
    if not raw:
        return {}
    try:
        obj = json.loads(raw.decode("utf-8"))
    except Exception as e:
        raise ValueError(f"Invalid JSON body: {e}") from e
    if not isinstance(obj, dict):
        raise ValueError("JSON body must be an object")
    return obj


def _send_json(handler: SimpleHTTPRequestHandler, status: int, obj: Any) -> None:
    data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Cache-Control", "no-store")
    handler.send_header("Content-Length", str(len(data)))
    handler.end_headers()
    handler.wfile.write(data)


def _error(handler: SimpleHTTPRequestHandler, status: int, message: str) -> None:
    _send_json(handler, status, {"ok": False, "error": message})


def _eye_enum_to_name(v: Any) -> str:
    # EyeColor Enum has .name as 'RED'/'BLUE'.
    return str(getattr(getattr(v, "eye_color", None), "name", ""))


def _village_to_state(village: Village, num_red: int, num_blue: int) -> dict[str, Any]:
    villagers = []
    for v in village.villagers:
        villagers.append(
            {
                "id": int(v.id),
                "name": str(v.name),
                "eyeColor": _eye_enum_to_name(v),
                "villagerType": str(getattr(v, "villager_type", "dummy")),
                "hasLeft": bool(v.has_left),
                "leftOnDay": int(v.left_on_day) if v.left_on_day is not None else None,
                "observedRedEyes": int(getattr(v, "observed_red_eyes", 0)),
                "observedLeftYesterday": int(getattr(v, "observed_left_yesterday", 0)),
                "observedLeftTotal": int(getattr(v, "observed_left_total", 0)),
                "reasoningLog": list(getattr(v, "reasoning_log", []) or []),
            }
        )

    return {
        "numRed": int(num_red),
        "numBlue": int(num_blue),
        "announcementMade": bool(getattr(village, "announcement_made", False)),
        "currentDay": int(getattr(village, "current_day", 0)),
        "knowledgeLevel": int(getattr(village, "knowledge_level", 0)),
        "villagers": villagers,
        "dailyLog": list(getattr(village, "daily_log", []) or []),
    }


def _build_reasoning_policy(openai_style: str) -> ReasoningPolicy:
    # Keep mapping names aligned with existing Python policies.
    return PolicyByVillagerType(
        {
            "dummy": PerfectInductionPolicy(),
            "openai": OpenAIReasoningPolicy(
                style=openai_style,
                align_to_standard_proof=(openai_style == "absolute_rational"),
            ),
        },
        default=PerfectInductionPolicy(),
    )


def _build_villager_types(num_red: int, num_blue: int, mode: str) -> list[str]:
    total = num_red + num_blue
    if total <= 0:
        return []

    if mode == "all_openai":
        return ["openai"] * total
    if mode == "all_dummy":
        return ["dummy"] * total

    # mixed_ends (default): first and last are openai, rest dummy.
    types = ["dummy"] * total
    types[0] = "openai"
    if total > 1:
        types[-1] = "openai"
    return types


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(_WEB_DIR), **kwargs)

    def do_GET(self) -> None:  # noqa: N802
        if self.path.startswith("/api/"):
            return self._handle_api_get()
        return super().do_GET()

    def do_POST(self) -> None:  # noqa: N802
        if self.path.startswith("/api/"):
            return self._handle_api_post()
        self.send_error(404)

    def _handle_api_get(self) -> None:
        if self.path.startswith("/api/state"):
            if APP_STATE.village is None:
                return _send_json(self, 200, {"ok": True, "state": None})
            return _send_json(
                self,
                200,
                {
                    "ok": True,
                    "state": _village_to_state(APP_STATE.village, APP_STATE.num_red, APP_STATE.num_blue),
                },
            )

        if self.path.startswith("/api/health"):
            return _send_json(self, 200, {"ok": True})

        return _error(self, 404, "Unknown API endpoint")

    def _handle_api_post(self) -> None:
        try:
            body = _read_json_body(self)
        except ValueError as e:
            return _error(self, 400, str(e))

        started = time.time()
        print(f"[API] start {self.command} {self.path}", flush=True)

        try:
            if self.path.startswith("/api/verify_password"):
                password = body.get("password", "")
                if password == _APP_PASSWORD:
                    return _send_json(self, 200, {"ok": True, "valid": True})
                else:
                    return _send_json(self, 200, {"ok": True, "valid": False})
            if self.path.startswith("/api/init"):
                return self._api_init(body)
            if self.path.startswith("/api/announce"):
                return self._api_announce()
            if self.path.startswith("/api/next"):
                return self._api_next()
            if self.path.startswith("/api/run_all"):
                return self._api_run_all()
            if self.path.startswith("/api/reset"):
                with APP_STATE.lock:
                    APP_STATE.village = None
                    APP_STATE.num_red = 0
                    APP_STATE.num_blue = 0
                    APP_STATE.reasoning_policy = None
                return _send_json(self, 200, {"ok": True, "state": None})
        except ValueError as e:
            return _error(self, 400, str(e))
        except Exception as e:
            # Surface errors to the UI; OpenAI errors are expected when key/model is misconfigured.
            traceback.print_exc()
            return _error(self, 500, str(e))
        finally:
            elapsed_ms = int((time.time() - started) * 1000)
            print(f"[API] end   {self.command} {self.path} ({elapsed_ms}ms)", flush=True)

        return _error(self, 404, "Unknown API endpoint")

    def _api_init(self, body: dict[str, Any]) -> None:
        num_red = int(body.get("numRed", 0))
        num_blue = int(body.get("numBlue", 0))
        mode = str(body.get("villagerMode", "mixed_ends") or "mixed_ends")
        openai_style = str(body.get("openaiStyle", os.getenv("OPENAI_STYLE", "social")) or "social")

        if num_red < 0 or num_blue < 0 or (num_red + num_blue) > 200:
            raise ValueError("Invalid population size")

        policy = _build_reasoning_policy(openai_style=openai_style)
        types = _build_villager_types(num_red, num_blue, mode)
        village = create_village(
            num_red,
            num_blue,
            reasoning_policy=policy,
            villager_types=types,
        )

        # Add an initial log line so the UI always has context.
        village.daily_log.append(
            f"[Backend] 初始化：红眼睛 {num_red} 人，蓝眼睛 {num_blue} 人；mode={mode}；openaiStyle={openai_style}"
        )

        with APP_STATE.lock:
            APP_STATE.village = village
            APP_STATE.num_red = num_red
            APP_STATE.num_blue = num_blue
            APP_STATE.reasoning_policy = policy

        return _send_json(self, 200, {"ok": True, "state": _village_to_state(village, num_red, num_blue)})

    def _api_announce(self) -> None:
        with APP_STATE.lock:
            if APP_STATE.village is None:
                raise ValueError("Not initialized")
            APP_STATE.village.make_announcement()
            return _send_json(
                self,
                200,
                {"ok": True, "state": _village_to_state(APP_STATE.village, APP_STATE.num_red, APP_STATE.num_blue)},
            )

    def _api_next(self) -> None:
        with APP_STATE.lock:
            if APP_STATE.village is None:
                raise ValueError("Not initialized")
            APP_STATE.village.simulate_day()
            return _send_json(
                self,
                200,
                {"ok": True, "state": _village_to_state(APP_STATE.village, APP_STATE.num_red, APP_STATE.num_blue)},
            )

    def _api_run_all(self) -> None:
        if APP_STATE.village is None:
            raise ValueError("Not initialized")

        village = APP_STATE.village
        num_red = APP_STATE.num_red

        def is_finished() -> bool:
            if num_red == 0:
                return True
            return all(v.has_left for v in village.villagers if _eye_enum_to_name(v) == "RED")

        cap = max(5, num_red + 10) if village.announcement_made else 20
        steps = 0
        while not is_finished() and steps < cap:
            village.simulate_day()
            steps += 1

        if not village.announcement_made and not is_finished():
            village.daily_log.append(f"\n⏹️ 已停止：未宣布时不会收敛，已演示 {cap} 天。")

        return _send_json(
            self,
            200,
            {"ok": True, "state": _village_to_state(village, APP_STATE.num_red, APP_STATE.num_blue)},
        )


def main() -> None:
    host = os.getenv("WEB_HOST", "127.0.0.1")
    port = int(os.getenv("WEB_PORT", "8000"))

    server = ThreadingHTTPServer((host, port), Handler)
    print(f"Serving UI+API on http://{host}:{port} (web dir: {_WEB_DIR})")
    server.serve_forever()


if __name__ == "__main__":
    main()
