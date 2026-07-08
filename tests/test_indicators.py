import numpy as np
import pandas as pd
import pytest

from marketsignal.indicators import (
    compute_indicators,
    drawdown,
    mean_cross_correlation,
    momentum,
    portfolio_returns,
    volatility_shock_ratio,
)


def test_compute_indicators_columns_and_no_nan(demo_prices):
    from marketsignal.indicators import INDICATOR_COLUMNS

    ind = compute_indicators(demo_prices)
    assert list(ind.columns) == INDICATOR_COLUMNS
    assert not ind.isna().any().any()
    # Les fenêtres initiales (turbulence 120j + percentile 252j) sont perdues.
    assert len(ind) > 700


def test_drawdown_is_nonpositive(demo_prices):
    dd = drawdown(demo_prices)
    assert (dd <= 1e-12).all()


def test_drawdown_detects_crash():
    dates = pd.bdate_range("2024-01-01", periods=100)
    level = np.concatenate([np.full(50, 100.0), np.full(50, 80.0)])
    prices = pd.DataFrame({"a": level}, index=dates)
    assert drawdown(prices).iloc[-1] == pytest.approx(-0.20)


def test_momentum_sign():
    dates = pd.bdate_range("2024-01-01", periods=100)
    up = pd.DataFrame({"a": np.linspace(100, 150, 100)}, index=dates)
    assert momentum(up, window=60).iloc[-1] > 0


def test_volatility_shock_ratio_rises_on_regime_change():
    rng = np.random.default_rng(0)
    calm = rng.normal(0, 0.005, 200)
    stressed = rng.normal(0, 0.03, 30)
    returns = pd.Series(
        np.concatenate([calm, stressed]),
        index=pd.bdate_range("2023-01-01", periods=230),
    )
    ratio = volatility_shock_ratio(returns)
    assert ratio.iloc[-1] > 1.5


def test_mean_correlation_in_range(demo_prices):
    corr = mean_cross_correlation(demo_prices).dropna()
    assert corr.between(-1.0, 1.0).all()


def test_mean_correlation_single_asset_is_zero(demo_prices):
    single = demo_prices.iloc[:, :1]
    corr = mean_cross_correlation(single)
    assert (corr == 0.0).all()


def test_portfolio_returns_length(demo_prices):
    returns = portfolio_returns(demo_prices)
    assert len(returns) == len(demo_prices) - 1
