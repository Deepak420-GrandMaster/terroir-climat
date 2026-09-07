#!/bin/bash
# Double-click this file to run Terroir & Climat in your browser.
cd "$(dirname "$0")" || exit 1

echo "Terroir & Climat"
echo "================"
echo

if [ ! -d .venv ]; then
  echo "First run — creating a Python environment (about 60 seconds)…"
  python3 -m venv .venv || { echo; echo "Could not create the environment."; \
    echo "Is Python 3 installed?  Try:  python3 --version"; read -r; exit 1; }
  ./.venv/bin/pip install --quiet --upgrade pip
  echo "Installing packages…"
  ./.venv/bin/pip install --quiet -r requirements.txt || { echo; \
    echo "Install failed. Scroll up for the reason."; read -r; exit 1; }
  echo "Done."
  echo
fi

if [ ! -f data/processed/monthly_climate.parquet ]; then
  echo "The climate table has not been built yet."
  echo "Checking the connection to Open-Meteo…"
  echo
  if ! ./.venv/bin/python scripts/build_climate_table.py --check; then
    echo
    echo "Could not reach Open-Meteo. Check your internet connection and try again."
    echo "The app will still start, but it will show the setup screen."
    echo
    read -r -p "Press Return to start anyway… "
  else
    echo
    echo "Connection is good. Downloading the weather history."
    echo "This takes a few minutes and only happens once."
    echo
    ./.venv/bin/python scripts/build_climate_table.py || { echo; \
      echo "The download stopped early. Everything fetched so far is cached —"; \
      echo "run this file again and it resumes."; read -r; exit 1; }
    echo
  fi
fi

echo "Opening http://localhost:8501 in your browser."
echo "Leave this window open while you use it. Press Ctrl+C here to stop."
echo
./.venv/bin/streamlit run app.py
