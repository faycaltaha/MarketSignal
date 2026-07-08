"""Modèle prédictif de crise.

Une date est étiquetée *pré-crise* (classe 1) si le portefeuille subit,
dans les ``horizon`` jours suivants, un drawdown d'au moins ``threshold``
par rapport au niveau courant. Une régression logistique est entraînée
sur les indicateurs d'alerte pour estimer la probabilité de cet
événement, avec une évaluation en découpage temporel strict (le passé
prédit le futur, jamais l'inverse).

Le modèle entraîné est sérialisable en JSON (coefficients + paramètres de
standardisation), sans dépendance à pickle.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

from .indicators import INDICATOR_COLUMNS, compute_indicators

DEFAULT_HORIZON = 30       # jours de bourse
DEFAULT_THRESHOLD = -0.10  # drawdown de 10 %

FEATURES = list(INDICATOR_COLUMNS)


def label_crises(
    prices: pd.DataFrame,
    horizon: int = DEFAULT_HORIZON,
    threshold: float = DEFAULT_THRESHOLD,
) -> pd.Series:
    """Étiquette chaque date : 1 si un drawdown sévère survient dans l'horizon.

    Les ``horizon`` dernières dates, dont le futur est inconnu, valent NaN.
    """
    level = prices.mean(axis=1)
    # Plus bas atteint sur les `horizon` prochains jours (fenêtre future).
    future_min = level[::-1].rolling(horizon).min()[::-1].shift(-1)
    future_drawdown = future_min / level - 1.0
    labels = (future_drawdown <= threshold).astype(float)
    labels.iloc[-horizon:] = np.nan
    return labels


@dataclass
class CrisisModel:
    """Régression logistique + standardisation, sérialisable en JSON."""

    horizon: int = DEFAULT_HORIZON
    threshold: float = DEFAULT_THRESHOLD
    coef: list[float] = field(default_factory=list)
    intercept: float = 0.0
    feature_means: list[float] = field(default_factory=list)
    feature_stds: list[float] = field(default_factory=list)
    auc: float | None = None

    @property
    def is_fitted(self) -> bool:
        return len(self.coef) == len(FEATURES)

    def fit(self, prices: pd.DataFrame, test_fraction: float = 0.25) -> "CrisisModel":
        """Entraîne le modèle et mesure l'AUC sur la fin de l'historique.

        Les ``test_fraction`` derniers pour cent servent de jeu de test
        temporel ; le modèle final est ensuite réentraîné sur tout
        l'historique étiquetable.
        """
        indicators = compute_indicators(prices)
        labels = label_crises(prices, self.horizon, self.threshold)
        data = indicators.join(labels.rename("label"), how="inner").dropna()
        if len(data) < 100:
            raise ValueError(
                f"Historique insuffisant : {len(data)} points étiquetés, minimum 100."
            )
        if data["label"].nunique() < 2:
            raise ValueError(
                "L'historique ne contient aucun épisode de crise selon les "
                f"paramètres (horizon={self.horizon}j, seuil={self.threshold:.0%}) : "
                "impossible d'entraîner le modèle. Assouplissez le seuil ou "
                "allongez l'historique."
            )

        X = data[FEATURES].to_numpy()
        y = data["label"].to_numpy()

        split = int(len(data) * (1 - test_fraction))
        if len(np.unique(y[:split])) == 2 and len(np.unique(y[split:])) == 2:
            eval_model = self._new_estimator()
            mean, std = X[:split].mean(axis=0), X[:split].std(axis=0) + 1e-12
            eval_model.fit((X[:split] - mean) / std, y[:split])
            proba = eval_model.predict_proba((X[split:] - mean) / std)[:, 1]
            self.auc = float(roc_auc_score(y[split:], proba))
        else:
            self.auc = None  # pas de crise dans l'une des deux périodes

        mean, std = X.mean(axis=0), X.std(axis=0) + 1e-12
        final = self._new_estimator()
        final.fit((X - mean) / std, y)
        self.coef = final.coef_[0].tolist()
        self.intercept = float(final.intercept_[0])
        self.feature_means = mean.tolist()
        self.feature_stds = std.tolist()
        return self

    @staticmethod
    def _new_estimator() -> LogisticRegression:
        return LogisticRegression(class_weight="balanced", max_iter=1000)

    def predict_proba(self, indicators: pd.DataFrame) -> pd.Series:
        """Probabilité de crise pour chaque ligne d'indicateurs."""
        if not self.is_fitted:
            raise ValueError("Modèle non entraîné : appelez fit() ou load().")
        X = indicators[FEATURES].to_numpy()
        Xn = (X - np.array(self.feature_means)) / np.array(self.feature_stds)
        z = Xn @ np.array(self.coef) + self.intercept
        return pd.Series(1.0 / (1.0 + np.exp(-z)), index=indicators.index)

    def save(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps(self.__dict__, indent=2))

    @classmethod
    def load(cls, path: str | Path) -> "CrisisModel":
        payload = json.loads(Path(path).read_text())
        model = cls(**payload)
        if not model.is_fitted:
            raise ValueError(f"Fichier de modèle invalide ou incomplet : {path}")
        return model
