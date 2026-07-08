"""Moteur d'alertes : transforme les indicateurs en messages actionnables."""

from __future__ import annotations

from dataclasses import dataclass

from .scoring import RiskSnapshot


@dataclass
class Alert:
    """Alerte métier : sévérité (``info``, ``warning``, ``critical``) + message."""

    severity: str
    code: str
    message: str


def evaluate_alerts(snapshot: RiskSnapshot, crisis_probability: float | None = None) -> list[Alert]:
    """Évalue les règles d'alerte sur une photographie du risque.

    ``crisis_probability`` est la sortie du modèle ML si disponible.
    Les alertes sont triées de la plus sévère à la moins sévère.
    """
    alerts: list[Alert] = []
    ind = snapshot.indicators

    if snapshot.score >= 75:
        alerts.append(Alert(
            "critical", "SCORE_CRITIQUE",
            f"Score de risque critique ({snapshot.score:.0f}/100) : configuration de "
            "crise avérée. Activez votre plan de continuité et réduisez les expositions.",
        ))
    elif snapshot.score >= 50:
        alerts.append(Alert(
            "warning", "SCORE_ELEVE",
            f"Score de risque élevé ({snapshot.score:.0f}/100) : surveillez "
            "quotidiennement et préparez les mesures de couverture.",
        ))

    if crisis_probability is not None and crisis_probability >= 0.5:
        alerts.append(Alert(
            "critical" if crisis_probability >= 0.75 else "warning",
            "PROBABILITE_CRISE",
            f"Le modèle estime à {crisis_probability:.0%} la probabilité d'un "
            "drawdown sévère à court terme.",
        ))

    if ind.get("vol_shock_ratio", 0) >= 1.8:
        alerts.append(Alert(
            "warning", "CHOC_VOLATILITE",
            f"Choc de volatilité : la volatilité récente est {ind['vol_shock_ratio']:.1f}x "
            "supérieure à sa moyenne de long terme.",
        ))

    if ind.get("drawdown", 0) <= -0.10:
        alerts.append(Alert(
            "warning", "DRAWDOWN",
            f"Le panier suivi a perdu {abs(ind['drawdown']):.0%} depuis son plus haut annuel.",
        ))

    if ind.get("mean_correlation", 0) >= 0.7:
        alerts.append(Alert(
            "warning", "CORRELATION_SYSTEMIQUE",
            f"Corrélation moyenne entre actifs à {ind['mean_correlation']:.2f} : "
            "la diversification ne protège plus, signe de stress systémique.",
        ))

    if not alerts:
        alerts.append(Alert(
            "info", "RAS",
            f"Aucun signal de crise : score {snapshot.score:.0f}/100 "
            f"(niveau {snapshot.level}).",
        ))

    order = {"critical": 0, "warning": 1, "info": 2}
    alerts.sort(key=lambda a: order[a.severity])
    return alerts
