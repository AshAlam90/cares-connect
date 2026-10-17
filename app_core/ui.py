"""Shared look-and-feel: colours, number formats, charts and small widgets."""
from __future__ import annotations

import os

import plotly.graph_objects as go
import streamlit as st

from engine import COUNTRIES
from engine.solar import MONTHS

DISCLAIMER = ("Independent prototype. Real Solar Village sites come from public sources (linked); "
              "modelled figures are estimates; sign-in profiles and pledges are fictional demo data. "
              "Not an official Solar Village SDG product.")

# Map tiles (override only for offline screenshots)
MAP_STYLE = os.environ.get("CC_MAP_STYLE", "carto-positron")

# Categorical slots (validated: dataviz palette, adjacent order; light + dark steps)
_SLOTS = {
    "light": ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"],
    "dark": ["#3987e5", "#d95926", "#199e70", "#c98500", "#d55181", "#008300", "#9085e9", "#e66767"],
}
_INK = {
    "light": dict(primary="#0b0b0b", secondary="#52514e", muted="#898781", grid="#e1e0d9",
                  axis="#c3c2b7", neutral="#c3c2b7", surface="#fcfcfb"),
    "dark": dict(primary="#f0efec", secondary="#c3c2b7", muted="#898781", grid="#2c2c2a",
                 axis="#383835", neutral="#52514e", surface="#1a1a19"),
}
# Colour follows the entity, everywhere in the app (within a country no two share a slot)
ENTITY_SLOT = {"irrigation": 0, "cold_storage": 1, "cold_storage_lk": 1, "erickshaw": 2, "fence": 2,
               "mill": 3, "classroom": 3, "water": 4, "water_lk": 4, "grid": 6}
# Ordinal ramp for the six pipeline stages (one hue, light -> dark, from step 250)
STAGE_RAMP = {"light": ["#86b6ef", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"],
              "dark": ["#184f95", "#1c5cab", "#256abf", "#3987e5", "#6da7ec", "#9ec5f4"]}


def mode() -> str:
    try:
        return "dark" if st.context.theme.type == "dark" else "light"
    except Exception:
        return "light"


def slot(i: int) -> str:
    return _SLOTS[mode()][i]


def entity_color(key: str) -> str:
    return slot(ENTITY_SLOT.get(key, 7))


def ink(name: str) -> str:
    return _INK[mode()][name]


def stage_colors() -> list[str]:
    return STAGE_RAMP[mode()]


# ------------------------------------------------------------------ formats
def cur(country: str) -> str:
    return COUNTRIES[country]["currency"]


def fmt_money(x: float | None, country: str = "LK") -> str:
    """Local currency in lakh / crore, as used in both Sri Lanka and Bangladesh."""
    if x is None:
        return "—"
    c = cur(country)
    a = abs(x)
    if a >= 1e7:
        return f"{c} {x / 1e7:.2f} crore"
    if a >= 1e5:
        return f"{c} {x / 1e5:.1f} lakh"
    return f"{c} {x:,.0f}"


def fmt_money_lang(x: float | None, country: str, lang: str = "en") -> str:
    """Bangla words and digits for Bangladesh (e.g. ২৮.১ লাখ টাকা); otherwise as fmt_money."""
    s = fmt_money(x, country)
    if lang != "bn" or x is None or country != "BD":
        return s
    s = s.replace("Tk ", "").replace(" crore", " কোটি").replace(" lakh", " লাখ")
    return bn_digits(s) + " টাকা"


def to_gbp(x: float, country: str) -> float:
    return x / COUNTRIES[country]["gbp_rate"]


def fmt_gbp(x: float | None, country: str = "LK") -> str:
    return "—" if x is None else f"≈ £{to_gbp(x, country):,.0f}"


def fmt_years(y: float | None) -> str:
    return "Not within lifetime" if y is None else f"{y:.1f} years"


_BN_DIGITS = str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯")


def bn_digits(s: str) -> str:
    return str(s).translate(_BN_DIGITS)


# ------------------------------------------------------------------ charts
def base_layout(fig: go.Figure, title: str, y_title: str, height: int = 340) -> go.Figure:
    fig.update_layout(
        title=dict(text=title, font=dict(size=15, color=ink("primary")), x=0, xanchor="left",
                   yref="container", y=0.98, yanchor="top"),
        height=height, margin=dict(l=72, r=16, t=96, b=40),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Noto Sans, system-ui, -apple-system, Segoe UI, sans-serif", color=ink("secondary"), size=12),
        legend=dict(orientation="h", yref="container", yanchor="top", y=0.89, xanchor="left", x=0,
                    font=dict(color=ink("secondary"))),
        hovermode="x unified", bargap=0.25,
    )
    fig.update_xaxes(showgrid=False, linecolor=ink("axis"), tickfont=dict(color=ink("muted")))
    fig.update_yaxes(title=dict(text=y_title, font=dict(color=ink("muted")), standoff=10), gridcolor=ink("grid"),
                     automargin=True,
                     zeroline=True, zerolinecolor=ink("axis"), tickfont=dict(color=ink("muted")))
    return fig


def sun_chart(climate: dict, poa: list[float]) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=MONTHS, y=climate["ghi"], name="On flat ground",
                             mode="lines+markers", line=dict(width=2, color=slot(0)),
                             marker=dict(size=8), hovertemplate="%{y:.2f} kWh/m²/day"))
    fig.add_trace(go.Scatter(x=MONTHS, y=poa, name="On the tilted panel",
                             mode="lines+markers", line=dict(width=2, color=slot(1)),
                             marker=dict(size=8), hovertemplate="%{y:.2f} kWh/m²/day"))
    return base_layout(fig, "Daily sunshine by month", "kWh per m² per day", 300)


