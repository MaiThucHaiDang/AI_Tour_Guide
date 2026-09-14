"""Run deterministic backend/frontend quality gates and store machine-readable results."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = PROJECT_ROOT / "evaluation" / "results" / "system_results.json"


def _git_commit() -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        return result.stdout.strip() or None
    except FileNotFoundError:
        return None


def _npm_executable() -> str:
    executable = "npm.cmd" if os.name == "nt" else "npm"
    return shutil.which(executable) or executable


def _run_check(
    name: str,
    command: list[str],
    cwd: Path,
    env_overrides: dict[str, str] | None = None,
) -> dict[str, Any]:
    started = time.perf_counter()
    process_env = os.environ.copy()
    process_env.update(env_overrides or {})
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            env=process_env,
        )
        output = "\n".join(
            part.strip() for part in (completed.stdout, completed.stderr) if part.strip()
        )
        return {
            "name": name,
            "status": "passed" if completed.returncode == 0 else "failed",
            "return_code": completed.returncode,
            "duration_seconds": round(time.perf_counter() - started, 3),
            "command": command,
            "output_tail": output[-6000:],
        }
    except FileNotFoundError as exc:
        return {
            "name": name,
            "status": "unavailable",
            "return_code": None,
            "duration_seconds": round(time.perf_counter() - started, 3),
            "command": command,
            "output_tail": str(exc),
        }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--skip-backend", action="store_true")
    parser.add_argument("--skip-frontend", action="store_true")
    args = parser.parse_args()

    checks: list[dict[str, Any]] = []
    if not args.skip_backend:
        checks.append(
            _run_check(
                "backend_pytest",
                [sys.executable, "-m", "pytest", "backend/tests", "-q"],
                PROJECT_ROOT,
                {"RAG_DEBUG_LOG_ENABLED": "0"},
            )
        )
    if not args.skip_frontend:
        npm = _npm_executable()
        checks.append(_run_check("frontend_build", [npm, "run", "build"], PROJECT_ROOT / "frontend"))
        checks.append(
            _run_check(
                "web_speech_tests",
                [npm, "run", "test:web-speech"],
                PROJECT_ROOT / "frontend",
            )
        )

    payload = {
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "git_commit": _git_commit(),
            "python": sys.version.split()[0],
        },
        "summary": {
            "total": len(checks),
            "passed": sum(check["status"] == "passed" for check in checks),
            "failed": sum(check["status"] == "failed" for check in checks),
            "unavailable": sum(check["status"] == "unavailable" for check in checks),
        },
        "checks": checks,
    }
    output_path = args.output.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(payload["summary"], indent=2))
    print(f"Results: {output_path}")

    if payload["summary"]["failed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
