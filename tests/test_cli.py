from marketsignal.cli import main
from marketsignal.data import generate_demo_prices


def test_demo_command(tmp_path):
    out = tmp_path / "demo.csv"
    assert main(["demo", "--out", str(out), "--days", "300"]) == 0
    assert out.exists()
    assert out.read_text().startswith("date,")


def test_analyze_command(tmp_path, capsys, demo_prices):
    path = tmp_path / "prices.csv"
    demo_prices.to_csv(path)
    assert main(["analyze", str(path)]) == 0
    captured = capsys.readouterr().out
    assert "Score de risque" in captured
    assert "Probabilité de crise" in captured
    assert "Alertes" in captured


def test_train_then_analyze_with_model(tmp_path, capsys, demo_prices):
    prices_path = tmp_path / "prices.csv"
    demo_prices.to_csv(prices_path)
    model_path = tmp_path / "model.json"

    assert main(["train", str(prices_path), "--model-out", str(model_path)]) == 0
    assert model_path.exists()

    assert main(["analyze", str(prices_path), "--model", str(model_path)]) == 0
    assert "Score de risque" in capsys.readouterr().out


def test_analyze_missing_file_fails(capsys):
    assert main(["analyze", "inexistant.csv"]) == 1
    assert "Erreur" in capsys.readouterr().err
