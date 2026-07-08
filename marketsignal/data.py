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
    lead_lag_days: int = 3,
) -> pd.DataFrame:
    """Génère des prix synthétiques avec des régimes de crise incorporés.

    Le marché alterne entre un régime calme (dérive positive, faible
    volatilité, corrélations modérées) et des épisodes de crise (dérive
    négative, volatilité triplée, corrélations proches de 1) déclenchés
    aléatoirement et durant 20 à 60 jours.

    Le premier actif (``actif_A``) joue le rôle d'une série *amont* de
    chaîne d'approvisionnement (par exemple un indice de fret) : il entre
    en crise ``lead_lag_days`` jours avant les autres, ce qui incorpore
    une structure avance/retard détectable par les signaux faibles
    (lead-lag, causalité de Granger).
    """
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range("2020-01-01", periods=n_days)

    calm_drift, calm_vol, calm_corr = 0.0004, 0.010, 0.35
    crisis_drift, crisis_vol, crisis_corr = -0.004, 0.032, 0.85

    # Régime de la série amont (meneuse), les autres suivent avec retard.
    leader_flags = np.zeros(n_days, dtype=bool)
    in_crisis = False
    crisis_days_left = 0
    for t in range(n_days):
        if in_crisis:
            crisis_days_left -= 1
            if crisis_days_left <= 0:
                in_crisis = False
        elif rng.random() < crisis_probability:
            in_crisis = True
            crisis_days_left = int(rng.integers(20, 61))
        leader_flags[t] = in_crisis

    flags = np.zeros((n_days, n_assets), dtype=bool)
    flags[:, 0] = leader_flags
    if n_assets > 1 and lead_lag_days > 0:
        flags[lead_lag_days:, 1:] = leader_flags[:-lead_lag_days, None]
    else:
        flags[:, 1:] = leader_flags[:, None]

    returns = np.zeros((n_days, n_assets))
    for t in range(n_days):
        vols = np.where(flags[t], crisis_vol, calm_vol)
        drifts = np.where(flags[t], crisis_drift, calm_drift)
        corr = crisis_corr if flags[t].any() else calm_corr
        cov = corr * np.outer(vols, vols)
        np.fill_diagonal(cov, vols**2)
        returns[t] = rng.multivariate_normal(drifts, cov)

    prices = 100.0 * np.exp(np.cumsum(returns, axis=0))
    columns = [f"actif_{chr(ord('A') + i)}" for i in range(n_assets)]
    df = pd.DataFrame(prices, index=dates, columns=columns)
    df.index.name = "date"
    return df
