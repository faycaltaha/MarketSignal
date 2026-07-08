"""Indicateurs d'alerte précoce calculés sur un panier d'actifs.

Tous les indicateurs sont calculés sur le portefeuille équipondéré des
colonnes du DataFrame de prix, sauf la corrélation croisée qui utilise
les actifs individuels. Les fenêtres sont exprimées en jours de bourse.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

TRADING_DAYS_PER_YEAR = 252

# Fenêtres par défaut (jours de bourse)
SHORT_VOL_WINDOW = 20
LONG_VOL_WINDOW = 120
DRAWDOWN_WINDOW = 252
MOMENTUM_WINDOW = 60
CORRELATION_WINDOW = 60


def portfolio_returns(prices: pd.DataFrame) -> pd.Series:
    """Rendements journaliers du portefeuille équipondéré."""
    return prices.pct_change().mean(axis=1).iloc[1:]


def rolling_volatility(returns: pd.Series, window: int = SHORT_VOL_WINDOW) -> pd.Series:
    """Volatilité glissante annualisée."""
    return returns.rolling(window).std() * np.sqrt(TRADING_DAYS_PER_YEAR)


def volatility_shock_ratio(
    returns: pd.Series,
    short_window: int = SHORT_VOL_WINDOW,
    long_window: int = LONG_VOL_WINDOW,
) -> pd.Series:
    """Ratio volatilité courte / volatilité longue.

    Un ratio nettement supérieur à 1 signale un choc de volatilité récent,
    précurseur fréquent des crises.
    """
    short_vol = returns.rolling(short_window).std()
    long_vol = returns.rolling(long_window).std()
    return short_vol / long_vol


def drawdown(prices: pd.DataFrame, window: int = DRAWDOWN_WINDOW) -> pd.Series:
    """Drawdown courant du portefeuille par rapport à son plus haut glissant.

    Valeur négative ou nulle : -0.15 signifie une perte de 15 % depuis le pic.
    """
    level = prices.mean(axis=1)
    rolling_peak = level.rolling(window, min_periods=1).max()
    return level / rolling_peak - 1.0


def momentum(prices: pd.DataFrame, window: int = MOMENTUM_WINDOW) -> pd.Series:
    """Rendement du portefeuille sur les ``window`` derniers jours."""
    level = prices.mean(axis=1)
    return level.pct_change(window)


def mean_cross_correlation(
    prices: pd.DataFrame, window: int = CORRELATION_WINDOW
) -> pd.Series:
    """Corrélation moyenne entre paires d'actifs sur une fenêtre glissante.

    Lorsque tout devient corrélé, la diversification disparaît : c'est un
    marqueur classique de stress systémique. Pour un actif unique, retourne 0.
    """
    returns = prices.pct_change().iloc[1:]
    n = returns.shape[1]
    if n < 2:
        return pd.Series(0.0, index=returns.index)

    pair_count = n * (n - 1) / 2
    corr = returns.rolling(window).corr()
    # Moyenne des éléments hors diagonale de chaque matrice de corrélation.
    mean_corr = (corr.groupby(level=0).sum().sum(axis=1) - n) / (2 * pair_count)
    return mean_corr.reindex(returns.index)


def compute_indicators(prices: pd.DataFrame) -> pd.DataFrame:
    """Calcule tous les indicateurs et les aligne dans un DataFrame.

    Colonnes : ``volatility``, ``vol_shock_ratio``, ``drawdown``,
    ``momentum``, ``mean_correlation``. Les premières lignes (fenêtres
    incomplètes) sont supprimées.
    """
    returns = portfolio_returns(prices)
    out = pd.DataFrame(
        {
            "volatility": rolling_volatility(returns),
            "vol_shock_ratio": volatility_shock_ratio(returns),
            "drawdown": drawdown(prices).reindex(returns.index),
            "momentum": momentum(prices).reindex(returns.index),
            "mean_correlation": mean_cross_correlation(prices),
        }
    )
    return out.dropna()
