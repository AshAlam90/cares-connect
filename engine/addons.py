"""
Productive uses of solar power beyond irrigation.

Each add-on is described by what it costs, how much energy it needs on a day
it runs, which months it runs, and the net income it earns on a full day of
operation (in local currency). If energy is short, it simply runs fewer days.

ALL FIGURES ARE ILLUSTRATIVE PLACEHOLDERS, except where a note cites a source.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field

ALL_MONTHS = list(range(1, 13))


@dataclass
class AddonSpec:
    key: str
    name: str
    name_bn: str
    capex: float
    kwh_per_day: float
    income_per_day: float         # fees and avoided losses on a full day of running
    om_per_year: float
    months: list[int] = field(default_factory=lambda: list(ALL_MONTHS))
    jobs: int = 1
    sdgs: list[int] = field(default_factory=list)
    note: str = ""
    country: str = "BD"

    @property
    def income_per_kwh(self) -> float:
        return self.income_per_day / self.kwh_per_day if self.kwh_per_day else 0.0


CATALOG: dict[str, AddonSpec] = {
    # ---------------------------------------------------------------- Bangladesh (Tk)
    "cold_storage": AddonSpec(
        "cold_storage", "Cold storage room (5 t)", "হিমাগার / কোল্ড স্টোরেজ (৫ টন)",
        capex=1_500_000, kwh_per_day=25, income_per_day=900, om_per_year=40_000,
        months=[3, 4, 5, 6, 7, 8, 9], jobs=2, sdgs=[2, 12],
        note="Storage fees plus reduced post-harvest loss for potato and vegetables."),
    "erickshaw": AddonSpec(
        "erickshaw", "E-rickshaw (easy bike) charging, 10 vehicles", "ইজিবাইক চার্জিং (১০টি)",
        capex=250_000, kwh_per_day=50, income_per_day=700, om_per_year=20_000,
        jobs=1, sdgs=[7, 11], note="Charging fees; daytime charging of spare batteries."),
    "mill": AddonSpec(
        "mill", "Rice & maize mill (15 kW)", "ধান ও ভুট্টা ভাঙানোর মিল (১৫ কিলোওয়াট)",
        capex=700_000, kwh_per_day=60, income_per_day=2_400, om_per_year=40_000,
        months=[1, 5, 6, 11, 12], jobs=3, sdgs=[8, 9],
        note="Milling fees after the Aman and Boro harvests."),
    "water": AddonSpec(
        "water", "Drinking-water purification (2,000 L/day)", "নিরাপদ খাবার পানি শোধন (২,০০০ লিটার/দিন)",
        capex=900_000, kwh_per_day=8, income_per_day=1_000, om_per_year=50_000,
        jobs=2, sdgs=[3, 6], note="Water sold at about Tk 0.5 per litre."),
    # ---------------------------------------------------------------- Sri Lanka (Rs)
    "water_lk": AddonSpec(
        "water_lk", "Drinking-water purification centre", "Drinking-water purification centre",
        capex=2_000_000, kwh_per_day=15, income_per_day=3_000, om_per_year=120_000,
        jobs=2, sdgs=[3, 6], country="LK",
        note="Modelled on Nochchiya, which sells purified water to about eight nearby villages for a "
             "nominal fee (source). Cost, volume and price here are assumptions."),
    "classroom": AddonSpec(
        "classroom", "Smart classroom (computers & internet)", "Smart classroom (computers & internet)",
        capex=900_000, kwh_per_day=6, income_per_day=0, om_per_year=60_000,
        months=[1, 2, 3, 5, 6, 7, 9, 10, 11], jobs=0, sdgs=[4], country="LK",
        note="Planned for solar village schools (source); no income, a social benefit. Costs assumed."),
    "fence": AddonSpec(
        "fence", "Solar electric fence (elephant deterrent)", "Solar electric fence (elephant deterrent)",
        capex=750_000, kwh_per_day=2, income_per_day=0, om_per_year=40_000,
        jobs=1, sdgs=[15], country="LK",
        note="Planned at Mediyawa, where elephant attacks killed two people (source). Costs assumed."),
    "cold_storage_lk": AddonSpec(
        "cold_storage_lk", "Cold room for vegetables & fruit", "Cold room for vegetables & fruit",
        capex=3_000_000, kwh_per_day=25, income_per_day=2_500, om_per_year=100_000,
        months=[2, 3, 4, 7, 8, 9], jobs=2, sdgs=[2, 12], country="LK",
        note="Storage after the Maha and Yala harvests. All figures assumed."),
}

NEED_TO_ADDON = {
    "Cold storage": {"BD": "cold_storage", "LK": "cold_storage_lk"},
    "E-rickshaw charging": {"BD": "erickshaw"},
    "Grain milling": {"BD": "mill"},
    "Drinking water": {"BD": "water", "LK": "water_lk"},
    "School electricity & smart classroom": {"LK": "classroom"},
    "Elephant fence": {"LK": "fence"},
}


def catalog_for(country: str) -> list[str]:
    return [k for k, a in CATALOG.items() if a.country == country]


def default_addons_for_needs(needs: list[str], country: str = "BD") -> list[AddonSpec]:
    keys = [NEED_TO_ADDON[n][country] for n in needs if country in NEED_TO_ADDON.get(n, {})]
    return [AddonSpec(**asdict(CATALOG[k])) for k in keys]


def addon_from_dict(d: dict) -> AddonSpec:
    return AddonSpec(**d)
