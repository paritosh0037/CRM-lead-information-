import pandas as pd
import pytest

from app.ml.engine import MLEngine


def test_ml_engine_initialization_and_scoring():
    engine = MLEngine(model_path="data/model.joblib")
    df = pd.read_csv("data/model_ready_features.csv").head(5)

    probs = engine.predict_proba(df)
    scores = engine.score(df)
    preds = engine.predict(df)

    assert len(probs) == 5
    assert len(scores) == 5
    assert len(preds) == 5
    for p, s in zip(probs, scores):
        assert 0.0 <= p <= 1.0
        assert 0 <= s <= 100
        assert s == int(round(p * 100))
