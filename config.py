"""Dola Pool Configuration: Environment variable based with smart defaults."""
import os
from pathlib import Path
from urllib.parse import quote, unquote


def _load_local_env():
    """Load ignored .env.local for local/tunnel runs; real environment wins."""
    path = Path(__file__).with_name(".env.local")
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def get_playwright_proxy(raw: str | None = None) -> dict | None:
    """Parses any proxy format (ip:port:user:pass, user:pass@ip:port, http://..., socks5://...)
    into Playwright's proxy dict {'server': '...', 'username': '...', 'password': '...'}.
    """
    val = (PROXY if raw is None else raw) or ""
    val = val.strip().strip('"').strip("'")
    if not val:
        return None

    scheme = "http"
    rest = val
    if "://" in val:
        scheme, rest = val.split("://", 1)
        scheme = scheme.lower().strip() or "http"

    rest = rest.strip().rstrip("/")
    username = None
    password = None
    host_port = rest

    if "@" in rest:
        auth_part, host_port = rest.rsplit("@", 1)
        if ":" in auth_part:
            u, p = auth_part.split(":", 1)
            username = unquote(u)
            password = unquote(p)
        else:
            username = unquote(auth_part)
            password = ""
    else:
        parts = rest.split(":")
        if len(parts) >= 4 and parts[1].isdigit():
            host_port = f"{parts[0]}:{parts[1]}"
            username = parts[2]
            password = ":".join(parts[3:])

    out: dict[str, str] = {"server": f"{scheme}://{host_port}"}
    if username is not None and username != "":
        out["username"] = username
        out["password"] = password or ""
    return out


def get_aiohttp_proxy(raw: str | None = None) -> str | None:
    """Returns a standard URL (http://user:pass@host:port) suitable for aiohttp."""
    parsed = get_playwright_proxy(raw)
    if not parsed:
        return None
    server = parsed["server"]
    if "username" in parsed and parsed["username"]:
        scheme, hp = server.split("://", 1)
        u = quote(parsed["username"], safe="")
        p = quote(parsed.get("password", ""), safe="")
        return f"{scheme}://{u}:{p}@{hp}"
    return server


def update_proxy(new_proxy: str) -> str:
    """Update DOLA_PROXY in memory and overwrite it in .env.local."""
    global PROXY
    cleaned = (new_proxy or "").strip().strip('"').strip("'")
    os.environ["DOLA_PROXY"] = cleaned
    PROXY = cleaned

    env_path = Path(__file__).with_name(".env.local")
    if env_path.exists():
        lines = env_path.read_text(encoding="utf-8-sig").splitlines()
    else:
        lines = [
            "# Cau hinh Dola Render Gateway",
            f"DOLA_HOST={HOST}",
            f"DOLA_PORT={PORT}",
            "",
            "# Proxy HTTP neu co (de trong neu dung VPN hoac mang truc tiep)",
            f"DOLA_PROXY={cleaned}",
        ]

    out_lines: list[str] = []
    replaced = False
    for raw in lines:
        stripped = raw.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            k, _ = stripped.split("=", 1)
            if k.strip() == "DOLA_PROXY":
                if not replaced:
                    out_lines.append(f"DOLA_PROXY={cleaned}")
                    replaced = True
                continue
        out_lines.append(raw)

    if not replaced:
        out_lines.append(f"DOLA_PROXY={cleaned}")

    env_path.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
    return cleaned


_load_local_env()
_portable_browsers = Path(__file__).with_name("runtime") / "browsers"
if _portable_browsers.exists():
    os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", str(_portable_browsers.resolve()))
HOST = os.getenv("DOLA_HOST", "0.0.0.0")
PORT = int(os.getenv("DOLA_PORT", "8000"))

# Service API keys (comma-separated; empty = no auth, local debug only)
API_KEYS = [k.strip() for k in os.getenv("DOLA_API_KEYS", "").split(",") if k.strip()]

# Account pool cookie file (one dola.com cookie per line)
COOKIES_FILE = os.getenv("DOLA_COOKIES_FILE", "cookies.txt")

# Max concurrent video generation tasks
MAX_CONCURRENCY = int(os.getenv("DOLA_MAX_CONCURRENCY", "3"))

# Global pending task queue limit (queued + processing), 0 = unlimited
MAX_PENDING_TASKS = int(os.getenv("DOLA_MAX_PENDING_TASKS", "100"))

# Video generation timeout in seconds
VIDEO_TIMEOUT = int(os.getenv("DOLA_VIDEO_TIMEOUT", "900"))

# SQLite database path
DB_PATH = os.getenv("DOLA_DB_PATH", "tasks.db")

# Video download storage directory (served statically by FastAPI)
DOWNLOAD_DIR = os.getenv("DOLA_DOWNLOAD_DIR", "downloads")

# Explicit browser proxy (must point to JP/KR egress; empty = system proxy / direct)
PROXY = os.getenv("DOLA_PROXY", "").strip()

# Run browser in headless mode (login always runs with head)
HEADLESS = os.getenv("DOLA_HEADLESS", "1") == "1"

# Base public URL for returning static video links
PUBLIC_BASE = os.getenv("DOLA_PUBLIC_BASE", f"http://127.0.0.1:{PORT}")

# Admin web dashboard password (empty = no auth)
ADMIN_KEY = os.getenv("DOLA_ADMIN_KEY", "")

# Dola 30s / Watermark Removal Chromium extension path
EXTENSION_DIR = os.getenv("DOLA_EXTENSION_DIR", "extensions/dola30")
EXTENSION_ENABLED = os.getenv("DOLA_EXTENSION_ENABLED", "1") == "1"

# Daily quota reset timezone (Japan midnight by default)
LIMIT_RESET_TZ = os.getenv("DOLA_LIMIT_RESET_TZ", "Asia/Tokyo")

# Conservative credit check before video generation (default 2 points)
VIDEO_REQUIRED_POINTS = int(os.getenv("DOLA_VIDEO_REQUIRED_POINTS", "2"))

# Public reference image download limits
REFERENCE_IMAGE_MAX_BYTES = int(os.getenv("DOLA_REFERENCE_IMAGE_MAX_BYTES", str(15 * 1024 * 1024)))
REFERENCE_DOWNLOAD_TIMEOUT = int(os.getenv("DOLA_REFERENCE_DOWNLOAD_TIMEOUT", "60"))
REFERENCE_IMAGE_MAX_COUNT = int(os.getenv("DOLA_REFERENCE_IMAGE_MAX_COUNT", "30"))

# Extended generation window for reference image tasks (seconds)
REFERENCE_VIDEO_TIMEOUT = int(os.getenv("DOLA_REFERENCE_VIDEO_TIMEOUT", "900"))
