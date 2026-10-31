# Map + alerts (app/routes_map.py)
Both use `all_trusted_units(db)` from trust.py (never raw events), `occurred_at`, and `clock.now()`. Test with fake TrustedUnit lists via monkeypatch, so you do not wait for trust.py.

## GET /map?pincode=&days=7&radius_km=2
- days default MAP_DEFAULT_DAYS=7; radius_km default MAP_DEFAULT_RADIUS=2.
- Window: units with occurred_at in (now - days, now].
- With pincode: areas within radius_km (haversine from that area's directory point; the area itself always included) that have >= 1 unit. Without pincode: all areas.
- One cluster per area: count = units, top_scam_type = most common, lat/lng from areas.json ONLY.
- severity: count >= SEV_CRIT (10) -> CRIT, >= SEV_HIGH (5) -> HIGH, else MED.
- Unknown pincode param -> 400.

## GET /alerts?pincode= (optional; absent = all areas)
Per area:
- last24 = units in (now-24h, now]; baseline_per_day = units in [now-24h-7d, now-24h) / 7 (round 2).
- **SPIKE** if last24 >= SPIKE_MIN (5) AND last24 >= SPIKE_FACTOR (2) x baseline_per_day.
  `{"type":"SPIKE","pincode","window":"24h","count","baseline_per_day"}`
- **NEW_TYPE** for each scam_type present in last24: fire if NO unit of that type in that area in [now-24h-30d, now-24h) AND the area had >= MIN_HISTORY_FOR_NEW_TYPE (2) units in that prior 30-day window (stops every first report in an empty area from alerting).
  `{"type":"NEW_TYPE","pincode","scam_type","window":"24h"}`
- Nothing -> `{"alerts":[]}`.

## tests/test_map_alerts.py
8-day-old and month-old units excluded from map; area points from directory; radius filter; SPIKE at 4 vs 5 and exactly 2x baseline; baseline 0 with 5 units fires; NEW_TYPE with and without history; alerts use occurred_at not reported_at.
