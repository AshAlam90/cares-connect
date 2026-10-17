"""
Real Solar Village sites in Sri Lanka, from public sources only.

Every fact below is taken from the sources listed with it. Where a source does
not give something (system size, households, exact location), it is left out
rather than guessed. Locations are approximate and flagged as such.
Modelled numbers in the app (output, income, payback) are estimates from the
engine, not reported figures.
"""

S = {
    "projects": ("Solar Village SDG - Projects", "https://www.solarvillagesdg.org/projects"),
    "report": ("Solar Village project report (NIFS, 2024)",
               "https://www.nifs.ac.lk/sites/default/files/2024-12/Solar%20village%20project.pdf"),
    "kaduruwewa": ("Solar Village SDG - Kaduruwewa Primary School", "https://www.solarvillagesdg.org/projecto-1"),
    "pulmudai": ("Solar Village SDG - Pulmudai", "https://www.solarvillagesdg.org/projecto-2"),
    "nochchiya": ("Solar Village SDG - Nochchiya", "https://www.solarvillagesdg.org/projecto-3"),
    "puthier": ("Solar Village SDG - Puthier Nagar", "https://www.solarvillagesdg.org/projecto-4"),
    "moneragala": ("Solar Village SDG - Moneragala", "https://www.solarvillagesdg.org/projecto-5"),
    "uoc": ("University of Colombo, Faculty of Technology - Solar Village Project",
            "https://tech.cmb.ac.lk/solar-village-project/"),
    "whatwedo": ("Solar Village SDG - What we do", "https://www.solarvillagesdg.org/services-4"),
    "sun": ("The Sun (Sri Lanka), 7 March 2025",
            "https://www.thesun.lk/fashion/EMPOWERING-RURAL-COMMUNITIES-WITH-RENEWABLE-ENERGY/555-302762l"),
    "strategy": ("Dharmadasa, Solar Energy Strategy for Sri Lanka (SHU Research Archive)",
                 "https://shura.shu.ac.uk/13387/"),
}

PROGRAMME_FACTS = [
    "Pioneered by Emeritus Prof. I. M. Dharmadasa (Sheffield Hallam University); first Solar Village "
    "piloted at Kaduruwewa in 2008 from his own funds.",
    "Now run by Solar Village SDG CIC (UK community interest company, no. 16089126).",
    "A typical 5 kW solar roof costs about Rs 1,200,000 including installation, and produces "
    "500-600 kWh a month.",
    "Under the CEB Net-Plus scheme a roof sells all its output: older contracts Rs 22/unit for 7 years "
    "then Rs 15/unit; newer contracts Rs 37/unit for 20 years (at least Rs 18,500 a month for 5 kW).",
    "Reported simple payback: 3.5-6.0 years. Panels guaranteed 20 years, inverters 10 years.",
    "Each village forms a Village Development Committee (VDC), with equal numbers of women and men "
    "encouraged, a bank account with two signatories, and audited accounts.",
]
PROGRAMME_SOURCES = ["report", "sun", "whatwedo"]

