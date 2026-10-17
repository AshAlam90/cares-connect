import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from app_core import auth, store, ui
from app_core.i18n import OPTIONS, opt_label, t
from engine import COUNTRIES

user = auth.current_user()
community = user if user and user["role"] == "community" else None

# ------------------------------------------------------------------ country and language
codes = list(COUNTRIES)
default_cc = (user or {}).get("country") or "LK"
cc = st.segmented_control("Country", codes, format_func=lambda c: COUNTRIES[c]["name"], required=True,
                          default=default_cc, key="local_country")
C = COUNTRIES[cc]
langs = list(C["languages"])
lang = "en"
if len(langs) > 1:
    pick = st.segmented_control("Language / ভাষা", langs, format_func=C["languages"].get, required=True,
                                default="bn" if community and community["language"] == "bn" else "en",
                                key=f"local_lang_{cc}")
    lang = pick or "en"
elif cc == "LK":
    st.caption("Sinhala and Tamil versions are planned, written with local partners.")

st.title(t("title", lang))
st.write(t("intro", lang))
ui.disclaimer()
if community:
    st.caption(f"{t('signed_in_as', lang)}: {community['organisation']}")
elif user and user["role"] == "cares":
    st.info("You're signed in as a CARES unit, so this request will be sent as a field worker "
            "on behalf of a community.")
else:
    st.page_link("views/account.py", icon=":material/login:",
                 label="Sign in as a community to follow your requests on your own dashboard")

# ------------------------------------------------------------------ map pin
st.markdown(f"**{t('map', lang)}**")
pin_key = f"local_pin_{cc}"
pin = st.session_state.get(pin_key)
m = folium.Map(location=list(C["center"]), zoom_start=7, tiles="OpenStreetMap")
if pin:
    folium.Marker(pin, icon=folium.Icon(color="green", icon="home")).add_to(m)
out = st_folium(m, height=380, use_container_width=True, returned_objects=["last_clicked"], key=f"map_{cc}")
if out and out.get("last_clicked"):
    new_pin = [round(out["last_clicked"]["lat"], 4), round(out["last_clicked"]["lng"], 4)]
    if new_pin != pin:
        st.session_state[pin_key] = new_pin
        st.rerun()
if pin:
    st.caption(f"📍 {t('pin_set', lang)}: {pin[0]:.4f}, {pin[1]:.4f}")
with st.expander(t("coords", lang)):
    q1, q2, q3 = st.columns([2, 2, 1])
    (la0, la1), (lo0, lo1) = C["lat_range"], C["lon_range"]
    lat_in = q1.number_input("Latitude", la0, la1, float(pin[0]) if pin else C["center"][0], 0.01, format="%.4f")
    lon_in = q2.number_input("Longitude", lo0, lo1, float(pin[1]) if pin else C["center"][1], 0.01, format="%.4f")
    if q3.button(t("use_coords", lang)):
        st.session_state[pin_key] = [round(lat_in, 4), round(lon_in, 4)]
        st.rerun()

# ------------------------------------------------------------------ form
mine = community if community and community["country"] == cc else None
unit = "বিঘা" if lang == "bn" else C["land_unit"] + "s"
with st.form("request_form", clear_on_submit=False):
    c1, c2, c3 = st.columns(3)
    village = c1.text_input(t("village", lang), value=mine["village"] if mine else "")
    district = c2.selectbox(t("district", lang), C["districts"], placeholder="—",
                            index=C["districts"].index(mine["district"]) if mine and mine["district"] in C["districts"] else None)
    upazila = c3.text_input(t("upazila", lang) if cc == "BD" else "Divisional Secretariat (optional)")

    c4, c5 = st.columns(2)
    households = c4.number_input(t("households", lang), min_value=1, max_value=5000, value=100, step=5)
    area = c5.number_input(f"{t('area', lang).split('(')[0].strip()} ({unit})", min_value=0.0, max_value=5000.0,
                           value=60.0 if cc == "BD" else 10.0, step=1.0,
                           help="Only needed if you are asking for irrigation")

    crops = st.multiselect(t("crops", lang), C["crops"], default=[C["crops"][0]],
                           format_func=lambda v: opt_label("crops", v, lang))
    needs = st.multiselect(t("needs", lang), C["needs"], default=[C["needs"][0]],
                           format_func=lambda v: opt_label("needs", v, lang))

    c6, c7, c8 = st.columns(3)
    water_source = c6.radio(t("water_source", lang), list(C["water_sources"]),
                            format_func=lambda v: opt_label("water_source", v, lang))
    current_pump = c7.radio(t("pump", lang), list(OPTIONS["pump"]), format_func=lambda v: opt_label("pump", v, lang))
    spend = c8.number_input(f"{t('spend', lang).split('(')[0].strip()} ({'টাকা' if lang == 'bn' else C['currency']})", min_value=0,
                            max_value=10_000_000, value=20_000, step=1_000)

    who_opts = list(OPTIONS["who"])
    who_default = (who_opts.index(mine["group_type"]) if mine and mine["group_type"] in who_opts
                   else 3 if user and user["role"] == "cares" else 0)
    who = st.selectbox(t("who", lang), who_opts, index=who_default, format_func=lambda v: opt_label("who", v, lang))
    notes = st.text_area(t("notes", lang), height=80)
    sent = st.form_submit_button(t("submit", lang), type="primary")

if sent:
    if not village.strip() or not district:
        st.error(t("need_village", lang))
    elif not st.session_state.get(pin_key):
        st.error(t("pin_missing", lang))
    else:
        lat, lon = st.session_state[pin_key]
        ref = store.add_request(dict(
            country=cc, village=village.strip(), district=district, upazila=upazila.strip(),
            lat=lat, lon=lon, precision="Marked on the map by the requester", households=int(households),
            area_local=float(area), crops=crops, needs=needs, water_source=water_source, current_pump=current_pump,
            energy_spend_month=float(spend), submitted_by=who, language=lang, notes=notes.strip()),
            user_id=community["id"] if community else None)
        st.session_state.setdefault("my_refs", []).append(ref)
        st.success(f"{t('thanks', lang)} **{ui.bn_digits(ref) if lang == 'bn' else ref}**")
        st.info(t("next", lang))
        if community:
            st.page_link("views/dashboard.py", label=t("dash_title", lang), icon=":material/dashboard:")

# ------------------------------------------------------------------ tracking
st.subheader(t("track", lang))
refs = set(st.session_state.get("my_refs", []))
rows = [p for p in store.list_projects() if (community and p["user_id"] == community["id"]) or p["ref"] in refs]
if not rows:
    st.caption(t("none_yet", lang))
else:
    st.dataframe(pd.DataFrame([{
        t("ref", lang): p["ref"], t("village", lang): p["village"],
        t("status", lang): opt_label("status", p["status"], lang)} for p in rows]), hide_index=True)
