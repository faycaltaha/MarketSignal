import pandas as pd
import pytest

from marketsignal.data import generate_demo_prices, load_prices


def test_generate_demo_prices_shape(demo_prices):
    assert demo_prices.shape == (1200, 4)
    assert (demo_prices > 0).all().all()
    assert demo_prices.index.is_monotonic_increasing


def test_generate_demo_prices_reproducible():
    a = generate_demo_prices(n_days=100, seed=1)
    b = generate_demo_prices(n_days=100, seed=1)
    pd.testing.assert_frame_equal(a, b)


def test_load_prices_roundtrip(tmp_path, demo_prices):
    path = tmp_path / "prices.csv"
    demo_prices.to_csv(path)
    loaded = load_prices(path)
    assert list(loaded.columns) == list(demo_prices.columns)
    assert len(loaded) == len(demo_prices)


def test_load_prices_requires_date_column(tmp_path):
    path = tmp_path / "bad.csv"
    path.write_text("jour,actif\n2024-01-01,100\n")
    with pytest.raises(ValueError, match="date"):
        load_prices(path)


def test_load_prices_rejects_non_numeric(tmp_path):
    path = tmp_path / "bad.csv"
    path.write_text("date,actif\n2024-01-01,abc\n")
    with pytest.raises(ValueError, match="non numériques"):
        load_prices(path)


def test_load_prices_rejects_negative_prices(tmp_path):
    path = tmp_path / "bad.csv"
    path.write_text("date,actif\n2024-01-01,-5\n")
    with pytest.raises(ValueError, match="positifs"):
        load_prices(path)
