"""JavaScript checker for multi-rep-set."""
from pathlib import Path

from ..utils import ok, fail, sh, shq, BASE, TOTAL_FILES


def check_javascript(files: list[Path]) -> None:
    from ..utils import section
    section("JavaScript/Node (.js .mjs)")
    for f in files:
        global TOTAL_FILES
        TOTAL_FILES += 1
        rel = f.relative_to(BASE) if BASE in f.parents else f.name
        rc, _, err = sh(f"node --check {shq(f)}")
        if rc == 0:
            ok(f"{rel}")
        else:
            e = err.split('\n')[-1].strip()[:120] if err else "?"
            if "Warning: To load an ES module" in err:
                ok(f"{rel} (ESM)")
            else:
                fail(f"{rel}", e)
