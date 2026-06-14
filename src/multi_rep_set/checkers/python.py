"""Python checker for multi-rep-set."""
from pathlib import Path

from ..utils import ok, fail, skip, sh, shq, BASE, TOTAL_FILES


def check_python(files: list[Path]) -> None:
    from ..utils import section
    section("Python (.py)")
    for f in files:
        global TOTAL_FILES
        TOTAL_FILES += 1
        rel = f.relative_to(BASE) if BASE in f.parents else f.name
        if f.name == "__init__.py":
            ok(f"{rel} (init)")
            continue
        rc, _, err = sh(f"python3 -m py_compile {shq(f)}")
        if rc == 0:
            ok(f"{rel}")
        else:
            e = err.split('\n')[-1].strip()[:120] if err else "?"
            fail(f"{rel}", e)


def check_python_ruff(files: list[Path], fix: bool = False) -> None:
    from ..utils import section
    section("Python ruff")
    rc, _, _ = sh("which ruff")
    if rc != 0:
        skip("ruff nicht installiert (pip install ruff)")
        return
    for f in files[:20]:
        if f.name == "__init__.py":
            continue
        rel = f.relative_to(BASE) if BASE in f.parents else f.name
        cmd = f"ruff check --quiet {shq(f)}"
        if fix:
            cmd = f"ruff check --fix --unsafe-fixes --quiet {shq(f)}"
        rc, out, _ = sh(cmd)
        if rc == 0:
            ok(f"{rel}")
        else:
            lines = [l for l in out.split('\n') if l.strip()][:3]
            fail(f"{rel}", "; ".join(lines[:3])[:150])
