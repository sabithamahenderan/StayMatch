"""Explainable preference matching and alternative recommendation engine for StayMatch."""
import heapq

# Synonym dictionary for flexible amenity matching
AMENITY_SYNONYMS = {
    "ro water": {"ro water", "drinking water", "24/7 water", "water"},
    "drinking water": {"ro water", "drinking water", "24/7 water"},
    "power backup": {"power backup", "generator", "ups"},
    "attached bathroom": {"attached bathroom", "attached bath", "private bath"},
    "wi-fi": {"wi-fi", "wifi", "internet"},
    "wifi": {"wi-fi", "wifi", "internet"},
    "ac": {"ac", "air conditioning", "air conditioner"},
    "food": {"food", "meals", "breakfast", "dinner"},
    "cctv": {"cctv", "security", "surveillance"},
    "laundry": {"laundry", "washing machine"},
    "housekeeping": {"housekeeping", "cleaning", "daily cleaning"},
    "parking": {"parking", "two wheeler parking", "car parking"}
}

def parse_amenities(value):
    """Parses a comma-separated amenity string into a normalized set of lowercase terms."""
    return {x.strip().casefold() for x in str(value or "").split(",") if x.strip()}

def _amenity_matches(wanted_item, listing_amenities):
    """Checks if a requested amenity is present in listing amenities, accounting for synonyms."""
    wanted_cf = str(wanted_item).casefold().strip()
    if wanted_cf in listing_amenities:
        return True
    synonyms = AMENITY_SYNONYMS.get(wanted_cf, {wanted_cf})
    return bool(synonyms & listing_amenities)

def score_listing(row, preferences):
    """
    Computes an explainable preference match score (0 to 100) and returns (score, matched_reasons).
    All points are calculated transparently based on active user requirements.
    """
    score = 0
    matched = []

    # 1. Sharing, Food, Accommodation Type checks
    checks = [
        ("sharing", 25, "sharing type"),
        ("food", 15, "food preference"),
        ("gender_policy", 10, "accommodation type")
    ]
    for key, weight, label in checks:
        wanted = preferences.get(key, "Any")
        if wanted in (None, "", "Any") or row.get(key) == wanted or (key == "gender_policy" and row.get(key) == "Co-living"):
            score += weight
            if wanted not in (None, "", "Any"):
                matched.append(label)

    # 2. AC preference check (up to 15 pts)
    ac_pref = preferences.get("ac_type", "Any")
    listing_amenities = parse_amenities(row.get("amenities"))
    has_ac = _amenity_matches("ac", listing_amenities)

    if ac_pref in (None, "", "Any"):
        score += 15
    elif ac_pref == "AC" and has_ac:
        score += 15
        matched.append("AC room")
    elif ac_pref == "Non-AC" and not has_ac:
        score += 15
        matched.append("Non-AC room")

    # 3. Amenities match (up to 25 pts)
    requested = list(preferences.get("amenities", []))
    if not requested:
        score += 25
    else:
        hits = [x for x in requested if _amenity_matches(x, listing_amenities)]
        score += round(25 * len(hits) / len(requested))
        matched += [str(x) for x in hits]

    # 4. Locality match (up to 10 pts)
    locality = preferences.get("locality", "Any")
    if locality in (None, "", "Any", "None"):
        score += 10
    elif str(row.get("locality", "")).casefold() == str(locality).casefold():
        score += 10
        matched.append("locality")

    final_score = max(0, min(100, round(score)))
    return final_score, matched