def _bar(fig, y, name, color):
    fig.add_trace(go.Bar(x=MONTHS, y=y, name=name, hovertemplate="%{y:,.0f} kWh",
                         marker=dict(color=color, line=dict(width=2, color=ink("surface")))))


def energy_chart(monthly: list[dict], addons: list, labels: dict, scheme: str = "none") -> go.Figure:
    """Where each month's solar energy goes, and what the village needs."""
    fig = go.Figure()
    if scheme == "net_plus":
        _bar(fig, [r["grid_export_kwh"] for r in monthly], "Solar output sold to the grid", entity_color("grid"))
        if any(r["grid_import_kwh"] > 0 for r in monthly):
            fig.add_trace(go.Scatter(x=MONTHS, y=[r["grid_import_kwh"] for r in monthly],
                                     name="Village loads bought from the grid", mode="lines+markers",
                                     line=dict(width=2, color=ink("primary")), marker=dict(size=8),
                                     hovertemplate="%{y:,.0f} kWh"))
        return base_layout(fig, "Net-Plus: every solar unit is sold; loads are bought back", "kWh per month", 360)
    if any(r["pump_demand_kwh"] > 0 for r in monthly):
        _bar(fig, [r["pump_served_kwh"] for r in monthly], "Irrigation pump", entity_color("irrigation"))
    for a in addons:
        _bar(fig, [r[f"addon:{a.key}"] for r in monthly], labels.get(a.key, a.name), entity_color(a.key))
    if any(r["grid_export_kwh"] > 0 for r in monthly):
        _bar(fig, [r["grid_export_kwh"] for r in monthly], "Sold to the grid", entity_color("grid"))
    _bar(fig, [r["unused_kwh"] for r in monthly], "Unused surplus", ink("neutral"))
    if any(r["pump_demand_kwh"] > 0 for r in monthly):
        fig.add_trace(go.Scatter(x=MONTHS, y=[r["pump_demand_kwh"] for r in monthly], name="Pump needs",
                                 mode="lines+markers", line=dict(width=2, color=ink("primary")),
                                 marker=dict(size=8, color=ink("primary")), hovertemplate="%{y:,.0f} kWh"))
    fig.update_layout(barmode="stack")
    return base_layout(fig, "Where the solar energy goes each month", "kWh per month", 380)


