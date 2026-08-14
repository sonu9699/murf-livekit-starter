"""Triage, eligibility, and vaccination schedule guidelines for Aarogya Saathi.

Provides rules and Hinglish/Devanagari verbal responses representing standard public
health guidance (Universal Immunization Programme and Socio-Economic criteria).
"""

import re

# High-risk symptoms for RED triage level (emergency)
_RED_KEYWORDS = [
    r"saans.*takleef",
    r"saans.*phool",
    r"trouble.*breath",
    r"breath",
    r"chest.*pain",
    r"seene.*dard",
    r"blood",
    r"khoon",
    r"bleeding",
    r"paralysis",
    r"lakwa",
    r"fits",
    r"daura",
    r"unconscious",
    r"behosh",
    r"pregnancy",
    r"delivery",
]

_RED_RE = re.compile("|".join(_RED_KEYWORDS), re.IGNORECASE)


def classify_triage(symptoms: str, duration_days: int) -> str:
    """Classify user symptoms to RED, YELLOW, or GREEN triage level.

    Returns Hinglish advice based on August 2026 health guidelines.
    """
    if not symptoms:
        return "मुझे आपके symptoms समझ नहीं आए। कृपया अपनी तकलीफ़ दोबारा बताएं।"

    clean_symptoms = symptoms.lower().strip()

    # Check RED level (Emergency symptoms)
    if _RED_RE.search(clean_symptoms):
        return (
            "August 2026 guidelines के अनुसार, यह गंभीर Emergency हो सकती है। "
            "तुरंत नज़दीकी सरकारी अस्पताल या doctor के पास जाएँ, या 108 helpline पर call करें।"
        )

    # Check YELLOW level (Persistent/moderate symptoms)
    # E.g. fever for more than 3 days, or sugar/BP complications
    is_moderate = (
        "fever" in clean_symptoms
        or "bukhar" in clean_symptoms
        or "ताप" in clean_symptoms
    ) and duration_days >= 3

    if (
        is_moderate
        or "sugar" in clean_symptoms
        or "bp" in clean_symptoms
        or "blood pressure" in clean_symptoms
    ):
        return (
            "August 2026 guidelines के अनुसार, आपको doctor को दिखाना चाहिए। "
            "कृपया 1-2 दिन में नज़दीकी PHC या clinic जाकर checkup करवा लें।"
        )

    # Check GREEN level (Mild symptoms)
    return (
        "August 2026 guidelines के अनुसार, यह mild symptom लग रहा है। "
        "भरपूर आराम करें, पानी या ORS घोल पीते रहें, और आराम न मिलने पर doctor से मिलें।"
    )


def check_ayushman(
    rural_household: bool, has_pucca_house: bool, landless_manual_labor: bool
) -> str:
    """Check Ayushman Bharat PM-JAY eligibility based on rural deprivation criteria.

    Returns Hinglish information based on August 2026 guidelines.
    """
    # Eligibility criteria: rural household with landless manual labor, OR no pucca house
    if rural_household and (landless_manual_labor or not has_pucca_house):
        return (
            "August 2026 guidelines के अनुसार, आप eligible हो सकते हैं! "
            "इसके तहत 5 लाख रुपये तक का मुफ्त इलाज मिलता है। Jan Seva Kendra जाकर Aadhaar से card बनवाएँ।"
        )
    else:
        return (
            "August 2026 guidelines के अनुसार, criteria match नहीं हुआ। "
            "अधिक जानकारी के लिए toll-free number 14555 पर call करें या CSC center पर check करवाएँ।"
        )


def get_vaccination_schedule(baby_age_months: int) -> str:
    """Determine upcoming vaccines from India UIP based on baby age in months.

    Returns Hinglish recommendation based on August 2026 immunization schedule.
    """
    if baby_age_months < 0:
        return "कृपया बच्चे की सही उम्र (months में) बताइए।"

    if baby_age_months == 0:
        return (
            "August 2026 guidelines के अनुसार, birth के समय BCG, OPV 0-dose, "
            "और Hepatitis B का टीका सरकारी अस्पताल में तुरंत लगना चाहिए।"
        )
    elif baby_age_months == 1 or baby_age_months == 2:
        return (
            "August 2026 guidelines के अनुसार, 1.5 months (6 weeks) पर Pentavalent 1, "
            "OPV 1, Rotavirus 1, IPV 1, और PCV 1 का टीका लगेगा।"
        )
    elif baby_age_months == 3:
        return (
            "August 2026 guidelines के अनुसार, 3.5 months (14 weeks) पर Pentavalent 3, "
            "OPV 3, Rotavirus 3, IPV 2, और PCV 2 का टीका लगेगा।"
        )
    elif baby_age_months >= 4 and baby_age_months <= 8:
        return (
            "August 2026 guidelines के अनुसार, 9 months पूरे होने पर Measles-Rubella (MR) 1st dose, "
            "Vitamin A, और PCV Booster का टीका लगेगा।"
        )
    elif baby_age_months >= 9 and baby_age_months <= 24:
        return (
            "August 2026 guidelines के अनुसार, 16 से 24 months पर DPT Booster 1, "
            "OPV Booster, और MR 2nd dose का टीका लगेगा।"
        )
    else:
        return (
            "August 2026 guidelines के अनुसार, basic childhood vaccines complete हो चुके हैं। "
            "5-6 साल की उम्र में DPT Booster 2 लगेगा, ASHA worker से संपर्क करें।"
        )


