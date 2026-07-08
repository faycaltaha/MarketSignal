"""Signaux faibles : mesures fines de corrélation et de contagion.

Ce module implémente des mesures issues de la recherche académique en
finance systémique, particulièrement adaptées à la surveillance des
chaînes d'approvisionnement lorsqu'on alimente MarketSignal avec des
séries amont/aval (indices de fret, prix de matières premières
critiques, délais fournisseurs PMI, indices sectoriels...) :

- **Indice de turbulence** (Kritzman & Li, 2010, *Skulls, Financial
  Turbulence, and Risk Management*, Financial Analysts Journal) :
  distance de Mahalanobis des rendements du jour par rapport à leur
  comportement historique. Capture les jours « statistiquement
  anormaux » même quand la volatilité reste basse — typique des débuts
  de rupture d'approvisionnement.

- **Ratio d'absorption** (Kritzman, Li, Page & Rigobon, 2011,
  *Principal Components as a Measure of Systemic Risk*, Journal of
  Portfolio Management) : fraction de la variance totale expliquée par
  les premières composantes principales. Quand il monte, les actifs se
  mettent à bouger ensemble : le système devient fragile et un choc
  local (un maillon de la chaîne) se propage à tout le réseau. Le
  signal opérationnel est le **choc d'absorption standardisé**
  (moyenne 15 j − moyenne 1 an, en écarts-types).

- **Corrélation baissière et asymétrie de corrélation** (Longin &
  Solnik, 2001, Journal of Finance ; Ang & Chen, 2002, Journal of
  Financial Economics) : les corrélations conditionnelles aux jours de
  baisse dépassent celles des jours de hausse à l'approche des crises.
  L'asymétrie (baissière − haussière) est un signal faible précoce que
  la corrélation moyenne classique dilue.

- **Densité du réseau de causalité de Granger** (Billio, Getmansky,
  Lo & Pelizzon, 2012, *Econometric Measures of Connectedness and
  Systemic Risk*, Journal of Financial Economics) : fraction des paires
  d'actifs où le passé de l'un prédit significativement l'autre. Une
  densité croissante signale des canaux de contagion qui s'ouvrent
  entre maillons de la chaîne.

- **Matrice avance/retard (lead-lag)** : identifie quelles séries
  *mènent* les autres et avec quel délai — l'esprit des indicateurs
  avancés du Global Supply Chain Pressure Index de la Fed de New York
  (Benigno, di Giovanni, Groen & Noble, 2022) : le fret (Baltic Dry,
  Harpex) et les délais fournisseurs bougent avant l'activité aval.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

TURBULENCE_WINDOW = 120
TURBULENCE_RANK_WINDOW = 252
ABSORPTION_WINDOW = 120
ABSORPTION_SHORT = 15
ABSORPTION_LONG = 252
CONDITIONAL_CORR_WINDOW = 120
GRANGER_WINDOW = 120
GRANGER_STRIDE = 5
GRANGER_T_CRITICAL = 1.96
LEAD_LAG_WINDOW = 250
MAX_LEAD_LAG = 5


def _returns_matrix(prices: pd.DataFrame) -> tuple[np.ndarray, pd.DatetimeIndex]:
    returns = prices.pct_change().iloc[1:]
    return returns.to_numpy(), returns.index


def turbulence_index(prices: pd.DataFrame, window: int = TURBULENCE_WINDOW) -> pd.Series:
    """Distance de Mahalanobis des rendements du jour (Kritzman & Li, 2010).

    d_t = (r_t − μ)' Σ⁻¹ (r_t − μ), avec μ et Σ estimés sur les ``window``
    jours précédents (hors jour courant). Une valeur élevée signale un
    jour statistiquement inhabituel, même à faible volatilité.
    """
    R, index = _returns_matrix(prices)
    n_days, n_assets = R.shape
    out = np.full(n_days, np.nan)
    ridge = 1e-10 * np.eye(n_assets)
    for t in range(window, n_days):
        hist = R[t - window:t]
        mu = hist.mean(axis=0)
        cov = np.atleast_2d(np.cov(hist, rowvar=False)) + ridge
        diff = R[t] - mu
        out[t] = float(diff @ np.linalg.solve(cov, diff))
    return pd.Series(out, index=index, name="turbulence")


def turbulence_percentile(
    prices: pd.DataFrame,
    window: int = TURBULENCE_WINDOW,
    rank_window: int = TURBULENCE_RANK_WINDOW,
) -> pd.Series:
    """Rang percentile [0, 1] de la turbulence du jour sur l'année écoulée."""
    turb = turbulence_index(prices, window)

    def _rank(values: np.ndarray) -> float:
        return float((values[:-1] <= values[-1]).mean())

    return turb.rolling(rank_window).apply(_rank, raw=True)


