import pandas as pd
import streamlit as st

from app_core import auth, store, ui
from app_core.i18n import STEPS, t
from app_core.summary import summary
from engine import COUNTRIES

user = auth.current_user()
if not user:
    st.title("My dashboard")
    st.info("Sign in to see your dashboard. Demo profiles are ready for all three fronts, "
            "or you can register your own.")
    st.page_link("views/account.py", label="Sign in or register", icon=":material/login:")
    st.stop()

projects = store.list_projects()
by_id = {p["id"]: p for p in projects}


def funding_share(p: dict) -> float:
    if p["status"] == "Operating":
        return 1.0
    target = p["results"]["finance"]["funder_total"] if p["results"] else 0
    return min(1.0, p["pledged"] / target) if target else 0.0


# ====================================================================== community
def community_dashboard(u: dict) -> None:
    cc = u["country"] or "LK"
    langs = COUNTRIES[cc]["languages"]
    lang = "en"
    if len(langs) > 1:
        lang = st.segmented_control("Language / ভাষা", list(langs), format_func=langs.get, required=True,
                                    key="dash_lang", default=u["language"] if u["language"] in langs else "en") or "en"
    num = ui.bn_digits if lang == "bn" else str

    st.title(t("dash_title", lang))
    st.caption(f"{t('signed_in_as', lang)}: {u['organisation']} · {u['district']}, {COUNTRIES[cc]['name']}")
    ui.disclaimer()

    mine = [p for p in projects if p["user_id"] == u["id"]]
    m1, m2, m3 = st.columns(3)
    m1.metric(t("m_requests", lang), num(len(mine)))
    m2.metric(t("m_designed", lang), num(sum(1 for p in mine if p["design"])))
    m3.metric(t("m_funded", lang), num(sum(1 for p in mine if p["status"] in ("Funded", "Operating"))))

    if not mine:
        st.caption(t("no_requests", lang))
    for p in reversed(mine):
        pc = p["country"]
        with st.container(border=True):
            st.markdown(f"#### {p['village']} · {p['ref']}")
            step = store.STATUSES.index(p["status"])
            cols = st.columns(6)
            for i, label in enumerate(STEPS[lang]):
                cols[i].markdown(f"{'✅' if i <= step else '⬜'} {label}")   # icon + text, never colour alone
            if p["design"]:
                F, I = p["results"]["finance"], p["results"]["impact"]
                a, b, c, d = st.columns(4)
                a.metric(t("total_cost", lang), ui.fmt_money_lang(F["capex"], pc, lang))
                b.metric(t("your_share", lang), ui.fmt_money_lang(F["community_share"], pc, lang))
                cpb = F["community_payback"]
                c.metric(t("earn_back", lang), f"{num(f'{cpb:.1f}')} {t('years', lang)}" if cpb else "—",
                         help=None if cpb else "Funders pay for all the equipment, so the community has nothing to earn back")
                if p["design"]["grid_scheme"] == "net_plus":
                    d.metric("Grid income per year", ui.fmt_money(F["grid_income_year1"], pc))
                else:
                    d.metric(t("diesel_saved", lang), f"{num(format(I['diesel_l'], ',.0f'))} {t('litres', lang)}")
                if p["status"] in ("Published", "Partly funded", "Funded"):
                    st.progress(funding_share(p), text=f"{t('funding', lang)}: "
                                f"{ui.fmt_money_lang(p['pledged'], pc, lang)} / {ui.fmt_money_lang(F['funder_total'], pc, lang)}")
                st.info(summary(p["village"], p["design"], p["results"], lang))
                st.caption(f"{t('designed_by', lang)}: {p['cares_unit']}")
            else:
                st.caption(t("waiting", lang))
    if st.button(t("new_request", lang), type="primary", icon=":material/add:"):
        st.switch_page("views/local.py")