def recommend_listings(records, preferences, top_k=None):
    """
    Filters and ranks listings according to user preferences.
    Applies hard filters (district, budget, vacancy, gender policy, ac type)
    and sorts by explainable match score (descending) and rent (ascending).
    """
    out = []
    district = preferences.get("district", "All districts")
    low = int(preferences.get("min_budget", 0))
    high = int(preferences.get("max_budget", 10**9))
    available_only = preferences.get("available_only", True)
    gender_policy = preferences.get("gender_policy", "Any")
    ac_type = preferences.get("ac_type", "Any")

    for r in records:
        # District filter
        if district not in (None, "All districts") and r.get("district") != district:
            continue

        # Budget filter
        rent = int(r.get("rent", 0))
        if not (low <= rent <= high):
            continue

        # Vacancy filter
        if available_only and int(r.get("vacancy", 0)) != 1:
            continue

        # Gender policy filter
        if gender_policy not in (None, "Any"):
            if r.get("gender_policy") not in (gender_policy, "Co-living"):
                continue

        # AC type filter
        listing_amenities = parse_amenities(r.get("amenities"))
        has_ac = _amenity_matches("ac", listing_amenities)
        if ac_type == "AC" and not has_ac:
            continue
        elif ac_type == "Non-AC" and has_ac:
            continue

        # Compute match score and reasons
        score, matched = score_listing(r, preferences)
        out.append((r, score, matched))

    # Sort key: highest match score first, then lowest rent
    key = lambda x: (x[1], -int(x[0].get("rent", 0)))
    if top_k:
        return heapq.nlargest(int(top_k), out, key=key)
    return sorted(out, key=key, reverse=True)

def get_alternative_recommendations(records, preferences, top_k=4):
    """
    Provides intelligent, transparent alternative recommendations when exact match returns 0 results.
    Progressively relaxes filters while explaining exactly why each alternative is suggested.
    """
    district = preferences.get("district", "All districts")
    low = int(preferences.get("min_budget", 0))
    high = int(preferences.get("max_budget", 10**9))

    alternatives = []
    seen_ids = set()

    # Tier 1: Relax budget by +/- 35% (or min +₹2,000 window) within the same district
    relaxed_prefs_1 = dict(preferences)
    relaxed_prefs_1["min_budget"] = max(0, int(low * 0.70))
    relaxed_prefs_1["max_budget"] = max(int(high * 1.35), high + 2000)
    tier1_results = recommend_listings(records, relaxed_prefs_1, top_k=top_k)

    for item, score, matched in tier1_results:
        lid = item.get("id")
        if lid not in seen_ids:
            seen_ids.add(lid)
            diff = int(item.get("rent", 0)) - high
            if diff > 0:
                reason = f"Closest budget match in {item.get('district')} (₹{diff:,} above budget, ₹{item.get('rent',0):,}/mo)"
            else:
                reason = f"Closest budget match in {item.get('district')} (₹{item.get('rent',0):,}/mo)"
            alternatives.append((item, score, matched, reason))

    if len(alternatives) >= top_k:
        return alternatives[:top_k]

    # Tier 2: Relax AC and amenities filter within same district
    relaxed_prefs_2 = dict(preferences)
    relaxed_prefs_2["ac_type"] = "Any"
    relaxed_prefs_2["amenities"] = []
    tier2_results = recommend_listings(records, relaxed_prefs_2, top_k=top_k)

    for item, score, matched in tier2_results:
        lid = item.get("id")
        if lid not in seen_ids:
            seen_ids.add(lid)
            reason = f"Alternative option in {item.get('district')} ({item.get('sharing')}, {item.get('food')} food)"
            alternatives.append((item, score, matched, reason))

    if len(alternatives) >= top_k:
        return alternatives[:top_k]

    # Tier 3: Search all Tamil Nadu districts for matching budget & sharing
    relaxed_prefs_3 = dict(preferences)
    relaxed_prefs_3["district"] = "All districts"
    relaxed_prefs_3["amenities"] = []
    relaxed_prefs_3["ac_type"] = "Any"
    tier3_results = recommend_listings(records, relaxed_prefs_3, top_k=top_k)

    for item, score, matched in tier3_results:
        lid = item.get("id")
        if lid not in seen_ids:
            seen_ids.add(lid)
            reason = f"Recommended alternative in {item.get('district')} ({item.get('sharing')} at ₹{item.get('rent',0):,}/mo)"
            alternatives.append((item, score, matched, reason))

    return alternatives[:top_k]
