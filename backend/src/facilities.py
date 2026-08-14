"""Local health facilities directory for Aarogya Saathi.

Provides a database of Primary Health Centers (PHCs), Community Health Centers (CHCs),
and District Hospitals for several major districts in rural/semi-urban India,
along with normalization and lookup logic.
"""

import re

# Normalization regex for cleaning district names
_CLEAN_RE = re.compile(r"[^a-z0-9]+")


def normalize_key(name: str) -> str:
    """Normalize a name to a stable lookup key (lowercase, letters/numbers only)."""
    if not name:
        return ""
    # Lowercase, remove anything that is not alphanumeric, and strip
    val = name.lower().strip()
    # Strip common suffixes that the pincode API might add, e.g., "district"
    for suffix in (" district", " rural", " urban"):
        if val.endswith(suffix):
            val = val[: -len(suffix)]
    return _CLEAN_RE.sub("", val)


# Realistic health facility data for representative districts in India.
# This serves as our local database (August 2026 directory).
FACILITIES_DIRECTORY = {
    # BIHAR
    "patna": [
        {
            "name": "PHC Phulwari Sharif",
            "type": "Primary Health Center",
            "address": "Phulwari Sharif, Patna, Bihar",
            "phone": "0612-2252101",
        },
        {
            "name": "CHC Danapur",
            "type": "Community Health Center",
            "address": "Danapur, Patna, Bihar",
            "phone": "0612-2510202",
        },
        {
            "name": "Patna Medical College and Hospital (PMCH)",
            "type": "District/State Hospital",
            "address": "Ashok Rajpath, Patna, Bihar",
            "phone": "0612-2300080",
        },
    ],
    "gaya": [
        {
            "name": "PHC Bodhgaya",
            "type": "Primary Health Center",
            "address": "Bodhgaya, Gaya, Bihar",
            "phone": "0631-2200102",
        },
        {
            "name": "Anugrah Narayan Magadh Medical College Hospital",
            "type": "District Hospital",
            "address": "Sherghati Road, Gaya, Bihar",
            "phone": "0631-2222049",
        },
    ],
    "muzaffarpur": [
        {
            "name": "PHC Mushahari",
            "type": "Primary Health Center",
            "address": "Mushahari, Muzaffarpur, Bihar",
            "phone": "0621-2210344",
        },
        {
            "name": "Sri Krishna Medical College and Hospital (SKMCH)",
            "type": "District Hospital",
            "address": "Umanagar, Muzaffarpur, Bihar",
            "phone": "0621-2230460",
        },
    ],
    # UTTAR PRADESH
    "lucknow": [
        {
            "name": "CHC Chinhat",
            "type": "Community Health Center",
            "address": "Chinhat, Deva Road, Lucknow, UP",
            "phone": "0522-2810101",
        },
        {
            "name": "PHC Kakori",
            "type": "Primary Health Center",
            "address": "Kakori, Lucknow, UP",
            "phone": "0522-2992020",
        },
        {
            "name": "Dr. Ram Manohar Lohia Hospital",
            "type": "District Hospital",
            "address": "Vibhuti Khand, Gomti Nagar, Lucknow, UP",
            "phone": "0522-2307520",
        },
    ],
    "varanasi": [
        {
            "name": "PHC Harahua",
            "type": "Primary Health Center",
            "address": "Harahua Block, Varanasi, UP",
            "phone": "0542-2622020",
        },
        {
            "name": "CHC Cholapur",
            "type": "Community Health Center",
            "address": "Cholapur, Varanasi, UP",
            "phone": "0542-2830303",
        },
        {
            "name": "Pandit Deen Dayal Upadhyaya Hospital",
            "type": "District Hospital",
            "address": "Pandeypur, Varanasi, UP",
            "phone": "0542-2586252",
        },
    ],
    "gorakhpur": [
        {
            "name": "PHC Chargawan",
            "type": "Primary Health Center",
            "address": "Chargawan, Gorakhpur, UP",
            "phone": "0551-2283030",
        },
        {
            "name": "CHC Bhathat",
            "type": "Community Health Center",
            "address": "Bhathat, Gorakhpur, UP",
            "phone": "0551-2854040",
        },
        {
            "name": "BRD Medical College and Hospital",
            "type": "District Hospital",
            "address": "Gorakhpur Road, Gorakhpur, UP",
            "phone": "0551-2501755",
        },
    ],
    # RAJASTHAN
    "jaipur": [
        {
            "name": "PHC Sanganer",
            "type": "Primary Health Center",
            "address": "Sanganer, Tonk Road, Jaipur, Rajasthan",
            "phone": "0141-2731102",
        },
        {
            "name": "CHC Amer",
            "type": "Community Health Center",
            "address": "Amer Road, Jaipur, Rajasthan",
            "phone": "0141-2530101",
        },
        {
            "name": "Sawai Man Singh (SMS) Hospital",
            "type": "District Hospital",
            "address": "JLN Marg, Jaipur, Rajasthan",
            "phone": "0141-2560291",
        },
    ],
    # MADHYA PRADESH
    "bhopal": [
        {
            "name": "PHC Kolar",
            "type": "Primary Health Center",
            "address": "Kolar Road, Bhopal, MP",
            "phone": "0755-2420101",
        },
        {
            "name": "CHC Phanda",
            "type": "Community Health Center",
            "address": "Phanda Block, Bhopal, MP",
            "phone": "0755-2850202",
        },
        {
            "name": "Hamidia Hospital",
            "type": "District Hospital",
            "address": "Near Taj-ul-Masajid, Bhopal, MP",
            "phone": "0755-4003000",
        },
    ],
    # MAHARASHTRA
    "pune": [
        {
            "name": "PHC Wagholi",
            "type": "Primary Health Center",
            "address": "Wagholi, Pune-Nagar Road, Pune, Maharashtra",
            "phone": "020-2705101",
        },
        {
            "name": "CHC Haveli",
            "type": "Community Health Center",
            "address": "Haveli Block, Pune, Maharashtra",
            "phone": "020-24450202",
        },
        {
            "name": "Sassoon General Hospital",
            "type": "District Hospital",
            "address": "Near Pune Station, Pune, Maharashtra",
            "phone": "020-26128000",
        },
    ],
    # JHARKHAND
    "ranchi": [
        {
            "name": "PHC Kanke",
            "type": "Primary Health Center",
            "address": "Kanke Road, Ranchi, Jharkhand",
            "phone": "0651-2451010",
        },
        {
            "name": "CHC Ratu",
            "type": "Community Health Center",
            "address": "Ratu Block, Ranchi, Jharkhand",
            "phone": "0651-2530202",
        },
        {
            "name": "Rajendra Institute of Medical Sciences (RIMS)",
            "type": "District Hospital",
            "address": "Bariatu, Ranchi, Jharkhand",
            "phone": "0651-2541533",
        },
    ],
}