# ====================================================================== CARES
def cares_dashboard(u: dict) -> None:
    cov = set(u["coverage"] or [])
    cc = u["country"] or "LK"
    st.title(u["organisation"])
    st.caption(f"CARES unit dashboard · {COUNTRIES[cc]['name']} · Districts covered: "
               + (", ".join(sorted(cov)) if len(cov) < 12 else f"all {len(cov)}"))
    ui.disclaimer()

    in_area = lambda p: p["country"] == cc and p["district"] in cov
    queue = [p for p in projects if p["status"] == "New request" and in_area(p)]
    ours = [p for p in projects if p["cares_user_id"] == u["id"]]
    real_here = [p for p in projects if p["kind"] == "real" and p["status"] in ("Operating", "Funded") and in_area(p)]
    count = lambda *s: sum(1 for p in ours if p["status"] in s)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("New requests in your districts", len(queue), border=True)
    m2.metric("Drafts not yet published", count("Designed"), border=True)
    m3.metric("Seeking funding", count("Published", "Partly funded"), border=True)
    m4.metric("Real solar villages in your area", len(real_here), border=True)

    st.subheader("Requests waiting for you")
    if not queue:
        st.caption("No new requests in your districts.")
    for p in queue:
        with st.container(border=True):
            a, b, c, d = st.columns([3, 2, 3, 2], vertical_alignment="center")
            a.markdown(f"**{p['village']}**, {p['district']}  \n{p['ref']} · received {p['created']}")
            unit = COUNTRIES[p["country"]]["land_unit"]
            b.markdown((f"{p['households']} households" if p["households"] else "Households to confirm")
                       + (f"  \n{p['area_local']:g} {unit}s" if p["area_local"] else ""))
            c.markdown(f"Needs: {', '.join(p['needs'])}  \nFrom: {p['submitted_by']}")
            if d.button("Open in design tool", key=f"open_{p['id']}", type="primary"):
                st.session_state["cares_open"] = p["id"]
                st.switch_page("views/cares.py")
    others = sum(1 for p in projects if p["status"] == "New request" and not in_area(p))
    if others:
        st.caption(f"{others} new request(s) are in areas covered by other CARES units.")

    st.subheader("Your projects")
    if not ours:
        st.caption("You haven't designed any projects yet.")
    else:
        df = pd.DataFrame([{
            "Ref": p["ref"], "Village": p["village"], "District": p["district"], "Status": ui.status_badge(p["status"]),
            "Equipment": ui.fmt_money(p["results"]["finance"]["capex"], p["country"]),
            "Funding": funding_share(p),
            "Payback (yrs)": round(p["results"]["finance"]["simple_payback"] or 0, 1),
            "CO₂ avoided (t/yr)": round(p["results"]["impact"]["co2_t"], 1)} for p in ours])
        st.dataframe(df, hide_index=True, column_config={
            "Funding": st.column_config.ProgressColumn("Funding", min_value=0, max_value=1, format="percent")})
        c1, c2 = st.columns([3, 1], vertical_alignment="bottom")
        pick = c1.selectbox("Open one of your projects", [p["id"] for p in ours],
                            format_func=lambda i: f"{by_id[i]['ref']} · {by_id[i]['village']}")
        if c2.button("Open in design tool", key="open_ours"):
            st.session_state["cares_open"] = pick
            st.switch_page("views/cares.py")

    if real_here:
        st.subheader("Real solar villages in your area")
        st.caption("Learn from these when designing: " + " · ".join(
            f"{p['village']} ({p['status'].lower()}{', ' + p['year'] if p.get('year') else ''})" for p in real_here))

    st.subheader("Income that keeps your unit running")
    fin = lambda s: [(p["results"]["finance"], p["country"]) for p in ours if p["status"] in s]
    tot = lambda pairs, key: sum(ui.to_gbp(f[key], c) for f, c in pairs)
    i1, i2, i3 = st.columns(3)
    i1.metric("Design fees earned (funded)", f"≈ £{tot(fin(('Funded', 'Operating')), 'cares_design_fee'):,.0f}")
    i2.metric("Design fees in the pipeline", f"≈ £{tot(fin(('Published', 'Partly funded')), 'cares_design_fee'):,.0f}")
    i3.metric("Yearly support share (funded)", f"≈ £{tot(fin(('Funded', 'Operating')), 'cares_mgmt_year1'):,.0f}")
    st.caption("The CARES model: funders pay a design and facilitation fee, and each project shares a small part "
               "of its yearly benefit so the unit can keep supporting the community after installation.")


