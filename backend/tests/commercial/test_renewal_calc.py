"""Tests for `renewal_calc` — pure renewal-date arithmetic (no DB, no LLM).

Weekday anchors used below are verified against the real calendar:
  2027-01-01 Fri · 2027-11-02 Tue · 2026-06-05 Fri · 2026-06-06 Sat ·
  2026-06-07 Sun · 2026-05-29 Fri · 2026-05-30 Sat · 2026-05-31 Sun ·
  2026-02-28 Sat · 2024-02-29 Thu
"""

from datetime import date

from app.services import renewal_calc as calc


class TestTermEndDate:
    def test_simple_year(self):
        assert calc.term_end_date(date(2026, 1, 1), 12) == date(2027, 1, 1)

    def test_multi_year_rollover(self):
        # Matches the B1 repo test data (effective 2026-01-01, 24-month term).
        assert calc.term_end_date(date(2026, 1, 1), 24) == date(2028, 1, 1)

    def test_end_of_month_clamps_to_february(self):
        # Jan 31 + 1 month has no Feb 31 → clamp to last valid day.
        assert calc.term_end_date(date(2026, 1, 31), 1) == date(2026, 2, 28)

    def test_end_of_month_clamps_to_leap_february(self):
        assert calc.term_end_date(date(2024, 1, 31), 1) == date(2024, 2, 29)

    def test_month_within_year(self):
        assert calc.term_end_date(date(2026, 12, 1), 1) == date(2027, 1, 1)

    def test_zero_term_returns_effective_date(self):
        assert calc.term_end_date(date(2026, 6, 15), 0) == date(2026, 6, 15)


class TestCancelByCalendar:
    def test_matches_b1_fixture(self):
        # term_end(2026-01-01, 24) = 2028-01-01; minus 60 calendar days = 2027-11-02.
        assert calc.cancel_by_calendar(date(2026, 1, 1), 24, 60) == date(2027, 11, 2)

    def test_zero_notice_equals_term_end(self):
        assert calc.cancel_by_calendar(date(2026, 1, 1), 12, 0) == date(2027, 1, 1)

    def test_notice_exceeding_term_lands_before_effective(self):
        # term_end 2026-02-01, minus 60 days → 2025-12-03 (a valid, earlier date).
        assert calc.cancel_by_calendar(date(2026, 1, 1), 1, 60) == date(2025, 12, 3)


class TestCancelByEffective:
    def test_weekday_unchanged(self):
        # 2027-11-02 is a Tuesday → already a business day, no roll-back.
        assert calc.cancel_by_effective(date(2026, 1, 1), 24, 60) == date(2027, 11, 2)

    def test_saturday_rolls_back_to_friday(self):
        # effective 2025-06-06 + 12mo = 2026-06-06 (Sat) → roll back to 2026-06-05 (Fri).
        assert calc.cancel_by_effective(date(2025, 6, 6), 12, 0) == date(2026, 6, 5)

    def test_result_is_always_a_business_day(self):
        result = calc.cancel_by_effective(date(2025, 6, 7), 12, 0)
        assert result.weekday() < 5


class TestSendByEffective:
    def test_no_buffer_equals_cancel_by_effective(self):
        assert calc.send_by_effective(date(2026, 1, 1), 24, 60) == date(2027, 11, 2)

    def test_buffer_subtracts_then_stays_business_day(self):
        # cancel_by_effective = 2026-06-05 (Fri); minus 3 days = 2026-06-02 (Tue).
        assert calc.send_by_effective(date(2025, 6, 6), 12, 0, transit_buffer_days=3) == date(
            2026, 6, 2
        )

    def test_buffer_landing_on_weekend_rolls_back(self):
        # cancel_by_effective = 2026-06-05 (Fri); minus 5 days = 2026-05-31 (Sun)
        # → roll back to 2026-05-29 (Fri).
        assert calc.send_by_effective(date(2025, 6, 6), 12, 0, transit_buffer_days=5) == date(
            2026, 5, 29
        )

    def test_result_is_always_a_business_day(self):
        result = calc.send_by_effective(date(2025, 6, 7), 12, 0, transit_buffer_days=2)
        assert result.weekday() < 5


class TestUrgencyBucket:
    def test_red_below_14(self):
        assert calc.urgency_bucket(0) == "red"
        assert calc.urgency_bucket(13) == "red"

    def test_negative_is_red(self):
        assert calc.urgency_bucket(-5) == "red"

    def test_orange_14_to_44(self):
        assert calc.urgency_bucket(14) == "orange"
        assert calc.urgency_bucket(44) == "orange"

    def test_yellow_45_to_89(self):
        assert calc.urgency_bucket(45) == "yellow"
        assert calc.urgency_bucket(89) == "yellow"

    def test_green_90_and_above(self):
        assert calc.urgency_bucket(90) == "green"
        assert calc.urgency_bucket(365) == "green"
