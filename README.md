# City commute map

Interactive London map: tube lines serving Old Street, Moorgate, Liverpool Street and Bank; boroughs within N minutes of those stations by tube; walking-distance shading around every station.

## Run

```bash
./start.sh
```

Opens http://localhost:8765. (Double-clicking `index.html` also works — data is embedded as JS, not fetched.) Needs internet for map tiles and Leaflet.

## How it works

- **Lines:** Northern, Central, Circle, Hammersmith & City, Metropolitan, Waterloo & City, plus the Elizabeth line (Liverpool Street), DLR (Bank) Overground Weaver line (Liverpool Street), and the District line via Monument (linked underground to Bank; times run to Monument's platforms). Interchange platforms are merged into one marker by TfL hub id. Geometry and stations come from the TfL open API.
- **Journey times** are estimated per line (no changes to other lines): `0.8 min per stop + 1.2 min per km` (1.0 for the Elizabeth line), shortest path to the nearest of the four stations. Calibrated against real journeys (Morden→Bank ≈ 30, Stratford→Liverpool St ≈ 10, Hammersmith→Moorgate ≈ 28); expect ±20%. Excludes walking and waiting.
- **Borough highlighted** if it contains at least one station within the max journey time.
- **Walking shading:** fixed-radius circles (80 m/min, so 10 min = 800 m) around each station.

## Fare zones

Zone areas are traced from every TfL Tube/DLR/Overground/Elizabeth line station (`raw-allstations.json`): each spot takes the zone of its nearest station (Voronoi cells, capped at 2.2 km so the outskirts don't sprawl), and boundaries are drawn between neighbouring stations in different zones. Approximate — fares actually depend on the station you use. Dual-zone stations (2/3) count as the cheaper zone.

The fares table and popups use TfL's 2026 adult caps and Travelcards ([PDF](https://content.tfl.gov.uk/adult-fares.pdf)) for Zones 1–N, since all four destination stations are in Zone 1. Update `FARES` in `build_data.py` each March.

## Bouldering gyms

`data/gyms.js` is a hand-checked list of ~30 indoor bouldering gyms (locations from OpenStreetMap, names/status checked against operators' sites, Sept 2026). Shown only in highlighted boroughs unless "Show all London gyms" is ticked; red pins also have roped climbing. Edit the file to add or fix gyms.

## Flats

`python3 fetch_listings.py` pulls live furnished 2-bed whole flats/houses from OpenRent and Rightmove within 1 km of a mapped station (≤ £3,000 pcm) into `data/listings.js`. Re-run it to refresh — listings let quickly.

Budget model (a couple + a single sharing a 2-bed): rent split **60/40** couple/single — the usual middle ground between per-room (50/50) and per-head (⅔/⅓) — and bills split **per head**. Where bills aren't included they're estimated at £370/month for the flat. Pins are coloured:

- **Green:** single pays ≤ ~£1,050 including their bill share.
- **Amber:** single's 40% rent share fits, but estimated bills push it over.
- **Purple (off by default):** only fits if split per head (single pays ⅓).

A blue dot on a pin means the landlord ticked "bills included" — often partial (e.g. council tax/water/broadband but not energy), so check the listing. Constants live at the top of `fetch_listings.py`.

Rightmove is queried in price bands (it caps searches at ~1,000 results); student-only lets, room shares and OpenRent re-listings are dropped, and the same flat on both sites is de-duplicated. Rightmove has no bills flag, so bills are read from the summary/key features — most listings don't mention bills and are treated as not included. Rightmove's terms restrict use of its data to Rightmove. Zoopla isn't included. If a site fails (blocked, format change), its listings from the previous run are kept.

## Rebuild data

```bash
./fetch_data.sh && python3 build_data.py
```

Tune the time model via `DWELL_MIN` / `MIN_PER_KM` in `build_data.py`.

## Hosting

Hosted on GitHub Pages via `.github/workflows/deploy.yml`:

- Every push to `main` redeploys the site.
- A daily schedule (05:30 UTC) re-runs `fetch_listings.py`, commits `data/listings.js` if it changed, and redeploys. Trigger it manually from the repo's **Actions** tab ("Run workflow").
- Pages source must be set to **GitHub Actions** (Settings → Pages).

To take the listings down: deleting `data/listings.js` isn't enough — it stays in git history. Delete the repo (or rewrite history and force-push).