# ====================================================================== funder
def funder_dashboard(u: dict) -> None:
    interests = u["interests"] or {}
    st.title(u["organisation"])
    bits = [u["funder_type"]]
    if interests.get("districts"):
        bits.append("Districts: " + ", ".join(interests["districts"]))
    if interests.get("solutions"):
        bits.append("Interested in: " + ", ".join(interests["solutions"]))
    st.caption("Funder dashboard · " + " · ".join(bits))
    ui.disclaimer()

    pledges = store.pledges_by_user(u["id"])
    mine: dict[int, float] = {}
    for x in pledges:
        mine[x["project_id"]] = mine.get(x["project_id"], 0) + x["amount"]
    backed = [by_id[i] for i in mine]
    total_gbp = sum(ui.to_gbp(mine[p["id"]], p["country"]) for p in backed)
    share = {p["id"]: mine[p["id"]] / p["results"]["finance"]["funder_total"] for p in backed}
    co2_share = sum(share[p["id"]] * p["results"]["impact"]["co2_t"] for p in backed)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total pledged", f"≈ £{total_gbp:,.0f}", help="Pledges in Rs and Tk converted at assumed rates", border=True)
    m2.metric("Projects backed", len(backed), border=True)
    m3.metric("Households in projects you back", f"{sum(p['households'] for p in backed):,}" if backed else "0",
              border=True, help="Only where the household count is known")
    m4.metric("Your share of CO₂ avoided", f"{co2_share:.1f} t/yr", border=True,
              help="Each project's CO₂ saving multiplied by your share of the money it asked funders for")

    st.subheader("Your pledges")
    if not pledges:
        st.caption("No pledges yet. See the recommendations below.")
    else:
        st.dataframe(pd.DataFrame([{
            "Date": x["created"], "Village": by_id[x["project_id"]]["village"],
            "District": by_id[x["project_id"]]["district"],
            "Your pledge": ui.fmt_money(x["amount"], by_id[x["project_id"]]["country"]),
            "Project status": ui.status_badge(by_id[x["project_id"]]["status"]),
            "Project funded": funding_share(by_id[x["project_id"]])} for x in pledges]),
            hide_index=True, column_config={
                "Project funded": st.column_config.ProgressColumn(min_value=0, max_value=1, format="percent")})
        sdgs = sorted({s for p in backed for s in p["results"]["impact"]["sdgs"]})
        st.caption("Your portfolio contributes to: " + ui.sdg_text(sdgs))

    st.subheader("Recommended for you")
    want_d, want_s = set(interests.get("districts") or []), set(interests.get("solutions") or [])
    open_p = [p for p in projects if p["status"] in store.OPEN_STATUSES and p["results"]]
    match = [p for p in open_p if (not want_d and not want_s) or p["district"] in want_d or want_s & set(p["needs"])]
    match.sort(key=lambda p: ui.to_gbp(p["results"]["impact"]["grant_per_t_co2"] or 1e18, p["country"]))
    if not match:
        st.caption("No open projects match your interests right now. Browse them all on the funders page.")
    for p in match[:3]:
        F, I, pc = p["results"]["finance"], p["results"]["impact"], p["country"]
        why = ([p["district"]] if p["district"] in want_d else []) + sorted(want_s & set(p["needs"]))
        with st.container(border=True):
            a, b = st.columns([4, 1], vertical_alignment="center")
            a.markdown(f"**{ui.place(p)}** · {ui.status_badge(p['status'])}  \n"
                       f"Still needs {ui.fmt_money(max(0, F['funder_total'] - p['pledged']), pc)} · "
                       f"{I['co2_t']:.1f} t CO₂/yr · {ui.fmt_money(I['grant_per_t_co2'], pc)} per tonne"
                       + (f"  \nMatches: {', '.join(why)}" if why else ""))
            if b.button("View and pledge", key=f"rec_{p['id']}"):
                st.switch_page("views/funders.py")
    st.page_link("views/villages.py", label="See the track record of the real solar villages",
                 icon=":material/solar_power:")


{"community": community_dashboard, "cares": cares_dashboard, "funder": funder_dashboard}[user["role"]](user)
