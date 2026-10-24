#!/bin/zsh
set -e
APP="${0:A:h}"
if command -v python3 >/dev/null 2>&1; then
  exec python3 "$APP/scripts/serve.py" --open --bank pathology
else
  echo "Python 3 is needed for the local launcher."
  read -k 1 "?Press any key to close."
fi
