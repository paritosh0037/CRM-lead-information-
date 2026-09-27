import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from app.ml.engine import MLEngine
from app.ml.explain import (
    FEATURE_DISPLAY_NAMES,
    SHAPExplainer,
    generate_natural_language_explanation,
    get_display_name,
)


@pytest.fixture
def sample_dataset():
    data_path = "data/model_ready_features.csv"
    return pd.read_csv(data_path)


@pytest.fixture
def explainer():
    return SHAPExplainer(model_path="data/model.joblib")


def test_shap_explainer_initialization(explainer):
    assert explainer.model is not None
    assert explainer.explainer is not None
    assert len(explainer.feature_names) > 0


def test_explain_single_lead_structure(explainer, sample_dataset):
    single_lead = sample_dataset.iloc[0].to_dict()
    explanation = explainer.explain_lead(
        single_lead,
        lead_id="L00001",
        lead_score=85,
        conversion_probability=0.85,
        top_n=5,
    )

    assert explanation["lead_id"] == "L00001"
    assert explanation["lead_score"] == 85
    assert explanation["conversion_probability"] == 0.85
    assert "base_value" in explanation
    assert "positive_factors" in explanation
    assert "negative_factors" in explanation
    assert "top_factors" in explanation
    assert "explanation_text" in explanation
    assert len(explanation["top_factors"]) <= 5


def test_positive_and_negative_factors_sorting(explainer, sample_dataset):
    single_lead = sample_dataset.iloc[0].to_dict()
    explanation = explainer.explain_lead(single_lead, top_n=10)

    pos = explanation["positive_factors"]
    neg = explanation["negative_factors"]

    # Check all positive factors have impact > 0 and are sorted descending
    for i in range(len(pos)):
        assert pos[i]["impact"] > 0
        if i > 0:
            assert pos[i - 1]["impact"] >= pos[i]["impact"]

    # Check all negative factors have impact < 0 and are sorted ascending (strongest negative first)
    for i in range(len(neg)):
        assert neg[i]["impact"] < 0
        if i > 0:
            assert neg[i - 1]["impact"] <= neg[i]["impact"]


def test_display_name_mapping():
    assert get_display_name("demo_requested") == "Demo Requested"
    assert get_display_name("pricing_page_visit") == "Pricing Page Visits"
    assert get_display_name("opportunity_stage_Qualified") == "Opportunity Stage: Qualified"
    assert get_display_name("unknown_custom_feature") == "Unknown Custom Feature"


def test_natural_language_explanation_generation():
    pos_factors = [
        {"display_name": "Demo Requested", "impact": 0.22},
        {"display_name": "Pricing Page Visits", "impact": 0.15},
    ]
    neg_factors = [
        {"display_name": "Days Since Last Contact", "impact": -0.10},
    ]

    text = generate_natural_language_explanation(
        pos_factors, neg_factors, lead_score=85
    )
    assert "High conversion potential" in text
    assert "demo requested" in text.lower()
    assert "pricing page visits" in text.lower()
    assert "days since last contact" in text.lower()


def test_global_feature_importance(explainer, sample_dataset, tmp_path):
    X = sample_dataset.drop(columns=["lead_id", "converted"])
    out_file = tmp_path / "global_importance.json"

    importance = explainer.save_global_importance(X, output_path=str(out_file), top_n=10)

    assert out_file.exists()
    assert len(importance) == 10
    assert "feature" in importance[0]
    assert "display_name" in importance[0]
    assert "mean_abs_shap" in importance[0]

    # Verify descending sort
    for i in range(1, len(importance)):
        assert importance[i - 1]["mean_abs_shap"] >= importance[i]["mean_abs_shap"]


def test_explanation_reproducibility(explainer, sample_dataset):
    lead = sample_dataset.iloc[2].to_dict()
    exp1 = explainer.explain_lead(lead, lead_id="L00003", lead_score=70)
    exp2 = explainer.explain_lead(lead, lead_id="L00003", lead_score=70)

    assert exp1["positive_factors"] == exp2["positive_factors"]
    assert exp1["negative_factors"] == exp2["negative_factors"]
    assert exp1["explanation_text"] == exp2["explanation_text"]
    assert exp1["base_value"] == exp2["base_value"]


def test_ml_engine_explain_lead_integration(sample_dataset):
    engine = MLEngine(model_path="data/model.joblib")
    lead = sample_dataset.iloc[1].to_dict()

    res = engine.explain_lead(lead, lead_id="L00002")

    assert "lead_score" in res
    assert "conversion_probability" in res
    assert "positive_factors" in res
    assert "negative_factors" in res
    assert "explanation_text" in res
    assert isinstance(res["lead_score"], int)


def test_sensitive_attributes_exclusion_in_explanation(explainer, sample_dataset):
    dirty_lead = sample_dataset.iloc[0].to_dict()
    dirty_lead["gender"] = "Male"
    dirty_lead["religion"] = "None"

    res = explainer.explain_lead(dirty_lead)

    all_features = [f["feature"] for f in res["top_factors"]]
    assert "gender" not in all_features
    assert "religion" not in all_features
