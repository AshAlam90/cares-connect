# CARES Connect

**Connecting rural communities, local university experts and funders, built on the real Solar Village model in Sri Lanka.**

A working prototype of a three-sided decision support tool for community solar energy, in Python with Streamlit. It is seeded with the real Solar Village sites in Sri Lanka (from public sources), and the same engine also designs solar irrigation hubs in Bangladesh.

> **Independent prototype.** Real Solar Village sites come from public sources, linked in the app and below. Modelled figures are estimates. Sign-in profiles and pledges are fictional demo data. Not an official Solar Village SDG product.

**Live demo:** _[CARES_Connect](https://cares-connect-solarvillagesdg.streamlit.app/)_ 
---

## The idea

Since 2008, solar villages in Sri Lanka have shown what a small solar asset can do when a community controls the income. The technology is not the hard part. The hard part is connecting three groups:

| Front | Who | What they do in the app |
|---|---|---|
| **Communities** | Village Development Committees, cooperatives, farmers | Describe their needs (water, income, irrigation, schooling, protection from elephants), on a phone or with a field worker |
| **CARES** | *Centres for Application of Renewable Energy Sources*: local university units with local and technical knowledge | Size the system, test the business case, publish a costed project |
| **Funders** | Company CSR budgets, diaspora givers, NGOs, development banks, government | Compare projects by cost and impact, check the track record, pledge |

A fourth view gives **government and planners** the national picture and a replication scenario.

The CARES concept builds on a social-enterprise model I co-developed with colleagues at Sheffield Hallam University and the University of Liberal Arts Bangladesh (ULAB). In that model, CARES units are paid by a commission from funders and a small share of the wealth each project creates.

## Real sites included

From public sources: Kaduruwewa (pilot, 2008), Pulmudai, Nochchiya (2017), Puthier Nagar, Moneragala (Tissapura Kanishta Vidyalaya, 2021-22), Mediyawa (2024), Kanatholuwa (2025), Sobithagama (being built) and Panama. Four areas the programme says it is exploring (Jaffna, Puttalam, Batticaloa, Medagama) appear as district-level requests.

Rules followed:
- **Only published facts.** System sizes, households and exact locations are left out where a source does not give them.
- **Not modelled without a size.** Sites without a published system size are not modelled.
- **Locations are approximate** and each one says how precise it is.
- **Assumed tariffs are flagged.** Where a site's Net-Plus contract terms are not published, the assumption is stated.
- **No invented money from real funders.** Real funders appear only as published history. No pledges are attributed to real organisations; all demo funders, CARES units and communities are marked *fictional*.

## Checking the model against field reports

The Solar Village report says a 5 kW roof produces 500-600 kWh a month, earns at least Rs 18,500 a month at Rs 37/unit, and pays back in 3.5-6.0 years.

| Measure | Reported | Textbook model (14% losses) | Calibrated model (26% losses) |
|---|---|---|---|
| Output, 5 kW roof (kWh/month) | 500-600 | about 640 | about 550 |
| Net-Plus income at Rs 37 (Rs/month) | at least 18,500 | about 23,700 | about 20,400 |
| Simple payback, Rs 1.2 m roof (years) | 3.5-6.0 | 4.4 | 5.1 |

With textbook losses the model over-predicts by about 16%. That points to real-world losses such as roof orientation, shading, dust, heat and grid downtime, so Sri Lankan designs use the calibrated value. With metered data, each roof could be calibrated individually.

## What the prototype shows

1. **Real solar villages.** Map, facts, reported outcomes, sources, and the model check above.
2. **Communities** (Sri Lanka in English, Bangladesh in English or Bangla). Request form with a map pin, local districts and land units (acres or bigha), and a personal dashboard with a progress tracker.
3. **CARES units.** A queue of requests in their districts. The design tool covers:
   - live NASA POWER sunshine data;
   - tilted-panel physics;
   - irrigation (optional);
   - productive uses (clean water, smart classroom, elephant fence, cold storage, milling, e-rickshaw charging);
   - grid options (off-grid, sell surplus, or Sri Lanka's Net-Plus with older and newer tariff terms);
   - costs, payback, NPV, a sensitivity table and a plain-language summary.

   Real sites open as locked *as-built* models.
4. **Funders.** Open projects with transparent cost breakdowns, a track-record tab of the real sites, pledging, and a dashboard with their share of impact in pounds across currencies.
5. **Overview & scenarios.**
   - **Sri Lanka:** what a national programme of N village roofs would cost and earn, and how payback depends on the Net-Plus tariff.
   - **Bangladesh:** how a subsidy changes community payback for solar irrigation hubs.

## Where the numbers come from

All numbers come from one pure-Python engine in `engine/`, kept separate from the screens. The single entry point is `engine.model.run_design()`. It can be tested on its own, reused in other tools, or called by an AI assistant that explains results without ever calculating them.

| Step | Method |
|---|---|
| Solar resource | NASA POWER monthly climatology; approximate built-in values per country if offline |
| Sunshine on a tilted panel | Klein (1977) monthly method; Erbs et al. (1982) diffuse fraction; isotropic sky |
| Panel temperature | NOCT model with the energy-weighted irradiance of a half-sine day; -0.4%/°C |
| Irrigation | Monthly irrigation depths per cropping pattern; hydraulic energy ρgVH; wire-to-water efficiency |
| Grid | Off-grid; sell surplus; or Net-Plus (all output sold, loads bought back), with tariff changes over time |
| Money | 20-year cash flow: diesel or grid income, productive-use income, upkeep, inverter replacement in year 10, CARES fees, discounting |
| CO₂ | Diesel replaced (2.68 kg/L) plus grid electricity displaced in Sri Lanka (assumed 0.6 kg/kWh) |

**Sri Lanka figures from the Solar Village report:** a 5 kW roof costs Rs 1.2 m installed; a 5 kW inverter costs Rs 375,000; Net-Plus pays Rs 37/unit, or Rs 22 then Rs 15 on older contracts; upkeep is cleaning only.

**Everything else is an illustrative assumption,** listed in `engine/countries.py` and `engine/addons.py`. That includes productive-use costs and incomes, the buying price of electricity, diesel prices and exchange rates.

### Known limitations

- **Monthly energy balance only.** It ignores timing within the day; off-grid night loads would need batteries.
- **Approximate locations;** two real sites have no published location and use central climate.
- **Languages.** Sinhala and Tamil are not yet included; the Bangla text needs checking by a native speaker.
- **Demo sign-in only.** There are no passwords, and refreshing the browser signs you out. The data store resets when a free host restarts.

## Sources

- Solar Village SDG, Projects: https://www.solarvillagesdg.org/projects (and the individual project pages)
- Solar Village project report (NIFS, 2024): https://www.nifs.ac.lk/sites/default/files/2024-12/Solar%20village%20project.pdf
- University of Colombo, Faculty of Technology, Solar Village Project: https://tech.cmb.ac.lk/solar-village-project/
- The Sun (Sri Lanka), 7 March 2025: https://www.thesun.lk/fashion/EMPOWERING-RURAL-COMMUNITIES-WITH-RENEWABLE-ENERGY/555-302762l
- Dharmadasa, Solar Energy Strategy for Sri Lanka: https://shura.shu.ac.uk/13387/

## Run it locally

```bash
pip install -r requirements.txt
streamlit run app.py
pytest              # 26 tests: physics, finance, Net-Plus, field calibration, real-site data rules, full cycle
```

## Put it online (free, about 10 minutes)

1. Create a new **public** GitHub repository and upload everything in this folder.
2. Go to **share.streamlit.io**, sign in with GitHub, choose **Create app**, pick the repository and set the main file to `app.py`.
3. Deploy. Live NASA POWER data then replaces the built-in values.

## Project structure

```
app.py                 navigation, sign-in switcher and setup
views/                 one file per screen (home, villages, dashboard, account, local, cares, funders, overview)
engine/                the calculation engine: no user interface code
  countries.py         Sri Lanka and Bangladesh settings (costs, tariffs, units, districts, climate fallback)
  solar.py             NASA POWER, tilted-panel irradiation, panel temperature, PV output
  irrigation.py        water need, pumping energy, diesel equivalence
  addons.py            productive uses of solar power
  model.py             energy balance (incl. Net-Plus), finance, impact, run_design()
app_core/
  real_sites.py        the real Solar Village sites, facts and sources
  store.py             data store, profiles, seeding
  ...                  sign-in, charts and formats, translations, summaries, cached climate
tests/                 pytest tests
```

## Roadmap

- **Work with the Solar Village programme and partner universities** to confirm locations and add metered output, VDC accounts and outcome data for each site.
- **Sinhala and Tamil versions** written with local partners, plus SMS or WhatsApp intake for communities.
- **Per-site calibration** from meter readings, and hourly modelling with batteries.
- **Secure accounts, verified organisations,** consent for personal data, and an audit trail for pledges.
- **Monitoring module** for the indicators communities care about: water, school results, income, health, savings.
- **AI assistant** that answers questions in local languages by calling `run_design()`.

## Licence

MIT. See `LICENSE`.