def absorption_ratio(
    prices: pd.DataFrame,
    window: int = ABSORPTION_WINDOW,
    n_components: int | None = None,
) -> pd.Series:
    """Ratio d'absorption (Kritzman, Li, Page & Rigobon, 2011).

    Fraction de la variance totale expliquée par les ``n_components``
    premières composantes principales (par défaut 1/5 du nombre
    d'actifs, comme dans l'article). Vaut 1 pour un actif unique.
    """
    R, index = _returns_matrix(prices)
    n_days, n_assets = R.shape
    if n_components is None:
        n_components = max(1, round(n_assets / 5))
    n_components = min(n_components, n_assets)

    out = np.full(n_days, np.nan)
    for t in range(window, n_days):
        cov = np.atleast_2d(np.cov(R[t - window:t], rowvar=False))
        eigvals = np.linalg.eigvalsh(cov)  # ordre croissant
        total = eigvals.sum()
        out[t] = float(eigvals[-n_components:].sum() / total) if total > 0 else np.nan
    return pd.Series(out, index=index, name="absorption_ratio")


def absorption_shift(
    prices: pd.DataFrame,
    window: int = ABSORPTION_WINDOW,
    short: int = ABSORPTION_SHORT,
    long: int = ABSORPTION_LONG,
) -> pd.Series:
    """Choc d'absorption standardisé : (moyenne courte − moyenne longue) / σ longue.

    C'est le signal opérationnel de l'article de 2011 : un choc supérieur
    à 1 écart-type a historiquement précédé la majorité des drawdowns
    sévères. Vaut 0 quand le ratio est constant (actif unique).
    """
    ar = absorption_ratio(prices, window)
    short_ma = ar.rolling(short).mean()
    long_ma = ar.rolling(long).mean()
    long_std = ar.rolling(long).std()
    shift = (short_ma - long_ma) / long_std
    return shift.replace([np.inf, -np.inf], np.nan).where(long_std > 1e-12, 0.0)


def conditional_correlations(
    prices: pd.DataFrame, window: int = CONDITIONAL_CORR_WINDOW, min_obs: int = 20
) -> pd.DataFrame:
    """Corrélations moyennes conditionnelles aux jours de baisse et de hausse.

    Colonnes : ``downside_correlation``, ``upside_correlation`` et
    ``correlation_asymmetry`` (baissière − haussière, cf. Ang & Chen,
    2002). Le conditionnement se fait sur le signe du rendement du
    portefeuille équipondéré. Pour un actif unique, tout vaut 0.
    """
    R, index = _returns_matrix(prices)
    n_days, n_assets = R.shape
    if n_assets < 2:
        zeros = pd.Series(0.0, index=index)
        return pd.DataFrame({
            "downside_correlation": zeros,
            "upside_correlation": zeros,
            "correlation_asymmetry": zeros,
        })

    portfolio = R.mean(axis=1)
    iu = np.triu_indices(n_assets, k=1)
    down = np.full(n_days, np.nan)
    up = np.full(n_days, np.nan)
    for t in range(window, n_days):
        sl = slice(t - window, t)
        hist, port = R[sl], portfolio[sl]
        for mask, dest in ((port < 0, down), (port >= 0, up)):
            subset = hist[mask]
            if len(subset) >= min_obs:
                corr = np.corrcoef(subset, rowvar=False)
                dest[t] = float(corr[iu].mean())
    frame = pd.DataFrame(
        {"downside_correlation": down, "upside_correlation": up}, index=index
    ).ffill()
    frame["correlation_asymmetry"] = (
        frame["downside_correlation"] - frame["upside_correlation"]
    )
    return frame


