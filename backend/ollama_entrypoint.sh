#!/bin/bash
# =============================================================================
# AegisAI — Ollama Entrypoint
# Starts the Ollama server and pre-pulls catalog models on first boot.
# Keep this list in sync with backend/app/core/model_catalog.json (enabled tags).
# =============================================================================

set -e

# 3B defaults — do not pull 7B/VL here unless a later slice requires it.
MODELS=(
  "qwen2.5:3b"
  "qwen2.5-coder:3b"
)

model_present() {
  local tag="$1"
  ollama list 2>/dev/null | awk 'NR > 1 { print $1 }' | grep -Fxq "$tag"
}

echo "[AegisAI] Starting Ollama server..."
export OLLAMA_HOST="${OLLAMA_HOST:-0.0.0.0}"
ollama serve &
SERVER_PID=$!

echo "[AegisAI] Waiting for Ollama to become ready..."
MAX_WAIT=90
WAITED=0
until ollama list > /dev/null 2>&1; do
  sleep 2
  WAITED=$((WAITED + 2))
  if [ $WAITED -ge $MAX_WAIT ]; then
    echo "[AegisAI] ERROR: Ollama did not become ready within ${MAX_WAIT}s. Continuing anyway..."
    break
  fi
done
echo "[AegisAI] Ollama is ready."

for MODEL in "${MODELS[@]}"; do
  echo "[AegisAI] Checking model: ${MODEL}..."
  if model_present "$MODEL"; then
    echo "[AegisAI] Model '${MODEL}' already present — skipping pull."
  elif [ "${AEGIS_ALLOW_MODEL_DOWNLOADS:-false}" != "true" ]; then
    echo "[AegisAI] Model '${MODEL}' is missing and downloads are disabled."
    echo "[AegisAI] Provision it into the ollama_models volume before air-gapped startup."
  else
    echo "[AegisAI] Pulling model '${MODEL}'... (first run may take several minutes)"
    if ollama pull "${MODEL}"; then
      echo "[AegisAI] Successfully pulled '${MODEL}'."
    else
      echo "[AegisAI] WARNING: Failed to pull '${MODEL}'. Chat will use the deterministic fallback until this tag is available."
    fi
  fi
done

echo "[AegisAI] Catalog model checks complete. Ollama is serving."
wait $SERVER_PID
