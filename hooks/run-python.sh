#!/usr/bin/env bash
# run-python.sh — Cross-platform Python launcher for Claude Dashboard hooks.
#
# On Windows + Git Bash, `python3` typically resolves to the Microsoft Store
# stub which exits with code 49 silently in non-TTY subprocess context.
# This shim probes each candidate and skips any that fails.
#
# Order: python3.11 → python3 → python → py -3
set -e

# Force UTF-8 for all Python IO operations (critical on Windows).
export PYTHONUTF8=1

# On Windows (Git Bash/MSYS), convert POSIX paths to Windows native paths.
# Without this, python.exe misinterprets /c/Users/... paths.
if command -v cygpath >/dev/null 2>&1; then
    converted=()
    for a in "$@"; do
        case "$a" in
            /*) converted+=("$(cygpath -w "$a")") ;;
            *)  converted+=("$a") ;;
        esac
    done
    set -- "${converted[@]}"
fi

# Find a working Python 3.11+ interpreter (preferred)
# Then fall back to Python 3+
for cmd in "python3.11" "python3" "python" "py -3"; do
    # Check if command exists
    if ! command -v "$cmd" >/dev/null 2>&1; then
        continue
    fi

    # Check Python version (need 3.11+ for backend, 3.7+ for hooks)
    version=$($cmd -c "import sys; print(sys.version_info.major, sys.version_info.minor)" 2>/dev/null || echo "0 0")
    major=$(echo $version | cut -d' ' -f1)
    minor=$(echo $version | cut -d' ' -f2)

    if [ "$major" -ge 3 ] && [ "$minor" -ge 7 ]; then
        # shellcheck disable=SC2086
        exec $cmd "$@"
    fi
done

echo "claude-dashboard: no working Python 3.7+ interpreter found." >&2
echo "  tried: python3.11, python3, python, py -3" >&2
echo "  on Windows, install Python from https://python.org (NOT the Microsoft Store)" >&2
exit 1
