# 004 Fixes

## Goal

Remove real IPs from tracked files. Report gitleaks findings.

## Context

The README contained example IPs (192.168.1.100, 192.168.1.55) in code examples and expected output. No bugs were noted from baseline tests (Phase 4 skipped for this hardware project).

## Scope

- Replace real IPs with `192.168.x.x` in README.md
- Run gitleaks and report findings

## Out of scope

- History rewriting for gitleaks findings (none found)

## Acceptance criteria

- No real IPs or domains in tracked files
- gitleaks reports no leaks

## Test plan

- Grep for real IP patterns across tracked files

## Notes

- gitleaks: 8 commits scanned, no leaks found
- `.env` is properly gitignored and was never committed to history
- `config.py` is auto-generated and gitignored
