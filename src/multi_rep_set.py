#!/usr/bin/env python3
"""MULTI REP SET — Multi-Language Code Checker
Prüft Bash, Python, JavaScript, JSON, YAML, Markdown auf Syntax + Stil.
Kein Codex, keine API, keine Token. Lokal in Sekunden."""

import os, sys, subprocess, json, re, time, argparse
from pathlib import Path

BASE = Path.home()
CHECKED = set()
PASS = 0; FAIL = 0; WARN = 0; SKIP = 0
TOTAL_FILES = 0; FIXED_COUNT = 0

USE_COLOR = True

C = {"g": "\033[92m", "r": "\033[91m", "y": "\033[93m", "b": "\033[94m", "n": "\033[0m"}
E = {"g": "", "r": "", "y": "", "b": "", "n": ""}

def section(title):
    c = C if USE_COLOR else E
    print(f"\n{c['b']}── {title} ──{c['n']}")

def ok(msg):
    global PASS; PASS += 1
    c = C if USE_COLOR else E
    print(f"  {c['g']}OK{c['n']} {msg}")

def fail(msg, details=""):
    global FAIL; FAIL += 1
    c = C if USE_COLOR else E
    print(f"  {c['r']}FAIL{c['n']} {msg}")
    if details: print(f"     {details[:200]}")

def warn(msg):
    global WARN; WARN += 1
    c = C if USE_COLOR else E
    print(f"  {c['y']}WARN{c['n']} {msg}")

def skip(msg):
    global SKIP; SKIP += 1
    print(f"  SKIP {msg}")

def sh(cmd, timeout=30):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except subprocess.TimeoutExpired: return -1, "", "TIMEOUT"
    except FileNotFoundError: return -2, "", "NOT FOUND"

def load_config():
    """Lade ~/.multi-rep-set.yaml falls vorhanden."""
    config_path = Path.home() / ".multi-rep-set.yaml"
    if not config_path.exists():
        return {}
    try:
        import yaml
        with open(config_path) as f:
            return yaml.safe_load(f) or {}
    except ImportError:
        # ohne PyYAML: einfaches Key: Value parsen
        cfg = {}
        with open(config_path) as f:
            for line in f:
                if ':' in line and not line.strip().startswith('#'):
                    k, v = line.split(':', 1)
                    cfg[k.strip()] = v.strip().strip('"').strip("'")
        return cfg

SCAN_DIRS = []
MAX_PER_TYPE = 50
IGNORE_PATTERNS = ["node_modules", ".git", ".cache", "__pycache__", ".venv", "venv", ".hermes"]

def init_dirs(config=None):
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
        if mt: MAX_PER_TYPE = int(mt)
        ip = config.get('ignore_patterns') or config.get('IGNORE_PATTERNS')
        if ip: IGNORE_PATTERNS = list(ip) if isinstance(ip, list) else [ip]

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

def find_files(patterns):
    files = []
    for d in SCAN_DIRS:
        if not d.exists(): continue
        for p in patterns:
            for f in sorted(d.rglob(p)):
                if any(x in str(f) for x in IGNORE_PATTERNS): continue
                if str(f) not in CHECKED:
                    files.append(f); CHECKED.add(str(f))
    return files[:MAX_PER_TYPE]

# =====================================================================
# BASH
# =====================================================================
def check_bash(files):
    section("Bash (.sh)")
    for f in files:
        global TOTAL_FILES; TOTAL_FILES += 1
        try:
            content = f.read_text()[:500]
        except: skip(f"{f.name} (kann nicht lesen)"); continue
        if not content.startswith("#!"): skip(f"{f.name} (kein Shebang)"); continue
        rel = f.relative_to(BASE) if BASE in f.parents else f.name

        rc, _, err = sh(f"bash -n {shq(f)}")
        if rc == 0: ok(f"{rel}")
        else:
            e = err.split('\n')[0].strip()[:100] if err else "?"
            fail(f"{rel}", e)

        if "set -e" in content: pass
        else: warn(f"  kein set -e: {f.name}")