# Jan Aushadhi generic medicines database
GENERIC_MEDICINES = {
    "paracetamol": {
        "generic": "Paracetamol 650mg",
        "branded_price": "₹30-40",
        "generic_price": "₹10-12",
        "usage": "बुखार और बदन दर्द (Fever and body pain)",
        "brands": ["paracetamol", "dolo", "crocin", "calpol"],
    },
    "pantoprazole": {
        "generic": "Pantoprazole 40mg (Pantocid/Pan-40)",
        "branded_price": "₹120-150",
        "generic_price": "₹22-25",
        "usage": "गैस और एसिडिटी (Gas and acidity)",
        "brands": ["pantoprazole", "pantocid", "pan-40", "pan40", "pan 40", "pantocid"],
    },
    "cetirizine": {
        "generic": "Cetirizine 10mg (Okacet)",
        "branded_price": "₹35-50",
        "generic_price": "₹5-8",
        "usage": "एलर्जी, सर्दी aur छींक (Allergy, cold and sneezing)",
        "brands": ["cetirizine", "okacet", "ceteze"],
    },
    "metformin": {
        "generic": "Metformin 500mg (Glycomet)",
        "branded_price": "₹50-70",
        "generic_price": "₹12-15",
        "usage": "शुगर या डायबिटीज (Diabetes/Sugar control)",
        "brands": ["metformin", "glycomet", "glucophage"],
    },
    "amlodipine": {
        "generic": "Amlodipine 5mg (Amlong)",
        "branded_price": "₹30-45",
        "generic_price": "₹6-8",
        "usage": "हाई ब्लड प्रेशर या BP (High blood pressure)",
        "brands": ["amlodipine", "amlong", "amlopres"],
    },
    "amoxicillin": {
        "generic": "Amoxicillin 500mg",
        "branded_price": "₹120-160",
        "generic_price": "₹40-50",
        "usage": "बैक्टीरियल इन्फेक्शन या एंटीबायोटिक (Bacterial infection/Antibiotic)",
        "brands": ["amoxicillin", "amoxil", "mox"],
    },
}


def lookup_generic_medicine(medicine_name: str) -> str:
    """Compare branded medicine price with generic Jan Aushadhi price.

    Returns Hinglish information based on August 2026 guidelines.
    """
    if not medicine_name:
        return "कृपया दवाई का नाम बताइए ताकि मैं उसका generic विकल्प ढूंढ सकूँ।"

    # Normalize medicine name
    name_clean = medicine_name.lower().strip()

    # Matching against keys and brand lists
    matched_key = None
    for key, med in GENERIC_MEDICINES.items():
        if key in name_clean or any(
            brand in name_clean for brand in med.get("brands", [])
        ):
            matched_key = key
            break

    if matched_key:
        med = GENERIC_MEDICINES[matched_key]
        return (
            f"August 2026 PMBJP (Jan Aushadhi) directory के अनुसार, {med['generic']} "
            f"(जो {med['usage']} के काम आती है) का branded पत्ता {med['branded_price']} का मिलता है, "
            f"लेकिन जन औषधि केंद्र पर generic पत्ता सिर्फ {med['generic_price']} का मिलता है।"
        )
    else:
        return (
            f"माफ़ कीजिये, '{medicine_name}' के generic version की specific price अभी database में नहीं है। "
            f"लेकिन आप नज़दीकी प्रधानमंत्री जन औषधि केंद्र (Jan Aushadhi Kendra) पर जाकर 50% से 90% तक की बचत कर सकते हैं।"
        )


def check_maternity_benefit(
    is_first_child: bool, is_second_child_girl: bool, is_govt_employee: bool
) -> str:
    """Check eligibility for PM Matru Vandana Yojana (PMMVY) maternity benefit.

    Returns Hinglish information based on August 2026 guidelines.
    """
    if is_govt_employee:
        return (
            "August 2026 PMMVY guidelines के अनुसार, सरकारी नौकरी वाले (Central/State Govt or PSU) "
            "कर्मचारी इस योजना के लिए eligible नहीं हैं क्योंकि उन्हें paid maternity leave मिलती है।"
        )

    if is_first_child:
        return (
            "August 2026 guidelines के अनुसार, पहले बच्चे के जन्म पर PM Matru Vandana Yojana (PMMVY) "
            "के तहत ₹5,000 की नकद सहायता (maternity benefit) 2 किस्तों में मिलती है। नज़दीकी आंगनवाड़ी केंद्र पर संपर्क करें।"
        )
    elif is_second_child_girl:
        return (
            "August 2026 guidelines के अनुसार, दूसरे बच्चे के लड़की होने पर PM Matru Vandana Yojana (PMMVY) "
            "के तहत ₹6,000 की नकद सहायता सीधे बैंक खाते में मिलती है। आप इसके लिए eligible हैं।"
        )
    else:
        return (
            "August 2026 guidelines के अनुसार, PMMVY का लाभ केवल पहले बच्चे के लिए, "
            "या दूसरे बच्चे के लड़की होने पर ही मिलता है। अधिक जानकारी के लिए आंगनवाड़ी कार्यकर्ता से संपर्क करें।"
        )
