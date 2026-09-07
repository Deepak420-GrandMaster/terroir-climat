#!/bin/bash
# Double-click this and walk away.
#
# The Open-Meteo free tier has a daily data-volume budget that this download
# exceeds. Rather than failing when the budget runs out, this keeps the machine
# awake and retries every 20 minutes until the table is complete. Every chunk is
# cached, so each attempt resumes exactly where the last one stopped.
#
# Safe to close (Ctrl+C) and rerun at any point.

cd "$(dirname "$0")" || exit 1

if [ ! -d .venv ]; then
  echo "Creating the Python environment…"
  python3 -m venv .venv && ./.venv/bin/pip install --quiet -r requirements.txt \
    || { echo "Setup failed."; read -r; exit 1; }
fi

TARGET="data/processed/monthly_climate.parquet"
ATTEMPT=0

# caffeinate stops macOS idle-sleeping mid-download. -i is idle only: closing
# the lid still sleeps, so leave it open.
RUN="./.venv/bin/python scripts/build_climate_table.py"
command -v caffeinate >/dev/null && RUN="caffeinate -i $RUN"

echo "Terroir & Climat — finishing the climate table"
echo "=============================================="
echo "Leave this window open and the lid up. Ctrl+C to stop; nothing is lost."
echo

while true; do
  ATTEMPT=$((ATTEMPT + 1))
  echo
  echo "--- attempt $ATTEMPT · $(date '+%H:%M') ---"

  if $RUN; then
    echo
    echo "Done. The climate table is built."
    break
  fi

  if [ -f "$TARGET" ]; then
    echo "Table exists; stopping."
    break
  fi

  echo
  echo "Open-Meteo's budget is spent for now. Sleeping 20 minutes, then resuming"
  echo "automatically. You can leave this running overnight — press Ctrl+C to stop."
  sleep 1200
done

echo
DONE=$(ls data/raw/openmeteo_cache/b*_m39.json 2>/dev/null | wc -l | tr -d ' ')
echo "$DONE of 232 chunks cached."
if [ -f "$TARGET" ]; then
  echo
  echo "Next, to publish it:"
  echo "  git add -f $TARGET"
  echo "  git commit -m 'data: monthly climate table'"
  echo "  git push"
  echo
  echo "Then deploy at share.streamlit.io"
fi
read -r -p "Press Return to close… "
