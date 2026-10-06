import pytest

try:
    from app.ml.monitoring import RetrainingEngine
    HAS_DEPS = True
except ImportError:
    HAS_DEPS = False

pytestmark = pytest.mark.skipif(not HAS_DEPS, reason="Blocked by Windows sklearn/scipy DLL policy")


def test_retraining_decision_better_candidate():
    engine = RetrainingEngine()
    current_metrics = {"classification_metrics": {"roc_auc": 0.70}}
    candidate_metrics = {"classification_metrics": {"roc_auc": 0.75}}
    
    assert engine.evaluate_candidate(current_metrics, candidate_metrics) is True


def test_retraining_decision_worse_candidate():
    engine = RetrainingEngine()
    current_metrics = {"classification_metrics": {"roc_auc": 0.80}}
    candidate_metrics = {"classification_metrics": {"roc_auc": 0.75}}
    
    assert engine.evaluate_candidate(current_metrics, candidate_metrics) is False


def test_retraining_decision_equal_candidate():
    engine = RetrainingEngine()
    current_metrics = {"classification_metrics": {"roc_auc": 0.80}}
    candidate_metrics = {"classification_metrics": {"roc_auc": 0.80}}
    
    # Needs strictly greater ROC-AUC to promote
    assert engine.evaluate_candidate(current_metrics, candidate_metrics) is False


def test_retraining_evaluation_failure_keeps_current():
    engine = RetrainingEngine()
    current_metrics = {"classification_metrics": {"roc_auc": 0.80}}
    # Malformed candidate metrics
    candidate_metrics = {}
    
    assert engine.evaluate_candidate(current_metrics, candidate_metrics) is False
