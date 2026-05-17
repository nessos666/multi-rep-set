# MULTI REP SET — Multi-Language Code Checker

> **Prüft Bash, Python, JavaScript, JSON, YAML, Markdown + System-Prozesse.**  
> Kein Codex, keine API, keine Token-Kosten. Läuft lokal in Sekunden.

```bash
check                    # Alles prüfen
check --fix              # Prüfen + automatisch fixen  
check --watch            # Live-Überwachung
check --ci               # CI-Modus (JSON-Output)
check --deep             # Tiefenanalyse
```

## Features

| Sprache | Prüfung | Tool |
|---------|---------|------|
| Bash | Syntax + Shellcheck | `bash -n`, `shellcheck` |
| Python | Syntax + Lint | `py_compile`, `ruff` |
| JavaScript | Syntax | `node --check` |
| JSON | Validierung | `json.loads()` |
| YAML | Validierung | `yaml.safe_load()` |
| Markdown | Broken Links | Regex |
| System | Prozesse, CDP, Gateway | `pgrep`, `curl`, `systemctl` |

- **0 Dependencies** — nur Python stdlib (ruff optional)
- **0 Token-Kosten** — kein API-Call
- **~250 Dateien in 15s** — auch auf großen Projekten
- **Farbe + Klartext** — lesbare Ausgabe

## Installation

```bash
git clone https://github.com/nessos666/multi-rep-set.git
cd multi-rep-set
ln -sf $(pwd)/src/multi_rep_set.py ~/bin/check
check
```

Oder direkt:

```bash
pip install .
multi-rep-set
```

## Konfiguration

Lege `~/.multi-rep-set.yaml` an, um zu steuern welche Ordner geprüft werden:

```yaml
scan_dirs:
  - ~/HAUPTLAGER/27_TV_Watch_Agent
  - ~/HAUPTLAGER/24_Strategie_Builder
  - ~/linkedin-mcp-server
  - ~/hermes-test
max_per_type: 50
ignore_patterns:
  - node_modules
  - .git
  - __pycache__
```

## --fix Modus

```bash
check --fix
```

1. Prüft alle Dateien
2. Fixt automatisch was geht (ruff --fix, shellcheck-Empfehlungen)
3. Listet was nicht automatisch fixbar ist
4. Zeigt: "12 von 15 Fehlern automatisch gefixt"

## --watch Modus

```bash
check --watch
```

Überwacht alle Dateien in `scan_dirs`. Bei Änderung: nur die geänderte Datei prüfen.  
Nutzt `inotify` (Linux) mit Fallback auf Polling (5s).  
`Ctrl+C` zum Beenden.

## --ci Modus

Für GitHub Actions, GitLab CI, Pre-Commit-Hooks:

```bash
check --ci
```

- Exit-Code = Anzahl Fehler (0 = alles OK)
- JSON-Output: `{"files":258,"passed":293,"failed":1,"warnings":54,"duration_seconds":14.2}`
- Keine Farbe, keine ANSI-Codes
- Bricht nach 30s ab (Timeout)

## --deep Modus

Tiefere Analyse:

- Leere `except: pass` Blöcke
- `while True:` ohne `break`
- Hardcodierte Pfade die nicht existieren
- `print()` statt logging
- TODO/FIXME/XXX Kommentare

## Lizenz

MIT — machen damit was du willst.

---

# MULTI REP SET — Multi-Language Code Checker

> Checks Bash, Python, JavaScript, JSON, YAML, Markdown + System processes.  
> No Codex, no API, no token costs. Runs locally in seconds.

[Same content in English — see above for full README]
