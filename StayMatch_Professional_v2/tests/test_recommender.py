"""Automated test suite for StayMatch recommendation engine, filtering, and database."""
import pytest
from recommender import parse_amenities, recommend_listings, score_listing, get_alternative_recommendations
import database

def test_parse_amenities_normalizes_and_removes_blanks():
    assert parse_amenities(" Wi-Fi, Laundry, ,wi-fi ") == {"wi-fi", "laundry"}

def test_budget_and_district_hard_filters():
    records = [
        {"name":"A","district":"Erode","rent":5000,"vacancy":1,"sharing":"2-sharing","food":"Included",
         "amenities":"Wi-Fi","locality":"Thindal","gender_policy":"Any"},
        {"name":"B","district":"Chennai","rent":5000,"vacancy":1,"sharing":"2-sharing","food":"Included",
         "amenities":"Wi-Fi","locality":"Guindy","gender_policy":"Any"},
        {"name":"C","district":"Erode","rent":15000,"vacancy":1,"sharing":"2-sharing","food":"Included",
         "amenities":"Wi-Fi","locality":"Thindal","gender_policy":"Any"},
    ]
    prefs = {"district":"Erode","min_budget":4000,"max_budget":8000,"available_only":True,
             "sharing":"Any","food":"Any","amenities":[],"locality":"Any","gender_policy":"Any"}
    result = recommend_listings(records, prefs)
    assert [x[0]["name"] for x in result] == ["A"]

def test_top_k_returns_requested_count():
    records = [
        {"name":str(i),"district":"Erode","rent":5000+i*100,"vacancy":1,"sharing":"2-sharing","food":"Included",
         "amenities":"Wi-Fi","locality":"Thindal","gender_policy":"Any"} for i in range(8)
    ]
    prefs = {"district":"All districts","min_budget":0,"max_budget":10000,"available_only":True,
             "sharing":"Any","food":"Any","amenities":[],"locality":"Any","gender_policy":"Any"}
    assert len(recommend_listings(records, prefs, top_k=3)) == 3

def test_score_is_bounded():
    row = {"sharing":"2-sharing","food":"Included","amenities":"Wi-Fi, Laundry","locality":"Thindal","gender_policy":"Any"}
    score, matched = score_listing(row, {"sharing":"2-sharing","food":"Included","amenities":["Wi-Fi"],
                                         "locality":"Thindal","gender_policy":"Any"})
    assert 0 <= score <= 100
    assert "Wi-Fi" in matched

def test_ac_filter_behavior():
    records = [
        {"id": 1, "name": "AC Stay", "district": "Chennai", "rent": 8000, "vacancy": 1,
         "sharing": "2-sharing", "food": "Included", "amenities": "Wi-Fi, AC", "locality": "Guindy", "gender_policy": "Co-living"},
        {"id": 2, "name": "Non-AC Stay", "district": "Chennai", "rent": 6000, "vacancy": 1,
         "sharing": "2-sharing", "food": "Included", "amenities": "Wi-Fi, RO Water", "locality": "Guindy", "gender_policy": "Co-living"}
    ]
    # Filter for AC
    prefs_ac = {"district": "Chennai", "min_budget": 0, "max_budget": 10000, "available_only": True,
                "ac_type": "AC", "sharing": "Any", "food": "Any", "amenities": [], "gender_policy": "Any"}
    res_ac = recommend_listings(records, prefs_ac)
    assert len(res_ac) == 1
    assert res_ac[0][0]["name"] == "AC Stay"

    # Filter for Non-AC
    prefs_non_ac = {"district": "Chennai", "min_budget": 0, "max_budget": 10000, "available_only": True,
                    "ac_type": "Non-AC", "sharing": "Any", "food": "Any", "amenities": [], "gender_policy": "Any"}
    res_non_ac = recommend_listings(records, prefs_non_ac)
    assert len(res_non_ac) == 1
    assert res_non_ac[0][0]["name"] == "Non-AC Stay"

def test_alternative_recommendations_when_no_exact_match():
    records = [
        {"id": 10, "name": "Slightly Over Budget", "district": "Madurai", "rent": 6500, "vacancy": 1,
         "sharing": "2-sharing", "food": "Included", "amenities": "Wi-Fi, RO Water", "locality": "KK Nagar", "gender_policy": "Co-living"},
        {"id": 11, "name": "Other District", "district": "Trichy", "rent": 4500, "vacancy": 1,
         "sharing": "2-sharing", "food": "Included", "amenities": "Wi-Fi", "locality": "Thillai Nagar", "gender_policy": "Co-living"}
    ]
    # Exact search for Madurai with max_budget 5000 -> 0 exact matches
    prefs = {"district": "Madurai", "min_budget": 3000, "max_budget": 5000, "available_only": True,
             "sharing": "2-sharing", "food": "Any", "amenities": [], "gender_policy": "Any", "ac_type": "Any"}
    exact = recommend_listings(records, prefs)
    assert len(exact) == 0

    # Alternatives should find the slightly over budget one in Madurai
    alts = get_alternative_recommendations(records, prefs, top_k=2)
    assert len(alts) > 0
    assert alts[0][0]["name"] == "Slightly Over Budget"
    assert "budget" in alts[0][3].lower()

def test_register_and_login_round_trip(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "auth_test.db")
    database.init_db()
    created = database.register_user("Test User", "Test.User@example.com", "securePass123")

    assert created["email"] == "test.user@example.com"
    assert database.authenticate_user("TEST.USER@EXAMPLE.COM", "securePass123")["id"] == created["id"]
    assert database.authenticate_user("test.user@example.com", "wrongPass123") is None

def test_login_rejects_unknown_user(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "auth_empty.db")
    database.init_db()
    assert database.authenticate_user("missing@example.com", "password123") is None

def test_toggle_saved_and_search_history(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "saved_test.db")
    database.init_db()
    user = database.register_user("Demo User", "demo@example.com", "demoPass123")
    uid = user["id"]

    listings = database.get_all_listings()
    assert not listings.empty
    lid = int(listings.iloc[0]["id"])

    # Toggle save
    saved_now = database.toggle_saved(uid, lid)
    assert saved_now is True
    saved_ids = database.get_saved_ids(uid)
    assert lid in saved_ids

    # Unsave
    saved_now = database.toggle_saved(uid, lid)
    assert saved_now is False
    assert lid not in database.get_saved_ids(uid)

    # Search history
    database.record_search(uid, {"district": "Chennai", "rent": 6000}, 3)
    history = database.get_search_history(uid)
    assert len(history) == 1
    assert history.iloc[0]["result_count"] == 3
