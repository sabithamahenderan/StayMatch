"""SQLite persistence, authentication, listings, saved PGs and per-user activity for StayMatch."""
from pathlib import Path
import hashlib
import hmac
import os
import sqlite3
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "staymatch.db"
CSV_PATH = BASE_DIR / "data" / "pg_listings.csv"

def connect():
    conn = sqlite3.connect(DB_PATH, timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def _hash_password(password, salt=None):
    salt = salt or os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 310000)
    return salt.hex() + "$" + digest.hex()

def _verify_password(password, stored):
    try:
        salt_hex, digest_hex = stored.split("$", 1)
        candidate = _hash_password(password, bytes.fromhex(salt_hex)).split("$", 1)[1]
        return hmac.compare_digest(candidate, digest_hex)
    except (ValueError, TypeError, IndexError):
        return False

def init_db():
    with connect() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS users(
          id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
          email TEXT NOT NULL UNIQUE COLLATE NOCASE, password_hash TEXT NOT NULL,
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS pg_listings(
          id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, district TEXT NOT NULL,
          city TEXT NOT NULL, locality TEXT NOT NULL, rent INTEGER NOT NULL CHECK(rent>=0),
          deposit INTEGER NOT NULL DEFAULT 0 CHECK(deposit>=0), sharing TEXT NOT NULL, food TEXT NOT NULL,
          amenities TEXT NOT NULL DEFAULT '', vacancy INTEGER NOT NULL DEFAULT 1 CHECK(vacancy IN (0,1)),
          gender_policy TEXT NOT NULL DEFAULT 'Co-living', contact TEXT NOT NULL DEFAULT '',
          description TEXT NOT NULL DEFAULT '', source_type TEXT NOT NULL DEFAULT 'User submitted',
          verified INTEGER NOT NULL DEFAULT 0 CHECK(verified IN (0,1)),
          image_url TEXT NOT NULL DEFAULT '', rules TEXT NOT NULL DEFAULT '',
          food_meals TEXT NOT NULL DEFAULT '', distance_km REAL NOT NULL DEFAULT 0,
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS saved_pgs(
          user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          listing_id INTEGER NOT NULL REFERENCES pg_listings(id) ON DELETE CASCADE,
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY(user_id,listing_id)
        );
        CREATE TABLE IF NOT EXISTS search_history(
          id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          filters_json TEXT NOT NULL, result_count INTEGER NOT NULL DEFAULT 0,
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS view_history(
          id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          listing_id INTEGER NOT NULL REFERENCES pg_listings(id) ON DELETE CASCADE,
          viewed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_pg_district ON pg_listings(district);
        CREATE INDEX IF NOT EXISTS idx_pg_rent ON pg_listings(rent);
        CREATE INDEX IF NOT EXISTS idx_pg_vacancy ON pg_listings(vacancy);
        CREATE INDEX IF NOT EXISTS idx_search_user ON search_history(user_id);
        """)

        # Safe migration for databases created by earlier versions
        existing = {r["name"] for r in c.execute("PRAGMA table_info(pg_listings)")}
        for col, definition in [
            ("image_url", "TEXT NOT NULL DEFAULT ''"), ("rules", "TEXT NOT NULL DEFAULT ''"),
            ("food_meals", "TEXT NOT NULL DEFAULT ''"), ("distance_km", "REAL NOT NULL DEFAULT 0")
        ]:
            if col not in existing:
                c.execute(f"ALTER TABLE pg_listings ADD COLUMN {col} {definition}")

        # Seed initial dataset if database is empty
        count = c.execute("SELECT COUNT(*) FROM pg_listings").fetchone()[0]
        if count == 0 and CSV_PATH.exists():
            frame = pd.read_csv(CSV_PATH).fillna("")
            for _, r in frame.iterrows():
                c.execute("""INSERT INTO pg_listings
                (name,district,city,locality,rent,deposit,sharing,food,amenities,vacancy,
                 gender_policy,contact,description,source_type,verified)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
                    str(r.get("name","")), str(r.get("district","")), str(r.get("city","")),
                    str(r.get("locality","")), int(r.get("rent",0)), int(r.get("deposit",0)),
                    str(r.get("sharing","2-sharing")),
                    str(r.get("food","")), str(r.get("amenities","")), int(r.get("vacancy",1)),
                    {"Women only":"Girls PG","Men only":"Boys PG","Any":"Co-living"}.get(
                        str(r.get("gender_policy","Any")), str(r.get("gender_policy","Co-living"))
                    ),
                    str(r.get("contact","")), str(r.get("description","")),
                    str(r.get("source_type","Synthetic demo data")),
                    int(r.get("verified",0))
                ))
        c.commit()

def register_user(name, email, password):
    with connect() as c:
        c.execute("INSERT INTO users(name,email,password_hash) VALUES(?,?,?)",
                  (name.strip(), email.strip().lower(), _hash_password(password)))
        return c.execute("SELECT id,name,email FROM users WHERE email=?", (email.strip().lower(),)).fetchone()

def authenticate_user(email, password):
    with connect() as c:
        row = c.execute("SELECT * FROM users WHERE email=?", (email.strip().lower(),)).fetchone()
        if row and _verify_password(password, row["password_hash"]):
            return {"id": row["id"], "name": row["name"], "email": row["email"]}
    return None

def get_all_listings():
    with connect() as c:
        return pd.read_sql_query("SELECT * FROM pg_listings ORDER BY created_at DESC, id DESC", c)

def get_listing(listing_id):
    with connect() as c:
        r = c.execute("SELECT * FROM pg_listings WHERE id=?", (int(listing_id),)).fetchone()
        return dict(r) if r else None

def add_listing(d):
    fields = [
        "name", "district", "city", "locality", "rent", "deposit", "sharing", "food", "amenities", "vacancy",
        "gender_policy", "contact", "description", "source_type", "verified", "image_url", "rules", "food_meals", "distance_km"
    ]
    # Sanitize values
    values = [
        str(d.get("name", "")).strip(),
        str(d.get("district", "")).strip(),
        str(d.get("city", "")).strip() or str(d.get("district", "")).strip(),
        str(d.get("locality", "")).strip(),
        max(0, int(d.get("rent", 0) or 0)),
        max(0, int(d.get("deposit", 0) or 0)),
        str(d.get("sharing", "2-sharing")),
        str(d.get("food", "Optional")),
        str(d.get("amenities", "")),
        1 if int(d.get("vacancy", 1) or 0) else 0,
        str(d.get("gender_policy", "Co-living")),
        str(d.get("contact", "")).strip(),
        str(d.get("description", "")).strip(),
        str(d.get("source_type", "User submitted")),
        1 if int(d.get("verified", 0) or 0) else 0,
        str(d.get("image_url", "")).strip(),
        str(d.get("rules", "")).strip(),
        str(d.get("food_meals", "")).strip(),
        max(0.0, float(d.get("distance_km", 0.0) or 0.0))
    ]
    with connect() as c:
        cur = c.execute(f"INSERT INTO pg_listings({','.join(fields)}) VALUES({','.join('?' for _ in fields)})", values)
        return cur.lastrowid

def update_listing(listing_id, d):
    fields = [
        "name", "district", "city", "locality", "rent", "deposit", "sharing", "food", "amenities", "vacancy",
        "gender_policy", "contact", "description", "image_url", "rules", "food_meals", "distance_km"
    ]
    values = [
        str(d.get("name", "")).strip(),
        str(d.get("district", "")).strip(),
        str(d.get("city", "")).strip() or str(d.get("district", "")).strip(),
        str(d.get("locality", "")).strip(),
        max(0, int(d.get("rent", 0) or 0)),
        max(0, int(d.get("deposit", 0) or 0)),
        str(d.get("sharing", "2-sharing")),
        str(d.get("food", "Optional")),
        str(d.get("amenities", "")),
        1 if int(d.get("vacancy", 1) or 0) else 0,
        str(d.get("gender_policy", "Co-living")),
        str(d.get("contact", "")).strip(),
        str(d.get("description", "")).strip(),
        str(d.get("image_url", "")).strip(),
        str(d.get("rules", "")).strip(),
        str(d.get("food_meals", "")).strip(),
        max(0.0, float(d.get("distance_km", 0.0) or 0.0))
    ]
    with connect() as c:
        c.execute("UPDATE pg_listings SET " + ",".join(f"{k}=?" for k in fields) + " WHERE id=?",
                  values + [int(listing_id)])

def delete_listing(listing_id):
    with connect() as c:
        c.execute("DELETE FROM pg_listings WHERE id=?", (int(listing_id),))

def toggle_saved(user_id, listing_id):
    with connect() as c:
        exists = c.execute("SELECT 1 FROM saved_pgs WHERE user_id=? AND listing_id=?", (int(user_id), int(listing_id))).fetchone()
        if exists:
            c.execute("DELETE FROM saved_pgs WHERE user_id=? AND listing_id=?", (int(user_id), int(listing_id)))
            return False
        c.execute("INSERT OR IGNORE INTO saved_pgs(user_id,listing_id) VALUES(?,?)", (int(user_id), int(listing_id)))
        return True

def get_saved_ids(user_id):
    with connect() as c:
        return {r[0] for r in c.execute("SELECT listing_id FROM saved_pgs WHERE user_id=?", (int(user_id),))}

def get_saved_listings(user_id):
    with connect() as c:
        return pd.read_sql_query("""SELECT p.*, s.created_at as saved_at 
          FROM pg_listings p JOIN saved_pgs s ON p.id=s.listing_id
          WHERE s.user_id=? ORDER BY s.created_at DESC""", c, params=(int(user_id),))

def record_search(user_id, filters, result_count):
    import json
    with connect() as c:
        c.execute("INSERT INTO search_history(user_id,filters_json,result_count) VALUES(?,?,?)",
                  (int(user_id), json.dumps(filters, ensure_ascii=False), int(result_count)))

def get_search_history(user_id):
    with connect() as c:
        return pd.read_sql_query("SELECT * FROM search_history WHERE user_id=? ORDER BY id DESC LIMIT 50", c, params=(int(user_id),))

def delete_search_history(user_id, history_id):
    with connect() as c:
        c.execute("DELETE FROM search_history WHERE id=? AND user_id=?", (int(history_id), int(user_id)))

def clear_all_search_history(user_id):
    with connect() as c:
        c.execute("DELETE FROM search_history WHERE user_id=?", (int(user_id),))

def record_view(user_id, listing_id):
    with connect() as c:
        c.execute("INSERT INTO view_history(user_id,listing_id) VALUES(?,?)", (int(user_id), int(listing_id)))

def get_view_history(user_id):
    with connect() as c:
        return pd.read_sql_query("""SELECT p.*, v.viewed_at FROM view_history v JOIN pg_listings p ON p.id=v.listing_id
        WHERE v.user_id=? ORDER BY v.id DESC LIMIT 50""", c, params=(int(user_id),))

def dashboard_stats():
    with connect() as c:
        total = c.execute("SELECT COUNT(*) FROM pg_listings").fetchone()[0]
        available = c.execute("SELECT COUNT(*) FROM pg_listings WHERE vacancy=1").fetchone()[0]
        districts = c.execute("SELECT COUNT(DISTINCT district) FROM pg_listings").fetchone()[0]
        avg_rent_row = c.execute("SELECT AVG(rent) FROM pg_listings WHERE vacancy=1").fetchone()[0]
        avg_rent = round(avg_rent_row) if avg_rent_row is not None else 0
        verified = c.execute("SELECT COUNT(*) FROM pg_listings WHERE verified=1").fetchone()[0]
        return {
            "total": total,
            "available": available,
            "districts": districts,
            "average_rent": avg_rent,
            "verified": verified
        }

def get_district_summary():
    with connect() as c:
        query = """
        SELECT 
            district,
            COUNT(*) as total_listings,
            SUM(CASE WHEN vacancy = 1 THEN 1 ELSE 0 END) as available_listings,
            MIN(rent) as min_rent,
            ROUND(AVG(rent)) as avg_rent,
            MAX(rent) as max_rent,
            COUNT(DISTINCT locality) as locality_count
        FROM pg_listings
        GROUP BY district
        ORDER BY total_listings DESC, district ASC
        """
        return pd.read_sql_query(query, c)
