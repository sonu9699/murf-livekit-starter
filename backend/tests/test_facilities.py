import asyncio
from unittest.mock import MagicMock, patch

import pytest

import facilities
from agent import Assistant


def test_normalize_key():
    assert facilities.normalize_key("Patna") == "patna"
    assert facilities.normalize_key("Patna District") == "patna"
    assert facilities.normalize_key("Lucknow Rural") == "lucknow"
    assert facilities.normalize_key("Pune Urban") == "pune"
    assert facilities.normalize_key("  Gaya  ") == "gaya"
    assert facilities.normalize_key("") == ""

def test_lookup_facilities_by_district_matched():
    # Patna is in our directory
    res = facilities.lookup_facilities_by_district("Patna", "Bihar", "Phulwari Sharif")
    assert "Patna" in res
    assert "Phulwari Sharif" in res
    assert "PHC Phulwari Sharif" in res
    assert "PMCH" in res

def test_lookup_facilities_by_district_fallback():
    # Basti is not in our directory
    res = facilities.lookup_facilities_by_district("Basti", "Uttar Pradesh", "Basti Block")
    assert "Basti" in res
    assert "specific local hospital details" in res
    assert "108" in res
    assert "102" in res

@pytest.mark.asyncio
async def test_lookup_nearest_facility_invalid_pin():
    assistant = Assistant()
    context_mock = MagicMock()

    # 5-digit PIN
    res = await assistant.lookup_nearest_facility(context_mock, "12345")
    assert "गलत PIN code है" in res

    # Alphabetic PIN
    res = await assistant.lookup_nearest_facility(context_mock, "12345a")
    assert "गलत PIN code है" in res

class MockResponse:
    def __init__(self, status, data):
        self.status = status
        self._data = data

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    async def json(self):
        return self._data

class MockSession:
    def __init__(self, response=None, get_side_effect=None):
        self.response = response
        self.get_side_effect = get_side_effect

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    def get(self, url, timeout=None):
        if self.get_side_effect:
            raise self.get_side_effect
        return self.response

@pytest.mark.asyncio
async def test_lookup_nearest_facility_api_success():
    assistant = Assistant()
    context_mock = MagicMock()

    # Mock response data for Patna PIN code 800001
    mock_response_data = [
        {
            "Status": "Success",
            "Message": "Number of pincode(s) found:1",
            "PostOffice": [
                {
                    "District": "Patna",
                    "State": "Bihar",
                    "Block": "Phulwari Sharif"
                }
            ]
        }
    ]

    mock_session = MockSession(response=MockResponse(200, mock_response_data))

    with patch("aiohttp.ClientSession", return_value=mock_session):
        res = await assistant.lookup_nearest_facility(context_mock, "800001")
        assert "August 2026 health directory" in res
        assert "Patna" in res
        assert "PHC Phulwari Sharif" in res

@pytest.mark.asyncio
async def test_lookup_nearest_facility_api_timeout():
    assistant = Assistant()
    context_mock = MagicMock()

    mock_session = MockSession(get_side_effect=asyncio.TimeoutError())

    with patch("aiohttp.ClientSession", return_value=mock_session):
        res = await assistant.lookup_nearest_facility(context_mock, "800001")
        assert "Pincode lookup server response me time lag raha hai" in res
        assert "108" in res

# --- Day 5 Expanded Tools Tests ---

def test_triage_classification():
    import triage
    # RED emergency
    res_red = triage.classify_triage("seene me dard aur saans lene me dikkat", 1)
    assert "Emergency" in res_red
    assert "108" in res_red

    # YELLOW doctor visit
    res_yellow = triage.classify_triage("4 din se bukhar hai", 4)
    assert "doctor" in res_yellow
    assert "PHC" in res_yellow

    # GREEN home care
    res_green = triage.classify_triage("halki khansi aur zukaam", 1)
    assert "home care" not in res_green  # translated to Hinglish "mild symptom"
    assert "mild symptom" in res_green
    assert "ORS" in res_green

def test_ayushman_eligibility():
    import triage
    # Eligible (rural + landless labor)
    eligible = triage.check_ayushman(rural_household=True, has_pucca_house=True, landless_manual_labor=True)
    assert "eligible हो सकते हैं" in eligible
    assert "5 लाख" in eligible

    # Eligible (rural + no pucca house)
    eligible_kucha = triage.check_ayushman(rural_household=True, has_pucca_house=False, landless_manual_labor=False)
    assert "eligible हो सकते हैं" in eligible_kucha

    # Not match
    not_eligible = triage.check_ayushman(rural_household=False, has_pucca_house=True, landless_manual_labor=False)
    assert "criteria match नहीं हुआ" in not_eligible
    assert "14555" in not_eligible

def test_vaccination_schedule():
    import triage
    # Birth
    v_birth = triage.get_vaccination_schedule(0)
    assert "BCG" in v_birth

    # 1.5 months
    v_6w = triage.get_vaccination_schedule(2)
    assert "Pentavalent 1" in v_6w

    # 9 months
    v_9m = triage.get_vaccination_schedule(6)
    assert "Measles-Rubella" in v_9m

    # Older
    v_old = triage.get_vaccination_schedule(36)
    assert "basic childhood vaccines complete" in v_old

@pytest.mark.asyncio
async def test_agent_health_tools():
    assistant = Assistant()
    context_mock = MagicMock()

    # Test triage tool calling
    res_triage = await assistant.classify_triage_level(context_mock, "seene me bahut tez dard hai", 1)
    assert "Emergency" in res_triage

    # Test Ayushman tool calling
    res_ayushman = await assistant.check_ayushman_eligibility(context_mock, rural_household=True, has_pucca_house=False, landless_manual_labor=False)
    assert "eligible हो सकते हैं" in res_ayushman

    # Test vaccination tool calling
    res_vaccine = await assistant.get_vaccination_schedule(context_mock, 0)
    assert "BCG" in res_vaccine

