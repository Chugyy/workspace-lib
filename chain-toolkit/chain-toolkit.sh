#!/bin/bash
# chain-toolkit.sh — Helpers bash pour les scripts d'action des PIDs
#
# Usage dans un script d'action :
#   source "/data/workspace/lib/chain-toolkit/chain-toolkit.sh"
#   parse_event "$1"
#   roadmap_trap
#   emit_progress 1 5 "Starting schema generation"
#   emit_business_event "step.schema.done"
#
# Variables d'environnement requises :
#   AGGREGATOR_URL  — URL de l'aggregator
#   AGG_API_KEY     — Cle API aggregator
#
# Variables injectees par le handler runner (ou par parse_event) :
#   TASK_ID         — ID de la tache en cours
#   ROADMAP_ID      — ID de la roadmap
#   ROADMAP_SOURCE  — Source pour les events (ex: "roadmap:rm-123")
#   EVENT_ID        — ID de l'event trigger (pour related_to)

# --- Config & env ---

ROADMAP_SOURCE="${ROADMAP_SOURCE:-roadmap}"

# --- Core: emit_event, verify_file ---

# emit_event — Emet un event vers l'aggregator.
#
# $1 = event type (ex: "roadmap.task.completed")
# $2 = payload JSON (ex: '{"task_id":"task-123"}'), optionnel
# $3 = related_to event ID, optionnel
emit_event() {
  local event_type="$1"
  local payload="${2:-"{}"}"
  local related_to="${3:-}"
  local source="${ROADMAP_SOURCE:-roadmap}"

  # Validate jq is available
  if ! command -v jq &>/dev/null; then
    echo "[chain-toolkit] WARNING: jq not found, cannot emit ${event_type}" >&2
    return 0
  fi

  # Build JSON with jq for correctness
  local body
  if [[ -n "$related_to" ]]; then
    body=$(jq -n \
      --arg source "$source" \
      --arg type "$event_type" \
      --argjson payload "$payload" \
      --arg related_to "$related_to" \
      '{source: $source, type: $type, payload: $payload, related_to: $related_to}')
  else
    body=$(jq -n \
      --arg source "$source" \
      --arg type "$event_type" \
      --argjson payload "$payload" \
      '{source: $source, type: $type, payload: $payload}')
  fi

  curl -sk -X POST "${AGGREGATOR_URL}/events" \
    -H "X-Api-Key: ${AGG_API_KEY}" \
    -H "Content-Type: application/json" \
    -d "$body" \
    > /dev/null 2>&1 || echo "[chain-toolkit] WARNING: failed to emit ${event_type}" >&2
}

# verify_file — Verifie qu'un fichier existe et n'est pas vide. Return 1 si echec.
#
# $1 = chemin du fichier
# $2 = message d'erreur optionnel
verify_file() {
  local filepath="$1"
  local msg="${2:-File missing or empty: ${filepath}}"

  if [[ ! -f "$filepath" ]]; then
    echo "[chain-toolkit] ERROR: ${msg}" >&2
    return 1
  fi

  if [[ ! -s "$filepath" ]]; then
    echo "[chain-toolkit] ERROR: ${msg} (file is empty)" >&2
    return 1
  fi

  return 0
}

# --- Parsing ---

# parse_event — Parse le JSON event d'entree et exporte les variables standard.
#
# $1 = event JSON (passe par le handler en $1 du script)
#
# Exporte : EVENT_ID, EVENT_SOURCE, EVENT_TYPE, TASK_ID, ROADMAP_ID, ROADMAP_SOURCE
#
# Failsafe : si jq n'est pas dispo ou si le JSON est invalide, affiche un warning et exit 1.
parse_event() {
  local raw="${1:-}"

  if [[ -z "$raw" ]]; then
    echo "[chain-toolkit] ERROR: parse_event called with empty argument" >&2
    exit 1
  fi

  if ! command -v jq &>/dev/null; then
    echo "[chain-toolkit] ERROR: jq is required for parse_event" >&2
    exit 1
  fi

  # Validate JSON
  if ! echo "$raw" | jq -e . &>/dev/null; then
    echo "[chain-toolkit] ERROR: parse_event received invalid JSON" >&2
    exit 1
  fi

  export EVENT_ID
  export EVENT_SOURCE
  export EVENT_TYPE
  export TASK_ID
  export ROADMAP_ID
  export ROADMAP_SOURCE

  EVENT_ID=$(echo "$raw" | jq -r '.id // empty')
  EVENT_SOURCE=$(echo "$raw" | jq -r '.source // empty')
  EVENT_TYPE=$(echo "$raw" | jq -r '.type // empty')
  TASK_ID=$(echo "$raw" | jq -r '.payload.task_id // empty')
  ROADMAP_ID=$(echo "$raw" | jq -r '.payload.roadmap_id // empty')

  # ROADMAP_SOURCE : utilise la valeur existante si deja set, sinon derive de EVENT_SOURCE
  if [[ -z "${ROADMAP_SOURCE:-}" ]] || [[ "${ROADMAP_SOURCE}" == "roadmap" ]]; then
    ROADMAP_SOURCE="${EVENT_SOURCE:-roadmap}"
  fi

  if [[ -z "$TASK_ID" ]]; then
    echo "[chain-toolkit] WARNING: task_id missing from event payload" >&2
  fi

  if [[ -z "$ROADMAP_ID" ]]; then
    echo "[chain-toolkit] WARNING: roadmap_id missing from event payload" >&2
  fi
}

