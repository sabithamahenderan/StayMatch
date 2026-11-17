# StayMatch — Project Summary

## Objective
Help students and working professionals discover and compare paying guest accommodation using budget, location and lifestyle preferences.

## Main navigation (five sections)
1. **Home** — overview metrics, shortcuts and recently added PG listings.
2. **Smart PG Finder** — district/locality, rent, sharing, food, facilities, accommodation type, distance and vacancy filters with explainable preference matching.
3. **PG Compare** — side-by-side comparison of two to four PG listings.
4. **Analytics Dashboard** — district listing counts, average rent, accommodation type, sharing and budget distribution.
5. **PG Listing Management** — create, update and delete listing records in SQLite.

The PG Details screen is an internal detail view opened from listing cards; it is not a separate navigation item. PG Rentals and Saved History navigation sections have been removed.

## Authentication
Account registration and sign-in use case-insensitive email matching and salted PBKDF2-HMAC-SHA256 password hashes. Registration validates email format, password length, letters, numbers and confirmation.

## Technology
Python, Streamlit, Pandas, Plotly, SQLite3, hashlib/PBKDF2, pytest.

## Database tables
`users`, `pg_listings`, `saved_pgs`, `search_history`, and `view_history`. Existing database tables are retained for compatibility with a previous local database; Saved History is not exposed in the current app navigation.

## Limitations
The supplied dataset is synthetic. No live inventory provider, OTP/email verification, map distance API, owner verification or payment system is integrated. The app is designed for local academic demonstration; a public deployment requires additional security and operational controls.
