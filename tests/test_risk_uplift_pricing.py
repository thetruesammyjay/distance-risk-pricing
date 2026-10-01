from decimal import Decimal as D

import pytest

from services.pricing_engine.calculator import (
    calculate_fare,
    classify_risk,
    round_to_increment,
)
from services.pricing_engine.models import PricingConfig, PricingContext


def cfg(**overrides) -> PricingConfig:
    values = dict(
        base_fare=D("500"),
        distance_rate=D("150"),
        risk_rate=D("1"),
        demand_sensitivity=D("1"),
        demand_cap=D("2.5"),
    )
    values.update(overrides)
    return PricingConfig(**values)


def fare(distance="2", risk="0.125", demand="1.0", **overrides):
    return calculate_fare(
        PricingContext(D(distance), D(risk), D(demand)), cfg(**overrides)
    )


# ---- classification boundaries (Table 4.3) --------------------------------
@pytest.mark.parametrize(
    "score, expected",
    [
        ("0", "Low"), ("0.25", "Low"), ("0.2501", "Moderate"),
        ("0.50", "Moderate"), ("0.5001", "High"),
        ("0.75", "High"), ("0.7501", "Very High"), ("1", "Very High"),
    ],
)
def test_classification_boundaries(score, expected):
    assert classify_risk(D(score)) == expected


# ---- tiered uplift on a 2 km trip (base = NGN 500 minimum) ----------------
@pytest.mark.parametrize(
    "risk, expected_total, expected_pct",
    [
        ("0.125", "500.00", "0"),
        ("0.25", "500.00", "0"),
        ("0.2501", "550.00", "0.10"),
        ("0.375", "550.00", "0.10"),
        ("0.50", "550.00", "0.10"),
        ("0.5001", "625.00", "0.25"),
        ("0.75", "625.00", "0.25"),
        ("0.7501", "700.00", "0.40"),
        ("0.875", "700.00", "0.40"),
        ("1", "700.00", "0.40"),
    ],
)
def test_tiered_uplift_no_demand(risk, expected_total, expected_pct):
    result = fare(risk=risk)
    assert result.total == D(expected_total)
    assert result.risk_uplift_pct == D(expected_pct)
    assert result.cap_applied is False


def test_day_versus_night_scenario_is_meaningful():
    day = fare(risk="0.125", demand="1.05")    # 10 AM: low risk, small demand
    night = fare(risk="0.375", demand="1.0")   # 10 PM: moderate risk
    assert day.total == D("525.00")
    assert night.total == D("550.00")
    assert night.risk_adjustment == D("50.00")


def test_components_sum_to_total():
    result = fare(distance="4.1", risk="0.375")   # base 615, risk 61.50
    assert result.base_fare == D("615.00")
    assert result.risk_adjustment == D("61.50")
    assert result.total == D("675.00")            # 676.50 -> nearest 5
    assert result.rounding_adjustment == D("-1.50")
    assert (
        result.base_fare + result.risk_adjustment
        + result.demand_adjustment + result.rounding_adjustment
    ) == result.total


def test_long_trip_scales_with_base_fare():
    result = fare(distance="10", risk="0.875")    # base 1500, +40%
    assert result.base_fare == D("1500.00")
    assert result.risk_adjustment == D("600.00")
    assert result.total == D("2100.00")


# ---- demand interaction ----------------------------------------------------
def test_additive_mode_sums_uplifts():
    result = fare(risk="0.875", demand="1.5")     # 500 + 200 + 250
    assert result.demand_adjustment == D("250.00")
    assert result.total == D("950.00")
    assert result.cap_applied is False


def test_multiplicative_mode_compounds_and_cap_applies():
    result = fare(risk="0.875", demand="1.5", formula_mode="multiplicative")
    # uncapped would be 700 * 1.5 = 1050; capped at 2.0 x 500 = 1000
    assert result.cap_applied is True
    assert result.total == D("1000.00")
    assert result.risk_adjustment == D("200.00")
    assert result.demand_adjustment == D("300.00")


def test_cap_reduces_risk_when_cap_is_tighter_than_risk_uplift():
    result = fare(risk="0.875", max_total_multiplier=D("1.2"))
    assert result.cap_applied is True
    assert result.risk_adjustment == D("100.00")
    assert result.demand_adjustment == D("0.00")
    assert result.total == D("600.00")


def test_off_peak_has_no_demand_charge():
    assert fare(risk="0.125", demand="1.0").demand_adjustment == D("0.00")


# ---- rounding --------------------------------------------------------------
@pytest.mark.parametrize(
    "value, expected",
    [("524.99", "500.00"), ("525", "550.00"), ("549", "550.00"), ("575", "600.00")],
)
def test_round_to_nearest_50_half_up(value, expected):
    assert round_to_increment(D(value), D("50")) == D(expected)


def test_default_rounding_keeps_day_and_night_fares_distinct():
    # A coarse NGN 50 step would push 525 up to 550 and erase the difference.
    assert fare(risk="0.125", demand="1.05").total != fare(risk="0.375").total
    assert fare(risk="0.125", demand="1.05", rounding_increment=D("50")).total == D("550.00")


def test_rounding_can_be_disabled():
    result = fare(distance="4.1", risk="0.375", rounding_increment=D("0.01"))
    assert result.total == D("676.50")
    assert result.rounding_adjustment == D("0.00")


# ---- legacy mode reproduces v2 exactly ------------------------------------
def test_legacy_mode_matches_original_formula():
    result = fare(risk="0.375", demand="1.05", risk_mode="legacy")
    assert result.risk_adjustment == D("0.75")
    assert result.demand_adjustment == D("1.05")
    assert result.total == D("501.80")


# ---- config validation -----------------------------------------------------
def test_uplifts_must_be_non_decreasing():
    with pytest.raises(ValueError):
        cfg(risk_uplift_moderate=D("0.30"), risk_uplift_high=D("0.20"))


def test_cap_and_rounding_validation():
    with pytest.raises(ValueError):
        cfg(max_total_multiplier=D("0.9"))
    with pytest.raises(ValueError):
        cfg(rounding_increment=D("0"))
    with pytest.raises(ValueError):
        cfg(risk_mode="other")