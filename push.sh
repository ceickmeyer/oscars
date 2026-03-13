#!/bin/bash
set -e

DEST=/home/cody/Programming/oscars

# Find the most recent ballots CSV in ~/Downloads
LATEST_OSCARS=$(ls -t ~/Downloads/Copy\ of\ Oscars\ Pool\ 2026\ -\ THE\ RESULTS\ -\ Form\ Responses\ 14*.csv 2>/dev/null | head -1)

if [ -z "$LATEST_OSCARS" ]; then
    echo "Error: No ballots CSV found in ~/Downloads"
    exit 1
fi
echo "Found ballots: $LATEST_OSCARS"
cp "$LATEST_OSCARS" "$DEST/oscars.csv"

# Find the most recent scores CSV in ~/Downloads
LATEST_SCORES=$(ls -t ~/Downloads/Copy\ of\ Oscars\ Pool\ 2026\ -\ THE\ RESULTS\ -\ *Scoreboard*.csv 2>/dev/null | head -1)

if [ -z "$LATEST_SCORES" ]; then
    echo "Warning: No scores CSV found in ~/Downloads — skipping scores update"
else
    echo "Found scores: $LATEST_SCORES"
    cp "$LATEST_SCORES" "$DEST/scores.csv"
fi

cd "$DEST"

python build_oscars.py
python build_viz.py

if [ -f scores.csv ]; then
    python build_scores.py
fi

git add index.html viz.html oscars.csv
[ -f scores.html ] && git add scores.html
[ -f scores.csv ]  && git add scores.csv

git commit -m "update ballots + viz"
git push

echo "Done — all pages pushed to GitHub"