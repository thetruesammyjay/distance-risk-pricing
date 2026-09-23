from datetime import UTC, datetime
from decimal import Decimal

from services.risk_service.futo_survey import FutoSurveyRiskProvider
from services.risk_service.service import RiskComponents, RiskService


async def test_exact_survey_route_and_time_are_used() -> None:
    provider = FutoSurveyRiskProvider()
    observation = await provider.get_observation(
        (5.4005546, 6.9841672),
        (5.3830451, 6.9961520),
        datetime(2026, 9, 23, 6, 30, tzinfo=UTC),
    )

    assert observation.source_type == "questionnaire"
    assert observation.composite_score == Decimal("0.2768")
    assert observation.components.questionnaire == Decimal("0.2768")
    assert observation.components.accident is None
    assert "exact surveyed route" in observation.data_sources[1]
    assert "7:00 AM - 10:00 AM" in observation.data_sources[2]


async def test_unknown_route_uses_explicit_survey_time_prior() -> None:
    provider = FutoSurveyRiskProvider()
    service = RiskService(
        provider,
        RiskComponents(Decimal("0.4"), Decimal("0.3"), Decimal("0.3")),
    )
    estimate = await service.assess(
        (5.4005546, 6.9841672),
        (5.395214, 7.009140),
        datetime(2026, 9, 23, 12, 30, tzinfo=UTC),
    )

    assert estimate.source_type == "questionnaire"
    assert estimate.weight_strategy == "questionnaire_composite_score"
    assert estimate.components_available == ("questionnaire",)
    assert estimate.components_missing == ("accident", "road", "security")
    assert "all surveyed routes time prior" in estimate.data_sources[1]
    assert Decimal("0") <= estimate.score <= Decimal("1")
