# US Locations v1 provenance

- Artifact: `us_locations_v1.json`
- Version: `us-census-gazetteer-places-2025-v1`
- Official source: United States Census Bureau, 2025 National Places Gazetteer
- Source page: https://www.census.gov/geographies/reference-files/time-series/geo/gazetteer-files.2025.html
- Source file: `2025_Gaz_place_national.zip` / `2025_Gaz_place_national.txt`
- Source URL: https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2025_Gazetteer/2025_Gaz_place_national.zip
- Source status: United States government public data; retain this provenance notice.
- State-name mapping: `pycountry` US subdivisions, an existing project dependency.
- Generated: 2026-07-15
- Generator: `src/pipeline/location_data/generate_us_locations.py`

Generation command:

```text
python src/pipeline/location_data/generate_us_locations.py \
  /path/to/2025_Gaz_place_national.zip \
  src/pipeline/location_data/us_locations_v1.json
```

The generated artifact intentionally excludes coordinates, area, population, geometry, and
other fields not needed for deterministic location preference matching. Place entity suffixes
such as `city`, `town`, and `CDP` are removed. Entries with the same normalized place name in
different states are preserved. Duplicate normalized names within one state are collapsed to
the first source record because the application canonical ID is city/state based.
