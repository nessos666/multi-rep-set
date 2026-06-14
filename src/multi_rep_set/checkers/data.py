"""JSON, YAML, Markdown checkers for multi-rep-set."""
import json
import re
from pathlib import Path

from ..utils import ok, fail, warn, skip, BASE, TOTAL_FILES


def check_json(files: list[Path]) -> None:
    from ..utils import section
    section("JSON (.json)")
    for f in files:
        global TOTAL_FILES
        TOTAL_FILES += 1
        rel = f.relative_to(BASE) if BASE in f.parents else f.name
        if f.stat().st_size > 500000:
            skip(f"{rel} (zu gross)")
            continue
        try:
            json.loads(f.read_text())
            ok(f"{rel}")
        except json.JSONDecodeError as e:
            fail(f"{rel}", str(e)[:100])


def check_yaml(files: list[Path]) -> None:
    from ..utils import section
    section("YAML (.yaml .yml)")
    for f in files:
        global TOTAL_FILES
        TOTAL_FILES += 1
        rel = f.relative_to(BASE) if BASE in f.parents else f.name
        try:
            import yaml as _y
            _y.safe_load(f.read_text())
            ok(f"{rel}")
        except ImportError:
            content = f.read_text()
            if '{' in content or '}' in content:
                try:
                    json.loads(content)
                    ok(f"{rel}")
                except Exception:
                    warn(f"{rel} (kein YAML-Parser)")
            else:
                ok(f"{rel} (basic)")
        except Exception as e:
            fail(f"{rel}", str(e)[:100])


def check_markdown(files: list[Path]) -> None:
    from ..utils import section
    section("Markdown (.md)")
    for f in files:
        global TOTAL_FILES
        TOTAL_FILES += 1
        rel = f.relative_to(BASE) if BASE in f.parents else f.name
        try:
            content = f.read_text()
            broken = re.findall(r'\[([^\]]+)\]\(\)', content)
            if broken:
                warn(f"{rel} (leere Links: {len(broken)})")
            else:
                ok(f"{rel}")
        except Exception:
            skip(f"{rel} (kann nicht lesen)")
