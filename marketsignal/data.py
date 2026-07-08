"""Chargement des données de prix et génération de données synthétiques.

Le format attendu est un CSV avec une colonne ``date`` (ISO YYYY-MM-DD) et
une colonne de prix de clôture par actif suivi.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


def load_prices(path: str | Path) -> pd.DataFrame:
    """Charge un CSV de prix et retourne un DataFrame indexé par date.

    Valide la présence de la colonne ``date``, la monotonie temporelle et
    l'absence de colonnes non numériques.
    """
    df = pd.read_csv(path)
    if "date" not in df.columns:
        raise ValueError("Le CSV doit contenir une colonne 'date'.")
    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date").sort_index()
    if df.empty:
        raise ValueError("Le fichier ne contient aucune ligne de données.")

    non_numeric = [c for c in df.columns if not pd.api.types.is_numeric_dtype(df[c])]
    if non_numeric:
        raise ValueError(
            f"Colonnes non numériques détectées : {non_numeric}. "
            "Chaque colonne (hors 'date') doit contenir des prix."
        )
    if (df <= 0).any().any():
        raise ValueError("Les prix doivent être strictement positifs.")
    # Les jours fériés/données manquantes sont propagés depuis la veille.
    df = df.ffill().dropna()
    return df


def generate_demo_prices(
    n_days: int = 1500,
    n_assets: int = 4,
    seed: int = 42,
    crisis_probability: float = 0.004,
) -> pd.DataFrame:
    """Génère des prix synthétiques avec des régimes de crise incorporés.

    Le marché alterne entre un régime calme (dérive positive, faible
    volatilité, corrélations modérées) et des épisodes de crise (dérive
    négative, volatilité triplée, corrélations proches de 1) déclenchés
    aléatoirement et durant 20 à 60 jours. Cela permet de démontrer et de
    tester le logiciel hors ligne sur des données au comportement réaliste.
    """
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range("2020-01-01", periods=n_days)

    calm_drift, calm_vol, calm_corr = 0.0004, 0.010, 0.35
    crisis_drift, crisis_vol, crisis_corr = -0.004, 0.032, 0.85

    in_crisis = False
    crisis_days_left = 0
    returns = np.zeros((n_days, n_assets))
    for t in range(n_days):
        if in_crisis:
            crisis_days_left -= 1
            if crisis_days_left <= 0:
                in_crisis = False
        elif rng.random() < crisis_probability:
            in_crisis = True
            crisis_days_left = int(rng.integers(20, 61))

        drift = crisis_drift if in_crisis else calm_drift
        vol = crisis_vol if in_crisis else calm_vol
        corr = crisis_corr if in_crisis else calm_corr

        cov = np.full((n_assets, n_assets), corr) * vol**2
        np.fill_diagonal(cov, vol**2)
        returns[t] = rng.multivariate_normal(np.full(n_assets, drift), cov)

    prices = 100.0 * np.exp(np.cumsum(returns, axis=0))
    columns = [f"actif_{chr(ord('A') + i)}" for i in range(n_assets)]
    df = pd.DataFrame(prices, index=dates, columns=columns)
    df.index.name = "date"
    return df
