from marketsignal.alerts import evaluate_alerts
from marketsignal.scoring import RiskSnapshot


def _snapshot(score, level, **indicators):
    base = {
        "volatility": 0.10,
        "vol_shock_ratio": 1.0,
        "drawdown": -0.01,
        "momentum": 0.02,
        "mean_correlation": 0.3,
    }
    base.update(indicators)
    return RiskSnapshot(date="2024-06-01", score=score, level=level, indicators=base)


def test_calm_market_yields_single_info():
    alerts = evaluate_alerts(_snapshot(10.0, "faible"))
    assert len(alerts) == 1
    assert alerts[0].severity == "info"
    assert alerts[0].code == "RAS"


def test_critical_score_alert():
    alerts = evaluate_alerts(_snapshot(80.0, "critique"))
    assert alerts[0].severity == "critical"
    assert alerts[0].code == "SCORE_CRITIQUE"


def test_high_probability_alert():
    alerts = evaluate_alerts(_snapshot(10.0, "faible"), crisis_probability=0.8)
    codes = {a.code for a in alerts}
    assert "PROBABILITE_CRISE" in codes
    assert alerts[0].severity == "critical"


def test_indicator_alerts():
    snap = _snapshot(
        60.0, "élevé",
        vol_shock_ratio=2.0, drawdown=-0.15, mean_correlation=0.8,
    )
    codes = {a.code for a in evaluate_alerts(snap)}
    assert {"SCORE_ELEVE", "CHOC_VOLATILITE", "DRAWDOWN", "CORRELATION_SYSTEMIQUE"} <= codes


def test_alerts_sorted_by_severity():
    snap = _snapshot(80.0, "critique", drawdown=-0.15)
    alerts = evaluate_alerts(snap)
    severities = [a.severity for a in alerts]
    assert severities == sorted(severities, key={"critical": 0, "warning": 1, "info": 2}.get)
