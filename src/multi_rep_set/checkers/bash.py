"""Bash checker for multi-rep-set."""
import json
from pathlib import Path

from ..utils import ok, fail, warn, skip, sh, shq, BASE, TOTAL_FILES


def check_bash(files: list[Path]) -> None:
    from ..utils import section
    section("Bash (.sh)")
    for f in files:
        global TOTAL_FILES
        TOTAL_FILES += 1
        try:
            content = f.read_text()[:500]
        except Exception:
            skip(f"{f.name} (kann nicht lesen)")
            continue
        if not content.startswith("#!"):
            skip(f"{f.name} (kein Shebang)")
            continue
        rel = f.relative_to(BASE) if BASE in f.parents else f.name

        rc, _, err = sh(f"bash -n {shq(f)}")
        if rc == 0:
            ok(f"{rel}")
        else:
            e = err.split('\n')[0].strip()[:100] if err else "?"
            fail(f"{rel}", e)

        if "set -e" in content:
            pass
        else:
            warn(f"  kein set -e: {f.name}")


def check_bash_shellcheck(files: list[Path]) -> None:
    from ..utils import section
    section("Bash shellcheck")
    for f in files[:20]:
        try:
            c = f.read_text()[:100]
            if not c.startswith("#!"):
                continue
        except Exception:
            continue
        rel = f.relative_to(BASE) if BASE in f.parents else f.name
        rc, out, _ = sh(f"shellcheck -s bash -f json {shq(f)}")
        if rc == 0:
            ok(f"{rel}")
        elif rc == -2:
            skip("shellcheck nicht installiert (sudo apt install shellcheck)")
            return
        else:
            try:
                findings = json.loads(out) if out else []
                errs = [x for x in findings if x.get('level') == 'error']
                warns = [x for x in findings if x.get('level') in ('warning', 'style')]
                if errs:
                    fail(f"{rel} ({len(errs)} errors)", errs[0].get('message', '')[:100])
                elif warns:
                    warn(f"{rel} ({len(warns)} warnings)")
            except Exception:
                warn(f"{rel} (parse error)")
