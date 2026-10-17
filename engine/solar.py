"""
Solar resource and PV output.

Monthly method (no hourly data needed):
  1. Monthly mean daily global horizontal irradiation (GHI) and air temperature
     come from NASA POWER, or from built-in approximate values if offline.
  2. Extraterrestrial irradiation and the clearness index for each month's
     representative day (Klein, 1977).
  3. Diffuse fraction from the monthly Erbs et al. (1982) correlation.
  4. Irradiation on a tilted, south-facing panel with the isotropic-sky model
     (Liu & Jordan, 1962).
  5. Cell temperature from the NOCT model, using the energy-weighted mean
     irradiance of a half-sine daily profile, then a linear power-temperature
     coefficient.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
DAYS_IN_MONTH = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
# Klein (1977) recommended average day of each month (day of year)
KLEIN_DAYS = [17, 47, 75, 105, 135, 162, 198, 228, 258, 288, 318, 344]
SOLAR_CONSTANT_KW = 1.367   # kW/m2

# Approximate monthly values per country (engine/countries.py), used ONLY when
# NASA POWER cannot be reached (e.g. demo running offline). Illustrative.
from .countries import COUNTRIES

FALLBACK_GHI = COUNTRIES["BD"]["fallback_ghi"]
FALLBACK_T2M = COUNTRIES["BD"]["fallback_t2m"]

NASA_POWER_URL = ("https://power.larc.nasa.gov/api/temporal/climatology/point"
                  "?parameters=ALLSKY_SFC_SW_DWN,T2M&community=RE"
                  "&longitude={lon:.4f}&latitude={lat:.4f}&format=JSON")
NASA_KEYS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN",
             "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]


@dataclass
class SiteClimate:
    lat: float
    lon: float
    ghi: list[float]          # kWh/m2/day, monthly mean
    t2m: list[float]          # deg C, monthly mean (24 h)
    source: str = "fallback"  # "nasa_power" or "fallback"
    note: str = ""


def fallback_climate(lat: float, lon: float, note: str = "", country: str = "BD") -> SiteClimate:
    c = COUNTRIES[country]
    return SiteClimate(lat, lon, list(c["fallback_ghi"]), list(c["fallback_t2m"]), "fallback",
                       note or f"Approximate built-in values for {c['name']} (NASA POWER not reached).")


def fetch_climate(lat: float, lon: float, country: str = "BD", timeout: float = 8.0) -> SiteClimate:
    """Monthly climatology from NASA POWER; falls back to built-in values."""
    try:
        import requests
        r = requests.get(NASA_POWER_URL.format(lat=lat, lon=lon), timeout=timeout)
        r.raise_for_status()
        params = r.json()["properties"]["parameter"]
        ghi = [float(params["ALLSKY_SFC_SW_DWN"][k]) for k in NASA_KEYS]
        t2m = [float(params["T2M"][k]) for k in NASA_KEYS]
        if min(ghi) <= 0 or min(t2m) < -50:        # NASA fill value is -999
            raise ValueError("missing values in NASA POWER response")
        return SiteClimate(lat, lon, ghi, t2m, "nasa_power",
                           "NASA POWER monthly climatology (all-sky GHI, 2 m air temperature).")
    except Exception as exc:  # network blocked, timeout, format change ...
        return fallback_climate(lat, lon, f"Approximate built-in values for {COUNTRIES[country]['name']} "
                                          f"(NASA POWER not reached: {type(exc).__name__}).", country)


# ---------------------------------------------------------------- geometry
def declination_deg(day_of_year: int) -> float:
    return 23.45 * math.sin(math.radians(360 * (284 + day_of_year) / 365))


def sunset_hour_angle_deg(lat_deg: float, decl_deg: float) -> float:
    x = -math.tan(math.radians(lat_deg)) * math.tan(math.radians(decl_deg))
    return math.degrees(math.acos(max(-1.0, min(1.0, x))))


def extraterrestrial_daily_kwh(lat_deg: float, day_of_year: int) -> float:
    """Daily extraterrestrial irradiation on a horizontal surface, kWh/m2/day."""
    phi = math.radians(lat_deg)
    d = declination_deg(day_of_year)
    delta = math.radians(d)
    ws = sunset_hour_angle_deg(lat_deg, d)
    ecc = 1 + 0.033 * math.cos(math.radians(360 * day_of_year / 365))
    return (24 / math.pi) * SOLAR_CONSTANT_KW * ecc * (
        math.cos(phi) * math.cos(delta) * math.sin(math.radians(ws))
        + math.radians(ws) * math.sin(phi) * math.sin(delta))


def erbs_monthly_diffuse_fraction(kt: float, ws_deg: float) -> float:
    kt = max(0.3, min(0.8, kt))                     # correlation validity range
    if ws_deg <= 81.4:
        return 1.391 - 3.560 * kt + 4.189 * kt**2 - 2.137 * kt**3
    return 1.311 - 3.022 * kt + 3.427 * kt**2 - 1.821 * kt**3


def tilted_daily_kwh(ghi: float, lat_deg: float, tilt_deg: float, day_of_year: int,
                     albedo: float = 0.2) -> float:
    """Monthly mean daily irradiation on a south-facing tilted plane (N hemisphere)."""
    phi = math.radians(lat_deg)
    beta = math.radians(tilt_deg)
    d = declination_deg(day_of_year)
    delta = math.radians(d)
    ws = sunset_hour_angle_deg(lat_deg, d)
    ws_tilt = min(ws, sunset_hour_angle_deg(lat_deg - tilt_deg, d))

    h0 = extraterrestrial_daily_kwh(lat_deg, day_of_year)
    kt = ghi / h0
    fd = erbs_monthly_diffuse_fraction(kt, ws)

    num = (math.cos(phi - beta) * math.cos(delta) * math.sin(math.radians(ws_tilt))
           + math.radians(ws_tilt) * math.sin(phi - beta) * math.sin(delta))
    den = (math.cos(phi) * math.cos(delta) * math.sin(math.radians(ws))
           + math.radians(ws) * math.sin(phi) * math.sin(delta))
    rb = num / den

    return (ghi * (1 - fd) * rb
            + ghi * fd * (1 + math.cos(beta)) / 2
            + ghi * albedo * (1 - math.cos(beta)) / 2)


# ---------------------------------------------------------------- PV output
@dataclass
class PVSpec:
    kwp: float = 28.8
    tilt_deg: float | None = None     # None -> latitude, rounded
    system_losses: float = 0.14       # soiling, wiring, mismatch, controller
    noct_c: float = 45.0
    gamma_per_c: float = -0.0040      # power temperature coefficient
    albedo: float = 0.2
    daytime_temp_uplift_c: float = 3.0  # daytime air is warmer than 24 h mean


def monthly_pv(climate: SiteClimate, spec: PVSpec) -> dict:
    """Monthly PV energy (kWh) plus the intermediate physics, for display."""
    tilt = spec.tilt_deg if spec.tilt_deg is not None else round(abs(climate.lat))
    out = {"poa_kwh_m2_day": [], "cell_temp_c": [], "temp_factor": [], "pv_kwh": []}
    for m in range(12):
        n = KLEIN_DAYS[m]
        h_t = tilted_daily_kwh(climate.ghi[m], climate.lat, tilt, n, spec.albedo)
        ws = sunset_hour_angle_deg(climate.lat, declination_deg(n))
        day_hours = 2 * ws / 15
        g_weighted = (math.pi**2 / 8) * 1000 * h_t / day_hours          # W/m2
        t_cell = climate.t2m[m] + spec.daytime_temp_uplift_c + (spec.noct_c - 20) / 800 * g_weighted
        f_t = 1 + spec.gamma_per_c * (t_cell - 25)
        e = spec.kwp * h_t * f_t * (1 - spec.system_losses) * DAYS_IN_MONTH[m]
        out["poa_kwh_m2_day"].append(h_t)
        out["cell_temp_c"].append(t_cell)
        out["temp_factor"].append(f_t)
        out["pv_kwh"].append(e)
    out["tilt_deg"] = tilt
    return out
