import streamlit as st

from app_core import auth, store, ui
from engine import COUNTRIES
from engine.addons import CATALOG, AddonSpec

st.title("Funders: back a project")
st.write("Projects here were designed by a local CARES unit. Compare them by cost and impact, see exactly where "
         "the money goes, check the track record of the real solar villages, and pledge support.")
ui.disclaimer()

user = auth.current_user()
funder = user if user and user["role"] == "funder" else None
interests = (funder or {}).get("interests") or {}
want_d, want_s = set(interests.get("districts") or []), set(interests.get("solutions") or [])
if funder:
    st.caption(f"Signed in as **{funder['organisation']}** · projects matching your interests are marked ⭐")
else:
    st.page_link("views/account.py", icon=":material/login:",
                 label="Sign in as a funder to pledge and track your impact on your own dashboard")

projects = store.list_projects()
open_projects = [p for p in projects if p["status"] in store.OPEN_STATUSES and p["results"]]
track = [p for p in projects if p["status"] in ("Funded", "Operating")]


def gap(p):
    return max(0.0, p["results"]["finance"]["funder_total"] - p["pledged"])


def solution_text(p):
    d = p["design"]
    parts = []
    if d["grid_scheme"] == "net_plus":
        parts.append(f"{d['pv']['kwp']:g} kW Net-Plus solar roof")
    elif d["area_ha"] > 0:
        parts.append(f"{d['pv']['kwp']:g} kW solar irrigation pump")
    else:
        parts.append(f"{d['pv']['kwp']:g} kW solar array")
    if d["area_ha"] > 0 and d["grid_scheme"] == "net_plus":
        parts.append("solar irrigation")
    parts += [CATALOG[a["key"]].name.split(" (")[0].lower() for a in d["addons"]]
    return " + ".join(parts)


tab_open, tab_track = st.tabs([f"Seeking funding ({len(open_projects)})", f"Track record ({len(track)})"])

