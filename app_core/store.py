"""
Tiny SQLite store for user profiles, requests, designs and pledges.

Seed data: the real Solar Village sites in Sri Lanka (app_core/real_sites.py,
public sources only) plus clearly fictional demo profiles for signing in.
On a free cloud host the file resets when the app restarts. A production
system would use a managed database, a secure login provider and a
data-protection plan for personal information.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path

from engine import COUNTRIES, defaults_for, design_to_dict, fallback_climate, run_design
from engine.addons import default_addons_for_needs
from engine.irrigation import pattern_from_crops
from engine.model import suggest_system

from . import real_sites as RS

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "cares.db"

STATUSES = ["New request", "Designed", "Published", "Partly funded", "Funded", "Operating"]
OPEN_STATUSES = ("Published", "Partly funded")
ROLES = {"community": "Community", "cares": "CARES unit", "funder": "Funder"}
FUNDER_TYPES = ["Corporation (CSR)", "SME", "NGO / charity", "Development bank", "Government", "Individual"]
LK_CENTER = COUNTRIES["LK"]["center"]

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role TEXT, name TEXT, organisation TEXT, country TEXT,
    village TEXT, district TEXT, group_type TEXT,
    coverage TEXT, funder_type TEXT, interests TEXT,
    language TEXT, created TEXT
);
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ref TEXT, created TEXT, country TEXT, kind TEXT,
    village TEXT, district TEXT, upazila TEXT, lat REAL, lon REAL, precision TEXT, year TEXT,
    households INTEGER, area_local REAL, crops TEXT, needs TEXT,
    water_source TEXT, current_pump TEXT, energy_spend_month REAL,
    submitted_by TEXT, language TEXT, notes TEXT, facts TEXT,
    status TEXT, cares_unit TEXT,
    design TEXT, results TEXT, designed_at TEXT, published_at TEXT,
    user_id INTEGER, cares_user_id INTEGER
);
CREATE TABLE IF NOT EXISTS pledges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER, funder TEXT, funder_type TEXT, amount REAL, created TEXT,
    user_id INTEGER
);
"""

JSON_FIELDS = ("crops", "needs", "design", "results", "facts")
USER_JSON_FIELDS = ("coverage", "interests")


def _conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH, check_same_thread=False)
    con.row_factory = sqlite3.Row
    return con


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def _row(r: sqlite3.Row, fields=JSON_FIELDS) -> dict:
    d = dict(r)
    for k in fields:
        d[k] = json.loads(d[k]) if d.get(k) else None
    return d


def init_db() -> None:
    with _conn() as con:
        con.executescript(SCHEMA)
        cols = {r[1] for r in con.execute("PRAGMA table_info(projects)").fetchall()}
        n = con.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
    if "facts" not in cols:                 # database from an older version
        reset_db()
        return
    if n == 0:
        seed()


def reset_db() -> None:
    if DB_PATH.exists():
        DB_PATH.unlink()
    init_db()


# ------------------------------------------------------------------ users
def add_user(role: str, name: str, organisation: str, *, country: str = "LK", village: str = "",
             district: str = "", group_type: str = "", coverage: list[str] | None = None,
             funder_type: str = "", interests: dict | None = None, language: str = "en") -> int:
    assert role in ROLES
    with _conn() as con:
        cur = con.execute(
            """INSERT INTO users (role, name, organisation, country, village, district, group_type, coverage,
               funder_type, interests, language, created) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (role, name, organisation, country, village, district, group_type, json.dumps(coverage or []),
             funder_type, json.dumps(interests or {}), language, _now()))
        return cur.lastrowid


def list_users(role: str | None = None) -> list[dict]:
    with _conn() as con:
        rows = (con.execute("SELECT * FROM users WHERE role=? ORDER BY id", (role,)) if role
                else con.execute("SELECT * FROM users ORDER BY role, id")).fetchall()
    return [_row(r, USER_JSON_FIELDS) for r in rows]


def get_user(uid: int | None) -> dict | None:
    if uid is None:
        return None
    with _conn() as con:
        r = con.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
    return _row(r, USER_JSON_FIELDS) if r else None


# ------------------------------------------------------------------ requests and projects
def _insert_project(p: dict, status: str = "New request", kind: str = "user", user_id: int | None = None) -> int:
    with _conn() as con:
        cur = con.execute(
            """INSERT INTO projects (created, country, kind, village, district, upazila, lat, lon, precision, year,
               households, area_local, crops, needs, water_source, current_pump, energy_spend_month,
               submitted_by, language, notes, facts, status, cares_unit, user_id)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (_now(), p.get("country", "LK"), kind, p["village"], p.get("district"), p.get("upazila", ""),
             p.get("lat"), p.get("lon"), p.get("precision", ""), p.get("year"),
             p.get("households", 0), p.get("area_local", 0), json.dumps(p.get("crops", [])),
             json.dumps(p.get("needs", [])), p.get("water_source", ""), p.get("current_pump", ""),
             p.get("energy_spend_month", 0), p.get("submitted_by", ""), p.get("language", "en"),
             p.get("notes", ""), json.dumps(p["facts"]) if p.get("facts") else None, status,
             p.get("cares_unit"), user_id))
        pid = cur.lastrowid
        con.execute("UPDATE projects SET ref=? WHERE id=?", (f"CC-{pid:04d}", pid))
    return pid


