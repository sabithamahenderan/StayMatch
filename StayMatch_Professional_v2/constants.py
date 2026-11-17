"""Reference data and constants for StayMatch — Smart PG Finder."""

TAMIL_NADU_DISTRICTS = [
    "Ariyalur", "Chengalpattu", "Chennai", "Coimbatore", "Cuddalore",
    "Dharmapuri", "Dindigul", "Erode", "Kallakurichi", "Kancheepuram",
    "Kanniyakumari", "Karur", "Krishnagiri", "Madurai", "Mayiladuthurai",
    "Nagapattinam", "Namakkal", "Nilgiris", "Perambalur", "Pudukkottai",
    "Ramanathapuram", "Ranipet", "Salem", "Sivaganga", "Tenkasi",
    "Thanjavur", "Theni", "Thoothukudi", "Tiruchirappalli", "Tirunelveli",
    "Tirupathur", "Tiruppur", "Tiruvallur", "Tiruvannamalai", "Tiruvarur",
    "Vellore", "Villupuram", "Virudhunagar"
]

# Regional grouping of Tamil Nadu districts for intuitive exploration
TN_REGIONS = {
    "Chennai Region": ["Chennai", "Chengalpattu", "Kancheepuram", "Tiruvallur"],
    "Western Tamil Nadu": ["Coimbatore", "Tiruppur", "Erode", "Salem", "Namakkal", "Dharmapuri", "Krishnagiri", "Nilgiris"],
    "Southern Tamil Nadu": ["Madurai", "Dindigul", "Theni", "Virudhunagar", "Sivaganga", "Ramanathapuram", "Thoothukudi", "Tirunelveli", "Tenkasi", "Kanniyakumari"],
    "Central Tamil Nadu": ["Tiruchirappalli", "Karur", "Perambalur", "Ariyalur", "Thanjavur", "Tiruvarur", "Nagapattinam", "Mayiladuthurai", "Pudukkottai"],
    "Northern Tamil Nadu": ["Ranipet", "Tirupathur", "Vellore", "Tiruvannamalai", "Villupuram", "Kallakurichi", "Cuddalore"]
}

AMENITIES = [
    "Wi-Fi", "AC", "Attached bathroom", "Food", "Laundry",
    "RO Water", "Parking", "CCTV", "Power backup", "Housekeeping",
    "24/7 water"
]

SHARING_OPTIONS = ["1-sharing", "2-sharing", "3-sharing", "4-sharing", "Multiple sharing"]
FOOD_OPTIONS = ["Any", "Included", "Not included", "Optional"]
GENDER_OPTIONS = ["Any", "Boys PG", "Girls PG", "Co-living"]
AC_OPTIONS = ["Any", "AC", "Non-AC"]

# Curated royalty-free high-resolution accommodation images for realistic, modern presentation
DEFAULT_PG_IMAGES = {
    "Co-living": [
        "https://images.unsplash.com/photo-1555854877-bab0e564b8d5?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1522771739844-6a9f6d5f14af?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?auto=format&fit=crop&w=800&q=80"
    ],
    "Boys PG": [
        "https://images.unsplash.com/photo-1595526114035-0d45ed16cfbf?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1590490360182-c33d57733427?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1586023492125-27b2c045efd7?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1505691938895-1758d7feb511?auto=format&fit=crop&w=800&q=80"
    ],
    "Girls PG": [
        "https://images.unsplash.com/photo-1598928506311-c55ded91a20c?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1513694203232-719a280e022f?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1540518614846-7ede433c4ef9?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&w=800&q=80"
    ]
}

def get_listing_image(listing_id, gender_policy="Co-living", custom_url=""):
    """Returns a valid accommodation image URL for a listing."""
    if custom_url and isinstance(custom_url, str) and custom_url.strip().startswith(("http://", "https://")):
        return custom_url.strip()
    policy = gender_policy if gender_policy in DEFAULT_PG_IMAGES else "Co-living"
    images = DEFAULT_PG_IMAGES[policy]
    idx = abs(int(listing_id or 0)) % len(images)
    return images[idx]
