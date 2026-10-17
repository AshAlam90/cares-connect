"""English / Bangla text for the community-facing pages.

The Bangla wording is a first draft and must be checked by a native speaker
(ideally by partners who work with the communities) before any real use.
"""

T = {
    "title": {"en": "Tell us what your community needs",
              "bn": "আপনার এলাকার প্রয়োজনের কথা জানান"},
    "intro": {"en": "Fill this in yourself, or ask a CARES field worker to fill it in with you. "
                    "There is no charge for asking.",
              "bn": "নিজে পূরণ করুন, অথবা CARES মাঠকর্মীর সাহায্য নিন। আবেদন করতে কোনো খরচ নেই।"},
    "map": {"en": "Tap the map to mark your village",
            "bn": "মানচিত্রে ট্যাপ করে আপনার গ্রাম চিহ্নিত করুন"},
    "pin_set": {"en": "Location marked", "bn": "অবস্থান চিহ্নিত হয়েছে"},
    "pin_missing": {"en": "Please tap the map to mark your village.",
                    "bn": "অনুগ্রহ করে মানচিত্রে আপনার গ্রাম চিহ্নিত করুন।"},
    "coords": {"en": "Map not loading? Type the location instead",
               "bn": "মানচিত্র দেখা যাচ্ছে না? অবস্থান লিখে দিন"},
    "use_coords": {"en": "Use this location", "bn": "এই অবস্থান নিন"},
    "village": {"en": "Village name", "bn": "গ্রামের নাম"},
    "district": {"en": "District", "bn": "জেলা"},
    "upazila": {"en": "Upazila (optional)", "bn": "উপজেলা (ঐচ্ছিক)"},
    "households": {"en": "Number of households", "bn": "পরিবারের সংখ্যা"},
    "area": {"en": "Land that needs irrigation (bigha)", "bn": "সেচের প্রয়োজন এমন জমি (বিঘা)"},
    "crops": {"en": "Main crops", "bn": "প্রধান ফসল"},
    "needs": {"en": "What do you need?", "bn": "আপনার কী প্রয়োজন?"},
    "water_source": {"en": "Where does irrigation water come from?", "bn": "সেচের পানি কোথা থেকে আসে?"},
    "pump": {"en": "Current irrigation pump", "bn": "বর্তমান সেচ পাম্প"},
    "spend": {"en": "Diesel spending per month in the dry season (Tk)",
              "bn": "শুকনো মৌসুমে মাসিক ডিজেল খরচ (টাকা)"},
    "who": {"en": "Who is filling in this form?", "bn": "কে এই ফর্ম পূরণ করছেন?"},
    "notes": {"en": "Anything else we should know?", "bn": "আর কিছু জানাতে চান?"},
    "submit": {"en": "Send request", "bn": "আবেদন পাঠান"},
    "need_village": {"en": "Please enter the village name and choose the district.",
                     "bn": "অনুগ্রহ করে গ্রামের নাম লিখুন এবং জেলা বেছে নিন।"},
    "thanks": {"en": "Thank you! Your request number is", "bn": "ধন্যবাদ! আপনার আবেদন নম্বর"},
    "next": {"en": "What happens next: a CARES team from a local university will review your request "
                   "and visit your community to understand your needs.",
             "bn": "এরপর কী হবে: স্থানীয় বিশ্ববিদ্যালয়ের একটি CARES দল আপনার আবেদন পর্যালোচনা করবে "
                   "এবং আপনার প্রয়োজন বুঝতে আপনার এলাকা পরিদর্শন করবে।"},
    "track": {"en": "Track your requests", "bn": "আপনার আবেদনের অবস্থা"},
    "none_yet": {"en": "You haven't sent a request in this session yet.",
                 "bn": "এই সেশনে আপনি এখনো কোনো আবেদন পাঠাননি।"},
    "ref": {"en": "Request", "bn": "আবেদন"},
    "status": {"en": "Status", "bn": "অবস্থা"},
}

