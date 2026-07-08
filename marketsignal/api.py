"""API REST FastAPI + tableau de bord web.

L'application est construite via :func:`create_app` à partir d'un fichier
de prix (et, en option, d'un modèle pré-entraîné ; sinon le modèle est
entraîné au démarrage sur l'historique fourni).
"""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse

from .alerts import evaluate_alerts
from .data import load_prices
from .indicators import compute_indicators
from .model import CrisisModel
from .scoring import latest_snapshot, risk_score

_DASHBOARD_TEMPLATE = (Path(__file__).parent / "dashboard.html").read_text()


def create_app(prices_path: str | Path, model_path: str | Path | None = None) -> FastAPI:
    """Construit l'application FastAPI pour un fichier de prix donné."""
    prices = load_prices(prices_path)
    indicators = compute_indicators(prices)
    if model_path is not None:
        model = CrisisModel.load(model_path)
    else:
        model = CrisisModel().fit(prices)

    app = FastAPI(
        title="MarketSignal",
        description="Anticipation des crises de marché pour les entreprises.",
        version="0.1.0",
    )

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok", "observations": len(prices), "assets": list(prices.columns)}

    @app.get("/risk/score")
    def score() -> dict:
        snap = latest_snapshot(indicators)
        return {"date": snap.date, "score": snap.score, "level": snap.level}

    @app.get("/risk/indicators")
    def risk_indicators() -> dict:
        snap = latest_snapshot(indicators)
        return {"date": snap.date, "indicators": snap.indicators}

    @app.get("/risk/alerts")
    def risk_alerts() -> dict:
        snap = latest_snapshot(indicators)
        proba = float(model.predict_proba(indicators.tail(1)).iloc[-1])
        alerts = evaluate_alerts(snap, crisis_probability=proba)
        return {"date": snap.date, "alerts": [asdict(a) for a in alerts]}

    @app.get("/risk/history")
    def history(days: int = Query(default=180, ge=2, le=100_000)) -> dict:
        scores = risk_score(indicators).tail(days)
        return {
            "dates": [str(d.date()) for d in scores.index],
            "scores": [float(s) for s in scores],
        }

    @app.get("/predict")
    def predict() -> dict:
        proba = float(model.predict_proba(indicators.tail(1)).iloc[-1])
        return {
            "date": str(indicators.index[-1].date()),
            "crisis_probability": round(proba, 4),
            "horizon_days": model.horizon,
            "drawdown_threshold": model.threshold,
            "model_auc": model.auc,
        }

    @app.get("/", response_class=HTMLResponse)
    def dashboard() -> str:
        try:
            snap = latest_snapshot(indicators)
        except ValueError as exc:  # historique trop court
            raise HTTPException(status_code=500, detail=str(exc)) from exc
        proba = float(model.predict_proba(indicators.tail(1)).iloc[-1])
        alerts = evaluate_alerts(snap, crisis_probability=proba)
        scores = risk_score(indicators).tail(180)

        import json

        payload = {
            "date": snap.date,
            "score": snap.score,
            "level": snap.level,
            "probability": round(proba, 4),
            "indicators": snap.indicators,
            "alerts": [asdict(a) for a in alerts],
            "history": {
                "dates": [str(d.date()) for d in scores.index],
                "scores": [float(s) for s in scores],
            },
        }
        return _DASHBOARD_TEMPLATE.replace("__PAYLOAD__", json.dumps(payload, ensure_ascii=False))

    return app