with tab_open:
    if not open_projects:
        st.info("No projects are seeking funding right now. A CARES unit can design and publish one.")
    else:
        f1, f2, f3 = st.columns([2, 2, 2])
        countries = sorted({p["country"] for p in open_projects})
        pick_c = f1.multiselect("Country", countries, format_func=lambda c: COUNTRIES[c]["name"], placeholder="All")
        pick_d = f2.multiselect("District", sorted({p["district"] for p in open_projects}), placeholder="All districts")
        sort_by = f3.selectbox("Sort by", ["Lowest cost per tonne of CO₂", "Lowest cost per household",
                                           "Quickest payback", "Smallest funding gap"])
        rows = [p for p in open_projects if (not pick_c or p["country"] in pick_c) and (not pick_d or p["district"] in pick_d)]
        key_fn = {
            "Lowest cost per tonne of CO₂": lambda p: ui.to_gbp(p["results"]["impact"]["grant_per_t_co2"] or 1e18, p["country"]),
            "Lowest cost per household": lambda p: ui.to_gbp(p["results"]["impact"]["grant_per_household"] or 1e18, p["country"]),
            "Quickest payback": lambda p: p["results"]["finance"]["simple_payback"] or 1e18,
            "Smallest funding gap": lambda p: ui.to_gbp(gap(p), p["country"]),
        }[sort_by]
        rows.sort(key=key_fn)

        m1, m2, m3 = st.columns(3)
        m1.metric("Projects shown", len(rows))
        m2.metric("Still to raise", f"≈ £{sum(ui.to_gbp(gap(p), p['country']) for p in rows):,.0f}",
                  help="Converted to pounds at assumed exchange rates")
        m3.metric("CO₂ avoided if all go ahead", f"{sum(p['results']['impact']['co2_t'] for p in rows):,.1f} t/yr")

        cols = st.columns(2)
        for idx, p in enumerate(rows):
            F, I = p["results"]["finance"], p["results"]["impact"]
            cc, target = p["country"], F["funder_total"]
            money = lambda x, cc=cc: ui.fmt_money(x, cc)
            with cols[idx % 2], st.container(border=True):
                star = " ⭐" if funder and (p["district"] in want_d or want_s & set(p["needs"])) else ""
                st.markdown(f"#### {ui.place(p)}{star}")
                st.caption(f"{ui.status_badge(p['status'])} · {p['ref']} · {COUNTRIES[cc]['name']} · "
                           f"Designed by {p['cares_unit']}")
                if p["kind"] == "real":
                    st.caption("An area the real Solar Village programme is exploring. This design is indicative, "
                               "made by a fictional demo CARES unit.")
                st.markdown(f"**Solution:** {solution_text(p)}")
                st.progress(min(1.0, p["pledged"] / target) if target else 0.0,
                            text=f"{money(p['pledged'])} pledged of {money(target)} ({ui.fmt_gbp(target, cc)})")
                a, b, c = st.columns(3)
                a.metric("Households", f"{p['households']}" if p["households"] else "TBC",
                         help=None if p["households"] else "To be confirmed with the community")
                b.metric("CO₂ avoided", f"{I['co2_t']:.1f} t/yr")
                c.metric("Payback", ui.fmt_years(F["simple_payback"]))
                st.markdown(
                    (f"Grid income for the village **{money(F['grid_income_year1'])}** a year · "
                     if F["grid_income_year1"] else "")
                    + (f"Grant per household **{money(I['grant_per_household'])}** · " if I["grant_per_household"] else "")
                    + f"Grant per tonne of CO₂ over its life **{money(I['grant_per_t_co2'])}**")
                st.caption(ui.sdg_text(I["sdgs"]) + f" · Women on committee: {I['women_share_committee']:.0%}")
                with st.expander("Where the money goes"):
                    st.markdown(
                        f"- Funders' share of equipment ({p['design']['finance']['funder_grant_share']:.0%}): **{money(F['grant'])}**\n"
                        f"- CARES design & facilitation fee: **{money(F['cares_design_fee'])}**\n"
                        f"- Community's own share: **{money(F['community_share'])}**"
                        + (f", earned back in about {ui.fmt_years(F['community_payback'])}" if F["community_share"] else ""))
                    st.plotly_chart(ui.energy_chart(p["results"]["monthly"], [AddonSpec(**a) for a in p["design"]["addons"]],
                                                    {a["key"]: CATALOG[a["key"]].name.split(" (")[0] for a in p["design"]["addons"]},
                                                    p["design"]["grid_scheme"]),
                                    theme=None, key=f"chart_{p['id']}")
                if funder:
                    with st.form(f"pledge_{p['id']}", border=False):
                        top = int(max(1_000, gap(p)))
                        amount = st.number_input(f"Pledge from {funder['organisation']} ({COUNTRIES[cc]['currency']})",
                                                 min_value=1_000, max_value=top, step=10_000, format="%d",
                                                 value=min(top, max(1_000, int(round(gap(p) / 2, -3)))))
                        if st.form_submit_button("Pledge support", type="primary"):
                            status = store.add_pledge(p["id"], funder["organisation"], funder["funder_type"], amount,
                                                      user_id=funder["id"])
                            st.toast(f"Thank you! {p['village']} is now: {status}.")
                            st.rerun()
                else:
                    st.caption("Sign in as a funder to pledge.")

with tab_track:
    st.write("Completed and funded projects. Real solar villages show who actually funded them, from public sources.")
    cols = st.columns(2)
    for idx, p in enumerate(track):
        f = p["facts"] or {}
        with cols[idx % 2], st.container(border=True):
            st.markdown(f"**{ui.place(p) if p['district'] else p['village'] + ' · district not published'}**")
            st.caption(f"{'🔨 Funded, being built' if p['status'] == 'Funded' else ui.status_badge(p['status'])}"
                       f"{' · since ' + p['year'] if p.get('year') else ''}")
            if p["kind"] == "real":
                st.markdown(f"**Funded by:** {f.get('funders') or 'Not published.'}")
                if f.get("outcomes"):
                    st.markdown("\n".join(f"- {o}" for o in f["outcomes"][:3]))
                st.caption("Sources: " + ui.sources_md(f.get("sources")))
            else:
                backers = ", ".join(x["funder"] for x in store.pledges_for(p["id"]))
                st.markdown(f"**Backed by (demo):** {backers or '—'}")
