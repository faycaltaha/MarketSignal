"""Score de risque composite 0–100 et niveaux de risque associés.

Chaque indicateur est transformé en une contribution [0, 1] par
interpolation linéaire entre une borne « calme » et une borne « crise »
calibrées sur les ordres de grandeur historiques des marchés actions.
Le score final est la moyenne pondérée de ces contributions, sur 100.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

# (borne calme, borne crise) : en dessous de la borne calme la contribution
# vaut 0, au-dessus de la borne crise elle vaut 1. Les bornes des signaux
# faibles suivent les seuils documentés dans la littérature (cf.
# weak_signals.py) : un choc d'absorption > 1 écart-type précède la
# majorité des drawdowns sévères (Kritzman et al., 2011), une asymétrie
# de corrélation nettement positive précède les retournements (Ang &
# Chen, 2002), une densité de Granger croissante précède la contagion
# (Billio et al., 2012).
INDICATOR_BOUNDS: dict[str, tuple[float, float]] = {
    "volatility": (0.10, 0.45),            # vol annualisée 10 % -> 45 %
    "vol_shock_ratio": (1.0, 2.5),         # vol courte = vol longue -> 2.5x
    "drawdown": (-0.03, -0.20),            # -3 % -> -20 % depuis le pic
    "momentum": (0.0, -0.15),              # momentum 60j nul -> -15 %
    "mean_correlation": (0.35, 0.85),      # corrélation moyenne 0.35 -> 0.85
    "turbulence_pct": (0.70, 0.98),        # percentile de turbulence sur 1 an
    "absorption_shift": (0.0, 2.0),        # choc d'absorption en écarts-types
    "downside_correlation": (0.35, 0.85),  # corrélation des jours de baisse
    "correlation_asymmetry": (0.0, 0.25),  # baissière − haussière
    "granger_density": (0.10, 0.50),       # fraction de paires causales
}

WEIGHTS: dict[str, float] = {
    "volatility": 0.14,
    "vol_shock_ratio": 0.10,
    "drawdown": 0.14,
    "momentum": 0.08,
    "mean_correlation": 0.08,
    "turbulence_pct": 0.12,
    "absorption_shift": 0.12,
    "downside_correlation": 0.08,
    "correlation_asymmetry": 0.07,
    "granger_density": 0.07,
}

RISK_LEVELS: list[tuple[float, str]] = [
    (25.0, "faible"),
    (50.0, "modéré"),
    (75.0, "élevé"),
    (float("inf"), "critique"),
]


def _normalize(values: pd.Series, calm: float, crisis: float) -> pd.Series:
    """Interpole linéairement entre borne calme (0) et borne crise (1).

    Fonctionne aussi quand la borne crise est inférieure à la borne calme
    (drawdown, momentum : plus c'est bas, plus c'est risqué).
    """
    normalized = (values - calm) / (crisis - calm)
    return normalized.clip(0.0, 1.0)


def risk_score(indicators: pd.DataFrame) -> pd.Series:
    """Score de risque composite 0–100 pour chaque date."""
    total = pd.Series(0.0, index=indicators.index)
    for name, (calm, crisis) in INDICATOR_BOUNDS.items():
        total += WEIGHTS[name] * _normalize(indicators[name], calm, crisis)
    return (100.0 * total).round(1)


def risk_level(score: float) -> str:
    """Niveau lisible pour un score : faible, modéré, élevé ou critique."""
    if not np.isfinite(score) or score < 0:
        raise ValueError(f"Score invalide : {score}")
    for threshold, label in RISK_LEVELS:
        if score < threshold:
            return label
    raise AssertionError("unreachable")


@dataclass
class RiskSnapshot:
    """Photographie du risque à une date donnée."""

    date: str
    score: float
    level: str
    indicators: dict[str, float]


def latest_snapshot(indicators: pd.DataFrame) -> RiskSnapshot:
    """Construit la photographie du risque sur la dernière date disponible."""
    if indicators.empty:
        raise ValueError("Aucun indicateur disponible (historique trop court ?).")
    score = risk_score(indicators).iloc[-1]
    last = indicators.iloc[-1]
    return RiskSnapshot(
        date=str(indicators.index[-1].date()),
        score=float(score),
        level=risk_level(float(score)),
        indicators={k: round(float(v), 4) for k, v in last.items()},
    )
