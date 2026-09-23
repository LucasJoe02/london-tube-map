#!/usr/bin/env bash
# Serve the map at http://localhost:8765 and open it in the default browser.
cd "$(dirname "$0")"
(sleep 1 && open "http://localhost:8765/") &
python3 -m http.server 8765
