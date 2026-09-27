"""Run the local API and Vite together on Linux/macOS, including process cleanup."""

import argparse
import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def check_port(port: int) -> None:
    with socket.socket() as probe:
        # Match Uvicorn: TIME_WAIT connections must not block a server restart.
        probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            probe.bind(("127.0.0.1", port))
        except OSError as exc:
            raise RuntimeError(f"Port {port} is already in use. Stop that server first.") from exc


def preflight(backend_port: int, frontend_port: int) -> None:
    from alembic.config import Config
    from alembic.runtime.migration import MigrationContext
    from alembic.script import ScriptDirectory
    from sqlalchemy import create_engine

    from backend.core.config import get_settings

    if not (ROOT / "frontend/node_modules/.bin/vite").exists():
        raise RuntimeError("Frontend dependencies are missing. Run make setup.")
    if backend_port == frontend_port:
        raise RuntimeError("Backend and frontend need different ports.")
    for port in (backend_port, frontend_port):
        check_port(port)
    try:
        settings = get_settings()
    except ValueError as exc:
        raise RuntimeError("Invalid settings. Check DATABASE_URL and SECRET_KEY in .env.") from exc
    connect_args = {"connect_timeout": 5} if settings.database_url.startswith("postgresql") else {}
    engine = None
    try:
        engine = create_engine(settings.database_url, connect_args=connect_args)
        with engine.connect() as connection:
            current = set(MigrationContext.configure(connection).get_current_heads())
        expected = set(ScriptDirectory.from_config(Config("backend/alembic.ini")).get_heads())
        if current != expected:
            raise RuntimeError("Database migrations are not current. Run make migrate.")
    except RuntimeError:
        raise
    except Exception as exc:
        raise RuntimeError("Cannot check the database. Check DATABASE_URL and PostgreSQL.") from exc
    finally:
        if engine is not None:
            engine.dispose()


def supervise(commands: list[list[str]], env: dict[str, str]) -> int:
    children: list[subprocess.Popen] = []
    stopped = 0

    def stop(signum: int, frame: object) -> None:
        nonlocal stopped
        stopped = signum

    previous = {sig: signal.signal(sig, stop) for sig in (signal.SIGINT, signal.SIGTERM)}
    try:
        for command in commands:
            children.append(subprocess.Popen(command, cwd=ROOT, env=env, start_new_session=True))
        while not stopped:
            for child in children:
                if child.poll() is not None:
                    print("A development server exited; stopping both servers.", file=sys.stderr)
                    return child.returncode or 1
            time.sleep(0.1)
        return 128 + stopped
    finally:
        # Kill process groups so reload workers and npm's Vite child also exit.
        for child in children:
            try:
                os.killpg(child.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
        deadline = time.monotonic() + 5
        for child in children:
            try:
                child.wait(timeout=max(0, deadline - time.monotonic()))
            except subprocess.TimeoutExpired:
                pass
        for child in children:
            try:
                os.killpg(child.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            child.wait()
        for sig, handler in previous.items():
            signal.signal(sig, handler)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backend-port", type=int, default=8000)
    parser.add_argument("--frontend-port", type=int, default=5173)
    args = parser.parse_args()
    if not all(1 <= port <= 65535 for port in (args.backend_port, args.frontend_port)):
        parser.error("Ports must be between 1 and 65535.")
    os.chdir(ROOT)
    try:
        preflight(args.backend_port, args.frontend_port)
        print(
            f"Starting API on http://127.0.0.1:{args.backend_port} "
            f"and UI on http://localhost:{args.frontend_port}",
            flush=True,
        )
        env = {**os.environ, "API_PROXY_TARGET": f"http://127.0.0.1:{args.backend_port}"}
        return supervise(
            [
                [
                    sys.executable,
                    "-m",
                    "uvicorn",
                    "backend.main:app",
                    "--reload",
                    "--port",
                    str(args.backend_port),
                ],
                [
                    "npm",
                    "--prefix",
                    "frontend",
                    "run",
                    "dev",
                    "--",
                    "--port",
                    str(args.frontend_port),
                ],
            ],
            env,
        )
    except (RuntimeError, OSError) as exc:
        print(f"Development startup failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
