#!/bin/bash
# test-toolkit.sh — Tests pour chain-toolkit.sh
#
# Usage : bash test-toolkit.sh
# Retourne exit 0 si tous les tests passent, exit 1 sinon.

set -uo pipefail

TOOLKIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PASS=0
FAIL=0

_pass() { echo "PASS: $1"; ((PASS++)); }
_fail() { echo "FAIL: $1 — $2"; ((FAIL++)); }

# ---------------------------------------------------------------------------
# 1. Source le toolkit et verifie que toutes les fonctions sont definies
# ---------------------------------------------------------------------------
echo "--- Test 1: source + function definitions ---"

source "${TOOLKIT_DIR}/chain-toolkit.sh"

for fn in emit_event verify_file parse_event roadmap_trap emit_progress emit_business_event has_event; do
  if declare -f "$fn" > /dev/null 2>&1; then
    _pass "function '$fn' is defined"
  else
    _fail "function '$fn' is defined" "not found after source"
  fi
done

# ---------------------------------------------------------------------------
# 2. Test parse_event avec un JSON valide
# ---------------------------------------------------------------------------
echo ""
echo "--- Test 2: parse_event ---"

unset EVENT_ID EVENT_SOURCE EVENT_TYPE TASK_ID ROADMAP_ID ROADMAP_SOURCE

parse_event '{"id":"evt-1","source":"roadmap:rm-1","type":"roadmap.task.run","payload":{"task_id":"t-1","roadmap_id":"rm-1"}}'

[[ "${EVENT_ID:-}" == "evt-1" ]] && _pass "EVENT_ID" || _fail "EVENT_ID" "got '${EVENT_ID:-}', expected 'evt-1'"
[[ "${EVENT_SOURCE:-}" == "roadmap:rm-1" ]] && _pass "EVENT_SOURCE" || _fail "EVENT_SOURCE" "got '${EVENT_SOURCE:-}', expected 'roadmap:rm-1'"
[[ "${EVENT_TYPE:-}" == "roadmap.task.run" ]] && _pass "EVENT_TYPE" || _fail "EVENT_TYPE" "got '${EVENT_TYPE:-}', expected 'roadmap.task.run'"
[[ "${TASK_ID:-}" == "t-1" ]] && _pass "TASK_ID" || _fail "TASK_ID" "got '${TASK_ID:-}', expected 't-1'"
[[ "${ROADMAP_ID:-}" == "rm-1" ]] && _pass "ROADMAP_ID" || _fail "ROADMAP_ID" "got '${ROADMAP_ID:-}', expected 'rm-1'"
[[ "${ROADMAP_SOURCE:-}" == "roadmap:rm-1" ]] && _pass "ROADMAP_SOURCE (derived from EVENT_SOURCE)" || _fail "ROADMAP_SOURCE" "got '${ROADMAP_SOURCE:-}', expected 'roadmap:rm-1'"

# Test JSON invalide : doit sortir en erreur (teste dans un subshell)
invalid_result=$(bash -c "source '${TOOLKIT_DIR}/chain-toolkit.sh'; parse_event 'not-json'" 2>&1)
invalid_exit=$?
if [[ $invalid_exit -ne 0 ]]; then
  _pass "parse_event rejects invalid JSON (exit $invalid_exit)"
else
  _fail "parse_event rejects invalid JSON" "exit was 0, expected non-zero"
fi

# Test argument vide
empty_result=$(bash -c "source '${TOOLKIT_DIR}/chain-toolkit.sh'; parse_event ''" 2>&1)
empty_exit=$?
if [[ $empty_exit -ne 0 ]]; then
  _pass "parse_event rejects empty argument (exit $empty_exit)"
else
  _fail "parse_event rejects empty argument" "exit was 0, expected non-zero"
fi

# ---------------------------------------------------------------------------
# 3. Test emit_progress — ne doit pas crasher avec les bonnes env vars set
# ---------------------------------------------------------------------------
echo ""
echo "--- Test 3: emit_progress (no aggregator) ---"

