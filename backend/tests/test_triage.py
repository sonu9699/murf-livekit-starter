from triage import (
    check_ayushman,
    check_maternity_benefit,
    classify_triage,
    get_vaccination_schedule,
    lookup_generic_medicine,
)


def test_classify_triage():
    # Emergency
    res = classify_triage("severe chest pain and trouble breathing", 1)
    assert "Emergency" in res

    # Moderate
    res = classify_triage("fever and cough", 3)
    assert "doctor" in res

    # Mild
    res = classify_triage("mild cold", 1)
    assert "mild symptom" in res


def test_check_ayushman():
    # Eligible rural, kucha house, manual labor
    assert "eligible हो सकते हैं" in check_ayushman(
        rural_household=True, has_pucca_house=False, landless_manual_labor=True
    )

    # Ineligible (urban or pucca house without manual labor)
    assert "criteria match नहीं हुआ" in check_ayushman(
        rural_household=False, has_pucca_house=True, landless_manual_labor=False
    )


def test_get_vaccination_schedule():
    assert "BCG" in get_vaccination_schedule(0)
    assert "Pentavalent 1" in get_vaccination_schedule(2)
    assert "Pentavalent 3" in get_vaccination_schedule(3)


def test_lookup_generic_medicine():
    # Paracetamol
    res = lookup_generic_medicine("Paracetamol")
    assert "Paracetamol 650mg" in res
    assert "10-12" in res

    # Pantoprazole
    res = lookup_generic_medicine("Pantocid tablet")
    assert "Pantoprazole 40mg" in res

    # Unknown
    res = lookup_generic_medicine("unknown_medicine")
    assert "generic version" in res


def test_check_maternity_benefit():
    # Govt employee
    assert "eligible नहीं हैं" in check_maternity_benefit(
        is_first_child=True, is_second_child_girl=False, is_govt_employee=True
    )

    # First child
    assert "5,000" in check_maternity_benefit(
        is_first_child=True, is_second_child_girl=False, is_govt_employee=False
    )

    # Second child girl
    assert "6,000" in check_maternity_benefit(
        is_first_child=False, is_second_child_girl=True, is_govt_employee=False
    )

    # Second child boy
    assert "आंगनवाड़ी" in check_maternity_benefit(
        is_first_child=False, is_second_child_girl=False, is_govt_employee=False
    )
