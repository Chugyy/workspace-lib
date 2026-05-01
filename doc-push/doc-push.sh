#!/bin/bash
# doc-push : git add + doc-sync agent + git commit + git push
#
# Usage: doc-push "commit message"
#
# 1. Fait git diff pour identifier les fichiers modifies
# 2. Determine si les changements impactent la documentation
# 3. Si oui : invoque l'agent doc-sync pour mettre a jour les docs
# 4. git add + git commit + git push (code + docs)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
AGENT_INVOKE_VENV="$WORKSPACE_ROOT/lib/agent-invoke/.venv/bin"

# Patterns de fichiers qui impactent la documentation
DOC_PATTERNS=(
    "app/database/migrations/"
    "app/database/crud/"
    "app/core/jobs/"
    "app/core/services/"
    "app/core/utils/"
    "app/api/routes/"
    "app/api/models/"
    "src/components/"
    "src/app/"
)

# --- Args ---
COMMIT_MSG="${1:-}"
if [ -z "$COMMIT_MSG" ]; then
    echo "Usage: doc-push \"commit message\""
    exit 1
fi

# --- Git diff ---
echo "[doc-push] Checking git diff..."
CHANGED_FILES=$(git diff --name-only HEAD 2>/dev/null || git diff --name-only --cached 2>/dev/null || echo "")

if [ -z "$CHANGED_FILES" ]; then
    # Check untracked files too
    CHANGED_FILES=$(git status --porcelain | awk '{print $2}')
fi

if [ -z "$CHANGED_FILES" ]; then
    echo "[doc-push] No changes detected."
    exit 0
fi

echo "[doc-push] Changed files:"
echo "$CHANGED_FILES" | sed 's/^/  /'

# --- Check if doc-sync needed ---
NEEDS_SYNC=false
for pattern in "${DOC_PATTERNS[@]}"; do
    if echo "$CHANGED_FILES" | grep -q "$pattern"; then
        NEEDS_SYNC=true
        break
    fi
done

if [ "$NEEDS_SYNC" = true ]; then
    echo "[doc-push] Documentation-impacting changes detected. Running doc-sync agent..."

    DIFF_CONTENT=$(git diff HEAD 2>/dev/null || git diff --cached 2>/dev/null || echo "no diff available")

    PROMPT="Voici le git diff des fichiers modifies. Mets a jour la documentation correspondante.

Fichiers modifies:
$CHANGED_FILES

Diff:
$DIFF_CONTENT"

    # Invoke doc-sync agent
    if [ -f "$AGENT_INVOKE_VENV/agent-invoke" ]; then
        "$AGENT_INVOKE_VENV/agent-invoke" ask doc-sync "$PROMPT" --model haiku --timeout 120
        echo "[doc-push] Doc-sync complete."
    else
        echo "[doc-push] WARNING: agent-invoke not found at $AGENT_INVOKE_VENV. Skipping doc-sync."
    fi
else
    echo "[doc-push] No documentation-impacting changes. Skipping doc-sync."
fi

# --- Git add + commit + push ---
echo "[doc-push] Staging all changes..."
git add -A
echo "[doc-push] Committing: $COMMIT_MSG"
git commit -m "$COMMIT_MSG"
echo "[doc-push] Pushing..."
git push
echo "[doc-push] Done."
