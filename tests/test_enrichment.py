"""
Automated Pytest for oncocare-automated-tumor-board Enrichment Modules.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from enrichment import (
    OverviewEngine,
    MolecularTumorBoardDecisionSupportWithTierbasedActionabilityScoringEngine,
    GoalEngine,
    DataModelChangesEngine,
    AgentChangesEngine,
    EngineChangesEngine,
    ApiChangesEngine,
    QualityAssuranceEngine,
    BaseEnrichmentEngine,
    EnrichmentResult,
    OncocareagentictumorboardEnrichmentSuite,
    enrichment_suite,
)

def test_enrichment_suite_execution():
    suite = OncocareagentictumorboardEnrichmentSuite()
    res = suite.execute_all(primary_val=0.5, secondary_val=0.2)
    assert len(res) >= 1
    for k, v in res.items():
        assert v.status in ["OPTIMAL", "WARNING", "CRITICAL_ALERT"]
        assert isinstance(v.recommendations, list)

def test_enrichment_threshold_escalation():
    suite = OncocareagentictumorboardEnrichmentSuite()
    res = suite.execute_all(primary_val=10.0, secondary_val=5.0)
    for k, v in res.items():
        assert v.status in ["WARNING", "CRITICAL_ALERT"]
        assert len(v.alerts) > 0

def test_base_engine_inheritance():
    """Verify all engines properly inherit from BaseEnrichmentEngine."""
    engines = [
        OverviewEngine(),
        MolecularTumorBoardDecisionSupportWithTierbasedActionabilityScoringEngine(),
        GoalEngine(),
        DataModelChangesEngine(),
        AgentChangesEngine(),
        EngineChangesEngine(),
        ApiChangesEngine(),
        QualityAssuranceEngine(),
    ]
    for engine in engines:
        assert isinstance(engine, BaseEnrichmentEngine)
        result = engine.evaluate(0.5)
        assert isinstance(result, EnrichmentResult)
        assert result.feature_name == engine.FEATURE_NAME

def test_engine_history_tracking():
    """Verify engines properly track evaluation history."""
    engine = OverviewEngine()
    assert len(engine.history) == 0
    engine.evaluate(1.0)
    engine.evaluate(2.0)
    assert len(engine.history) == 2