def cashflow_chart(cumulative: list[float], capex: float, country: str = "LK") -> go.Figure:
    c = cur(country)
    years = list(range(0, len(cumulative) + 1))
    values = [v / 1e5 for v in [-capex] + cumulative]          # lakh
    fig = go.Figure(go.Scatter(x=years, y=values, name="Running total", mode="lines+markers",
                               line=dict(width=2, color=slot(0)), marker=dict(size=8),
                               hovertemplate=f"Year %{{x}}: {c} %{{y:,.1f}} lakh<extra></extra>"))
    fig.add_hline(y=0, line=dict(color=ink("axis"), width=1))
    fig.update_xaxes(title=dict(text="Year", font=dict(color=ink("muted"))), dtick=2)
    fig = base_layout(fig, "Running total of money: spent upfront, then earned back", f"{c} lakh", 300)
    fig.update_layout(showlegend=False, hovermode="closest", margin=dict(t=56))
    return fig


# ------------------------------------------------------------------ widgets
def disclaimer() -> None:
    st.caption(f"ⓘ {DISCLAIMER}")


STATUS_ICON = {"New request": "🆕", "Designed": "📐", "Published": "📣", "Partly funded": "🟡",
               "Funded": "✅", "Operating": "🌞"}
# Badge colour + icon per stage. Yellow (the sun) is kept for what is already working.
STATUS_STYLE = {"New request": ("gray", ":material/fiber_new:"),
                "Designed": ("violet", ":material/architecture:"),
                "Published": ("blue", ":material/campaign:"),
                "Partly funded": ("orange", ":material/hourglass_top:"),
                "Funded": ("green", ":material/construction:"),
                "Operating": ("yellow", ":material/wb_sunny:")}


def status_text(status: str) -> str:
    """Plain text with an emoji, for tables (where markdown badges don't render)."""
    return f"{STATUS_ICON.get(status, '•')} {status}"


def status_label(p: dict) -> str:
    if p["status"] == "Funded" and p.get("kind") == "real":
        return "Funded, being built"
    return p["status"]


def status_badge(status: str, label: str | None = None) -> str:
    """Markdown badge, e.g. ':yellow-badge[:material/wb_sunny: Operating]'."""
    color, icon = STATUS_STYLE.get(status, ("gray", ":material/circle:"))
    return f":{color}-badge[{icon} {label or status}]"


def badge(text: str, color: str = "gray", icon: str | None = None) -> str:
    text = text.replace("[", "(").replace("]", ")")
    return f":{color}-badge[{icon + ' ' if icon else ''}{text}]"


def badges(*items: str) -> None:
    """One row of markdown badges."""
    st.markdown(" ".join(i for i in items if i))


def card(key: str, **kw):
    """A bordered container with a solid background (styled by its key in inject_css)."""
    return st.container(border=True, key=f"card_{key}", **kw)


def big_number(value: str, label: str) -> None:
    st.html(f'<div class="cc-big">{value}</div><div class="cc-big-label">{label}</div>')