def add_request(req: dict, user_id: int | None = None) -> str:
    pid = _insert_project(req, "New request", "user", user_id)
    return f"CC-{pid:04d}"


def list_projects() -> list[dict]:
    with _conn() as con:
        rows = con.execute("SELECT * FROM projects ORDER BY id").fetchall()
        pledged = dict(con.execute("SELECT project_id, SUM(amount) FROM pledges GROUP BY project_id").fetchall())
    out = []
    for r in rows:
        d = _row(r)
        d["pledged"] = pledged.get(d["id"], 0.0) or 0.0
        out.append(d)
    return out


def get_project(pid: int) -> dict | None:
    return next((p for p in list_projects() if p["id"] == pid), None)


def save_design(pid: int, design: dict, results: dict, publish: bool, cares_unit: str | None,
                cares_user_id: int | None = None) -> None:
    with _conn() as con:
        status = con.execute("SELECT status FROM projects WHERE id=?", (pid,)).fetchone()[0]
        if publish and status in ("New request", "Designed"):
            status = "Published"
        elif not publish and status == "New request":
            status = "Designed"
        con.execute(
            """UPDATE projects SET design=?, results=?, designed_at=?, status=?,
               cares_unit=COALESCE(?, cares_unit), cares_user_id=COALESCE(?, cares_user_id),
               published_at=COALESCE(published_at, CASE WHEN ? THEN ? END) WHERE id=?""",
            (json.dumps(design), json.dumps(results), _now(), status, cares_unit, cares_user_id,
             1 if publish else 0, _now(), pid))


# ------------------------------------------------------------------ pledges
def pledges_for(pid: int) -> list[dict]:
    with _conn() as con:
        return [dict(r) for r in con.execute("SELECT * FROM pledges WHERE project_id=? ORDER BY id", (pid,))]


def pledges_by_user(uid: int) -> list[dict]:
    with _conn() as con:
        return [dict(r) for r in con.execute("SELECT * FROM pledges WHERE user_id=? ORDER BY id", (uid,))]


def add_pledge(pid: int, funder: str, funder_type: str, amount: float, user_id: int | None = None) -> str:
    with _conn() as con:
        con.execute("""INSERT INTO pledges (project_id, funder, funder_type, amount, created, user_id)
                       VALUES (?,?,?,?,?,?)""", (pid, funder, funder_type, amount, _now(), user_id))
        total = con.execute("SELECT SUM(amount) FROM pledges WHERE project_id=?", (pid,)).fetchone()[0]
        res = json.loads(con.execute("SELECT results FROM projects WHERE id=?", (pid,)).fetchone()[0])
        status = "Funded" if total >= res["finance"]["funder_total"] - 1 else "Partly funded"
        con.execute("UPDATE projects SET status=? WHERE id=?", (status, pid))
    return status


