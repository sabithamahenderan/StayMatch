# StayMatch — Quick Run Guide (VS Code / Windows)

1. Extract the ZIP file.
2. Open the `StayMatch_Professional_v2` folder in VS Code.
3. Open **Terminal → New Terminal** and run:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

4. Open `http://localhost:8501`.
5. On the first run, choose **Create account**, register with a valid email and a password of at least 8 characters containing a letter and a number, then sign in.

If PowerShell activation is blocked, switch the terminal profile to **Command Prompt** and use:

```bat
.venv\Scripts\activate.bat
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Run the automated tests with:

```powershell
python -m pytest -q
```

**Existing account/data:** Keep your old `staymatch.db` in this project folder to retain existing users and PG listings. Back it up before replacing or moving the database.
