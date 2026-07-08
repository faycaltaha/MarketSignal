import pytest
from fastapi.testclient import TestClient

from marketsignal.api import create_app


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    from marketsignal.data import generate_demo_prices

    path = tmp_path_factory.mktemp("data") / "prices.csv"
    generate_demo_prices(n_days=1200, seed=7).to_csv(path)
    return TestClient(create_app(path))


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["observations"] == 1200


def test_risk_score(client):
    body = client.get("/risk/score").json()
    assert 0 <= body["score"] <= 100
    assert body["level"] in {"faible", "modéré", "élevé", "critique"}


def test_risk_indicators(client):
    body = client.get("/risk/indicators").json()
    assert set(body["indicators"]) == {
        "volatility", "vol_shock_ratio", "drawdown", "momentum", "mean_correlation",
    }


def test_risk_alerts(client):
    body = client.get("/risk/alerts").json()
    assert len(body["alerts"]) >= 1
    assert {"severity", "code", "message"} <= set(body["alerts"][0])


def test_history(client):
    body = client.get("/risk/history", params={"days": 30}).json()
    assert len(body["dates"]) == 30
    assert len(body["scores"]) == 30


def test_history_rejects_bad_days(client):
    assert client.get("/risk/history", params={"days": 0}).status_code == 422


def test_predict(client):
    body = client.get("/predict").json()
    assert 0 <= body["crisis_probability"] <= 1
    assert body["horizon_days"] == 30


def test_dashboard_renders(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "MarketSignal" in resp.text
    assert "__PAYLOAD__" not in resp.text  # les données ont bien été injectées
