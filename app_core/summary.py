"""Plain-language summary of a design, in English or Bangla.

Every number here comes from the engine's results. This is a fixed template;
a future AI assistant could phrase it more naturally, but it would receive the
same numbers from the engine rather than working anything out itself.
"""
from __future__ import annotations

from engine.addons import CATALOG

from .ui import bn_digits, cur


def _uses(design: dict, lang: str) -> str:
    names = [(CATALOG[a["key"]].name_bn if lang == "bn" else CATALOG[a["key"]].name).split(" (")[0]
             for a in design["addons"] if a["key"] in CATALOG]
    if lang != "bn":
        names = [n[0].lower() + n[1:] for n in names]
    return ", ".join(names)


def summary(village: str, design: dict, res: dict, lang: str = "en") -> str:
    e, f, i = res["energy"], res["finance"], res["impact"]
    country = design.get("country", "BD")
    c = cur(country)
    pb, cpb = f["simple_payback"], f["community_payback"]
    n = {
        "kwp": f"{design['pv']['kwp']:g}", "pump": f"{design['pump_kw']:g}",
        "diesel": f"{i['diesel_l']:,.0f}", "surplus": f"{e['pv_kwh'] - e['pump_served_kwh']:,.0f}",
        "capex": f"{f['capex'] / 1e5:.1f}", "share": f"{f['community_share'] / 1e5:.1f}",
        "pb": f"{pb:.1f}" if pb else "", "cpb": f"{cpb:.1f}" if cpb else "", "co2": f"{i['co2_t']:.1f}",
        "sold": f"{e['grid_export_kwh']:,.0f}", "grid_inc": f"{f['grid_income_year1'] / 1e5:.1f}",
        "per_month": f"{f['grid_income_year1'] / 12:,.0f}",
    }
    net_plus = design.get("grid_scheme") == "net_plus"
    irrigates = design.get("area_ha", 0) > 0
    uses = _uses(design, lang)

    if lang == "bn" and country == "BD":
        b = {k: bn_digits(v) for k, v in n.items()}
        parts = [
            f"{village}-এ {b['kwp']} কিলোওয়াট সৌর প্যানেল ও {b['pump']} কিলোওয়াট পাম্প "
            f"বছরে প্রায় {b['diesel']} লিটার ডিজেল সাশ্রয় করবে।",
            f"সেচের পরেও বছরে প্রায় {b['surplus']} কিলোওয়াট-ঘণ্টা বাড়তি বিদ্যুৎ থাকবে, যা কাজে লাগবে: {uses or 'এখনো কিছু নয়'}।",
            (f"মোট খরচ প্রায় {b['capex']} লাখ টাকা; পুরো প্রকল্পের খরচ প্রায় {b['pb']} বছরে উঠে আসবে।"
             if pb else "এই হিসাবে প্রকল্পের খরচ উঠে আসবে না।"),
            (f"গ্রামের নিজস্ব অংশ ({b['share']} লাখ টাকা) উঠে আসবে প্রায় {b['cpb']} বছরে।" if cpb else ""),
            f"প্রতি বছর প্রায় {b['co2']} টন কার্বন ডাই-অক্সাইড নির্গমন কমবে।",
        ]
        if e["deficit_months"]:
            parts.append("সতর্কতা: কিছু মাসে সৌর বিদ্যুৎ সেচের পুরো চাহিদা মেটাতে পারবে না; "
                         "সেসব মাসে বিকল্প ব্যবস্থা লাগবে।")
        return " ".join(p for p in parts if p)

    parts = []
    if net_plus:
        parts.append(f"In {village}, a {n['kwp']} kW solar roof would sell about {n['sold']} kWh a year to the "
                     f"grid under Net-Plus, earning about {c} {n['grid_inc']} lakh in the first year "
                     f"(about {c} {n['per_month']} a month) for the village committee.")
        if uses:
            parts.append(f"The village would also run: {uses}.")
    else:
        if irrigates:
            parts.append(f"In {village}, a {n['kwp']} kW solar array and a {n['pump']} kW pump would replace "
                         f"about {n['diesel']} litres of diesel a year.")
        else:
            parts.append(f"In {village}, a {n['kwp']} kW solar array would power: {uses or 'local loads'}.")
        if irrigates:
            parts.append(f"After irrigation there is about {n['surplus']} kWh of spare electricity a year"
                         + (f", used for: {uses}." if uses else "."))
    parts.append(f"The project costs about {c} {n['capex']} lakh and pays for itself in about {n['pb']} years."
                 if pb else "At these settings the project does not pay for itself.")
    if cpb:
        parts.append(f"The community's own share ({c} {n['share']} lakh) is earned back in about {n['cpb']} years.")
    parts.append(f"It avoids about {n['co2']} tonnes of CO₂ a year.")
    if e["deficit_months"]:
        parts.append(f"Caution: in {', '.join(e['deficit_months'])} the solar pump cannot meet all "
                     "irrigation needs, so a back-up is needed.")
    return " ".join(parts)
