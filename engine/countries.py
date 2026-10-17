"""
Country settings: currency, land units, districts, climate fallback, crops,
needs, default costs and grid rules.

Sri Lanka figures marked (source) come from the Solar Village project report
(NIFS, 2024): a 5 kW roof costs about Rs 1,200,000 installed, a 5 kW inverter
about Rs 375,000, and the CEB Net-Plus scheme now pays Rs 37/unit for 20 years
(older contracts: Rs 22/unit for 7 years, then Rs 15/unit). Everything else is
an illustrative assumption to be replaced with partners' data.
"""
from __future__ import annotations

COUNTRIES: dict[str, dict] = {
    "LK": {
        "name": "Sri Lanka",
        "currency": "Rs",
        "gbp_rate": 380.0,                      # assumed Rs per £
        "land_unit": "acre", "ha_per_land_unit": 0.4047,
        "languages": {"en": "English"},         # Sinhala and Tamil to be added with local partners
        "center": (7.85, 80.70), "zoom": 6.4,
        "lat_range": (5.8, 9.9), "lon_range": (79.5, 82.0),
        "districts": sorted([
            "Ampara", "Anuradhapura", "Badulla", "Batticaloa", "Colombo", "Galle", "Gampaha", "Hambantota",
            "Jaffna", "Kalutara", "Kandy", "Kegalle", "Kilinochchi", "Kurunegala", "Mannar", "Matale",
            "Matara", "Monaragala", "Mullaitivu", "Nuwara Eliya", "Polonnaruwa", "Puttalam", "Ratnapura",
            "Trincomalee", "Vavuniya"]),
        # Approximate dry-zone values, used only when NASA POWER is unreachable
        "fallback_ghi": [5.0, 5.8, 6.2, 6.0, 5.6, 5.4, 5.4, 5.6, 5.7, 5.0, 4.5, 4.4],
        "fallback_t2m": [25.5, 26.5, 28.0, 29.0, 29.5, 29.0, 28.8, 28.8, 28.7, 27.6, 26.4, 25.6],
        "crops": ["Paddy", "Vegetables", "Chilli", "Onion", "Maize", "Fruit", "Other"],
        "needs": ["Community income from a solar roof", "Drinking water", "Irrigation (agro-well)",
                  "School electricity & smart classroom", "Elephant fence", "Cold storage"],
        "irrigation_need": "Irrigation (agro-well)",
        "grid_need": "Community income from a solar roof",
        "water_sources": {"Agro-well (dug well)": 8.0, "Tube well": 25.0, "Tank or canal": 5.0},
        # Calibrated: with the standard 14% losses the model gives ~640 kWh/month for a 5 kW roof;
        # field reports say 500-600, so as-built and new Sri Lankan designs use 26% (midpoint 550).
        "pv_losses": 0.26,
        "costs": dict(pv_per_kwp=240_000,              # (source) Rs 1.2 m per 5 kW, installation included
                      pump_per_kw=60_000, fixed_install=0, distribution_per_ha=100_000,
                      solar_om_per_year=10_000,         # (source) cleaning only
                      controller_replacement_year=10,
                      inverter_per_kw=75_000),          # (source) Rs 375,000 per 5 kW inverter
        "finance": dict(diesel_price_per_l=300, diesel_escalation=0.05, diesel_fuel_to_water_eff=0.15,
                        diesel_maintenance_per_year=20_000, discount_rate=0.10, lifetime_years=20,
                        funder_grant_share=1.0, cares_design_fee=0.05, cares_mgmt_share=0.05),
        "grid": dict(grid_scheme="net_plus", grid_tariff=37.0, grid_tariff_after=37.0,
                     grid_tariff_switch_year=0, grid_buy_price=30.0),   # (source) Rs 37/unit; buy price assumed
    },
    "BD": {
        "name": "Bangladesh",
        "currency": "Tk",
        "gbp_rate": 160.0,                      # assumed Tk per £
        "land_unit": "bigha", "ha_per_land_unit": 1 / 7.475,
        "languages": {"en": "English", "bn": "বাংলা"},
        "center": (23.75, 90.2), "zoom": 6.0,
        "lat_range": (20.5, 26.7), "lon_range": (88.0, 92.7),
        "districts": sorted([
            "Bagerhat", "Bandarban", "Barguna", "Barishal", "Bhola", "Bogura", "Brahmanbaria", "Chandpur",
            "Chapai Nawabganj", "Chattogram", "Chuadanga", "Cox's Bazar", "Cumilla", "Dhaka", "Dinajpur",
            "Faridpur", "Feni", "Gaibandha", "Gazipur", "Gopalganj", "Habiganj", "Jamalpur", "Jashore",
            "Jhalokathi", "Jhenaidah", "Joypurhat", "Khagrachhari", "Khulna", "Kishoreganj", "Kurigram",
            "Kushtia", "Lakshmipur", "Lalmonirhat", "Madaripur", "Magura", "Manikganj", "Meherpur",
            "Moulvibazar", "Munshiganj", "Mymensingh", "Naogaon", "Narail", "Narayanganj", "Narsingdi",
            "Natore", "Netrokona", "Nilphamari", "Noakhali", "Pabna", "Panchagarh", "Patuakhali", "Pirojpur",
            "Rajbari", "Rajshahi", "Rangamati", "Rangpur", "Satkhira", "Shariatpur", "Sherpur", "Sirajganj",
            "Sunamganj", "Sylhet", "Tangail", "Thakurgaon"]),
        "fallback_ghi": [4.15, 4.85, 5.55, 5.85, 5.55, 4.55, 4.25, 4.40, 4.15, 4.40, 4.30, 4.00],
        "fallback_t2m": [18.6, 21.9, 26.2, 28.6, 29.0, 29.1, 28.8, 29.0, 28.7, 27.5, 24.0, 20.0],
        "crops": ["Boro rice", "Aman rice", "Wheat", "Maize", "Potato", "Vegetables", "Jute"],
        "needs": ["Irrigation", "Drinking water", "Cold storage", "Grain milling", "E-rickshaw charging"],
        "irrigation_need": "Irrigation",
        "grid_need": None,
        "water_sources": {"Groundwater": 18.0, "Surface water": 6.0},
        "pv_losses": 0.14,
        "costs": dict(pv_per_kwp=65_000, pump_per_kw=25_000, fixed_install=450_000, distribution_per_ha=15_000,
                      solar_om_per_year=35_000, controller_replacement_year=10, inverter_per_kw=0),
        "finance": dict(diesel_price_per_l=110, diesel_escalation=0.05, diesel_fuel_to_water_eff=0.15,
                        diesel_maintenance_per_year=30_000, discount_rate=0.10, lifetime_years=20,
                        funder_grant_share=0.70, cares_design_fee=0.05, cares_mgmt_share=0.05),
        "grid": dict(grid_scheme="none", grid_tariff=4.0, grid_tariff_after=4.0,
                     grid_tariff_switch_year=0, grid_buy_price=0.0),
    },
}

GRID_SCHEMES = {
    "none": "Not grid-connected",
    "export_surplus": "Use solar first, sell what is left over",
    "net_plus": "Sell all solar output to the grid (Net-Plus)",
}


def country(code: str) -> dict:
    return COUNTRIES[code]