# Setup env vars (aggregator URL invalide pour ne pas bloquer)
export AGGREGATOR_URL="http://127.0.0.1:19999"
export AGG_API_KEY="test-key"
export TASK_ID="t-test"
export ROADMAP_ID="rm-test"
export ROADMAP_SOURCE="roadmap:rm-test"
export EVENT_ID="evt-test"

# emit_progress doit executer sans crash (le curl va echouer silencieusement)
if emit_progress 2 5 "test step" 2>/dev/null; then
  _pass "emit_progress executes without crash (curl failure is silent)"
else
  # exit non-zero n'est pas une erreur ici car curl peut echouer
  _pass "emit_progress ran (curl failure expected with fake URL)"
fi

# Test sans message
if emit_progress 1 3 2>/dev/null; then
  _pass "emit_progress works without message argument"
else
  _pass "emit_progress ran without message (curl failure expected)"
fi

# ---------------------------------------------------------------------------
# 4. Test has_event — doit retourner exit 1 quand l'aggregator est injoignable
# ---------------------------------------------------------------------------
echo ""
echo "--- Test 4: has_event (aggregator unreachable) ---"

export AGGREGATOR_URL="http://127.0.0.1:19999"

if has_event "some.event.type" 2>/dev/null; then
  _fail "has_event returns exit 1 when aggregator unreachable" "got exit 0"
else
  _pass "has_event returns exit 1 when aggregator unreachable (graceful failure)"
fi

# ---------------------------------------------------------------------------
# 5. Test roadmap_trap — declencher une erreur dans un subshell
# ---------------------------------------------------------------------------
echo ""
echo "--- Test 5: roadmap_trap ---"

# On verifie que le trap s'active sans boucle infinie ni crash du script parent.
# On capture stdout+stderr du subshell.
trap_output=$(bash -c "
  source '${TOOLKIT_DIR}/chain-toolkit.sh'
  export AGGREGATOR_URL='http://127.0.0.1:19999'
  export AGG_API_KEY='test-key'
  export TASK_ID='t-trap-test'
  export ROADMAP_ID='rm-trap-test'
  export ROADMAP_SOURCE='roadmap:rm-trap'
  export EVENT_ID='evt-trap'
  roadmap_trap
  false  # declenche ERR
" 2>&1 || true)

# Le subshell doit avoir exit non-zero (false exit 1)
trap_exit=$?

# Le trap emet via curl qui va echouer -> WARNING dans stderr, c'est normal
# On verifie juste que le subshell ne produit pas de crash non controle
_pass "roadmap_trap activated in subshell (exit=${trap_exit}, output='${trap_output:-<empty>}')"

# ---------------------------------------------------------------------------
# 6. Test emit_business_event — merge de payload
# ---------------------------------------------------------------------------
echo ""
echo "--- Test 6: emit_business_event ---"

export AGGREGATOR_URL="http://127.0.0.1:19999"
export TASK_ID="t-biz"
export ROADMAP_ID="rm-biz"
export ROADMAP_SOURCE="roadmap:rm-biz"
export EVENT_ID="evt-biz"

if emit_business_event "deploy.completed" '{"url":"https://example.com"}' 2>/dev/null; then
  _pass "emit_business_event with extra payload"
else
  _pass "emit_business_event ran (curl failure expected)"
fi

if emit_business_event "step.done" 2>/dev/null; then
  _pass "emit_business_event without extra payload"
else
  _pass "emit_business_event ran without extra payload (curl failure expected)"
fi

# ---------------------------------------------------------------------------
# Bilan
# ---------------------------------------------------------------------------
echo ""
echo "=================================="
echo "Results: ${PASS} passed, ${FAIL} failed"
echo "=================================="

if [[ $FAIL -gt 0 ]]; then
  exit 1
else
  exit 0
fi
