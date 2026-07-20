from src.build_college_dataset import record_to_row


def _record(ownership, coa=50000, **brackets):
    base = {
        "school.name": "Test University",
        "school.state": "NC",
        "school.ownership": ownership,
        "latest.cost.attendance.academic_year": coa,
    }
    for key, value in brackets.items():
        base[key] = value
    return base


def test_public_school_reads_from_public_brackets():
    record = _record(
        ownership = 1,
        **{
            "latest.cost.net_price.public.by_income_level.0-30000": 5000,
            "latest.cost.net_price.public.by_income_level.30001-48000": 7000,
        },
    )

    row = record_to_row(record)

    assert row["requires_css_profile"] is False
    assert row["net_price_0_30k"] == 5000
    assert row["net_price_30k_48k"] == 7000


def test_private_school_reads_from_private_brackets():
    record = _record(
        ownership = 2,
        **{
            "latest.cost.net_price.private.by_income_level.0-30000": 9000,
            "latest.cost.net_price.private.by_income_level.30001-48000": 12000,
        },
    )

    row = record_to_row(record)

    assert row["requires_css_profile"] is True
    assert row["net_price_0_30k"] == 9000


def test_negative_net_price_is_clipped_to_zero():
    record = _record(
        ownership = 1,
        **{
            "latest.cost.net_price.public.by_income_level.0-30000": -361,
            "latest.cost.net_price.public.by_income_level.30001-48000": 7000,
        },
    )

    row = record_to_row(record)

    assert row["net_price_0_30k"] == 0


def test_school_with_fewer_than_two_brackets_is_excluded():
    record = _record(
        ownership = 1,
        **{"latest.cost.net_price.public.by_income_level.0-30000": 5000},
    )

    assert record_to_row(record) is None


def test_school_missing_cost_of_attendance_is_excluded():
    record = _record(
        ownership = 1,
        coa = None,
        **{
            "latest.cost.net_price.public.by_income_level.0-30000": 5000,
            "latest.cost.net_price.public.by_income_level.30001-48000": 7000,
        },
    )

    assert record_to_row(record) is None


def test_school_with_unrecognized_ownership_is_excluded():
    record = _record(
        ownership = 4,
        **{
            "latest.cost.net_price.public.by_income_level.0-30000": 5000,
            "latest.cost.net_price.public.by_income_level.30001-48000": 7000,
        },
    )

    assert record_to_row(record) is None