def lookup_facilities_by_district(
    district: str, state: str = "", block: str = ""
) -> str:
    """Lookup facilities in the given district and return a Hinglish spoken summary.

    If the district is not in the directory, returns a helpful fallback using
    the resolved district/state/block.
    """
    key = normalize_key(district)
    facilities = FACILITIES_DIRECTORY.get(key)

    district_disp = district.strip()
    state_disp = state.strip()
    block_disp = block.strip()

    location_desc = f"{district_disp}"
    if block_disp and block_disp != district_disp:
        location_desc += f" के {block_disp} block"
    elif state_disp:
        location_desc += f", {state_disp}"

    if facilities:
        # Format the facilities list. Keep it short so it fits in a couple of sentences.
        # We will list one primary center (PHC/CHC) and the main hospital.
        phc_chc = next(
            (
                f
                for f in facilities
                if f["type"] in ("Primary Health Center", "Community Health Center")
            ),
            None,
        )
        hospital = next(
            (
                f
                for f in facilities
                if f["type"] == "District Hospital" or "Hospital" in f["name"]
            ),
            None,
        )

        reply_parts = []
        if phc_chc:
            reply_parts.append(
                f"नज़दीकी local center {phc_chc['name']} है (Phone: {phc_chc['phone']})"
            )
        if hospital:
            reply_parts.append(
                f"बड़ा अस्पताल {hospital['name']} है (Phone: {hospital['phone']})"
            )

        facilities_summary = " और ".join(reply_parts)
        return f"{location_desc} में, {facilities_summary}।"
    else:
        # Fallback when the district is resolved but we do not have specific facilities stored
        # Return generic but very helpful local guidance.
        return (
            f"{location_desc} के लिए specific local hospital details database में नहीं हैं। "
            f"लेकिन आप अपने block के Primary Health Center (PHC) या district hospital जा सकते हैं, "
            f"या emergency के लिए 108 या 102 helpline पर call कर सकते हैं।"
        )
