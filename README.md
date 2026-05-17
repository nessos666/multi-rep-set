<p align="center">
  <h1 align="center">MULTI REP SET</h1>
  <p align="center">
    <strong>Multi-language code checker — lint Bash, Python, JavaScript, JSON, YAML, Markdown + system processes.</strong>
  </p>
  <p align="center">
    <em>Zero dependencies. Zero API costs. Runs locally in seconds.</em>
  </p>
  <p align="center">
    <a href="#features">Features</a> · <a href="#installation">Installation</a> · <a href="#usage">Usage</a> · <a href="#configuration">Configuration</a> · <a href="#modes">Modes</a>
  </p>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11+-blue?logo=python&logoColor=white" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="MIT License">
  <img src="https://img.shields.io/badge/dependencies-0-success" alt="Zero deps">
  <img src="https://img.shields.io/badge/token_cost-0-brightgreen" alt="Zero token cost">
  <img src="https://img.shields.io/badge/checks-6_languages-orange" alt="6 languages">
  <img src="https://img.shields.io/github/stars/nessos666/multi-rep-set?style=social" alt="Stars">
</p>

---

## Why?

AI code assistants like Claude Code or Codex are great, but they have a problem: **every syntax check costs tokens** — and when they timeout (45s), you get nothing.

**MULTI REP SET solves this.** It checks your code using local tools only:

- **Bash** → `bash -n` + `shellcheck`
- **Python** → `py_compile` + `ruff`
- **JavaScript** → `node --check`
- **JSON** → `json.loads()`
- **YAML** → `yaml.safe_load()`
- **Markdown** → Regex link validation
- **System** → process health, CDP connection, gateway status

All without a single API call. ~250 files in 7 seconds. Zero token cost.

---

## Features

| Feature | Detail |
|---------|--------|
| **Languages** | Bash, Python, JavaScript, JSON, YAML, Markdown |
| **System checks** | Process health (`pgrep`), CDP connection (`curl :9222`), gateway status (`systemctl`) |
| **Speed** | ~258 files in 7 seconds |
| **Dependencies** | Zero (stdlib only — `ruff` and `shellcheck` optional) |
| **Token cost** | $0 — no API calls |
| **Exit code** | 0 = all passed, N = number of failures (CI-friendly) |

---

## Quick Start

```bash
git clone https://github.com/nessos666/multi-rep-set.git
cd multi-rep-set
ln -sf $(pwd)/src/multi_rep_set.py ~/bin/check

# Run
check
```

Or via pip:

```bash
pip install .
multi-rep-set
```

---

## Usage

```bash
check                         # Scan all configured directories
check /path/to/project        # Scan a specific directory
check --fix                   # Auto-fix what's fixable (ruff, shellcheck)
check --watch                 # Watch mode — re-check on file changes
check --ci                    # CI mode — JSON output, exit code = failures
check --deep                  # Deep analysis — unused vars, empty except, hardcoded paths
check --no-color              # Plain text output (for logs)
```

---

## Modes

### Default mode

Scans all configured directories and reports:

```
── Bash (.sh) ──
  OK script.sh
  WARN kein set -e: deploy.sh

── Python (.py) ──
  OK module.py
  FAIL broken.py
     SyntaxError: invalid syntax at line 42

── JSON (.json) ──
  OK config.json
  FAIL data.json
     Expecting ',' delimiter at line 12

── Markdown (.md) ──
  OK README.md
  WARN Broken link: https://example.com/broken

── System ──
  OK Chrome CDP (port 9222)
  OK Gateway (hermes-gateway.service)
  WARN Service 'nq-scanner' not running

Results: 258 files, 278 passed, 1 failed, 53 warnings (6.7s)
```

### --fix mode

1. Checks all files
2. Auto-fixes what's fixable (`ruff --fix`, shellcheck recommendations)
3. Lists what couldn't be auto-fixed
4. Shows summary: "12 of 15 errors auto-fixed"

### --watch mode

Watches all files in `scan_dirs` using `inotify` (Linux) with polling fallback (5s). On change: re-checks only the changed file. `Ctrl+C` to stop.

### --ci mode

For CI/CD pipelines (GitHub Actions, GitLab CI, pre-commit hooks):

- Exit code = number of failures (0 = all good)
- JSON output: `{"files":258,"passed":278,"failed":1,"warnings":53,"duration_seconds":6.7}`
- No color codes, no ANSI
- 30s timeout

### --deep mode

Additional analysis beyond syntax:

- Empty `except: pass` blocks
- `while True:` without `break`
- Hardcoded paths that don't exist
- `print()` instead of proper logging
- TODO / FIXME / XXX comments

---

## Configuration

Create `~/.multi-rep-set.yaml` to control which directories are scanned:

```yaml
scan_dirs:
  - ~/projects/my-project
  - ~/projects/another-project
max_per_type: 50
ignore_patterns:
  - node_modules
  - .git
  - __pycache__
  - .venv
  - dist
  - build
```

Without config, the tool scans from the current directory.

---

## Project Structure

```
multi-rep-set/
├── src/
│   └── multi_rep_set.py     # Single-file checker (470 lines)
├── tests/                    # Test suite
├── examples/                 # Example configs
├── pyproject.toml            # Package metadata + CLI entrypoint
├── LICENSE                   # MIT
└── README.md
```

---

## Dependencies

| Tool | Required? | Used for |
|------|-----------|----------|
| Python 3.11+ | ✅ Required | Core checker |
| `ruff` | ❌ Optional | Python linting (auto-detected) |
| `shellcheck` | ❌ Optional | Advanced Bash linting (auto-detected) |
| `node` | ❌ Optional | JavaScript syntax check (auto-detected) |

Without optional tools, the checker still works — it just skips the deeper checks.

---

## Related

Part of the development tooling ecosystem:

- [nq-strategy-builder](https://github.com/nessos666/nq-strategy-builder) — Uses this checker for CI validation

---

## License

MIT — do whatever you want with it.

<p align="center">
  <small>Zero dependencies. Zero token costs. Runs locally in seconds.<br>
  <strong>github.com/nessos666</strong></small>
</p>
