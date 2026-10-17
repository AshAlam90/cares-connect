"""
Irrigation water need and pumping energy.

Hydraulic energy to lift water:  E = rho * g * V * H
  1 m3 of water lifted 1 m needs 1000 * 9.81 J = 9,810 J = 0.002725 kWh.
Electrical energy = hydraulic energy / wire-to-water efficiency (motor + pump).
Diesel use = hydraulic energy / (fuel-to-water efficiency * 10 kWh per litre).
"""
from __future__ import annotations

KWH_PER_M3_PER_M = 1000 * 9.81 / 3.6e6       # 0.002725 kWh
DIESEL_KWH_PER_LITRE = 10.0                   # lower heating value, approx.
HECTARE_PER_BIGHA = 1 / 7.475                 # standard Bangladesh bigha (33 decimals)
HECTARE_PER_ACRE = 0.4047

# Gross irrigation need, mm per month (Jan..Dec) for each hectare irrigated.
# Illustrative cropping patterns; a real tool would use FAO-56 crop water
# requirements, local rainfall and field losses.
PATTERNS = {
    # Bangladesh
    "boro_aman": {"country": "BD", "label": "Boro rice + supplementary Aman",
                  "mm": [250, 280, 300, 220, 30, 0, 0, 20, 60, 50, 0, 60]},
    "boro_rabi": {"country": "BD", "label": "Boro rice + Rabi vegetables",
                  "mm": [260, 290, 300, 230, 60, 20, 0, 0, 0, 40, 80, 110]},
    "rabi_upland": {"country": "BD", "label": "Wheat / maize / potato / vegetables",
                    "mm": [90, 100, 90, 60, 20, 0, 0, 0, 0, 30, 70, 80]},
    "mixed": {"country": "BD", "label": "Mixed (half Boro, half upland crops)",
              "mm": [170, 190, 195, 140, 25, 0, 0, 10, 30, 40, 35, 70]},
    # Sri Lanka (dry zone)
    "lk_ofc_dry": {"country": "LK", "label": "Agro-well vegetables, chilli & onion (dry season)",
                   "mm": [30, 50, 70, 70, 90, 110, 120, 120, 90, 30, 0, 10]},
    "lk_paddy_yala": {"country": "LK", "label": "Supplementary irrigation for Yala paddy",
                      "mm": [0, 0, 0, 60, 120, 150, 150, 100, 40, 0, 0, 0]},
    "none": {"country": "*", "label": "No irrigation", "mm": [0] * 12},
}


def patterns_for(country: str) -> list[str]:
    return [k for k, v in PATTERNS.items() if v["country"] in (country, "*")]


def pattern_from_crops(crops: list[str], country: str = "BD") -> str:
    """Guess a cropping pattern from the crops a community listed."""
    c = set(crops or [])
    if country == "LK":
        return "lk_paddy_yala" if c == {"Paddy"} else "lk_ofc_dry"
    has_boro = "Boro rice" in c
    upland = c & {"Wheat", "Maize", "Potato", "Vegetables"}
    if has_boro and upland:
        return "boro_rabi" if "Vegetables" in c or "Potato" in c else "mixed"
    if has_boro:
        return "boro_aman"
    if upland:
        return "rabi_upland"
    return "mixed"


def monthly_water_m3(area_ha: float, pattern: str) -> list[float]:
    mm = PATTERNS[pattern]["mm"]
    return [area_ha * 10_000 * v / 1000 for v in mm]      # 1 mm on 1 ha = 10 m3


def hydraulic_kwh(water_m3: float, head_m: float) -> float:
    return water_m3 * head_m * KWH_PER_M3_PER_M


def pump_electric_kwh(water_m3: float, head_m: float, wire_to_water_eff: float) -> float:
    return hydraulic_kwh(water_m3, head_m) / wire_to_water_eff


def diesel_litres_for_hydraulic(hydraulic_energy_kwh: float, fuel_to_water_eff: float) -> float:
    return hydraulic_energy_kwh / (fuel_to_water_eff * DIESEL_KWH_PER_LITRE)
