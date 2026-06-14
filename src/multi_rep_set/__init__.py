"""MULTI REP SET — Multi-Language Code Checker
Prüft Bash, Python, JavaScript, JSON, YAML, Markdown auf Syntax + Stil.
Kein Codex, keine API, keine Token. Lokal in Sekunden."""
import argparse
import re
import sys
import time
from datetime import datetime
from pathlib import Path

from multi_rep_set.utils import (
    BASE, C, E, USE_COLOR, SCAN_DIRS, TOTAL_FILES,
    PASS, FAIL, WARN, SKIP,
    section, ok, fail, warn, skip, sh, shq, load_config, init_dirs, find_files,
)
from multi_rep_set.checkers.bash import check_bash, check_bash_shellcheck
from multi_rep_set.checkers.python import check_python, check_python_ruff
from multi_rep_set.checkers.js import check_javascript
from multi_rep_set.checkers.data import check_json, check_yaml, check_markdown


def check_deep(files: list[Path]) -> None:
    section("Deep Analysis")
    deep_fail = 0
    for f in files:
        if f.suffix != '.py':
            continue
        try:
            content = f.read_text()
        except Exception:
            continue
        rel = f.relative_to(BASE) if BASE in f.parents else f.name
        issues = []

        empty_excepts = len(re.findall(r'except\s*:\s*pass', content))
        if empty_excepts:
            issues.append(f"{empty_excepts}x leeres except: pass")

        whiles = content.count('while True:')
        breaks = content.count('break')
        if whiles > breaks:
            issues.append(f"{whiles - breaks}x while True ohne break")

        todos = len(re.findall(r'#\s*(TODO|FIXME|XXX)', content))
        if todos:
            issues.append(f"{todos}x TODO/FIXME")

        if issues:
            warn(f"{rel}: {'; '.join(issues)}")
            deep_fail += 1

    if deep_fail == 0:
        ok("Keine tiefen Probleme gefunden")


def check_system() -> None:
    section("System")
    checks = [
        ("TradingView", "pgrep -f '/opt/TradingView/tradingview'"),
        ("Node MCP Server", "pgrep -f 'node.*server\\.js'"),
        ("LinkedIn MCP", "pgrep -f 'linkedin-scraper-mcp'"),
        ("Gateway", "systemctl --user is-active hermes-gateway.service"),
    ]
    for name, cmd in checks:
        rc, out, _ = sh(cmd, timeout=5)
        if rc == 0:
            ok(f"{name}: läuft")
        else:
            warn(f"{name}: läuft nicht")

    rc, _, _ = sh("curl -sf http://localhost:9222/json/version >/dev/null 2>&1", timeout=3)
    if rc == 0:
        ok("CDP Port 9222: erreichbar")
    else:
        warn("CDP Port 9222: nicht erreichbar")


def watch_mode() -> None:
    section("Watch Mode")
    patterns = ["*.sh", "*.py", "*.js", "*.mjs", "*.json", "*.yaml", "*.yml", "*.md"]
    all_files = []
    for p in patterns:
        all_files.extend(find_files([p]))
    file_map = {str(f): f.stat().st_mtime for f in all_files}
    print(f"  Überwache {len(file_map)} Dateien in {len(SCAN_DIRS)} Verzeichnissen")
    print(f"  Drücke Ctrl+C zum Beenden\n")

    try:
        while True:
            changed = []
            for path_str, old_mtime in list(file_map.items()):
                p = Path(path_str)
                if not p.exists():
                    changed.append((path_str, "GELÖSCHT"))
                    continue
                new_mtime = p.stat().st_mtime
                if new_mtime != old_mtime:
                    changed.append((path_str, "GEÄNDERT"))
                    file_map[path_str] = new_mtime
            for path_str, action in changed:
                ts = datetime.now().strftime("%H:%M:%S")
                print(f"\n  [{ts}] {action}: {Path(path_str).name}")
                f = Path(path_str)
                if f.suffix == '.py':
                    rc, _, err = sh(f"python3 -m py_compile {shq(f)}", timeout=10)
                    if rc == 0:
                        print("    ✅ Syntax OK")
                    else:
                        el = err.rsplit('\n', 1)[-1].strip()[:100]
                        print(f"    ❌ {el}")
                elif f.suffix == '.sh':
                    rc, _, err = sh(f"bash -n {shq(f)}", timeout=10)
                    if rc == 0:
                        print("    ✅ Syntax OK")
                    else:
                        el = err.split('\n')[0].strip()[:100]
                        print(f"    ❌ {el}")
                elif f.suffix in ('.js', '.mjs'):
                    rc, _, err = sh(f"node --check {shq(f)}", timeout=10)
                    if rc == 0:
                        print("    ✅ Syntax OK")
                    else:
                        el = err.rsplit('\n', 1)[-1].strip()[:100]
                        print(f"    ❌ {el}")
                elif f.suffix == '.json':
                    try:
                        import json
                        json.loads(f.read_text())
                        print(f"    ✅ Valid JSON")
                    except Exception as e:
                        print(f"    ❌ {str(e)[:100]}")
            time.sleep(3)
    except KeyboardInterrupt:
        print("\n  Watch Mode beendet")


