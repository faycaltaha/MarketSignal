import numpy as np
import pandas as pd

from marketsignal.data import generate_demo_prices
from marketsignal.weak_signals import (
    absorption_ratio,
    absorption_shift,
    compute_weak_signals,
    conditional_correlations,
    granger_network_density,
    lead_lag_matrix,
    turbulence_index,
    turbulence_percentile,
)


def _single_asset(n=600, seed=0):
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range("2022-01-01", periods=n)
    prices = pd.DataFrame(
        {"a": 100 * np.exp(np.cumsum(rng.normal(0.0003, 0.01, n)))}, index=dates
    )
    return prices


def test_turbulence_spikes_on_abnormal_day(demo_prices):
    """Un choc simultané sur tous les actifs doit produire une turbulence extrême."""
    shocked = demo_prices.copy()
    shocked.iloc[-1] = shocked.iloc[-2] * 0.90  # -10 % sur tout le panier
    turb = turbulence_index(shocked)
    baseline = turb.iloc[-260:-1].dropna()
    assert turb.iloc[-1] > baseline.quantile(0.99)


def test_turbulence_percentile_in_unit_interval(demo_prices):
    pct = turbulence_percentile(demo_prices).dropna()
    assert pct.between(0, 1).all()


def test_absorption_ratio_bounds(demo_prices):
    ar = absorption_ratio(demo_prices).dropna()
    # Avec 4 actifs, 1 composante explique entre 1/4 et 100 % de la variance.
    assert ar.between(0.25, 1.0).all()


def test_absorption_ratio_high_when_common_factor():
    """Des actifs quasi identiques doivent avoir un ratio d'absorption proche de 1."""
    rng = np.random.default_rng(1)
    n = 400
    common = rng.normal(0, 0.02, n)
    dates = pd.bdate_range("2022-01-01", periods=n)
    prices = pd.DataFrame(
        {f"a{i}": 100 * np.exp(np.cumsum(common + rng.normal(0, 0.001, n)))
         for i in range(4)},
        index=dates,
    )
    assert absorption_ratio(prices).dropna().iloc[-1] > 0.95


def test_absorption_shift_zero_for_single_asset():
    shift = absorption_shift(_single_asset())
    assert (shift.dropna() == 0.0).all()


def test_conditional_correlations_columns(demo_prices):
    frame = conditional_correlations(demo_prices)
    assert list(frame.columns) == [
        "downside_correlation", "upside_correlation", "correlation_asymmetry",
    ]
    valid = frame.dropna()
    assert valid["downside_correlation"].between(-1, 1).all()
    assert valid["upside_correlation"].between(-1, 1).all()


def test_conditional_correlations_single_asset_zero():
    frame = conditional_correlations(_single_asset())
    assert (frame == 0.0).all().all()


def test_granger_density_in_unit_interval(demo_prices):
    density = granger_network_density(demo_prices).dropna()
    assert density.between(0, 1).all()


def test_granger_density_single_asset_zero():
    density = granger_network_density(_single_asset())
    assert (density == 0.0).all()


def test_lead_lag_detects_engineered_leader():
    """Le générateur fait mener actif_A de 3 jours : le lead-lag doit le voir."""
    prices = generate_demo_prices(n_days=900, n_assets=4, seed=11, lead_lag_days=3,
                                  crisis_probability=0.01)
    matrix = lead_lag_matrix(prices, window=900)
    assert not matrix.empty
    top = matrix.head(6)
    # actif_A doit apparaître comme meneur dans les relations les plus fortes.
    assert (top["leader"] == "actif_A").any()


def test_lead_lag_empty_for_single_asset():
    matrix = lead_lag_matrix(_single_asset())
    assert matrix.empty


def test_compute_weak_signals_columns(demo_prices):
    frame = compute_weak_signals(demo_prices)
    assert list(frame.columns) == [
        "turbulence_pct", "absorption_shift", "downside_correlation",
        "correlation_asymmetry", "granger_density",
    ]
    assert not frame.dropna().empty
