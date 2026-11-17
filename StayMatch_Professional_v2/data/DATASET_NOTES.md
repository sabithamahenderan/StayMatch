# Dataset notes

`pg_listings.csv` contains 114 synthetic records: 3 demo rows for each of the 38 districts listed in `constants.py`.

- `source_type`: `Synthetic demo data`
- `verified`: `0`
- `contact`: placeholder `0000000000`
- The names, prices, amenities, vacancy flags and localities do not establish a real accommodation offer.
- Do not present this dataset as live or scraped data.
- The application imports these rows into SQLite only if the database table is empty.

For genuine listings, replace or append rows only after collecting data with permission and documenting source/date/verification.