def inject_css() -> None:
    dark = mode() == "dark"
    card_bg = "#18211d" if dark else "#ffffff"
    card_shadow = "none" if dark else "0 1px 2px rgba(22,58,99,.06), 0 4px 14px rgba(22,58,99,.05)"
    st.html(f"""
<style>
/* page width and rhythm */
[data-testid="stMainBlockContainer"] {{ max-width: 1240px; padding-top: 4.2rem; padding-bottom: 2rem; }}
h1 {{ color: {'#e8f0ea' if dark else '#163A63'}; letter-spacing: -0.015em; }}
h2, h3 {{ color: {'#e8f0ea' if dark else '#163A63'}; }}
/* solid cards on the tinted page */
div[class*="st-key-card_"] {{ background: {card_bg}; box-shadow: {card_shadow}; }}
[data-testid="stMetric"], [data-testid="stForm"] {{ background: {card_bg}; }}
/* hero band: the one bold element */
.st-key-hero {{ background: #163A63; border-radius: 1.1rem; padding: 2.4rem 2.4rem 2rem;
  background-image: radial-gradient(circle at 92% 8%, rgba(242,183,5,.28), rgba(242,183,5,0) 38%); }}
.st-key-hero h1 {{ color: #ffffff; font-size: 2.9rem; line-height: 1.1; margin-bottom: .2rem; }}
.st-key-hero p, .st-key-hero li {{ color: #dbe6f2; }}
.st-key-hero [data-testid="stCaptionContainer"] p {{ color: #a9bdd4; }}
.st-key-lede p {{ font-size: 1.22rem; color: #ffffff !important; }}
.st-key-hero button[kind="secondary"] {{ background: rgba(255,255,255,.08); color: #fff; border-color: rgba(255,255,255,.45); }}
.st-key-hero button[kind="secondary"]:hover {{ background: rgba(255,255,255,.16); border-color: #fff; color: #fff; }}
.st-key-hero [data-testid="stPlotlyChart"] {{ border-radius: .8rem; overflow: hidden; }}
.cc-eyebrow {{ display: inline-block; font-size: .8rem; font-weight: 700; letter-spacing: .06em; text-transform: uppercase;
  color: #F2B705; margin-bottom: .4rem; }}
/* big evidence numbers */
.cc-big {{ font-size: 2.3rem; font-weight: 800; line-height: 1.1; color: {'#F2B705' if dark else '#1E6B3C'}; }}
.cc-big-label {{ font-size: .95rem; font-weight: 600; margin-top: .25rem; color: {'#e8f0ea' if dark else '#163A63'}; }}
/* step numbers on the home page */
.cc-step {{ display: inline-flex; align-items: center; justify-content: center; width: 2.1rem; height: 2.1rem;
  border-radius: 50%; background: #F2B705; color: #163A63; font-weight: 800; font-size: 1.05rem; }}
/* account menu sits in the header, top right */
.st-key-account_bar {{ position: fixed; top: .6rem; right: 3.4rem; z-index: 1000001; width: auto !important; }}
.st-key-account_bar button {{ background: {card_bg}; }}
/* footer */
.st-key-footer {{ margin-top: 2.5rem; padding-top: 1rem; border-top: 1px solid {'#2c3a33' if dark else '#CFDAD2'}; }}
@media (max-width: 640px) {{
  [data-testid="stMainBlockContainer"] {{ padding-left: 1rem; padding-right: 1rem; padding-top: 3.6rem; }}
  .st-key-account_bar {{ position: static; }}
  /* KPI strips: two per row on phones instead of one tall stack */
  div[class*="st-key-kpis"] [data-testid="stHorizontalBlock"] {{ flex-wrap: wrap; flex-direction: row; gap: .6rem; }}
  div[class*="st-key-kpis"] [data-testid="stColumn"] {{ min-width: calc(50% - .4rem) !important; flex: 1 1 calc(50% - .4rem) !important; width: calc(50% - .4rem) !important; }}
  div[class*="st-key-kpis"] [data-testid="stMetricValue"] {{ font-size: 1.25rem; }}
  [data-testid="stMetric"] {{ padding: .75rem .8rem; }}
  .st-key-hero {{ padding: 1.5rem 1.2rem; }}
  .st-key-hero h1 {{ font-size: 2.1rem; }}
}}
</style>""")


SDG_NAMES = {1: "No poverty", 2: "Zero hunger", 3: "Good health", 4: "Quality education",
             5: "Gender equality", 6: "Clean water", 7: "Clean energy", 8: "Decent work",
             9: "Industry & innovation", 11: "Sustainable communities", 12: "Responsible consumption",
             13: "Climate action", 15: "Life on land"}


def sdg_text(sdgs: list[int]) -> str:
    return " · ".join(f"SDG {s} {SDG_NAMES.get(s, '')}".strip() for s in sdgs)


def place(p: dict) -> str:
    """'Village · District', without repeating the district when the name already contains it."""
    d = p.get("district")
    if not d or d in p["village"]:
        return p["village"]
    return f"{p['village']} · {d}"


def short_name(p: dict) -> str:
    """Name to use in sentences: 'a proposed village in Jaffna' rather than the placeholder title."""
    if p["village"].startswith("Proposed"):
        return f"a proposed village in {p.get('district')}"
    return p["village"]


def sources_md(sources: list[list[str]] | None) -> str:
    return " · ".join(f"[{t}]({u})" for t, u in (sources or []))
