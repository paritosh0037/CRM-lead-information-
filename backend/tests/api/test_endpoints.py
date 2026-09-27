import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data == {"status": "ok"}



def test_openapi_documentation():
    response = client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "paths" in data
    assert "/api/leads/score" in data["paths"]
    assert "/api/leads/explain" in data["paths"]
    assert "/api/leads/recommend" in data["paths"]
    assert "/api/leads/intelligence" in data["paths"]
    assert "/api/leads/ranked" in data["paths"]


def test_score_endpoint():
    payload = {
        "lead_id": "TEST_001",
        "demo_requested": 1,
        "pricing_page_visit": 2,
        "annual_revenue": 5000000.0,
        "deal_value": 50000.0,
        "days_since_last_contact": 10,
    }
    response = client.post("/api/leads/score", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["lead_id"] == "TEST_001"
    assert "conversion_probability" in data
    assert "lead_score" in data
    assert 0.0 <= data["conversion_probability"] <= 1.0
    assert 0 <= data["lead_score"] <= 100
    assert data["lead_score"] == int(round(data["conversion_probability"] * 100))


def test_explain_endpoint():
    payload = {
        "lead_id": "TEST_002",
        "demo_requested": 1,
        "pricing_page_visit": 2,
        "email_opened": 4,
        "days_since_last_contact": 15,
    }
    response = client.post("/api/leads/explain?top_n=3", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["lead_id"] == "TEST_002"
    assert "base_value" in data
    assert "positive_factors" in data
    assert "negative_factors" in data
    assert "top_factors" in data
    assert "explanation_text" in data
    assert len(data["top_factors"]) <= 3
    assert len(data["explanation_text"]) > 0


def test_recommend_endpoint():
    payload = {
        "lead_id": "TEST_003",
        "lead_score": 85,
        "demo_requested": 1,
    }
    response = client.post("/api/leads/recommend", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["lead_id"] == "TEST_003"
    assert data["recommended_action"] == "DEMO"
    assert 0.5 <= data["recommendation_confidence"] <= 1.0
    assert len(data["confidence_reasons"]) > 0
    assert "rationale" in data
    assert "rule_trace" in data
    assert data["rule_trace"]["action"] == "DEMO"


def test_combined_intelligence_endpoint():
    payload = {
        "lead_id": "TEST_004",
        "demo_requested": 2,
        "pricing_page_visit": 3,
        "days_since_last_contact": 5,
        "annual_revenue": 10000000.0,
    }
    response = client.post("/api/leads/intelligence", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["lead_id"] == "TEST_004"
    assert "conversion_probability" in data
    assert "lead_score" in data
    assert "explanation" in data
    assert "recommendation" in data
    assert data["explanation"]["lead_id"] == "TEST_004"
    assert data["recommendation"]["lead_id"] == "TEST_004"


def test_ranked_leads_endpoint():
    response = client.get("/api/leads/ranked?limit=10&offset=0")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "leads" in data
    assert len(data["leads"]) <= 10
    if len(data["leads"]) > 1:
        # Verify sorted descending by lead_score
        scores = [l["lead_score"] for l in data["leads"]]
        assert scores == sorted(scores, reverse=True)


def test_get_lead_by_id_existing():
    response = client.get("/api/leads/L00001")
    assert response.status_code == 200
    data = response.json()
    assert data["lead_id"] == "L00001"
    assert "conversion_probability" in data
    assert "lead_score" in data
    assert "explanation" in data
    assert "recommendation" in data


def test_get_lead_by_id_not_found():
    response = client.get("/api/leads/NONEXISTENT_LEAD_99999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_validation_error_invalid_query_params():
    # Negative limit should fail validation (ge=1)
    response = client.get("/api/leads/ranked?limit=-5")
    assert response.status_code == 422
