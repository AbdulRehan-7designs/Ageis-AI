#!/bin/bash
# =============================================================================
# AegisAI — Ollama Entrypoint
# Starts the Ollama server and pre-pulls all required models on first boot.
# Subsequent boots skip the pull if the model is already cached in the volume.
# =============================================================================

set -e

# Models to pull on startup (order: text first, coder, vision last)
MODELS=(
  "qwen2.5:7b"
  "qwen2.5-coder:7b"
)

echo "[AegisAI] Starting Ollama server..."
ollama serve &
SERVER_PID=$!

# Wait for Ollama to be healthy before pulling models
echo "[AegisAI] Waiting for Ollama to become ready..."
MAX_WAIT=60
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

# Pull each model only if not already present
for MODEL in "${MODELS[@]}"; do
  echo "[AegisAI] Checking model: ${MODEL}..."
  if ollama list 2>/dev/null | grep -q "^${MODEL%:*}"; then
    echo "[AegisAI] Model '${MODEL}' already present — skipping pull."
  else
    echo "[AegisAI] Pulling model '${MODEL}'... (this may take a while on first run)"
    if ollama pull "${MODEL}"; then
      echo "[AegisAI] Successfully pulled '${MODEL}'."
    else
      echo "[AegisAI] WARNING: Failed to pull '${MODEL}'. System will use fallback engine."
    fi
  fi
done

echo "[AegisAI] All model checks complete. Ollama is serving."

# Keep the server process in foreground
wait $SERVER_PID
