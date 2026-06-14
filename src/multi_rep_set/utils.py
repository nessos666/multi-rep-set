"""Shared utilities for multi-rep-set checkers."""
import os
import subprocess
from pathlib import Path

BASE = Path.home()
CHECKED: set[str] = set()
PASS = 0
FAIL = 0
WARN = 0
SKIP = 0
TOTAL_FILES = 0
USE_COLOR = True
SCAN_DIRS: list[Path] = []
MAX_PER_TYPE = 50
IGNORE_PATTERNS = ["node_modules", ".git", ".cache", "__pycache__", ".venv", "venv", ".hermes"]

C = {"g": "\033[92m", "r": "\033[91m", "y": "\033[93m", "b": "\033[94m", "n": "\033[0m"}
E = {"g": "", "r": "", "y": "", "b": "", "n": ""}


def section(title: str) -> None:
    c = C if USE_COLOR else E
    print(f"\n{c['b']}── {title} ──{c['n']}")


def ok(msg: str) -> None:
    global PASS
    PASS += 1
    c = C if USE_COLOR else E
    print(f"  {c['g']}OK{c['n']} {msg}")


def fail(msg: str, details: str = "") -> None:
    global FAIL
    FAIL += 1
    c = C if USE_COLOR else E
    print(f"  {c['r']}FAIL{c['n']} {msg}")
    if details:
        print(f"     {details[:200]}")


def warn(msg: str) -> None:
    global WARN
    WARN += 1
    c = C if USE_COLOR else E
    print(f"  {c['y']}WARN{c['n']} {msg}")


def skip(msg: str) -> None:
    global SKIP
    SKIP += 1
    print(f"  SKIP {msg}")


def sh(cmd: str, timeout: int = 30) -> tuple[int, str, str]:
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except subprocess.TimeoutExpired:
        return -1, "", "TIMEOUT"
    except FileNotFoundError:
        return -2, "", "NOT FOUND"


def shq(s: str | Path) -> str:
    s_str = str(s)
    q = chr(39)
    return q + s_str.replace(q, q + "\\" + q) + q


def load_config() -> dict:
    config_path = Path.home() / ".multi-rep-set.yaml"
    if not config_path.exists():
        return {}
    try:
        import yaml
        with open(config_path) as f:
            return yaml.safe_load(f) or {}
    except ImportError:
        cfg: dict = {}
        with open(config_path) as f:
            for line in f:
                if ':' in line and not line.strip().startswith('#'):
                    k, v = line.split(':', 1)
                    cfg[k.strip()] = v.strip().strip('"').strip("'")
        return cfg


def init_dirs(config: dict | None = None) -> None:
    global SCAN_DIRS, MAX_PER_TYPE, IGNORE_PATTERNS
    if config:
        user_dirs = config.get('scan_dirs') or config.get('SCAN_DIRS')
        if user_dirs:
            SCAN_DIRS = []
            for d in (user_dirs if isinstance(user_dirs, list) else [user_dirs]):
                p = Path(d).expanduser()
                if p.exists():
                    SCAN_DIRS.append(p)
        mt = config.get('max_per_type') or config.get('MAX_PER_TYPE')
        if mt:
            MAX_PER_TYPE = int(mt)
        ip = config.get('ignore_patterns') or config.get('IGNORE_PATTERNS')
        if ip:
            IGNORE_PATTERNS = list(ip) if isinstance(ip, list) else [ip]

    if not SCAN_DIRS:
        SCAN_DIRS = [
            BASE / "HAUPTLAGER/27_TV_Watch_Agent",
            BASE / "HAUPTLAGER/24_Strategie_Builder",
            BASE / "HAUPTLAGER/14_Scripts_Utilities",
            BASE / "HAUPTLAGER/28_JobHunter",
            BASE / "HAUPTLAGER/_GEDECHTNIS",
            BASE / "HAUPTLAGER/22_Werkbank",
            BASE / "HERMES_BIBLIOTHEK",
            BASE / "linkedin-mcp-server",
            BASE / "nq-strategy-builder",
            BASE / "hermes-test",
            BASE / "bin",
            BASE / "scripts",
        ]
        SCAN_DIRS = [d for d in SCAN_DIRS if d.exists()]


def find_files(patterns: list[str]) -> list[Path]:
    files: list[Path] = []
    for d in SCAN_DIRS:
        if not d.exists():
            continue
        for p in patterns:
            for f in sorted(d.rglob(p)):
                if any(x in str(f) for x in IGNORE_PATTERNS):
                    continue
                if str(f) not in CHECKED:
                    files.append(f)
                    CHECKED.add(str(f))
    return files[:MAX_PER_TYPE]
