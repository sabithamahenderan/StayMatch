# StayMatch — Smart PG Finder

A Streamlit application for discovering and comparing PG accommodation, viewing analytics, and managing PG listings. The interface uses a modern blue-and-white theme with SQLite-backed account authentication and listing storage.

## Main navigation

The sidebar contains exactly these five sections:

1. **Home** — overview and recently added PG listings.
2. **Smart PG Finder** — filter and rank PGs by location, budget, sharing, food, amenities and availability.
3. **PG Compare** — compare two to four PG listings side by side.
4. **Analytics Dashboard** — district, rent, accommodation type, sharing and budget insights.
5. **PG Listing Management** — add, edit and delete PG listings.

The PG Details view remains available from listing cards, but it is an internal detail view rather than a separate navigation section. PG Rentals and Saved History have been removed from the user interface.

## Login and account creation

On first launch, select **Create account** and register with a valid email address and a password containing at least eight characters, including a letter and a number. Then sign in using those credentials. Email matching is case-insensitive. Existing accounts in `staymatch.db` are retained when that database file is kept in the project folder.

## Run in VS Code (Windows)

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Open `http://localhost:8501` in your browser.

If PowerShell blocks activation, use Command Prompt:

```bat
.venv\Scripts\activate.bat
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Run tests

```powershell
python -m pytest -q
```

The starter CSV contains synthetic demonstration listings. Confirm rent, vacancy, address and contact details directly with a provider before making decisions.