# --- Lifecycle helpers ---

# roadmap_trap — Configure un trap ERR qui emet roadmap.task.failed avant que le process meure.
#
# A appeler apres parse_event pour que TASK_ID, ROADMAP_ID, ROADMAP_SOURCE soient set.
# Note : le handler runner emet aussi failed si le script exit != 0. Ce trap est un filet
# supplementaire — il envoie l'event AVANT que le process ne meure.
roadmap_trap() {
  trap '_roadmap_trap_handler $? $LINENO' ERR
}

_roadmap_trap_handler() {
  local exit_code="${1:-1}"
  local line="${2:-0}"

  # Cleanup temp files if TMPDIR is set
  if [[ -n "${TMPDIR:-}" && -d "${TMPDIR}" ]]; then
    rm -rf "${TMPDIR}" 2>/dev/null || true
  fi

  local payload
  payload=$(jq -n \
    --arg task_id "${TASK_ID:-}" \
    --arg roadmap_id "${ROADMAP_ID:-}" \
    --argjson exit_code "$exit_code" \
    --argjson line "$line" \
    '{task_id: $task_id, roadmap_id: $roadmap_id, exit_code: $exit_code, line: $line}')

  emit_event "roadmap.task.failed" "$payload" "${EVENT_ID:-}"
}

# emit_progress — Emet un event de progression roadmap.task.progress.
#
# $1 = step courant (entier)
# $2 = total steps (entier)
# $3 = message optionnel
#
# Variables requises : TASK_ID, ROADMAP_ID, ROADMAP_SOURCE, EVENT_ID (pour related_to)
emit_progress() {
  local step="$1"
  local total="$2"
  local message="${3:-}"

  local payload
  payload=$(jq -n \
    --arg task_id "${TASK_ID:-}" \
    --arg roadmap_id "${ROADMAP_ID:-}" \
    --argjson step "$step" \
    --argjson total "$total" \
    --arg message "$message" \
    '{task_id: $task_id, roadmap_id: $roadmap_id, step: $step, total: $total, message: $message}')

  emit_event "roadmap.task.progress" "$payload" "${EVENT_ID:-}"
}

# emit_business_event — Emet un event business pour le chainage.
#
# $1 = event type (ex: "deploy.completed", "step.schema.done")
# $2 = payload JSON supplementaire a merger, optionnel (ex: '{"url":"https://..."}')
#
# Variables requises : TASK_ID, ROADMAP_ID, ROADMAP_SOURCE
emit_business_event() {
  local event_type="$1"
  local extra_payload="${2:-}"

  local base_payload
  base_payload=$(jq -n \
    --arg task_id "${TASK_ID:-}" \
    --arg roadmap_id "${ROADMAP_ID:-}" \
    '{task_id: $task_id, roadmap_id: $roadmap_id}')

  local payload
  if [[ -n "$extra_payload" ]]; then
    # Merge base + extra (extra wins on conflict)
    payload=$(jq -n \
      --argjson base "$base_payload" \
      --argjson extra "$extra_payload" \
      '$base * $extra')
  else
    payload="$base_payload"
  fi

  emit_event "$event_type" "$payload" "${EVENT_ID:-}"
}

# --- Idempotency ---

# has_event — Verifie si un event du type donne a deja ete emis pour cette tache.
#
# $1 = event_type a chercher (ex: "step.schema.done")
# $2 = task_id a filtrer (defaut: $TASK_ID)
#
# Retourne exit 0 si l'event existe, exit 1 sinon ou si l'aggregator est injoignable.
#
# Usage :
#   if ! has_event "step.schema.done"; then
#     # executer l'etape schema
#     emit_event "step.schema.done" '{"task_id":"'$TASK_ID'"}'
#   fi
has_event() {
  local event_type="$1"
  local task_id="${2:-${TASK_ID:-}}"
  local source="${ROADMAP_SOURCE:-roadmap}"

  if ! command -v jq &>/dev/null; then
    echo "[chain-toolkit] WARNING: jq not found, has_event cannot filter results" >&2
    return 1
  fi

  # Query aggregator
  local response
  response=$(curl -sk \
    -H "X-Api-Key: ${AGG_API_KEY}" \
    "${AGGREGATOR_URL}/events?source=$(python3 -c "import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1]))" "$source")&type=$(python3 -c "import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1]))" "$event_type")&limit=50" \
    2>/dev/null) || {
    echo "[chain-toolkit] WARNING: has_event: aggregator unreachable" >&2
    return 1
  }

  # Validate response is JSON
  if ! echo "$response" | jq -e . &>/dev/null; then
    echo "[chain-toolkit] WARNING: has_event: invalid response from aggregator" >&2
    return 1
  fi

  # Filter by task_id in payload
  if [[ -n "$task_id" ]]; then
    local count
    count=$(echo "$response" | jq --arg tid "$task_id" '
      if type == "array" then
        [.[] | select(.payload.task_id == $tid)] | length
      elif .items then
        [.items[] | select(.payload.task_id == $tid)] | length
      else 0 end
    ' 2>/dev/null || echo "0")

    if [[ "$count" -gt 0 ]]; then
      return 0
    else
      return 1
    fi
  else
    # No task_id filter — check if any event of that type exists
    local count
    count=$(echo "$response" | jq '
      if type == "array" then length
      elif .items then .items | length
      else 0 end
    ' 2>/dev/null || echo "0")

    if [[ "$count" -gt 0 ]]; then
      return 0
    else
      return 1
    fi
  fi
}