# ------------------------------------------------------------------ designs
def model_point(p: dict) -> tuple[float, float, str]:
    """Where to take the climate from: the site, or the country centre if not published."""
    if p.get("lat") is not None and p.get("lon") is not None:
        return p["lat"], p["lon"], ""
    c = COUNTRIES[p["country"]]
    return c["center"][0], c["center"][1], f"Location not published: modelled with {c['name']}'s central climate."


def default_design_for(p: dict):
    """Starting design a CARES engineer would refine, built from the request."""
    cc = p.get("country") or "LK"
    c = COUNTRIES[cc]
    lat, lon, _ = model_point(p)
    needs = p.get("needs") or []
    irrigate = c["irrigation_need"] in needs
    area_ha = round((p.get("area_local") or 0) * c["ha_per_land_unit"], 1) if irrigate else 0.0
    pattern = pattern_from_crops(p.get("crops") or [], cc) if area_ha > 0 else "none"
    head = c["water_sources"].get(p.get("water_source"), list(c["water_sources"].values())[0])
    di = defaults_for(cc, lat, lon, households=p.get("households") or 0, area_ha=area_ha, pattern=pattern,
                      head_m=head, addons=default_addons_for_needs(needs, cc),
                      women_share_committee=0.5 if cc == "LK" else 0.4)
    if area_ha > 0:
        di.pump_kw, di.pv.kwp = suggest_system(area_ha, pattern, head)
    else:
        di.pump_kw = 0.0
    if cc == "LK":
        roof = c["grid_need"] in needs
        di.grid_scheme = "net_plus" if roof else "export_surplus"
        di.pv.kwp = max(di.pv.kwp if area_ha > 0 else 0.0, 5.0)
        di.costs.controller_replacement_cost = 75_000 * di.pv.kwp
    return di


def as_built_design(site: dict):
    """Engine model of a real site from its published size, cost and (assumed) tariff."""
    lat, lon, _ = model_point({**site, "country": "LK"})
    rate, after, switch = site["tariff"]
    di = defaults_for("LK", lat, lon, households=0, area_ha=0.0, pattern="none", pump_kw=0.0,
                      grid_scheme="net_plus", grid_tariff=rate, grid_tariff_after=after,
                      grid_tariff_switch_year=switch, women_share_committee=0.5)
    di.pv.kwp = site["kw"]
    if site.get("cost"):
        di.costs.pv_per_kwp = site["cost"] / site["kw"]
    di.costs.controller_replacement_cost = 75_000 * site["kw"]
    di.finance.funder_grant_share = 1.0          # donor-funded
    di.finance.cares_design_fee = 0.0
    di.finance.cares_mgmt_share = 0.0
    return di


def cares_unit_for(district: str | None, country: str = "LK") -> dict | None:
    return next((u for u in list_users("cares")
                 if u["country"] == country and district in (u["coverage"] or [])), None)


# ------------------------------------------------------------------ seed data
DEMO_CARES = [  # FICTIONAL demo units, not real universities
    dict(organisation="Demo CARES unit · North Central & North Western (fictional)", country="LK",
         coverage=["Anuradhapura", "Kurunegala", "Puttalam", "Polonnaruwa", "Matale"]),
    dict(organisation="Demo CARES unit · North & East (fictional)", country="LK",
         coverage=["Jaffna", "Kilinochchi", "Mullaitivu", "Vavuniya", "Mannar", "Trincomalee",
                   "Batticaloa", "Ampara"]),
    dict(organisation="Demo CARES unit · Uva & South (fictional)", country="LK",
         coverage=["Monaragala", "Badulla", "Hambantota", "Ratnapura", "Matara", "Galle"]),
    dict(organisation="Demo CARES unit · Bangladesh (fictional)", country="BD",
         coverage=list(COUNTRIES["BD"]["districts"])),
]
DEMO_FUNDERS = [  # FICTIONAL
    dict(organisation="Example Apparel PLC CSR fund (fictional)", funder_type="Corporation (CSR)",
         interests={"districts": ["Puttalam", "Kurunegala"], "solutions": ["Drinking water"]}),
    dict(organisation="Example Diaspora Giving Circle (fictional)", funder_type="Individual",
         interests={"districts": ["Jaffna", "Batticaloa", "Trincomalee"], "solutions": []}),
    dict(organisation="Example Climate Foundation (fictional)", funder_type="NGO / charity",
         interests={"districts": [], "solutions": ["Community income from a solar roof"]}),
    dict(organisation="Example Agri-Finance SME (fictional)", funder_type="SME",
         interests={"districts": [], "solutions": ["Irrigation", "Cold storage", "E-rickshaw charging"]}),
]
DEMO_COMMUNITIES = [  # FICTIONAL
    dict(organisation="Demo village committee (fictional)", country="LK", village="Demo village",
         district="Puttalam", group_type="Village Development Committee", language="en"),
    dict(organisation="Demo community (fictional)", country="BD", village="Demo gram",
         district="Kushtia", group_type="Farmers' cooperative", language="bn"),
]