T.update({
    "dash_title": {"en": "Your community's requests", "bn": "আপনার এলাকার আবেদনসমূহ"},
    "welcome": {"en": "Welcome", "bn": "স্বাগতম"},
    "m_requests": {"en": "Requests sent", "bn": "পাঠানো আবেদন"},
    "m_designed": {"en": "Designed by CARES", "bn": "CARES নকশা করেছে"},
    "m_funded": {"en": "Fully funded", "bn": "পূর্ণ অর্থায়িত"},
    "designed_by": {"en": "Designed by", "bn": "নকশা করেছে"},
    "total_cost": {"en": "Total cost", "bn": "মোট খরচ"},
    "your_share": {"en": "Your community's share", "bn": "আপনার এলাকার অংশ"},
    "earn_back": {"en": "Earned back in", "bn": "উঠে আসবে"},
    "diesel_saved": {"en": "Diesel saved per year", "bn": "বছরে ডিজেল সাশ্রয়"},
    "years": {"en": "years", "bn": "বছরে"},
    "litres": {"en": "litres", "bn": "লিটার"},
    "funding": {"en": "Funding", "bn": "অর্থায়ন"},
    "waiting": {"en": "A CARES team will contact you to arrange a visit.",
                "bn": "একটি CARES দল পরিদর্শনের জন্য আপনার সাথে যোগাযোগ করবে।"},
    "new_request": {"en": "Send a new request", "bn": "নতুন আবেদন পাঠান"},
    "no_requests": {"en": "No requests yet.", "bn": "এখনো কোনো আবেদন নেই।"},
    "signed_in_as": {"en": "Signed in as", "bn": "সাইন ইন করেছেন"},
})

STEPS = {
    "en": ["Request sent", "Designed by CARES", "Shared with funders", "Funding coming in", "Fully funded",
           "Operating"],
    "bn": ["আবেদন পাঠানো হয়েছে", "CARES নকশা করেছে", "অর্থদাতাদের কাছে প্রকাশিত", "অর্থ আসছে", "পূর্ণ অর্থায়িত",
           "চালু আছে"],
}

OPTIONS = {
    "crops": {"Boro rice": "বোরো ধান", "Aman rice": "আমন ধান", "Wheat": "গম", "Maize": "ভুট্টা",
              "Potato": "আলু", "Vegetables": "শাকসবজি", "Jute": "পাট"},
    "needs": {"Irrigation": "সেচ", "Drinking water": "নিরাপদ খাবার পানি", "Cold storage": "হিমাগার (কোল্ড স্টোরেজ)",
              "Grain milling": "ধান/ভুট্টা ভাঙানো", "E-rickshaw charging": "ইজিবাইক চার্জিং"},
    "water_source": {"Groundwater": "ভূগর্ভস্থ পানি (নলকূপ)", "Surface water": "ভূপৃষ্ঠের পানি (নদী/খাল/পুকুর)"},
    "pump": {"Diesel": "ডিজেল", "Electric": "বিদ্যুৎ", "None": "নেই"},
    "who": {"Community member": "গ্রামবাসী", "Village Development Committee": "গ্রাম উন্নয়ন কমিটি",
            "Farmers' cooperative": "কৃষক সমবায়",
            "CARES field worker on behalf of the community": "সম্প্রদায়ের পক্ষে CARES মাঠকর্মী"},
    "status": {"New request": "নতুন আবেদন", "Designed": "নকশা তৈরি হয়েছে",
               "Published": "অর্থায়নের জন্য প্রকাশিত", "Partly funded": "আংশিক অর্থায়িত",
               "Funded": "পূর্ণ অর্থায়িত", "Operating": "চালু আছে"},
}


def t(key: str, lang: str) -> str:
    return T[key].get(lang, T[key]["en"])


def opt_label(group: str, value: str, lang: str) -> str:
    """Bangla label where one exists; otherwise the English value (Sri Lankan options are English for now)."""
    return OPTIONS.get(group, {}).get(value, value) if lang == "bn" else value