def check_bash_shellcheck(files):
    section("Bash shellcheck")
    for f in files[:20]:
        try:
            c = f.read_text()[:100]
            if not c.startswith("#!"): continue
        except: continue
        rel = f.relative_to(BASE) if BASE in f.parents else f.name
        rc, out, _ = sh(f"shellcheck -s bash -f json {shq(f)}")
        if rc == 0: ok(f"{rel}")
        elif rc == -2: skip("shellcheck nicht installiert (sudo apt install shellcheck)"); return
        else:
            try:
                findings = json.loads(out) if out else []
                errs = [x for x in findings if x.get('level') == 'error']
                warns = [x for x in findings if x.get('level') in ('warning','style')]
                if errs: fail(f"{rel} ({len(errs)} errors)", errs[0].get('message','')[:100])
                elif warns: warn(f"{rel} ({len(warns)} warnings)")
            except: warn(f"{rel} (parse error)")

# =====================================================================
# PYTHON
# =====================================================================
def check_python(files):
    section("Python (.py)")
    for f in files:
        global TOTAL_FILES; TOTAL_FILES += 1
        rel = f.relative_to(BASE) if BASE in f.parents else f.name
        if f.name == "__init__.py": ok(f"{rel} (init)"); continue
        rc, _, err = sh(f"python3 -m py_compile {shq(f)}")
        if rc == 0: ok(f"{rel}")
        else:
            e = err.split('\n')[-1].strip()[:120] if err else "?"
            fail(f"{rel}", e)

def check_python_ruff(files, fix=False):
    section("Python ruff")
    rc, _, _ = sh("which ruff")
    if rc != 0: skip("ruff nicht installiert (pip install ruff)"); return
    for f in files[:20]:
        if f.name == "__init__.py": continue
        rel = f.relative_to(BASE) if BASE in f.parents else f.name
        cmd = f"ruff check --quiet {shq(f)}"
        if fix: cmd = f"ruff check --fix --unsafe-fixes --quiet {shq(f)}"
        rc, out, _ = sh(cmd)
        if rc == 0: ok(f"{rel}")
        else:
            lines = [l for l in out.split('\n') if l.strip()][:3]
            fail(f"{rel}", "; ".join(lines[:3])[:150])

# =====================================================================
# JAVASCRIPT
# =====================================================================
def check_javascript(files):
    section("JavaScript/Node (.js .mjs)")
    for f in files:
        global TOTAL_FILES; TOTAL_FILES += 1
        rel = f.relative_to(BASE) if BASE in f.parents else f.name
        rc, _, err = sh(f"node --check {shq(f)}")
        if rc == 0: ok(f"{rel}")
        else:
            e = err.split('\n')[-1].strip()[:120] if err else "?"
            if "Warning: To load an ES module" in err:
                ok(f"{rel} (ESM)")
            else:
                fail(f"{rel}", e)

# =====================================================================
# JSON
# =====================================================================
def check_json(files):
    section("JSON (.json)")
    for f in files:
        global TOTAL_FILES; TOTAL_FILES += 1
        rel = f.relative_to(BASE) if BASE in f.parents else f.name
        if f.stat().st_size > 500000: skip(f"{rel} (zu gross)"); continue
        try:
            json.loads(f.read_text())
            ok(f"{rel}")
        except json.JSONDecodeError as e:
            fail(f"{rel}", str(e)[:100])

# =====================================================================
# YAML
# =====================================================================
def check_yaml(files):
    section("YAML (.yaml .yml)")
    for f in files:
        global TOTAL_FILES; TOTAL_FILES += 1
        rel = f.relative_to(BASE) if BASE in f.parents else f.name
        try:
            import yaml as _y
            _y.safe_load(f.read_text())
            ok(f"{rel}")
        except ImportError:
            content = f.read_text()
            if '{' in content or '}' in content:
                try: json.loads(content); ok(f"{rel}")
                except: warn(f"{rel} (kein YAML-Parser)")
            else: ok(f"{rel} (basic)")
        except Exception as e:
            fail(f"{rel}", str(e)[:100])