def _facts(site: dict, sources: list[str]) -> dict:
    return {"system": site.get("system"), "beneficiaries": site.get("beneficiaries"),
            "funders": site.get("funders"), "partners": site.get("partners"),
            "outcomes": site.get("outcomes", []), "tariff_note": site.get("tariff_note"),
            "kw": site.get("kw"), "cost": site.get("cost"),
            "sources": [list(RS.S[k]) for k in sources]}


def seed() -> None:
    for c in DEMO_CARES:
        add_user("cares", "CARES coordinator (demo)", c["organisation"], country=c["country"],
                 coverage=c["coverage"])
    for f in DEMO_FUNDERS:
        add_user("funder", "Demo funder contact", f["organisation"], country="LK",
                 funder_type=f["funder_type"], interests=f["interests"])
    for m in DEMO_COMMUNITIES:
        add_user("community", "Committee secretary (demo)", m["organisation"], country=m["country"],
                 village=m["village"], district=m["district"], group_type=m["group_type"], language=m["language"])

    # Real Solar Village sites (public sources)
    for s in RS.SITES:
        pid = _insert_project(dict(country="LK", village=s["village"], district=s["district"], lat=s["lat"],
                                   lon=s["lon"], precision=s["precision"], year=s["year"], households=0,
                                   needs=["Community income from a solar roof"] if s["kw"] else [],
                                   submitted_by="Solar Village programme", facts=_facts(s, s["sources"]),
                                   cares_unit="Solar Village programme (real site)"),
                              status=s["status"], kind="real")
        if s["kw"]:
            p = get_project(pid)
            lat, lon, note = model_point(p)
            di = as_built_design(s)
            res = run_design(di, fallback_climate(lat, lon, note, country="LK"))
            with _conn() as con:
                con.execute("UPDATE projects SET design=?, results=?, designed_at=? WHERE id=?",
                            (json.dumps(design_to_dict(di)), json.dumps(res), _now(), pid))

    # Districts the programme is exploring (village not yet chosen)
    for i, prop in enumerate(RS.PROPOSED):
        place = prop.get("place")
        pid = _insert_project(dict(
            country="LK", village=f"Proposed solar village · {place or prop['district']}",
            district=prop["district"], lat=prop["lat"], lon=prop["lon"],
            precision="Approximate: district or town level. Site and coordinator not yet confirmed.",
            households=0, needs=["Community income from a solar roof"],
            submitted_by="Solar Village programme (exploring this area)",
            notes="Needs, village and coordinator to be confirmed with the community.",
            facts={"system": "Not yet designed.", "outcomes": [],
                   "sources": [list(RS.S[k]) for k in RS.PROPOSED_SOURCES]}), "New request", "real")
        # Two indicative designs by fictional demo CARES units, so the funder flow can be tried
        if prop["district"] in ("Puttalam", "Jaffna"):
            p = get_project(pid)
            unit = cares_unit_for(p["district"], "LK")
            needs = ["Community income from a solar roof"] + (["Drinking water"] if prop["district"] == "Puttalam" else [])
            di = default_design_for({**p, "needs": needs})
            res = run_design(di, fallback_climate(p["lat"], p["lon"], country="LK"))
            save_design(pid, design_to_dict(di), res, publish=prop["district"] == "Puttalam",
                        cares_unit=unit["organisation"], cares_user_id=unit["id"])
            with _conn() as con:
                con.execute("UPDATE projects SET needs=? WHERE id=?", (json.dumps(needs), pid))
