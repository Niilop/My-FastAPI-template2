import os
import signal
import subprocess
import sys
import time
from pathlib import Path

from scripts.setup_env import initialize_env


def test_setup_creates_private_env_and_preserves_existing(tmp_path: Path) -> None:
    (tmp_path / ".env.example").write_text("DATABASE_URL=example\nSECRET_KEY=\n")
    assert initialize_env(tmp_path)
    target = tmp_path / ".env"
    content = target.read_text()
    assert content.startswith("DATABASE_URL=example\nSECRET_KEY=")
    assert len(content.split("SECRET_KEY=")[1].strip()) >= 32
    assert target.stat().st_mode & 0o777 == 0o600
    assert not initialize_env(tmp_path)
    assert target.read_text() == content


def test_setup_does_not_follow_existing_env_symlink(tmp_path: Path) -> None:
    (tmp_path / ".env.example").write_text("SECRET_KEY=\n")
    target = tmp_path / "elsewhere"
    target.write_text("keep this")
    (tmp_path / ".env").symlink_to(target)
    assert not initialize_env(tmp_path)
    assert target.read_text() == "keep this"


def test_dev_stops_other_server_on_child_failure(tmp_path: Path) -> None:
    # Each simulated server records its PID. The failure waits until its sibling starts.
    pid_file = tmp_path / "child.pid"
    script = r"""
import os, sys
from scripts.dev import supervise
pid_file = sys.argv[1]
sleeper = ('import os,sys,time; from pathlib import Path; '
           'Path(sys.argv[1]).write_text(str(os.getpid())); time.sleep(60)')
failure = ('import sys,time; from pathlib import Path\n'
           'while not Path(sys.argv[1]).exists(): time.sleep(0.01)\nsys.exit(7)')
commands = [[sys.executable, '-c', sleeper, pid_file],
            [sys.executable, '-c', failure, pid_file]]
raise SystemExit(supervise(commands, dict(os.environ)))
"""
    result = subprocess.run([sys.executable, "-c", script, str(pid_file)], timeout=15)
    assert result.returncode == 7
    pid = int(pid_file.read_text())
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        pass
    else:
        raise AssertionError("Sibling development server was left running")


def test_dev_stops_server_on_termination(tmp_path: Path) -> None:
    pid_file = tmp_path / "child.pid"
    script = """
import os, sys
from scripts.dev import supervise
child = ('import os,sys,time; from pathlib import Path; '
         'Path(sys.argv[1]).write_text(str(os.getpid())); time.sleep(60)')
raise SystemExit(supervise([[sys.executable, '-c', child, sys.argv[1]]], dict(os.environ)))
"""
    process = subprocess.Popen([sys.executable, "-c", script, str(pid_file)])
    try:
        deadline = time.monotonic() + 10
        while not pid_file.exists() and time.monotonic() < deadline:
            time.sleep(0.01)
        assert pid_file.exists()
        process.send_signal(signal.SIGTERM)
        assert process.wait(timeout=10) == 128 + signal.SIGTERM
        pid = int(pid_file.read_text())
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            pass
        else:
            raise AssertionError("Development server was left running after termination")
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
