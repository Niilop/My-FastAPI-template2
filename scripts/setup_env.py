"""Initialize local settings without replacing existing configuration."""

import os
import secrets
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def initialize_env(root: Path) -> bool:
    content = (root / ".env.example").read_text()
    content = content.replace("SECRET_KEY=\n", f"SECRET_KEY={secrets.token_urlsafe(48)}\n")
    try:
        descriptor = os.open(root / ".env", os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        return False
    with os.fdopen(descriptor, "w") as destination:
        destination.write(content)
    return True


if __name__ == "__main__":
    if initialize_env(ROOT):
        print("Created .env with a generated SECRET_KEY (not displayed).")
    else:
        print("Existing .env preserved.")
    print("Set DATABASE_URL to your project's database, then run make migrate and make dev.")