def _granger_significant(x: np.ndarray, y: np.ndarray) -> bool:
    """Teste si x « Granger-cause » y au retard 1 (t-stat > seuil critique).

    Régression y_t = c + a·y_{t−1} + b·x_{t−1} ; retourne True si le
    coefficient b est significatif à 5 %.
    """
    y_t, y_lag, x_lag = y[1:], y[:-1], x[:-1]
    X = np.column_stack([np.ones_like(y_lag), y_lag, x_lag])
    coef, _, rank, _ = np.linalg.lstsq(X, y_t, rcond=None)
    if rank < 3:
        return False
    residuals = y_t - X @ coef
    dof = len(y_t) - 3
    sigma2 = float(residuals @ residuals) / dof
    xtx_inv = np.linalg.pinv(X.T @ X)
    se_b = np.sqrt(sigma2 * xtx_inv[2, 2])
    if se_b < 1e-12:
        return False
    return abs(coef[2] / se_b) > GRANGER_T_CRITICAL


def granger_network_density(
    prices: pd.DataFrame,
    window: int = GRANGER_WINDOW,
    stride: int = GRANGER_STRIDE,
) -> pd.Series:
    """Densité du réseau de causalité de Granger (Billio et al., 2012).

    Fraction des paires ordonnées (i → j) où le rendement passé de i
    prédit significativement celui de j sur la fenêtre glissante. La
    densité monte quand des canaux de contagion s'ouvrent entre les
    séries suivies. Calculée tous les ``stride`` jours puis propagée.
    Vaut 0 pour un actif unique.
    """
    R, index = _returns_matrix(prices)
    n_days, n_assets = R.shape
    if n_assets < 2:
        return pd.Series(0.0, index=index)

    n_pairs = n_assets * (n_assets - 1)
    out = pd.Series(np.nan, index=index)
    for t in range(window, n_days, stride):
        hist = R[t - window:t]
        significant = sum(
            _granger_significant(hist[:, i], hist[:, j])
            for i in range(n_assets)
            for j in range(n_assets)
            if i != j
        )
        out.iloc[t] = significant / n_pairs
    return out.ffill()


def lead_lag_matrix(
    prices: pd.DataFrame,
    window: int = LEAD_LAG_WINDOW,
    max_lag: int = MAX_LEAD_LAG,
) -> pd.DataFrame:
    """Relations avance/retard entre séries sur la fenêtre récente.

    Pour chaque paire ordonnée (meneur → suiveur), calcule la
    corrélation entre le rendement du meneur décalé de k jours et celui
    du suiveur, pour k = 1..max_lag, et retient le décalage le plus
    corrélé. Retourne un DataFrame trié par |corrélation| décroissante,
    colonnes : ``leader``, ``follower``, ``lag_days``, ``correlation``.

    C'est l'outil de détection des signaux faibles de chaîne
    d'approvisionnement : si « fret_maritime » mène « indice_secteur »
    de 3 jours avec une corrélation élevée, surveiller le fret donne
    3 jours d'avance sur l'aval.
    """
    returns = prices.pct_change().iloc[1:].tail(window)
    columns = list(returns.columns)
    rows = []
    for leader in columns:
        for follower in columns:
            if leader == follower:
                continue
            best_corr, best_lag = 0.0, 0
            for lag in range(1, max_lag + 1):
                lead = returns[leader].iloc[:-lag].to_numpy()
                follow = returns[follower].iloc[lag:].to_numpy()
                if len(lead) < 30 or np.std(lead) < 1e-12 or np.std(follow) < 1e-12:
                    continue
                corr = float(np.corrcoef(lead, follow)[0, 1])
                if abs(corr) > abs(best_corr):
                    best_corr, best_lag = corr, lag
            if best_lag > 0:
                rows.append({
                    "leader": leader,
                    "follower": follower,
                    "lag_days": best_lag,
                    "correlation": round(best_corr, 4),
                })
    frame = pd.DataFrame(rows, columns=["leader", "follower", "lag_days", "correlation"])
    if frame.empty:
        return frame
    return (
        frame.reindex(frame["correlation"].abs().sort_values(ascending=False).index)
        .reset_index(drop=True)
    )


def compute_weak_signals(prices: pd.DataFrame) -> pd.DataFrame:
    """Calcule les signaux faibles alignés sur l'index des rendements.

    Colonnes : ``turbulence_pct``, ``absorption_shift``,
    ``downside_correlation``, ``correlation_asymmetry``,
    ``granger_density``.
    """
    conditional = conditional_correlations(prices)
    return pd.DataFrame(
        {
            "turbulence_pct": turbulence_percentile(prices),
            "absorption_shift": absorption_shift(prices),
            "downside_correlation": conditional["downside_correlation"],
            "correlation_asymmetry": conditional["correlation_asymmetry"],
            "granger_density": granger_network_density(prices),
        }
    )