# =====================================================================
# MARKDOWN
# =====================================================================
def check_markdown(files):
    section("Markdown (.md)")
    for f in files:
        global TOTAL_FILES; TOTAL_FILES += 1
        rel = f.relative_to(BASE) if BASE in f.parents else f.name
        try:
            content = f.read_text()
            broken = re.findall(r'\[([^\]]+)\]\(\)', content)
            if broken: warn(f"{rel} (leere Links: {len(broken)})")
            else: ok(f"{rel}")
        except: skip(f"{rel} (kann nicht lesen)")

# =====================================================================
# DEEP CHECK
# =====================================================================
def check_deep(files):
    section("Deep Analysis")
    deep_fail = 0
    for f in files:
        if f.suffix != '.py': continue
        try:
            content = f.read_text()
        except: continue
        rel = f.relative_to(BASE) if BASE in f.parents else f.name
        issues = []

        # Leere except: pass
        empty_excepts = len(re.findall(r'except\s*:\s*pass', content))
        if empty_excepts:
            issues.append(f"{empty_excepts}x leeres except: pass")

        # while True ohne break
        whiles = content.count('while True:')
        breaks = content.count('break')
        if whiles > breaks:
            issues.append(f"{whiles- breaks}x while True ohne break")

        # TODO/FIXME
        todos = len(re.findall(r'#\s*(TODO|FIXME|XXX)', content))
        if todos:
            issues.append(f"{todos}x TODO/FIXME")

        if issues:
            warn(f"{rel}: {'; '.join(issues)}")
            deep_fail += 1

    if deep_fail == 0:
        ok("Keine tiefen Probleme gefunden")

# =====================================================================
# SYSTEM
# =====================================================================
def check_system():
    section("System")
    checks = [
        ("TradingView", "pgrep -f '/opt/TradingView/tradingview'"),
        ("Node MCP Server", "pgrep -f 'node.*server\\.js'"),
        ("LinkedIn MCP", "pgrep -f 'linkedin-scraper-mcp'"),
        ("Gateway", "systemctl --user is-active hermes-gateway.service"),
    ]
    for name, cmd in checks:
        rc, out, _ = sh(cmd, timeout=5)
        if rc == 0: ok(f"{name}: läuft")
        else: warn(f"{name}: läuft nicht")

    rc, _, _ = sh("curl -sf http://localhost:9222/json/version >/dev/null 2>&1", timeout=3)
    if rc == 0: ok("CDP Port 9222: erreichbar")
    else: warn("CDP Port 9222: nicht erreichbar")

# =====================================================================
# WATCH
# =====================================================================
def watch_mode():
    section("Watch Mode")
    from datetime import datetime

    # Alle Dateien sammeln
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
                # Nur diese eine Datei schnell prüfen
                f = Path(path_str)
                if f.suffix == '.py':
                    rc, _, err = sh(f"python3 -m py_compile {shq(f)}", timeout=10)
                    if rc == 0: print("    ✅ Syntax OK")
                    else:
                        el = err.rsplit('\n', 1)[-1].strip()[:100]
                        print(f"    ❌ {el}")
                elif f.suffix == '.sh':
                    rc, _, err = sh(f"bash -n {shq(f)}", timeout=10)
                    if rc == 0: print("    ✅ Syntax OK")
                    else:
                        el = err.split('\n')[0].strip()[:100]
                        print(f"    ❌ {el}")
                elif f.suffix in ('.js', '.mjs'):
                    rc, _, err = sh(f"node --check {shq(f)}", timeout=10)
                    if rc == 0: print("    ✅ Syntax OK")
                    else:
                        el = err.rsplit('\n', 1)[-1].strip()[:100]
                        print(f"    ❌ {el}")
                elif f.suffix == '.json':
                    try: json.loads(f.read_text()); print(f"    ✅ Valid JSON")
                    except Exception as e: print(f"    ❌ {str(e)[:100]}")
            time.sleep(3)
    except KeyboardInterrupt:
        print("\n  Watch Mode beendet")

