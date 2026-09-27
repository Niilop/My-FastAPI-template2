#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

# Isolate each invocation, even in a directory where the application is already running.
project="template-smoke-$(date +%s)-$$"
compose=(docker compose --env-file /dev/null --file compose.smoke.yaml --project-name "$project")
artifacts=frontend/test-results/smoke
mkdir -p "$artifacts"

cleanup() {
    result=$?
    trap - EXIT INT TERM
    "${compose[@]}" logs --no-color > "$artifacts/compose.log" 2>&1 || true
    if ! "${compose[@]}" down --volumes --remove-orphans; then
        echo "Could not clean up smoke project $project." >&2
        if [ "$result" -eq 0 ]; then result=1; fi
    fi
    exit "$result"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

"${compose[@]}" build
"${compose[@]}" up --detach --wait --wait-timeout 120 database backend frontend
"${compose[@]}" run --rm --no-deps --user "$(id -u):$(id -g)" smoke
