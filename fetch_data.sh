#!/usr/bin/env bash
# Re-download raw source data (TfL open API + London borough boundaries).
set -euo pipefail
cd "$(dirname "$0")/data"
for l in northern central circle hammersmith-city metropolitan waterloo-city elizabeth dlr weaver district; do
  curl -sf "https://api.tfl.gov.uk/Line/$l/Route/Sequence/all" -o "raw-$l.json"
done
curl -sf "https://api.tfl.gov.uk/StopPoint/Mode/tube,dlr,overground,elizabeth-line" -o raw-allstations.json
curl -sf "https://raw.githubusercontent.com/radoi90/housequest-data/master/london_boroughs.geojson" -o boroughs-raw.geojson
echo "Fetched. Now run: python3 build_data.py"