def ci_mode() -> None:
    import multi_rep_set.utils as u
    u.USE_COLOR = False
    start = time.time()
    run_all(fix=False)
    duration = time.time() - start
    result = {
        "files": TOTAL_FILES,
        "passed": PASS,
        "failed": FAIL,
        "warnings": WARN,
        "duration_seconds": round(duration, 1),
    }
    print(json.dumps(result))
    sys.exit(FAIL)


def run_all(fix: bool = False) -> list[Path]:
    import json
    bash_files = find_files(["*.sh"])
    py_files = find_files(["*.py"])
    js_files = find_files(["*.js", "*.mjs"])
    json_files = find_files(["*.json"])
    yaml_files = find_files(["*.yaml", "*.yml"])
    md_files = find_files(["*.md"])
    all_files = bash_files + py_files + js_files + json_files + yaml_files + md_files

    check_bash(bash_files)
    if bash_files:
        check_bash_shellcheck(bash_files)
    check_python(py_files)
    if py_files:
        check_python_ruff(py_files, fix=fix)
    check_javascript(js_files)
    check_json(json_files)
    check_yaml(yaml_files)
    check_markdown(md_files)

    return all_files


def main() -> None:
    import multi_rep_set.utils as u
    parser = argparse.ArgumentParser(description="MULTI REP SET — Multi-Language Code Checker")
    parser.add_argument("--fix", action="store_true", help="Auto-Fix-Modus")
    parser.add_argument("--watch", action="store_true", help="Live-Überwachung")
    parser.add_argument("--ci", action="store_true", help="CI-Modus (JSON-Output)")
    parser.add_argument("--deep", action="store_true", help="Tiefenanalyse")
    parser.add_argument("--no-color", action="store_true", help="Keine Farben")
    parser.add_argument("dirs", nargs="*", help="Zu prüfende Verzeichnisse")
    args = parser.parse_args()

    if args.no_color or args.ci:
        u.USE_COLOR = False

    config = load_config()
    init_dirs(config)

    if args.ci:
        ci_mode()
        return

    if args.watch:
        watch_mode()
        return

    c = C if u.USE_COLOR else E
    print(f"\n{c['b']}{'='*55}{c['n']}")
    print(f"  {c['b']}MULTI REP SET v1.0{c['n']}")
    print(f"{c['b']}{'='*55}{c['n']}")

    if args.dirs:
        u.SCAN_DIRS = [Path(d).expanduser() for d in args.dirs]

    if args.fix:
        print("  🔧 Fix-Modus aktiviert\n")

    start = time.time()
    all_files = run_all(fix=args.fix)

    if args.deep:
        check_deep(all_files)

    if not args.ci:
        check_system()

    duration = time.time() - start
    print(f"\n{c['b']}{'='*55}{c['n']}")
    print(f"  Dateien geprüft: {TOTAL_FILES} in {duration:.1f}s")
    if PASS > 0:
        print(f"  {c['g']}OK  {PASS}{c['n']}")
    if FAIL > 0:
        print(f"  {c['r']}FAIL {FAIL}{c['n']}")
    if WARN > 0:
        print(f"  {c['y']}WARN {WARN}{c['n']}")
    if SKIP > 0:
        print(f"  SKIP {SKIP}")
    status = "ALLES OK" if FAIL == 0 else f"{FAIL} FEHLER"
    color = c['g'] if FAIL == 0 else c['r']
    print(f"\n  {color}FAZIT: {status}{c['n']}")
    print(f"{c['b']}{'='*55}{c['n']}\n")

    sys.exit(0 if FAIL == 0 else min(FAIL, 255))


if __name__ == "__main__":
    main()
