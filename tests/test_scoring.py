import pandas as pd
import pytest

from marketsignal.indicators import compute_indicators
from marketsignal.scoring import latest_snapshot, risk_level, risk_score


def test_risk_score_bounds(demo_prices):
    ind = compute_indicators(demo_prices)
    scores = risk_score(ind)
    assert scores.between(0, 100).all()


def test_risk_score_calm_vs_crisis():
    calm = pd.DataFrame(
        {
            "volatility": [0.08],
            "vol_shock_ratio": [0.9],
            "drawdown": [-0.01],
            "momentum": [0.05],
            "mean_correlation": [0.2],
        },
        index=pd.to_datetime(["2024-01-01"]),
    )
    crisis = pd.DataFrame(
        {
            "volatility": [0.60],
            "vol_shock_ratio": [3.0],
            "drawdown": [-0.30],
            "momentum": [-0.25],
            "mean_correlation": [0.95],
        },
        index=pd.to_datetime(["2024-01-01"]),
    )
    assert risk_score(calm).iloc[0] == 0.0
    assert risk_score(crisis).iloc[0] == 100.0


@pytest.mark.parametrize(
    "score,expected",
    [(0, "faible"), (24.9, "faible"), (25, "modéré"), (49.9, "modéré"),
     (50, "élevé"), (74.9, "élevé"), (75, "critique"), (100, "critique")],
)
def test_risk_level_thresholds(score, expected):
    assert risk_level(score) == expected


def test_risk_level_rejects_invalid():
    with pytest.raises(ValueError):
        risk_level(-1)
    with pytest.raises(ValueError):
        risk_level(float("nan"))


def test_latest_snapshot(demo_prices):
    ind = compute_indicators(demo_prices)
    snap = latest_snapshot(ind)
    assert snap.date == str(ind.index[-1].date())
    assert 0 <= snap.score <= 100
    assert snap.level in {"faible", "modéré", "élevé", "critique"}
    assert set(snap.indicators) == set(ind.columns)


def test_latest_snapshot_empty_raises():
    with pytest.raises(ValueError):
        latest_snapshot(pd.DataFrame())
