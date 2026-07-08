import numpy as np
import pandas as pd
import pytest

from marketsignal.data import generate_demo_prices
from marketsignal.indicators import compute_indicators
from marketsignal.model import CrisisModel, label_crises


def test_label_crises_detects_engineered_crash():
    dates = pd.bdate_range("2024-01-01", periods=200)
    level = np.concatenate([np.full(100, 100.0), np.full(100, 80.0)])
    prices = pd.DataFrame({"a": level}, index=dates)
    labels = label_crises(prices, horizon=30, threshold=-0.10)
    # Juste avant la chute : crise dans l'horizon.
    assert labels.iloc[95] == 1.0
    # Bien avant la chute (chute hors horizon de 30 jours) : pas de crise.
    assert labels.iloc[10] == 0.0
    # Les dernières dates n'ont pas de futur observable.
    assert labels.iloc[-30:].isna().all()


def test_fit_predict_roundtrip(demo_prices, tmp_path):
    model = CrisisModel().fit(demo_prices)
    assert model.is_fitted

    ind = compute_indicators(demo_prices)
    proba = model.predict_proba(ind)
    assert proba.between(0, 1).all()

    path = tmp_path / "model.json"
    model.save(path)
    loaded = CrisisModel.load(path)
    reloaded_proba = loaded.predict_proba(ind)
    pd.testing.assert_series_equal(proba, reloaded_proba)


def test_model_discriminates(demo_prices):
    """Le modèle doit faire mieux que le hasard sur des données à régimes."""
    model = CrisisModel().fit(demo_prices)
    assert model.auc is None or model.auc > 0.6


def test_fit_rejects_short_history():
    prices = generate_demo_prices(n_days=120, seed=3)
    with pytest.raises(ValueError, match="insuffisant"):
        CrisisModel().fit(prices)


def test_fit_rejects_history_without_crisis():
    dates = pd.bdate_range("2020-01-01", periods=800)
    # Croissance régulière sans aucune crise.
    prices = pd.DataFrame({"a": np.linspace(100, 200, 800)}, index=dates)
    with pytest.raises(ValueError, match="aucun épisode de crise"):
        CrisisModel().fit(prices)


def test_predict_unfitted_raises(demo_prices):
    ind = compute_indicators(demo_prices)
    with pytest.raises(ValueError, match="non entraîné"):
        CrisisModel().predict_proba(ind)


def test_load_rejects_invalid_file(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text('{"horizon": 30, "threshold": -0.1, "coef": []}')
    with pytest.raises(ValueError, match="invalide"):
        CrisisModel.load(path)
