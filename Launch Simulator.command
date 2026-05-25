#!/bin/bash
# Double-clickable launcher for the Magical Athlete Simulator (Tkinter desktop UI).
# Uses the project-local .venv created with Homebrew Python so this works
# regardless of what `python3` resolves to globally — pyenv etc. don't matter.

# cd to this script's directory so the launcher works no matter where it's
# double-clicked from (Finder runs it from /).
cd "$(dirname "$0")" || {
    echo "Could not cd to script directory."
    read -rp "Press Enter to close..."
    exit 1
}

# Sanity-check the venv exists. If it's missing (e.g., the user moved or
# cloned the project to a new machine), point them at the rebuild steps
# rather than failing silently.
if [ ! -x ".venv/bin/python" ]; then
    echo "Missing .venv/bin/python in $(pwd)"
    echo
    echo "Rebuild the venv with:"
    echo "  /opt/homebrew/bin/python3.12 -m venv .venv"
    echo "  .venv/bin/pip install -r requirements.txt"
    echo
    read -rp "Press Enter to close..."
    exit 1
fi

echo "Launching Magical Athlete Simulator..."
.venv/bin/python main.py
status=$?

# Keep the Terminal window open on crash so the traceback is visible.
# Clean exits (closed window via the X button) close the terminal too.
if [ "$status" -ne 0 ]; then
    echo
    echo "Simulator exited with status $status."
    read -rp "Press Enter to close this window..."
fi
