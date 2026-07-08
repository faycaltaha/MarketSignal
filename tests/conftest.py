import pytest

from marketsignal.data import generate_demo_prices


@pytest.fixture(scope="session")
def demo_prices():
    return generate_demo_prices(n_days=1200, n_assets=4, seed=7)