# kw: published roof size (None = not published -> not modelled)
# cost: published cost in Rs (None -> typical Rs 240,000 per kW from the report)
# tariff: (rate, rate_after, switch_year)
SITES = [
    dict(village="Kaduruwewa", district="Kurunegala", lat=7.83, lon=80.27,
         precision="Approximate: Maho area, Kurunegala District", status="Operating", year="2008",
         system="Solar water pumping that replaced a diesel pump (September 2008), with grid electricity "
                "connected to the village school. Size not published.",
         beneficiaries="Village primary school and temple, which receive free tap water.",
         funders="Prof. I. M. Dharmadasa's personal funds (pilot).",
         partners="Government infrastructure, supported by a World Bank project.",
         outcomes=["School enrolment rose from about 20 (closure planned in 2007) to about 85.",
                   "Library and classroom built, much of the labour by parents.",
                   "Year-5 scholarship pass rate above 60%; ranked 2nd of 186 primary schools in the region (2023).",
                   "100,000 mango plants and a few hundred beehive boxes distributed.",
                   "When the pump failed after eight years, VDC savings paid for a replacement and expansion.",
                   "Reported reduction in kidney disease linked to poor water quality."],
         kw=None, cost=None, sources=["whatwedo", "report", "strategy", "sun"]),
    dict(village="Pulmudai", district="Trincomalee", lat=8.93, lon=81.00,
         precision="Assumed: Pulmoddai (Pulmudai), Trincomalee District. The source says only "
                   "'a conflict-affected area in the North'.",
         status="Operating", year=None,
         system="Not published.",
         beneficiaries="Conflict-affected village; aim to rebuild damaged infrastructure and support reconciliation.",
         funders="A retired professional donated Rs 1.5 million (Rs 15 lakhs) from his pension fund.",
         partners="Not published.", outcomes=[], kw=None, cost=None, sources=["pulmudai", "report"]),
    dict(village="Nochchiya", district=None, lat=None, lon=None,
         precision="Location not published (village with water scarcity and human-elephant conflict).",
         status="Operating", year="2017",
         system="7 kW solar roof under Net-Plus (the 'Raja Meehitiya Memorial Solar Village'); two water "
                "pumping systems and a water purification centre run on grid power.",
         beneficiaries="Village cluster of over 1,000 people; purified water sold for a nominal fee to about "
                       "eight surrounding villages.",
         funders="About Rs 18 lakhs, shared by APSL-UK and Hela Sarana.",
         partners="APSL-UK, Hela Sarana. Requested by the villagers in a letter with 104 signatures.",
         outcomes=["VDC savings of over Rs 60 lakhs, with Rs 50 lakhs in a fixed deposit.",
                   "Micro-credit for villagers' new development projects.",
                   "No new kidney-disease (CKDu) cases reported after clean drinking water became available "
                   "(February 2024 interviews).",
                   "Community hall rebuilt; office and library under construction.",
                   "About 300 people repaired the road to the village (February 2024)."],
         kw=7.0, cost=1_800_000, tariff=(22.0, 15.0, 7),
         tariff_note="Assumed: a 2017 contract on the older Net-Plus terms (Rs 22, then Rs 15 after 7 years).",
         sources=["nochchiya", "report", "strategy"]),
    dict(village="Puthier Nagar", district=None, lat=None, lon=None,
         precision="Location not published (area affected by ethnic conflict).",
         status="Operating", year=None,
         system="Not published.",
         beneficiaries="Part of APSL-UK's 'We Sri Lanka' reconciliation project.",
         funders="APSL-UK ('We Sri Lanka' project).",
         partners="APSL and the Foundation of Goodness (FOG).",
         outcomes=["FOG has since stopped its training there because take-up was low."],
         kw=None, cost=None, sources=["puthier", "report"]),
    dict(village="Moneragala (Tissapura Kanishta Vidyalaya)", district="Monaragala", lat=6.87, lon=81.35,
         precision="Approximate: district level. The school is at Ethimalewewa, Monaragala District.",
         status="Operating", year="2021-22",
         system="5 kW solar roof on the school building under Net-Plus; income pays for the school's water "
                "pumps, which serve a school with no well or water line of its own.",
         beneficiaries="More than 225 students, school staff and the surrounding community.",
         funders="About Rs 1,000,000 from Hela Sarana (for its 25th anniversary), through a donor.",
         partners="University of Colombo Faculty of Technology; Hela Sarana; SLAAS Section E1.",
         outcomes=["A share of the grid income (30-35% in different sources) pays for the children's water "
                   "supply and annual prizes; the VDC uses the rest for community development."],
         kw=5.0, cost=1_000_000, tariff=(22.0, 15.0, 7),
         tariff_note="Assumed: a pre-2023 contract on the older Net-Plus terms (Rs 22, then Rs 15 after 7 years).",
         sources=["moneragala", "uoc", "report"]),
    dict(village="Mediyawa", district="Kurunegala", lat=7.86, lon=80.24,
         precision="Approximate: near Maho, Kurunegala District", status="Operating", year="2024",
         system="5 kW solar roof on a community building (installed 10 November 2024). A solar electric "
                "fence against elephants was also planned.",
         beneficiaries="Village facing poverty and human-elephant conflict (two deaths, one a university student).",
         funders="APSL-UK (UK professional charity association); GoFundMe appeal and raffle.",
         partners="Locally coordinated (coordinator named in the report).",
         outcomes=["Beekeeping encouraged as a natural defence against elephants."],
         kw=5.0, cost=None, tariff=(37.0, 37.0, 0),
         tariff_note="Assumed: a 2024 contract on the newer Net-Plus terms (Rs 37 for 20 years).",
         sources=["projects", "report"]),
    dict(village="Kanatholuwa", district="Kurunegala", lat=7.49, lon=80.37,
         precision="Approximate: district level (Kurunegala District)", status="Operating", year="2025",
         system="5 kW solar roof, completed March 2025.",
         beneficiaries="Village selected by the National Science Foundation (NSF).",
         funders="Regen Renewables Ltd donated the roof from its CSR programme.",
         partners="National Science Foundation; Sarvodaya (three-day shramadana camp); Wayamba University.",
         outcomes=[], kw=5.0, cost=None, tariff=(37.0, 37.0, 0),
         tariff_note="Assumed: a 2025 contract on the newer Net-Plus terms (Rs 37 for 20 years).",
         sources=["projects", "report"]),
    dict(village="Sobithagama", district="Anuradhapura", lat=8.50, lon=80.32,
         precision="Approximate: about 16 miles from Anuradhapura on the Tantirimale road",
         status="Funded", year=None,
         system="Planned: 5 kW solar roof with water purification (first step), a solar pump for an "
                "agro-well, and support for a hospital roof.",
         beneficiaries="Settlement of families affected by the tsunami and the conflict; drought-prone.",
         funders="A British family, through their own charity.",
         partners="The village monk requested the agro-well.",
         outcomes=[], kw=5.0, cost=None, tariff=(37.0, 37.0, 0),
         tariff_note="Assumed: newer Net-Plus terms (Rs 37 for 20 years). Roof only is modelled.",
         sources=["projects", "report"]),
    dict(village="Panama", district="Ampara", lat=6.76, lon=81.80,
         precision="Approximate: Panama village, Ampara District", status="Operating", year=None,
         system="Three 5 kW solar roofs on three schools (Sinhala primary, Tamil primary and a shared "
                "secondary school), feeding the grid; CEB pays the VDC account quarterly.",
         beneficiaries="Mixed Sinhala and Tamil community; aims to support reconciliation.",
         funders="Helios Renewable Energy Foundation (report). A British family also supported the schools and "
                 "connected the project to an international charitable foundation (website).",
         partners="Education Director (permission); local supervision.",
         outcomes=["A transparent, gender-balanced Village Development Committee was set up.",
                   "Grid income is intended to fund community development."],
         kw=15.0, cost=None, tariff=(37.0, 37.0, 0),
         tariff_note="Assumed: newer Net-Plus terms (Rs 37 for 20 years).",
         sources=["projects", "report"]),
]

# Sites the programme says it is exploring (no village or coordinator confirmed yet)
PROPOSED = [
    dict(district="Jaffna", lat=9.66, lon=80.02),
    dict(district="Puttalam", lat=8.03, lon=79.83),
    dict(district="Batticaloa", lat=7.73, lon=81.69),
    dict(district="Monaragala", lat=7.02, lon=81.28, place="Medagama"),
]
PROPOSED_SOURCES = ["projects", "report"]