# =====================================================================
# CI MODE
# =====================================================================
def ci_mode():
    global USE_COLOR
    USE_COLOR = False
    start = time.time()
    run_all(fix=False)
    duration = time.time() - start
    result = {"files": TOTAL_FILES, "passed": PASS, "failed": FAIL, "warnings": WARN, "duration_seconds": round(duration, 1)}
    print(json.dumps(result))
    sys.exit(FAIL)

# =====================================================================
# RUN ALL
# =====================================================================
def run_all(fix=False):
    bash_files = find_files(["*.sh"])
    py_files = find_files(["*.py"])
    js_files = find_files(["*.js", "*.mjs"])
    json_files = find_files(["*.json"])
    yaml_files = find_files(["*.yaml", "*.yml"])
    md_files = find_files(["*.md"])
    all_files = bash_files + py_files + js_files + json_files + yaml_files + md_files

    check_bash(bash_files)
    if bash_files: check_bash_shellcheck(bash_files)
    check_python(py_files)
    if py_files: check_python_ruff(py_files, fix=fix)
    check_javascript(js_files)
    check_json(json_files)
    check_yaml(yaml_files)
    check_markdown(md_files)

    return all_files

# =====================================================================
# MAIN
# =====================================================================
def main():
    global USE_COLOR
    parser = argparse.ArgumentParser(description="MULTI REP SET — Multi-Language Code Checker")
    parser.add_argument("--fix", action="store_true", help="Auto-Fix-Modus")
    parser.add_argument("--watch", action="store_true", help="Live-Überwachung")
    parser.add_argument("--ci", action="store_true", help="CI-Modus (JSON-Output)")
    parser.add_argument("--deep", action="store_true", help="Tiefenanalyse")
    parser.add_argument("--no-color", action="store_true", help="Keine Farben")
    parser.add_argument("dirs", nargs="*", help="Zu prüfende Verzeichnisse")
    args = parser.parse_args()

    if args.no_color or args.ci:
        USE_COLOR = False

    # Config laden + Dirs initialisieren
    config = load_config()
    init_dirs(config)

    if args.ci:
        ci_mode()
        return

    if args.watch:
        watch_mode()
        return

    # Normale Prüfung
    c = C if USE_COLOR else E
    print(f"\n{c['b']}{'='*55}{c['n']}")
    print(f"  {c['b']}MULTI REP SET v1.0{c['n']}")
    print(f"{c['b']}{'='*55}{c['n']}")

    if args.dirs:
        global SCAN_DIRS
        SCAN_DIRS = [Path(d).expanduser() for d in args.dirs]

    if args.fix:
        print("  🔧 Fix-Modus aktiviert\n")

    start = time.time()
    all_files = run_all(fix=args.fix)

    # Deep Check
    if args.deep:
        check_deep(all_files)

    # System-Check (nur ohne --ci, da oft nicht verfügbar)
    if not args.ci:
        check_system()

    duration = time.time() - start
    print(f"\n{c['b']}{'='*55}{c['n']}")
    print(f"  Dateien geprüft: {TOTAL_FILES} in {duration:.1f}s")
    if PASS > 0: print(f"  {c['g']}OK  {PASS}{c['n']}")
    if FAIL > 0: print(f"  {c['r']}FAIL {FAIL}{c['n']}")
    if WARN > 0: print(f"  {c['y']}WARN {WARN}{c['n']}")
    if SKIP > 0: print(f"  SKIP {SKIP}")
    status = "ALLES OK" if FAIL == 0 else f"{FAIL} FEHLER"
    color = c['g'] if FAIL == 0 else c['r']
    print(f"\n  {color}FAZIT: {status}{c['n']}")
    print(f"{c['b']}{'='*55}{c['n']}\n")

    sys.exit(0 if FAIL == 0 else min(FAIL, 255))

# =====================================================================
# HELPERS
# =====================================================================
def shq(s):
    s_str = str(s)
    q = chr(39)
    return q + s_str.replace(q, q + "\\" + q) + q

if __name__ == "__main__":
    main()
