# 003 Standards and CI

## Goal

Add CI validation and clean up .gitignore.

## Context

MicroPython ESP32 project with bash shell scripts. No standard Python linting (MicroPython is not compatible with standard linters). Shell scripts can be validated with ShellCheck.

## Scope

- Add `.github/workflows/ci.yml` that runs ShellCheck on bash scripts
- Clean up `.gitignore` (remove boilerplate for languages not used)
- Add `secrets/` to `.gitignore`

## Out of scope

- Python linting (MicroPython imports like `machine` and `umqtt` are not available on standard Python)
- Unit tests (hardware-dependent code)

## Acceptance criteria

- CI workflow runs ShellCheck on push/PR to main and dev
- `.gitignore` is trimmed to relevant patterns

## Test plan

- CI YAML is valid
- ShellCheck passes on all .sh files

## Notes

- ShellCheck is pre-installed on GitHub Actions ubuntu-latest runners
